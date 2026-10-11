"""Publish source-bound SEAD numerical analysis values without event admission."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Iterator, Mapping
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256,
    SEAD_GOVERNED_ADMISSION_SHA256,
    SEAD_GOVERNED_BUILD_ID,
    SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
    SEAD_GOVERNED_PARENT_ADMISSION_SHA256,
    governed_sead_evidence_root,
)

CSV_FIELDS = (
    "analysis_numerical_value_id",
    "analysis_value_id",
    "observation_id",
    "site_id",
    "site_uuid",
    "country_code",
    "sample_group_id",
    "physical_sample_id",
    "analysis_entity_id",
    "dataset_id",
    "value_class_id",
    "value_class_name",
    "value_type_id",
    "value_type_name",
    "value_type_base_type",
    "value_type_unit_id",
    "value_semantics_id",
    "typed_value_json",
    "typed_value_state",
    "parent_value_json",
    "parent_value_state",
    "parent_parse_state",
    "value_comparison",
    "qualifier_json",
    "is_variant_json",
    "source_unit_id",
    "unit_status",
    "chronology_link_status",
    "eligible_claim_count",
    "event_eligibility",
    "event_refusal_reason_codes_json",
    "numerical_source_row_json",
    "parent_source_row_json",
    "value_class_source_row_json",
    "value_type_source_row_json",
)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_object(path: Path, digest: str) -> dict[str, Any]:
    payload = path.read_bytes()
    if _sha(payload) != digest:
        raise ValueError(f"SEAD source digest differs: {path}")
    document = json.loads(payload)
    if not isinstance(document, dict):
        raise ValueError(f"SEAD source document is not an object: {path}")
    return cast(dict[str, Any], document)


def _parts(
    root: Path,
    files: Mapping[str, Mapping[str, Any]],
    document: Mapping[str, Any],
    field: str,
) -> Iterator[dict[str, Any]]:
    partition = document["partitioned_fields"][field]
    count = 0
    for part in partition["parts"]:
        relative = part["path"]
        record = files.get(relative)
        if record is None or record["sha256"] != part["sha256"]:
            raise ValueError(f"SEAD part lacks matching manifest identity: {relative}")
        payload = _read_object(root / relative, part["sha256"])
        rows = payload[field]
        if not isinstance(rows, list) or len(rows) != part["row_count"]:
            raise ValueError(f"SEAD part row count differs: {relative}")
        count += len(rows)
        yield from cast(list[dict[str, Any]], rows)
    if count != partition["row_count"]:
        raise ValueError(f"SEAD {field} denominator differs")


def _raw_table(
    raw_root: Path,
    admission: Mapping[str, Any],
    table: str,
    key: str,
    expected_digest: str,
) -> dict[int, dict[str, Any]]:
    relative = f"payloads/{table}.json"
    records = [item for item in admission["copied_files"] if item["path"] == relative]
    if len(records) != 1 or records[0]["sha256"] != expected_digest:
        raise ValueError(f"SEAD raw admission does not bind {table}")
    document = _read_object(raw_root / relative, expected_digest)
    if document["table"] != table or not isinstance(document["rows"], list):
        raise ValueError(f"SEAD raw table identity differs: {table}")
    result: dict[int, dict[str, Any]] = {}
    for row in document["rows"]:
        source_id = row[key]
        if isinstance(source_id, bool) or not isinstance(source_id, int):
            raise ValueError(f"SEAD raw key is invalid: {table}")
        if source_id in result:
            raise ValueError(f"SEAD raw key repeats: {table}:{source_id}")
        result[source_id] = row
    return result


def _value_states(
    numerical: Mapping[str, Any], parent: Mapping[str, Any]
) -> tuple[str, str, str, str]:
    typed = numerical["value"]
    source_text = parent["analysis_value"]
    typed_state = "source_null" if typed is None else "reported"
    parent_state = "source_null" if source_text is None else "reported"
    if source_text is None:
        return typed_state, parent_state, "source_null", "not_comparable"
    try:
        parsed = Decimal(str(source_text))
    except InvalidOperation:
        return typed_state, parent_state, "parse_failed", "not_comparable"
    if not parsed.is_finite():
        return typed_state, parent_state, "parse_failed", "not_comparable"
    if typed is None:
        return typed_state, parent_state, "parsed_numeric", "not_comparable"
    if isinstance(typed, bool) or not isinstance(typed, int | float):
        raise ValueError("SEAD typed numerical value is not numeric or null")
    typed_decimal = Decimal(str(typed))
    if not typed_decimal.is_finite():
        raise ValueError("SEAD typed numerical value is not finite")
    comparison = "numeric_equal" if typed_decimal == parsed else "precision_difference"
    return typed_state, parent_state, "parsed_numeric", comparison


def _reconcile_component(
    observation: Mapping[str, Any],
    numerical: Mapping[str, Any],
    parent: Mapping[str, Any],
    parent_digest: str,
) -> None:
    parent_id = parent["analysis_value_id"]
    if (
        observation["source_table"] != "tbl_analysis_values"
        or observation["source_record_id"] != str(parent_id)
        or observation["source_payload_sha256"] != parent_digest
        or observation["source_row"] != parent
        or observation["source_value_field"] != "analysis_value"
        or observation["source_value"] != parent["analysis_value"]
        or observation["source_value_state"]
        != ("source_null" if parent["analysis_value"] is None else "reported")
    ):
        raise ValueError(f"SEAD parent observation differs from raw: {parent_id}")
    components = observation["source_components"]["tbl_analysis_numerical_values"]
    if components != [numerical]:
        raise ValueError(f"SEAD numerical component differs from raw: {parent_id}")
    if observation["event_eligibility"] != "refused" or (
        "source_classification_not_accepted"
        not in observation["event_refusal_reason_codes"]
    ):
        raise ValueError(f"SEAD source refusal changed: {parent_id}")


def build_report(data_root: Path) -> tuple[dict[str, Any], str]:
    """Reconcile every typed numerical component to admitted raw and public rows."""
    normalized_root = governed_sead_evidence_root(data_root)
    manifest = _read_object(
        normalized_root / "evidence_materialization_manifest.json",
        SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    )
    if (
        manifest["source_run_id"] != SEAD_GOVERNED_EVIDENCE_RUN_ID
        or manifest["build_id"] != SEAD_GOVERNED_BUILD_ID
        or manifest["parent_admission_sha256"] != SEAD_GOVERNED_PARENT_ADMISSION_SHA256
        or manifest["acquisition_manifest_sha256"]
        != SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256
    ):
        raise ValueError("SEAD normalized source identity differs")
    files = {record["path"]: record for record in manifest["files"]}
    if len(files) != len(manifest["files"]):
        raise ValueError("SEAD materialization file identities repeat")
    native = _read_object(
        normalized_root / "source_native_observations.json",
        files["source_native_observations.json"]["sha256"],
    )
    relations = _read_object(
        normalized_root / "observation_relation_index.json",
        files["observation_relation_index.json"]["sha256"],
    )
    numerical_digest = native["source_table_sha256"]["tbl_analysis_numerical_values"]
    parent_digest = native["source_table_sha256"]["tbl_analysis_values"]
    class_digest = native["source_table_sha256"]["tbl_value_classes"]
    type_digest = native["source_table_sha256"]["tbl_value_types"]
    if (
        relations["source_table_sha256"]["tbl_analysis_numerical_values"]
        != numerical_digest
        or relations["source_table_sha256"]["tbl_analysis_values"] != parent_digest
        or relations["source_table_sha256"]["tbl_value_classes"] != class_digest
        or relations["source_table_sha256"]["tbl_value_types"] != type_digest
    ):
        raise ValueError("SEAD normalized table digests disagree")
    raw_root = (
        data_root / "sead" / "raw" / "acquisitions" / SEAD_GOVERNED_EVIDENCE_RUN_ID
    )
    admission = _read_object(
        raw_root / "admission.json", SEAD_GOVERNED_ADMISSION_SHA256
    )
    if (
        admission["run_id"] != SEAD_GOVERNED_EVIDENCE_RUN_ID
        or admission["build_id"] != SEAD_GOVERNED_BUILD_ID
        or admission["parent_admission_sha256"] != SEAD_GOVERNED_PARENT_ADMISSION_SHA256
        or admission["acquisition_manifest_sha256"]
        != SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256
    ):
        raise ValueError("SEAD raw admission identity differs")
    numerical_rows = _raw_table(
        raw_root,
        admission,
        "tbl_analysis_numerical_values",
        "analysis_numerical_value_id",
        numerical_digest,
    )
    parent_rows = _raw_table(
        raw_root, admission, "tbl_analysis_values", "analysis_value_id", parent_digest
    )
    value_classes = _raw_table(
        raw_root, admission, "tbl_value_classes", "value_class_id", class_digest
    )
    value_types = _raw_table(
        raw_root, admission, "tbl_value_types", "value_type_id", type_digest
    )
    if (
        len(numerical_rows)
        != relations["source_table_counts"]["tbl_analysis_numerical_values"]
        or len(parent_rows) != relations["source_table_counts"]["tbl_analysis_values"]
        or len(value_classes) != relations["source_table_counts"]["tbl_value_classes"]
        or len(value_types) != relations["source_table_counts"]["tbl_value_types"]
    ):
        raise ValueError("SEAD raw table denominators differ")
    parent_ids = {row["analysis_value_id"] for row in numerical_rows.values()}
    if len(parent_ids) != len(numerical_rows) or not parent_ids <= parent_rows.keys():
        raise ValueError("SEAD numerical parent keys repeat or are missing")
    observations: dict[int, dict[str, Any]] = {}
    observation_count = 0
    for row in _parts(normalized_root, files, native, "observations"):
        observation_count += 1
        if row["source_table"] != "tbl_analysis_values":
            continue
        source_id = int(row["source_record_id"])
        if source_id in parent_ids:
            if source_id in observations:
                raise ValueError(f"SEAD parent observation repeats: {source_id}")
            observations[source_id] = row
    if (
        observation_count != manifest["observation_count"]
        or set(observations) != parent_ids
    ):
        raise ValueError("SEAD numerical observations do not reconcile")
    entity_ids = {row["entity_relation_id"] for row in observations.values()}
    entities: dict[str, dict[str, Any]] = {}
    for row in _parts(normalized_root, files, relations, "entity_relations"):
        entity_id = row["entity_relation_id"]
        if entity_id in entity_ids:
            if entity_id in entities:
                raise ValueError(f"SEAD entity repeats: {entity_id}")
            entities[entity_id] = row
    if set(entities) != entity_ids:
        raise ValueError("SEAD numerical entity relation is missing")
    represented_class_ids = {
        parent_rows[parent_id]["value_class_id"] for parent_id in parent_ids
    }
    value_semantics: dict[int, dict[str, Any]] = {}
    for row in _parts(normalized_root, files, relations, "value_semantics"):
        class_id = row["value_class"]["value_class_id"]
        if class_id in represented_class_ids:
            if class_id in value_semantics:
                raise ValueError(f"SEAD value semantics repeat: {class_id}")
            value_semantics[class_id] = row
    if set(value_semantics) != represented_class_ids:
        raise ValueError("SEAD numerical value class semantics are missing")

    counts: Counter[str] = Counter()
    states: Counter[str] = Counter()
    class_counts: Counter[int] = Counter()
    unit_status_counts: Counter[str] = Counter()
    sites: set[int] = set()
    samples: set[int] = set()
    datasets: set[int] = set()
    represented_type_ids: set[int] = set()
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for numerical_id, numerical in sorted(numerical_rows.items()):
        parent_id = numerical["analysis_value_id"]
        parent = parent_rows[parent_id]
        observation = observations[parent_id]
        _reconcile_component(observation, numerical, parent, parent_digest)
        entity = entities[observation["entity_relation_id"]]
        class_id = parent["value_class_id"]
        value_class = value_classes.get(class_id)
        if value_class is None:
            raise ValueError(f"SEAD numerical value class is missing: {class_id}")
        type_id = value_class["value_type_id"]
        value_type = value_types.get(type_id)
        if value_type is None:
            raise ValueError(f"SEAD numerical value type is missing: {type_id}")
        semantic = value_semantics[class_id]
        if (
            entity["analysis_entity_id"] != parent["analysis_entity_id"]
            or entity["country_code"] != observation["country_code"]
            or observation["source_semantics"]["value_semantics_id"]
            != f"sead-value-class:{parent['value_class_id']}"
            or observation["source_semantics"]["dataset_semantics_id"]
            != f"sead-dataset:{entity['dataset_id']}"
            or semantic["value_semantics_id"] != f"sead-value-class:{class_id}"
            or semantic["value_class"] != value_class
            or semantic["source_value_type"] != value_type
            or observation["source_semantics"]["source_unit_id"]
            != value_type["unit_id"]
        ):
            raise ValueError(f"SEAD numerical relation differs: {numerical_id}")
        typed_state, parent_state, parse_state, comparison = _value_states(
            numerical, parent
        )
        chronology = observation["chronology_link"]
        sites.add(entity["site_id"])
        samples.add(entity["physical_sample_id"])
        datasets.add(entity["dataset_id"])
        represented_type_ids.add(type_id)
        class_counts[class_id] += 1
        unit_status_counts[observation["source_semantics"]["unit_status"]] += 1
        counts[comparison] += 1
        states[f"typed:{typed_state}"] += 1
        states[f"parent:{parent_state}"] += 1
        states[f"parent_parse:{parse_state}"] += 1
        writer.writerow(
            {
                "analysis_numerical_value_id": numerical_id,
                "analysis_value_id": parent_id,
                "observation_id": observation["observation_id"],
                "site_id": entity["site_id"],
                "site_uuid": entity["site_uuid"],
                "country_code": entity["country_code"],
                "sample_group_id": entity["sample_group_id"],
                "physical_sample_id": entity["physical_sample_id"],
                "analysis_entity_id": entity["analysis_entity_id"],
                "dataset_id": entity["dataset_id"],
                "value_class_id": class_id,
                "value_class_name": value_class["name"],
                "value_type_id": type_id,
                "value_type_name": value_type["name"],
                "value_type_base_type": value_type["base_type"],
                "value_type_unit_id": value_type["unit_id"],
                "value_semantics_id": observation["source_semantics"][
                    "value_semantics_id"
                ],
                "typed_value_json": json.dumps(numerical["value"]),
                "typed_value_state": typed_state,
                "parent_value_json": json.dumps(parent["analysis_value"]),
                "parent_value_state": parent_state,
                "parent_parse_state": parse_state,
                "value_comparison": comparison,
                "qualifier_json": json.dumps(numerical["qualifier"]),
                "is_variant_json": json.dumps(numerical["is_variant"]),
                "source_unit_id": observation["source_semantics"]["source_unit_id"],
                "unit_status": observation["source_semantics"]["unit_status"],
                "chronology_link_status": chronology["status"],
                "eligible_claim_count": chronology["eligible_claim_count"],
                "event_eligibility": observation["event_eligibility"],
                "event_refusal_reason_codes_json": json.dumps(
                    observation["event_refusal_reason_codes"]
                ),
                "numerical_source_row_json": json.dumps(numerical, sort_keys=True),
                "parent_source_row_json": json.dumps(parent, sort_keys=True),
                "value_class_source_row_json": json.dumps(value_class, sort_keys=True),
                "value_type_source_row_json": json.dumps(value_type, sort_keys=True),
            }
        )
    csv_text = output.getvalue()
    report = {
        "schema_version": "sead-analysis-numerical-value-lineage.v1",
        "source_run_id": SEAD_GOVERNED_EVIDENCE_RUN_ID,
        "build_id": SEAD_GOVERNED_BUILD_ID,
        "raw_admission_sha256": SEAD_GOVERNED_ADMISSION_SHA256,
        "parent_admission_sha256": SEAD_GOVERNED_PARENT_ADMISSION_SHA256,
        "acquisition_manifest_sha256": SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256,
        "evidence_manifest_sha256": SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
        "raw_numerical_payload_sha256": numerical_digest,
        "raw_parent_payload_sha256": parent_digest,
        "raw_value_class_payload_sha256": class_digest,
        "raw_value_type_payload_sha256": type_digest,
        "source_observation_denominator": observation_count,
        "numerical_value_count": len(numerical_rows),
        "parent_analysis_value_count": len(parent_ids),
        "site_count": len(sites),
        "physical_sample_count": len(samples),
        "dataset_count": len(datasets),
        "value_class_count": len(represented_class_ids),
        "value_type_count": len(represented_type_ids),
        "value_classes": [
            {
                "value_class_id": class_id,
                "name": value_classes[class_id]["name"],
                "row_count": class_counts[class_id],
                "value_type_id": value_classes[class_id]["value_type_id"],
                "value_type_name": value_types[
                    value_classes[class_id]["value_type_id"]
                ]["name"],
                "source_unit_id": value_types[value_classes[class_id]["value_type_id"]][
                    "unit_id"
                ],
            }
            for class_id in sorted(represented_class_ids)
        ],
        "source_unit_status_counts": dict(sorted(unit_status_counts.items())),
        "site_ids": sorted(sites),
        "value_comparison_counts": dict(sorted(counts.items())),
        "value_state_counts": dict(sorted(states.items())),
        "event_admission_status": "refused",
        "eligible_event_count": 0,
        "interpretation": "Typed source numerical values and parent display strings are retained separately. Differences in precision are source facts, not conversion errors or approved scientific measurements.",
        "values_csv": "values.csv",
        "values_csv_sha256": _sha(csv_text.encode("utf-8")),
    }
    return report, csv_text


def main() -> None:
    """Write a deterministic public review of typed SEAD numerical values."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = cast(Path, args.output)
    if output.exists():
        raise ValueError(f"SEAD numerical report output already exists: {output}")
    report, csv_text = build_report(cast(Path, args.data_root))
    output.mkdir(parents=True)
    (output / "values.csv").write_text(csv_text, encoding="utf-8")
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "numerical_value_count": report["numerical_value_count"],
                "value_comparison_counts": report["value_comparison_counts"],
                "eligible_event_count": report["eligible_event_count"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
