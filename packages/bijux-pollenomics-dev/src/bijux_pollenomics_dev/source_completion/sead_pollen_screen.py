"""Screen source-native SEAD observations in pollen-named datasets."""

from __future__ import annotations

import argparse
from collections.abc import Iterator
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_BUILD_ID,
    SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
    SEAD_GOVERNED_PARENT_ADMISSION_SHA256,
    governed_sead_evidence_root,
)

CSV_FIELDS = (
    "observation_id",
    "source_table",
    "source_record_id",
    "dataset_id",
    "source_dataset_name",
    "country_code",
    "site_id",
    "site_uuid",
    "sample_group_id",
    "physical_sample_id",
    "analysis_entity_id",
    "taxon_relation_id",
    "source_value_json",
    "source_value_state",
    "source_unit_id",
    "chronology_link_status",
    "eligible_claim_count",
    "source_claim_ids_json",
    "refusal_reason_codes_json",
)


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _read_object(path: Path, expected_sha256: str) -> dict[str, Any]:
    content = path.read_bytes()
    if _sha(content) != expected_sha256:
        raise ValueError(f"SEAD source digest differs: {path}")
    value = json.loads(content)
    if not isinstance(value, dict):
        raise ValueError(f"SEAD source document is not an object: {path}")
    return cast(dict[str, Any], value)


def _parts(
    root: Path,
    manifest_files: dict[str, dict[str, Any]],
    document: dict[str, Any],
    field: str,
) -> Iterator[dict[str, Any]]:
    partition = document["partitioned_fields"][field]
    row_count = 0
    for part in partition["parts"]:
        relative = part["path"]
        record = manifest_files.get(relative)
        if record is None or record["sha256"] != part["sha256"]:
            raise ValueError(f"SEAD part lacks matching manifest identity: {relative}")
        payload = _read_object(root / relative, part["sha256"])
        chunk = payload[field]
        if not isinstance(chunk, list) or len(chunk) != part["row_count"]:
            raise ValueError(f"SEAD part row count differs: {relative}")
        row_count += len(chunk)
        yield from cast(list[dict[str, Any]], chunk)
    if row_count != partition["row_count"]:
        raise ValueError(f"SEAD {field} denominator differs")


def _refusal_reasons(observation: dict[str, Any]) -> list[str]:
    """Keep source refusals and add the unreviewed proxy-name boundary."""
    reasons = set(observation["event_refusal_reason_codes"])
    reasons.add("dataset_name_does_not_certify_pollen_proxy")
    if observation["chronology_link"]["eligible_claim_count"] == 0:
        reasons.add("eligible_chronology_claim_unavailable_at_analysis_entity")
    if observation["source_semantics"]["source_unit_id"] is None:
        reasons.add("source_unit_unavailable")
    return sorted(reasons)


def build_screen(data_root: Path) -> tuple[dict[str, Any], str]:
    """Return a source-bound refusal report and sample-level native export."""
    root = governed_sead_evidence_root(data_root)
    manifest = _read_object(
        root / "evidence_materialization_manifest.json",
        SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    )
    if (
        manifest["source_run_id"] != SEAD_GOVERNED_EVIDENCE_RUN_ID
        or manifest["build_id"] != SEAD_GOVERNED_BUILD_ID
        or manifest["parent_admission_sha256"] != SEAD_GOVERNED_PARENT_ADMISSION_SHA256
    ):
        raise ValueError("SEAD source run/build/raw-parent identity differs")
    files = {record["path"]: record for record in manifest["files"]}
    if len(files) != len(manifest["files"]):
        raise ValueError("SEAD materialization file identities repeat")

    def document(name: str) -> dict[str, Any]:
        record = files[name]
        return _read_object(root / name, record["sha256"])

    relations = document("observation_relation_index.json")
    native = document("source_native_observations.json")
    dataset_names: dict[str, str] = {}
    for row in _parts(root, files, relations, "dataset_semantics"):
        dataset_id = row["dataset_semantics_id"]
        name = str(row["dataset"]["dataset_name"])
        if dataset_id in dataset_names and dataset_names[dataset_id] != name:
            raise ValueError(
                f"SEAD dataset identity has conflicting names: {dataset_id}"
            )
        dataset_names[dataset_id] = name
    candidate_datasets = {
        key: name for key, name in dataset_names.items() if "pollen" in name.casefold()
    }
    candidate_rows: list[dict[str, Any]] = []
    observed_ids: set[str] = set()
    observation_count = 0
    for row in _parts(root, files, native, "observations"):
        observation_count += 1
        observation_id = row["observation_id"]
        if observation_id in observed_ids:
            raise ValueError(f"SEAD observation identity repeats: {observation_id}")
        observed_ids.add(observation_id)
        dataset_id = row["source_semantics"]["dataset_semantics_id"]
        if dataset_id in candidate_datasets:
            candidate_rows.append(row)
    if observation_count != manifest["observation_count"]:
        raise ValueError("SEAD observation total differs from governed manifest")

    needed_entities = {row["entity_relation_id"] for row in candidate_rows}
    entities: dict[str, dict[str, Any]] = {}
    for row in _parts(root, files, relations, "entity_relations"):
        key = row["entity_relation_id"]
        if key in needed_entities:
            if key in entities:
                raise ValueError(f"SEAD analysis entity repeats: {key}")
            entities[key] = row
    if set(entities) != needed_entities:
        raise ValueError("SEAD candidate observation lacks an analysis entity")

    counts: Counter[str] = Counter()
    countries: Counter[str] = Counter()
    tables: Counter[str] = Counter()
    sites: set[str] = set()
    samples: set[str] = set()
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in sorted(candidate_rows, key=lambda item: item["observation_id"]):
        entity = entities[row["entity_relation_id"]]
        dataset_id = row["source_semantics"]["dataset_semantics_id"]
        if dataset_id != f"sead-dataset:{entity['dataset_id']}":
            raise ValueError("SEAD observation and entity dataset identities differ")
        if row["country_code"] != entity["country_code"]:
            raise ValueError("SEAD observation and entity country identities differ")
        chronology = row["chronology_link"]
        source_claim_ids = entity["chronology_link"]["claim_ids"]
        if chronology["claim_count"] != len(source_claim_ids):
            raise ValueError("SEAD observation and entity chronology links differ")
        reasons = _refusal_reasons(row)
        counts.update(reasons)
        countries[row["country_code"]] += 1
        tables[row["source_table"]] += 1
        sites.add(str(entity["site_id"]))
        if entity["physical_sample_id"] is not None:
            samples.add(str(entity["physical_sample_id"]))
        writer.writerow(
            {
                "observation_id": row["observation_id"],
                "source_table": row["source_table"],
                "source_record_id": row["source_record_id"],
                "dataset_id": entity["dataset_id"],
                "source_dataset_name": candidate_datasets[dataset_id],
                "country_code": row["country_code"],
                "site_id": entity["site_id"],
                "site_uuid": entity["site_uuid"],
                "sample_group_id": entity["sample_group_id"],
                "physical_sample_id": entity["physical_sample_id"],
                "analysis_entity_id": entity["analysis_entity_id"],
                "taxon_relation_id": row["taxon_relation_id"],
                "source_value_json": json.dumps(
                    row["source_value"], ensure_ascii=False
                ),
                "source_value_state": row["source_value_state"],
                "source_unit_id": row["source_semantics"]["source_unit_id"],
                "chronology_link_status": chronology["status"],
                "eligible_claim_count": chronology["eligible_claim_count"],
                "source_claim_ids_json": json.dumps(source_claim_ids),
                "refusal_reason_codes_json": json.dumps(reasons),
            }
        )
    csv_text = output.getvalue()
    report = {
        "schema_version": "sead-pollen-named-dataset-screen.v1",
        "source_run_id": manifest["source_run_id"],
        "build_id": manifest["build_id"],
        "parent_admission_sha256": manifest["parent_admission_sha256"],
        "evidence_manifest_sha256": SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
        "screen_rule": "dataset_name_contains_pollen_case_insensitive; proxy identity is unconfirmed",
        "source_observation_denominator": observation_count,
        "pollen_named_dataset_count": len(candidate_datasets),
        "candidate_observation_count": len(candidate_rows),
        "candidate_site_count": len(sites),
        "candidate_physical_sample_count": len(samples),
        "country_observation_counts": dict(sorted(countries.items())),
        "source_table_observation_counts": dict(sorted(tables.items())),
        "refusal_reason_counts": dict(sorted(counts.items())),
        "admitted_pollen_time_series_count": 0,
        "admitted_lra_sample_count": 0,
        "admission_status": "refused",
        "admission_note": "A pollen word in a dataset name does not identify a pollen proxy, counted grain unit, accepted taxon classification, or sample-owned chronology.",
        "sample_observation_csv": "sample-observations.csv",
        "sample_observation_csv_sha256": _sha(csv_text.encode("utf-8")),
    }
    if len(candidate_rows) != sum(countries.values()) or len(candidate_rows) != sum(
        tables.values()
    ):
        raise ValueError("SEAD candidate denominators do not reconcile")
    return report, csv_text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = cast(Path, args.output)
    if output.exists():
        raise ValueError(f"SEAD screen output already exists: {output}")
    report, csv_text = build_screen(cast(Path, args.data_root))
    output.mkdir(parents=True)
    (output / "sample-observations.csv").write_text(csv_text, encoding="utf-8")
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "candidate_observation_count",
                    "pollen_named_dataset_count",
                    "admitted_pollen_time_series_count",
                    "admitted_lra_sample_count",
                )
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
