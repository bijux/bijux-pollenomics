"""Reconcile categorical item identities without interpreting source display text."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256,
    SEAD_GOVERNED_ADMISSION_SHA256,
    SEAD_GOVERNED_BUILD_ID,
    SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
    SEAD_GOVERNED_PARENT_ADMISSION_SHA256,
    governed_sead_evidence_root,
)

from ..sead_analysis_numerical_values import _parts, _raw_table, _read_object
from .boolean_values import _canonical


def _item_relation(
    component: Mapping[str, Any],
    parent: Mapping[str, Any],
    items: Mapping[int, Mapping[str, Any]],
    classes: Mapping[int, Mapping[str, Any]],
    types: Mapping[int, Mapping[str, Any]],
) -> tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]]:
    """Require source keys and matching category types without coercing labels."""
    item_id = component["value_type_item_id"]
    class_id = parent["value_class_id"]
    if type(item_id) is not int or item_id not in items:
        raise ValueError("SEAD categorical item key is missing or invalid")
    if type(class_id) is not int or class_id not in classes:
        raise ValueError("SEAD categorical class key is missing or invalid")
    item, value_class = items[item_id], classes[class_id]
    type_id = value_class["value_type_id"]
    if (
        type(type_id) is not int
        or type_id not in types
        or type(item["value_type_id"]) is not int
        or item["value_type_id"] != type_id
        or types[type_id]["base_type"] != "category"
    ):
        raise ValueError("SEAD categorical item and class types differ")
    return item, value_class, types[type_id]


def _reconcile_parent(
    observation: Mapping[str, Any],
    parent: Mapping[str, Any],
    components: list[dict[str, Any]],
    parent_digest: str,
) -> None:
    parent_id = parent["analysis_value_id"]
    entity_id = parent["analysis_entity_id"]
    if (
        type(entity_id) is not int
        or entity_id <= 0
        or observation.get("entity_relation_id") != f"sead-analysis-entity:{entity_id}"
    ):
        raise ValueError("SEAD categorical parent entity relation differs")
    if (
        observation["source_table"] != "tbl_analysis_values"
        or observation["source_record_id"] != str(parent_id)
        or observation["source_payload_sha256"] != parent_digest
        or _canonical(observation["source_row"]) != _canonical(parent)
        or observation["source_value_field"] != "analysis_value"
        or _canonical(observation["source_value"])
        != _canonical(parent["analysis_value"])
        or observation["source_value_state"]
        != ("source_null" if parent["analysis_value"] is None else "reported")
        or _canonical(
            observation["source_components"]["tbl_analysis_categorical_values"]
        )
        != _canonical(components)
    ):
        raise ValueError(f"SEAD categorical parent or components differ: {parent_id}")
    if (
        observation["event_eligibility"] != "refused"
        or "source_classification_not_accepted"
        not in observation["event_refusal_reason_codes"]
    ):
        raise ValueError(f"SEAD categorical source refusal changed: {parent_id}")


def _reconcile_support(
    observation: Mapping[str, Any],
    parent: Mapping[str, Any],
    value_type: Mapping[str, Any],
    units: Mapping[int, Mapping[str, Any]],
) -> tuple[str, str]:
    semantics = observation["source_semantics"]
    unit_id = value_type["unit_id"]
    unit_status = (
        "source_native_linked" if unit_id in units else "not_exposed_by_relation"
    )
    if (
        semantics["value_semantics_id"]
        != f"sead-value-class:{parent['value_class_id']}"
        or semantics["source_unit_id"] != (unit_id if unit_id in units else None)
        or semantics["unit_status"] != unit_status
    ):
        raise ValueError("SEAD categorical unit semantics differ")
    link = observation["chronology_link"]
    entity_id = parent["analysis_entity_id"]
    if (
        type(entity_id) is not int
        or entity_id <= 0
        or observation.get("entity_relation_id") != f"sead-analysis-entity:{entity_id}"
        or link.get("entity_relation_id") != observation["entity_relation_id"]
    ):
        raise ValueError("SEAD categorical chronology entity relation differs")
    eligible, claims = link["eligible_claim_count"], link["claim_count"]
    if (
        type(eligible) is not int
        or type(claims) is not int
        or not 0 <= eligible <= claims
    ):
        raise ValueError("SEAD categorical chronology counts are invalid")
    status = (
        "direct_analysis_entity_eligible_claim"
        if eligible
        else "direct_analysis_entity_context_only"
        if claims
        else "unavailable_at_analysis_entity"
    )
    if (
        link["selection_rule"] != "same_analysis_entity_only"
        or link["status"] != status
    ):
        raise ValueError("SEAD categorical chronology support differs")
    return unit_status, status


def build_report(data_root: Path) -> dict[str, Any]:
    """Bind category, class and type relations to every staged parent."""
    normalized = governed_sead_evidence_root(data_root)
    manifest = _read_object(
        normalized / "evidence_materialization_manifest.json",
        SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
    )
    raw = data_root / "sead/raw/acquisitions" / SEAD_GOVERNED_EVIDENCE_RUN_ID
    admission = _read_object(raw / "admission.json", SEAD_GOVERNED_ADMISSION_SHA256)
    _read_object(raw / "manifest.json", SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256)
    for document, run_key in ((manifest, "source_run_id"), (admission, "run_id")):
        if (
            document[run_key] != SEAD_GOVERNED_EVIDENCE_RUN_ID
            or document["build_id"] != SEAD_GOVERNED_BUILD_ID
            or document["acquisition_manifest_sha256"]
            != SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256
            or document["parent_admission_sha256"]
            != SEAD_GOVERNED_PARENT_ADMISSION_SHA256
        ):
            raise ValueError("SEAD categorical source identity differs")
    files = {row["path"]: row for row in manifest["files"]}
    if len(files) != len(manifest["files"]):
        raise ValueError("SEAD materialization file identities repeat")
    native_path = "source_native_observations.json"
    native = _read_object(normalized / native_path, files[native_path]["sha256"])
    if (
        native["source_run_id"] != manifest["source_run_id"]
        or native["build_id"] != manifest["build_id"]
        or native["acquisition_manifest_sha256"]
        != manifest["acquisition_manifest_sha256"]
    ):
        raise ValueError("SEAD categorical observation identity differs")
    digests = native["source_table_sha256"]
    keys = {
        "tbl_analysis_values": "analysis_value_id",
        "tbl_analysis_categorical_values": "analysis_categorical_value_id",
        "tbl_value_type_items": "value_type_item_id",
        "tbl_value_classes": "value_class_id",
        "tbl_value_types": "value_type_id",
        "tbl_units": "unit_id",
    }
    tables = {
        table: _raw_table(raw, admission, table, key, digests[table])
        for table, key in keys.items()
    }
    parents = tables["tbl_analysis_values"]
    categories = tables["tbl_analysis_categorical_values"]
    if (
        len(parents) != native["observation_table_counts"]["tbl_analysis_values"]
        or len(categories)
        != native["component_table_counts"]["tbl_analysis_categorical_values"]
    ):
        raise ValueError("SEAD categorical source denominator differs")
    by_parent: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for component in categories.values():
        parent_id = component["analysis_value_id"]
        if type(parent_id) is not int or parent_id not in parents:
            raise ValueError("SEAD categorical component has no exact parent key")
        _item_relation(
            component,
            parents[parent_id],
            tables["tbl_value_type_items"],
            tables["tbl_value_classes"],
            tables["tbl_value_types"],
        )
        by_parent[parent_id].append(component)
    seen: set[int] = set()
    groups: Counter[tuple[int, int, str, str, str]] = Counter()
    chronology: Counter[str] = Counter()
    units: Counter[str] = Counter()
    display_match: Counter[str] = Counter()
    total = 0
    for observation in _parts(normalized, files, native, "observations"):
        total += 1
        if observation["source_table"] != "tbl_analysis_values":
            continue
        parent_id = int(observation["source_record_id"])
        if parent_id in seen or parent_id not in parents:
            raise ValueError("SEAD categorical parent repeats or is unknown")
        seen.add(parent_id)
        parent = parents[parent_id]
        components = by_parent.get(parent_id, [])
        _reconcile_parent(
            observation, parent, components, digests["tbl_analysis_values"]
        )
        for component in components:
            item, value_class, value_type = _item_relation(
                component,
                parent,
                tables["tbl_value_type_items"],
                tables["tbl_value_classes"],
                tables["tbl_value_types"],
            )
            unit_status, chronology_status = _reconcile_support(
                observation, parent, value_type, tables["tbl_units"]
            )
            units[unit_status] += 1
            chronology[chronology_status] += 1
            display_match[
                "equal" if parent["analysis_value"] == item["name"] else "different"
            ] += 1
            groups[
                (
                    value_class["value_class_id"],
                    item["value_type_item_id"],
                    _canonical(component["value"]),
                    _canonical(component["is_variant"]),
                    _canonical(parent["analysis_value"]),
                )
            ] += 1
    if seen != set(parents) or total != manifest["observation_count"]:
        raise ValueError("SEAD categorical observation population differs")
    if sum(groups.values()) != len(categories):
        raise ValueError("SEAD categorical component population differs")
    readset = {
        (raw / "admission.json")
        .relative_to(data_root)
        .as_posix(): SEAD_GOVERNED_ADMISSION_SHA256,
        (raw / "manifest.json")
        .relative_to(data_root)
        .as_posix(): SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256,
        (normalized / "evidence_materialization_manifest.json")
        .relative_to(data_root)
        .as_posix(): SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
        (normalized / native_path).relative_to(data_root).as_posix(): files[
            native_path
        ]["sha256"],
    }
    for table in keys:
        readset[(raw / f"payloads/{table}.json").relative_to(data_root).as_posix()] = (
            digests[table]
        )
    for part in native["partitioned_fields"]["observations"]["parts"]:
        readset[(normalized / part["path"]).relative_to(data_root).as_posix()] = part[
            "sha256"
        ]
    return {
        "schema_version": "sead-analysis-categorical-value-lineage.v1",
        "source_run_id": SEAD_GOVERNED_EVIDENCE_RUN_ID,
        "build_id": SEAD_GOVERNED_BUILD_ID,
        "raw_admission_sha256": SEAD_GOVERNED_ADMISSION_SHA256,
        "acquisition_manifest_sha256": SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256,
        "evidence_manifest_sha256": SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
        "raw_table_sha256": {name: digests[name] for name in keys},
        "source_observation_denominator": total,
        "parent_analysis_value_count": len(parents),
        "categorical_component_count": len(categories),
        "categorical_parent_count": len(by_parent),
        "parent_display_vs_item_name": dict(sorted(display_match.items())),
        "unit_status_counts": dict(sorted(units.items())),
        "chronology_status_counts": dict(sorted(chronology.items())),
        "value_groups": [
            {
                "value_class_id": cid,
                "value_class_name": tables["tbl_value_classes"][cid]["name"],
                "value_type_id": tables["tbl_value_type_items"][iid]["value_type_id"],
                "value_type_item_id": iid,
                "item_name": tables["tbl_value_type_items"][iid]["name"],
                "component_value": json.loads(value),
                "is_variant": json.loads(variant),
                "parent_display": json.loads(display),
                "row_count": count,
            }
            for (cid, iid, value, variant, display), count in sorted(groups.items())
        ],
        "source_readset_sha256": dict(sorted(readset.items())),
        "event_admission_status": "refused",
        "eligible_event_count": 0,
        "interpretation": "Source category item identities, nullable component fields and parent display text remain distinct. Source chronology context and unit relations do not admit ecological events or specimen/assay equivalence.",
    }


def run(repository: Path, output: Path) -> None:
    """Publish a compact source account only to an absent artifact file."""
    if not repository.is_absolute() or repository.resolve(strict=True) != repository:
        raise ValueError("A real absolute repository root is required")
    artifacts = repository / "artifacts"
    if (
        output.resolve() != output
        or not output.is_relative_to(artifacts)
        or output == artifacts
        or any(path.is_symlink() for path in (output, *output.parents))
    ):
        raise ValueError("A real repository artifact file is required")
    if output.exists():
        raise ValueError("SEAD categorical account output already exists")
    report = build_report(repository / "data")
    for relative, digest in report["source_readset_sha256"].items():
        source = repository / "data" / relative
        if source.resolve(strict=True) != source or not source.is_file():
            raise ValueError("SEAD categorical source must remain a real regular file")
        with source.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != digest:
                raise ValueError("SEAD categorical source changed before publication")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    """Reconcile categorical item identities without interpreting source display text."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
