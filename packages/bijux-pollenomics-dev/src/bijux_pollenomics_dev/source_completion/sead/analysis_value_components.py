"""Reconcile every SEAD analysis-value parent to its native typed components."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Iterable, Mapping
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
from typing import Any

from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256,
    SEAD_GOVERNED_ADMISSION_SHA256,
    SEAD_GOVERNED_BUILD_ID,
    SEAD_GOVERNED_COUNTRY_DECISIONS_SHA256,
    SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
    SEAD_GOVERNED_PARENT_ADMISSION_SHA256,
    governed_sead_evidence_root,
)
from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from ..sead_country_source_units import _indexed, _required_parent
from .boolean_values import _canonical

TABLE_KEYS = {
    "tbl_sites": "site_id",
    "tbl_sample_groups": "sample_group_id",
    "tbl_physical_samples": "physical_sample_id",
    "tbl_analysis_entities": "analysis_entity_id",
    "tbl_analysis_values": "analysis_value_id",
    "tbl_analysis_integer_values": "analysis_integer_value_id",
    "tbl_analysis_numerical_values": "analysis_numerical_value_id",
    "tbl_analysis_boolean_values": "analysis_boolean_value_id",
    "tbl_analysis_categorical_values": "analysis_categorical_value_id",
    "tbl_value_classes": "value_class_id",
    "tbl_value_types": "value_type_id",
    "tbl_units": "unit_id",
}
KINDS = {
    "tbl_analysis_integer_values": "integer",
    "tbl_analysis_numerical_values": "numerical",
    "tbl_analysis_boolean_values": "boolean",
    "tbl_analysis_categorical_values": "categorical",
}
COUNTRIES = {"SE", "DK", "NO", "FI"}
CSV_FIELDS = (
    "country_code",
    "component_kind",
    "parent_value_state",
    "value_class_id",
    "value_class_name",
    "value_type_id",
    "value_type_name",
    "source_unit_id",
    "source_unit_name",
    "unit_status",
    "parent_count",
)


def _sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _read(root: Path, relative: str, expected: str) -> dict[str, Any]:
    """Read a real confined source file with its expected byte identity."""
    path = root / relative
    if path.resolve(strict=True) != path or not path.is_file():
        raise ValueError(f"SEAD source path is not real: {relative}")
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != expected:
        raise ValueError(f"SEAD source identity differs: {relative}")
    document = json.loads(payload)
    if not isinstance(document, dict):
        raise ValueError(f"SEAD source document is not an object: {relative}")
    return document


def _source_rows(
    tables: Mapping[str, list[dict[str, Any]]],
    decisions: list[dict[str, Any]],
    observations: Iterable[dict[str, Any]],
    parent_digest: str,
) -> tuple[list[dict[str, Any]], dict[str, Any], int]:
    """Refuse every orphan, overlap, or unaccounted analysis-value parent."""
    indexed = {
        name: _indexed(tables[name], key, name) for name, key in TABLE_KEYS.items()
    }
    sites = indexed["tbl_sites"]
    groups = indexed["tbl_sample_groups"]
    samples = indexed["tbl_physical_samples"]
    entities = indexed["tbl_analysis_entities"]
    parents = indexed["tbl_analysis_values"]
    classes = indexed["tbl_value_classes"]
    types = indexed["tbl_value_types"]
    units = indexed["tbl_units"]
    by_decision = _indexed(decisions, "site_id", "country decisions")
    site_country: dict[int, str] = {}
    for site_id, site in sites.items():
        decision = by_decision.get(site_id)
        if (
            decision is None
            or decision["site_uuid"] != site["site_uuid"]
            or decision["decision"]["decision_status"] != "assigned"
            or decision["decision"]["decision_method"] != "strict_boundary_containment"
            or decision["governed_country_code"] not in COUNTRIES
        ):
            raise ValueError(f"SEAD governed country decision differs: {site_id}")
        site_country[site_id] = decision["governed_country_code"]
    group_site = {
        key: _required_parent(row, "site_id", sites) for key, row in groups.items()
    }
    sample_site = {
        key: group_site[_required_parent(row, "sample_group_id", groups)]
        for key, row in samples.items()
    }
    entity_site = {
        key: sample_site[_required_parent(row, "physical_sample_id", samples)]
        for key, row in entities.items()
    }
    parent_country = {
        key: site_country[
            entity_site[_required_parent(row, "analysis_entity_id", entities)]
        ]
        for key, row in parents.items()
    }
    components: dict[int, tuple[str, dict[str, Any]]] = {}
    for table, kind in KINDS.items():
        for row in indexed[table].values():
            parent_id = row.get("analysis_value_id")
            if type(parent_id) is not int or parent_id not in parents:
                raise ValueError(f"SEAD {kind} component has no exact parent")
            if parent_id in components:
                raise ValueError(
                    f"SEAD analysis-value parent has overlapping components: {parent_id}"
                )
            components[parent_id] = (kind, row)
    counts: Counter[tuple[str, str, str, int, int, int | None, str]] = Counter()
    seen: set[int] = set()
    observation_count = 0
    for observation in observations:
        observation_count += 1
        if observation["source_table"] != "tbl_analysis_values":
            continue
        source_id = observation["source_record_id"]
        if (
            not isinstance(source_id, str)
            or not source_id.isdecimal()
            or str(int(source_id)) != source_id
        ):
            raise ValueError("SEAD parent observation key is not canonical")
        parent_id = int(source_id)
        if parent_id in seen or parent_id not in parents:
            raise ValueError(
                f"SEAD parent observation repeats or is unknown: {parent_id}"
            )
        seen.add(parent_id)
        parent = parents[parent_id]
        kind, component = components.get(parent_id, ("untyped_source_text", {}))
        for table, table_kind in KINDS.items():
            expected = [component] if kind == table_kind else []
            if _canonical(observation["source_components"][table]) != _canonical(
                expected
            ):
                raise ValueError(f"SEAD parent component relation differs: {parent_id}")
        class_id = _required_parent(parent, "value_class_id", classes)
        value_class = classes[class_id]
        type_id = _required_parent(value_class, "value_type_id", types)
        value_type = types[type_id]
        unit_id = value_type["unit_id"]
        if unit_id is not None and (type(unit_id) is not int or unit_id not in units):
            raise ValueError(f"SEAD source unit key is invalid: {class_id}")
        unit_status = (
            "source_native_linked" if unit_id is not None else "not_exposed_by_relation"
        )
        country = parent_country[parent_id]
        semantics = observation["source_semantics"]
        if (
            observation["source_payload_sha256"] != parent_digest
            or observation["entity_relation_id"]
            != f"sead-analysis-entity:{parent['analysis_entity_id']}"
            or _canonical(observation["source_row"]) != _canonical(parent)
            or _canonical(observation["source_value"])
            != _canonical(parent["analysis_value"])
            or observation["source_value_state"]
            != ("source_null" if parent["analysis_value"] is None else "reported")
            or observation["country_code"] != country
            or semantics["value_semantics_id"] != f"sead-value-class:{class_id}"
            or _canonical(semantics["source_unit_id"]) != _canonical(unit_id)
            or semantics["unit_status"] != unit_status
            or observation["event_eligibility"] != "refused"
            or "source_classification_not_accepted"
            not in observation["event_refusal_reason_codes"]
        ):
            raise ValueError(f"SEAD parent source lineage differs: {parent_id}")
        state = "source_null" if parent["analysis_value"] is None else "reported"
        counts[(country, kind, state, class_id, type_id, unit_id, unit_status)] += 1
    if seen != set(parents):
        raise ValueError("SEAD source analysis-value population does not close")
    rows = [
        {
            "country_code": country,
            "component_kind": kind,
            "parent_value_state": state,
            "value_class_id": class_id,
            "value_class_name": classes[class_id]["name"],
            "value_type_id": type_id,
            "value_type_name": types[type_id]["name"],
            "source_unit_id": unit_id,
            "source_unit_name": units[unit_id]["unit_name"]
            if unit_id is not None
            else None,
            "unit_status": unit_status,
            "parent_count": count,
        }
        for (
            country,
            kind,
            state,
            class_id,
            type_id,
            unit_id,
            unit_status,
        ), count in sorted(
            counts.items(), key=lambda item: tuple(str(part) for part in item[0])
        )
    ]
    typed = Counter(kind for _, kind, *_ in counts.elements())
    summary = {
        "parent_count": len(parents),
        "typed_parent_count": len(components),
        "untyped_parent_count": len(parents) - len(components),
        "component_counts": dict(sorted(typed.items())),
        "country_parent_counts": dict(sorted(Counter(parent_country.values()).items())),
        "unit_status_counts": dict(
            sorted(
                Counter(
                    row["unit_status"]
                    for row in rows
                    for _ in range(row["parent_count"])
                ).items()
            )
        ),
    }
    return rows, summary, observation_count


def build_report(repository: Path) -> tuple[dict[str, Any], bytes]:
    """Read pinned raw and materialized source bytes and produce a compact census."""
    data_root = repository / "data"
    raw = data_root / "sead/raw/acquisitions" / SEAD_GOVERNED_EVIDENCE_RUN_ID
    normalized = governed_sead_evidence_root(data_root)
    readset: dict[str, str] = {}

    def read(path: Path, expected: str) -> dict[str, Any]:
        relative = path.relative_to(repository).as_posix()
        readset[relative] = expected
        return _read(repository, relative, expected)

    admission = read(raw / "admission.json", SEAD_GOVERNED_ADMISSION_SHA256)
    read(raw / "manifest.json", SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256)
    decisions = read(
        raw / "country-decisions.json", SEAD_GOVERNED_COUNTRY_DECISIONS_SHA256
    )
    manifest = read(
        normalized / "evidence_materialization_manifest.json",
        SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    )
    if (
        admission["run_id"] != SEAD_GOVERNED_EVIDENCE_RUN_ID
        or manifest["source_run_id"] != SEAD_GOVERNED_EVIDENCE_RUN_ID
        or admission["build_id"] != SEAD_GOVERNED_BUILD_ID
        or manifest["build_id"] != SEAD_GOVERNED_BUILD_ID
        or admission["parent_admission_sha256"] != SEAD_GOVERNED_PARENT_ADMISSION_SHA256
        or manifest["parent_admission_sha256"] != SEAD_GOVERNED_PARENT_ADMISSION_SHA256
        or admission["acquisition_manifest_sha256"]
        != SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256
        or manifest["acquisition_manifest_sha256"]
        != SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256
    ):
        raise ValueError("SEAD source snapshot identity differs")
    records = {row["path"]: row for row in manifest["files"]}
    if len(records) != len(manifest["files"]):
        raise ValueError("SEAD materialization file identities repeat")
    native = read(
        normalized / "source_native_observations.json",
        records["source_native_observations.json"]["sha256"],
    )
    if (
        native["source_run_id"] != manifest["source_run_id"]
        or native["build_id"] != manifest["build_id"]
    ):
        raise ValueError("SEAD native observation snapshot differs")
    copied = {row["path"]: row for row in admission["copied_files"]}
    if len(copied) != len(admission["copied_files"]):
        raise ValueError("SEAD raw admission input identities repeat")
    tables = {}
    for table in TABLE_KEYS:
        relative = f"payloads/{table}.json"
        expected = native["source_table_sha256"][table]
        if copied[relative]["sha256"] != expected:
            raise ValueError(f"SEAD raw table admission differs: {table}")
        document = read(raw / relative, expected)
        rows = document["rows"]
        if (
            document["table"] != table
            or not isinstance(rows, list)
            or len(rows) != native["source_table_counts"][table]
        ):
            raise ValueError(f"SEAD raw table denominator differs: {table}")
        tables[table] = rows

    def observations() -> Iterable[dict[str, Any]]:
        part = native["partitioned_fields"]["observations"]
        count = 0
        for item in part["parts"]:
            relative = item["path"]
            if records[relative]["sha256"] != item["sha256"]:
                raise ValueError(f"SEAD native part identity differs: {relative}")
            document = read(normalized / relative, item["sha256"])
            rows = document["observations"]
            if not isinstance(rows, list) or len(rows) != item["row_count"]:
                raise ValueError(f"SEAD native part population differs: {relative}")
            count += len(rows)
            yield from rows
        if count != part["row_count"]:
            raise ValueError("SEAD native observation denominator differs")

    rows, summary, seen_observations = _source_rows(
        tables,
        decisions["decisions"],
        observations(),
        native["source_table_sha256"]["tbl_analysis_values"],
    )
    if (
        seen_observations != manifest["observation_count"]
        or summary["parent_count"] != 68705
        or summary["typed_parent_count"] != 41164
        or summary["untyped_parent_count"] != 27541
        or summary["component_counts"]
        != {
            "boolean": 11603,
            "categorical": 4800,
            "integer": 24701,
            "numerical": 60,
            "untyped_source_text": 27541,
        }
    ):
        raise ValueError("SEAD source component census denominator differs")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    csv_bytes = stream.getvalue().encode()
    report = {
        "schema_version": "sead-analysis-value-component-closure.v1",
        "source_run_id": SEAD_GOVERNED_EVIDENCE_RUN_ID,
        "build_id": SEAD_GOVERNED_BUILD_ID,
        "raw_admission_sha256": SEAD_GOVERNED_ADMISSION_SHA256,
        "evidence_manifest_sha256": SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
        "source_readset_sha256": dict(sorted(readset.items())),
        "source_observation_denominator": seen_observations,
        "summary": summary,
        "rows_csv_sha256": hashlib.sha256(csv_bytes).hexdigest(),
        "row_count": len(rows),
        "event_admission_status": "refused",
        "eligible_event_count": 0,
        "interpretation": "Source-native analysis-value component and unit linkage census; untyped parent text is preserved as untyped, never inferred as a measure or ecological event.",
    }
    return report, csv_bytes


def run(repository: Path, output: Path) -> dict[str, Any]:
    """Publish compact JSON and CSV only after a stable source readset is proved."""
    if not repository.is_absolute() or repository.resolve(strict=True) != repository:
        raise ValueError("A real absolute repository root is required")
    destination = require_absent_artifact_output(repository, output)
    stage = require_absent_artifact_output(
        repository, output.with_name(output.name + ".stage")
    )
    report, csv_bytes = build_report(repository)
    stage.mkdir()
    try:
        (stage / "report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n"
        )
        (stage / "rows.csv").write_bytes(csv_bytes)
        for relative, expected in report["source_readset_sha256"].items():
            source = repository / relative
            if (
                source.resolve(strict=True) != source
                or not source.is_file()
                or _sha(source) != expected
            ):
                raise ValueError(f"SEAD source changed before publication: {relative}")
        require_absent_artifact_output(repository, destination)
        stage.rename(destination)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return report


def main(argv: list[str] | None = None) -> int:
    """Write the source-bound SEAD analysis-value component census."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
