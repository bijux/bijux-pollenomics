"""Reconcile governed SEAD integer components with their parent observations."""

from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
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

from .sead_analysis_numerical_values import _parts, _raw_table, _read_object


def _value_states(
    integer: dict[str, Any], parent: dict[str, Any]
) -> tuple[str, str, str]:
    typed = integer["value"]
    source_text = parent["analysis_value"]
    if typed is not None and (isinstance(typed, bool) or not isinstance(typed, int)):
        raise ValueError("SEAD typed integer is neither an integer nor source null")
    typed_state = "source_null" if typed is None else "reported"
    if source_text is None:
        return typed_state, "source_null", "not_comparable"
    try:
        parsed = Decimal(str(source_text))
    except InvalidOperation:
        return typed_state, "parse_failed", "not_comparable"
    if not parsed.is_finite():
        return typed_state, "parse_failed", "not_comparable"
    if typed is None:
        return typed_state, "parsed_numeric", "not_comparable"
    return (
        typed_state,
        "parsed_numeric",
        "numeric_equal" if parsed == typed else "numeric_difference",
    )


def _reconcile_component(
    observation: dict[str, Any],
    integer: dict[str, Any],
    parent: dict[str, Any],
    digest: str,
) -> None:
    parent_id = parent["analysis_value_id"]
    if (
        observation["source_table"] != "tbl_analysis_values"
        or observation["source_record_id"] != str(parent_id)
        or observation["source_payload_sha256"] != digest
        or observation["source_row"] != parent
        or observation["source_value_field"] != "analysis_value"
        or observation["source_value"] != parent["analysis_value"]
        or observation["source_value_state"]
        != ("source_null" if parent["analysis_value"] is None else "reported")
    ):
        raise ValueError(f"SEAD parent observation differs from raw: {parent_id}")
    if observation["source_components"]["tbl_analysis_integer_values"] != [integer]:
        raise ValueError(f"SEAD integer component differs from raw: {parent_id}")
    if observation["event_eligibility"] != "refused" or (
        "source_classification_not_accepted"
        not in observation["event_refusal_reason_codes"]
    ):
        raise ValueError(f"SEAD source refusal changed: {parent_id}")


def _chronology_role(class_id: int) -> str:
    if class_id in {12, 13}:
        return "inferred_growth_year_bound"
    if class_id in {10, 11}:
        return "tree_age_bound"
    if class_id == 2:
        return "tree_ring_count"
    return "other_source_count"


def build_report(data_root: Path) -> dict[str, Any]:
    """Verify every admitted integer row and summarize its source-bound lineage."""
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
    tables = (
        ("tbl_analysis_integer_values", "analysis_integer_value_id"),
        ("tbl_analysis_values", "analysis_value_id"),
        ("tbl_value_classes", "value_class_id"),
        ("tbl_value_types", "value_type_id"),
    )
    digests = {name: native["source_table_sha256"][name] for name, _ in tables}
    if any(
        relations["source_table_sha256"][name] != digests[name] for name, _ in tables
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
    rows = {
        name: _raw_table(raw_root, admission, name, key, digests[name])
        for name, key in tables
    }
    if any(
        len(rows[name]) != relations["source_table_counts"][name] for name, _ in tables
    ):
        raise ValueError("SEAD raw table denominators differ")
    integers = rows["tbl_analysis_integer_values"]
    parents = rows["tbl_analysis_values"]
    classes = rows["tbl_value_classes"]
    types = rows["tbl_value_types"]
    parent_ids = {row["analysis_value_id"] for row in integers.values()}
    if len(parent_ids) != len(integers) or not parent_ids <= parents.keys():
        raise ValueError("SEAD integer parent keys repeat or are missing")
    observations: dict[int, dict[str, Any]] = {}
    observation_count = 0
    for row in _parts(normalized_root, files, native, "observations"):
        observation_count += 1
        if row["source_table"] == "tbl_analysis_values":
            source_id = int(row["source_record_id"])
            if source_id in parent_ids:
                if source_id in observations:
                    raise ValueError(f"SEAD parent observation repeats: {source_id}")
                observations[source_id] = row
    if (
        observation_count != manifest["observation_count"]
        or set(observations) != parent_ids
    ):
        raise ValueError("SEAD integer observations do not reconcile")
    entity_ids = {row["entity_relation_id"] for row in observations.values()}
    entities: dict[str, dict[str, Any]] = {}
    for row in _parts(normalized_root, files, relations, "entity_relations"):
        entity_id = row["entity_relation_id"]
        if entity_id in entity_ids:
            if entity_id in entities:
                raise ValueError(f"SEAD entity repeats: {entity_id}")
            entities[entity_id] = row
    if set(entities) != entity_ids:
        raise ValueError("SEAD integer entity relation is missing")
    class_ids = {parents[parent_id]["value_class_id"] for parent_id in parent_ids}
    semantics: dict[int, dict[str, Any]] = {}
    for row in _parts(normalized_root, files, relations, "value_semantics"):
        class_id = row["value_class"]["value_class_id"]
        if class_id in class_ids:
            if class_id in semantics:
                raise ValueError(f"SEAD value semantics repeat: {class_id}")
            semantics[class_id] = row
    if set(semantics) != class_ids:
        raise ValueError("SEAD integer value class semantics are missing")

    class_counts: Counter[int] = Counter()
    role_counts: Counter[str] = Counter()
    comparisons: Counter[str] = Counter()
    class_comparisons: dict[int, Counter[str]] = {
        class_id: Counter() for class_id in class_ids
    }
    states: Counter[str] = Counter()
    chronology_counts: Counter[str] = Counter()
    unit_counts: Counter[str] = Counter()
    sites: set[int] = set()
    samples: set[int] = set()
    datasets: set[int] = set()
    represented_types: set[int] = set()
    nonmatching_values: list[dict[str, Any]] = []
    parse_failure_examples: list[dict[str, Any]] = []
    for integer_id, integer in sorted(integers.items()):
        parent_id = integer["analysis_value_id"]
        parent = parents[parent_id]
        observation = observations[parent_id]
        _reconcile_component(
            observation, integer, parent, digests["tbl_analysis_values"]
        )
        entity = entities[observation["entity_relation_id"]]
        class_id = parent["value_class_id"]
        value_class = classes.get(class_id)
        if value_class is None:
            raise ValueError(f"SEAD integer value class is missing: {class_id}")
        type_id = value_class["value_type_id"]
        value_type = types.get(type_id)
        if value_type is None:
            raise ValueError(f"SEAD integer value type is missing: {type_id}")
        semantic = semantics[class_id]
        source_semantic = observation["source_semantics"]
        if (
            entity["analysis_entity_id"] != parent["analysis_entity_id"]
            or entity["country_code"] != observation["country_code"]
            or source_semantic["value_semantics_id"] != f"sead-value-class:{class_id}"
            or source_semantic["dataset_semantics_id"]
            != f"sead-dataset:{entity['dataset_id']}"
            or semantic["value_semantics_id"] != f"sead-value-class:{class_id}"
            or semantic["value_class"] != value_class
            or semantic["source_value_type"] != value_type
            or source_semantic["source_unit_id"] != value_type["unit_id"]
        ):
            raise ValueError(f"SEAD integer relation differs: {integer_id}")
        typed_state, parse_state, comparison = _value_states(integer, parent)
        class_counts[class_id] += 1
        role_counts[_chronology_role(class_id)] += 1
        comparisons[comparison] += 1
        class_comparisons[class_id][comparison] += 1
        if comparison == "numeric_difference":
            nonmatching_values.append(
                {
                    "analysis_integer_value_id": integer_id,
                    "analysis_value_id": parent_id,
                    "typed_value": integer["value"],
                    "parent_value": parent["analysis_value"],
                }
            )
        if parse_state == "parse_failed" and len(parse_failure_examples) < 10:
            parse_failure_examples.append(
                {
                    "analysis_integer_value_id": integer_id,
                    "analysis_value_id": parent_id,
                    "typed_value": integer["value"],
                    "parent_value": parent["analysis_value"],
                }
            )
        states[f"typed:{typed_state}"] += 1
        states[
            f"parent:{'source_null' if parent['analysis_value'] is None else 'reported'}"
        ] += 1
        states[f"parent_parse:{parse_state}"] += 1
        chronology_counts[observation["chronology_link"]["status"]] += 1
        unit_counts[source_semantic["unit_status"]] += 1
        sites.add(entity["site_id"])
        samples.add(entity["physical_sample_id"])
        datasets.add(entity["dataset_id"])
        represented_types.add(type_id)
    return {
        "schema_version": "sead-analysis-integer-value-lineage.v1",
        "source_run_id": SEAD_GOVERNED_EVIDENCE_RUN_ID,
        "build_id": SEAD_GOVERNED_BUILD_ID,
        "raw_admission_sha256": SEAD_GOVERNED_ADMISSION_SHA256,
        "parent_admission_sha256": SEAD_GOVERNED_PARENT_ADMISSION_SHA256,
        "acquisition_manifest_sha256": SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256,
        "evidence_manifest_sha256": SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
        "raw_table_sha256": dict(sorted(digests.items())),
        "source_observation_denominator": observation_count,
        "integer_value_count": len(integers),
        "parent_analysis_value_count": len(parent_ids),
        "site_count": len(sites),
        "physical_sample_count": len(samples),
        "dataset_count": len(datasets),
        "value_class_count": len(class_ids),
        "value_type_count": len(represented_types),
        "chronology_role_counts": dict(sorted(role_counts.items())),
        "chronology_link_status_counts": dict(sorted(chronology_counts.items())),
        "source_unit_status_counts": dict(sorted(unit_counts.items())),
        "value_comparison_counts": dict(sorted(comparisons.items())),
        "nonmatching_values": nonmatching_values,
        "parse_failure_examples": parse_failure_examples,
        "value_state_counts": dict(sorted(states.items())),
        "value_classes": [
            {
                "value_class_id": class_id,
                "name": classes[class_id]["name"],
                "chronology_role": _chronology_role(class_id),
                "row_count": class_counts[class_id],
                "value_comparison_counts": dict(
                    sorted(class_comparisons[class_id].items())
                ),
                "value_type_id": classes[class_id]["value_type_id"],
                "value_type_name": types[classes[class_id]["value_type_id"]]["name"],
                "source_unit_id": types[classes[class_id]["value_type_id"]]["unit_id"],
            }
            for class_id in sorted(class_ids)
        ],
        "public_consumer": {
            "surface": "SEAD atlas source-native observation table",
            "locator": "source_native_observations.json#observation_id={observation_id}",
            "exposed_value": "parent tbl_analysis_values.analysis_value",
            "typed_component_exposed": False,
        },
        "event_admission_status": "refused",
        "eligible_event_count": 0,
    }


def main() -> None:
    """Write a deterministic compact public summary of integer source lineage."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = cast(Path, args.output)
    if output.exists():
        raise ValueError(f"SEAD integer report output already exists: {output}")
    report = build_report(cast(Path, args.data_root))
    output.mkdir(parents=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "integer_value_count": report["integer_value_count"],
                "value_comparison_counts": report["value_comparison_counts"],
                "eligible_event_count": 0,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
