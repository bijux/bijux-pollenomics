"""Reconcile native SEAD boolean components without admitting events."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from collections.abc import Mapping
import hashlib
import io
import json
from pathlib import Path
from typing import Any, TextIO

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
from .boolean_staging import BooleanStagingWriter, project_row


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _boolean_state(value: object) -> str:
    if value is None:
        return "source_null"
    if type(value) is not bool:
        raise ValueError("SEAD boolean component must retain bool or source null")
    return "true" if value else "false"


def _reconcile_component(
    observation: Mapping[str, Any],
    parent: Mapping[str, Any],
    components: list[dict[str, Any]],
    parent_digest: str,
    *,
    allow_missing_value: bool = False,
) -> None:
    parent_id = parent["analysis_value_id"]
    entity_id = parent["analysis_entity_id"]
    if type(entity_id) is not int or entity_id <= 0:
        raise ValueError(f"SEAD boolean parent entity key is invalid: {parent_id}")
    if (
        observation["source_table"] != "tbl_analysis_values"
        or observation["source_record_id"] != str(parent_id)
        or observation.get("entity_relation_id") != f"sead-analysis-entity:{entity_id}"
        or observation["source_payload_sha256"] != parent_digest
        or _canonical(observation["source_row"]) != _canonical(parent)
        or observation["source_value_field"] != "analysis_value"
        or _canonical(observation["source_value"])
        != _canonical(parent["analysis_value"])
        or observation["source_value_state"]
        != ("source_null" if parent["analysis_value"] is None else "reported")
    ):
        raise ValueError(f"SEAD boolean parent observation differs: {parent_id}")
    actual = observation["source_components"]["tbl_analysis_boolean_values"]
    if _canonical(actual) != _canonical(components):
        raise ValueError(f"SEAD boolean components differ: {parent_id}")
    for component in components:
        if "value" in component or not allow_missing_value:
            _boolean_state(component["value"])
    if (
        observation["event_eligibility"] != "refused"
        or "source_classification_not_accepted"
        not in observation["event_refusal_reason_codes"]
    ):
        raise ValueError(f"SEAD boolean source refusal changed: {parent_id}")


def build_report(
    data_root: Path, *, staging_stream: TextIO | None = None
) -> dict[str, Any]:
    """Bind all boolean components to their exact staged parent observations."""
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
            raise ValueError("SEAD boolean source identity differs")
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
        raise ValueError("SEAD boolean observation identity differs")
    digests = native["source_table_sha256"]
    parent_digest = digests["tbl_analysis_values"]
    parents = _raw_table(
        raw, admission, "tbl_analysis_values", "analysis_value_id", parent_digest
    )
    booleans = _raw_table(
        raw,
        admission,
        "tbl_analysis_boolean_values",
        "analysis_boolean_value_id",
        digests["tbl_analysis_boolean_values"],
    )
    if (
        len(parents) != native["observation_table_counts"]["tbl_analysis_values"]
        or len(booleans)
        != native["component_table_counts"]["tbl_analysis_boolean_values"]
    ):
        raise ValueError("SEAD boolean source denominator differs")
    by_parent: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for component in booleans.values():
        parent_id = component["analysis_value_id"]
        if type(parent_id) is not int or parent_id not in parents:
            raise ValueError("SEAD boolean component has no exact parent key")
        if "value" in component or staging_stream is None:
            _boolean_state(component["value"])
        by_parent[parent_id].append(component)
    writer = (
        BooleanStagingWriter(staging_stream) if staging_stream is not None else None
    )
    tables: dict[str, dict[int, dict[str, Any]]] = {}
    entities: dict[str, dict[str, Any]] = {}
    extra_readset: dict[str, str] = {}
    if writer is not None:
        keys = {
            "tbl_value_classes": "value_class_id",
            "tbl_value_types": "value_type_id",
            "tbl_units": "unit_id",
            "tbl_sites": "site_id",
        }
        tables = {
            table: _raw_table(raw, admission, table, key, digests[table])
            for table, key in keys.items()
        }
        relation_path = "observation_relation_index.json"
        relations = _read_object(
            normalized / relation_path, files[relation_path]["sha256"]
        )
        if any(
            relations["source_table_sha256"][table] != digests[table]
            for table in (*keys, "tbl_analysis_values", "tbl_analysis_boolean_values")
        ):
            raise ValueError("SEAD Boolean staging source relation identities differ")
        needed = {
            f"sead-analysis-entity:{parents[key]['analysis_entity_id']}"
            for key in by_parent
        }
        for entity in _parts(normalized, files, relations, "entity_relations"):
            key = entity["entity_relation_id"]
            if key in needed:
                if key in entities:
                    raise ValueError("SEAD Boolean staging duplicate entity key")
                entities[key] = entity
        if set(entities) != needed:
            raise ValueError("SEAD Boolean staging missing entity parent")
        for table in keys:
            extra_readset[
                (raw / f"payloads/{table}.json").relative_to(data_root).as_posix()
            ] = digests[table]
        extra_readset[
            (normalized / relation_path).relative_to(data_root).as_posix()
        ] = files[relation_path]["sha256"]
        for part in relations["partitioned_fields"]["entity_relations"]["parts"]:
            extra_readset[
                (normalized / part["path"]).relative_to(data_root).as_posix()
            ] = part["sha256"]
    seen: set[int] = set()
    counts: Counter[str] = Counter()
    displays: Counter[str] = Counter()
    class_counts: Counter[int] = Counter()
    groups: Counter[tuple[int, str, str]] = Counter()
    total = 0
    for observation in _parts(normalized, files, native, "observations"):
        total += 1
        if observation["source_table"] != "tbl_analysis_values":
            continue
        parent_id = int(observation["source_record_id"])
        if parent_id in seen or parent_id not in parents:
            raise ValueError("SEAD boolean parent observation repeats or is unknown")
        seen.add(parent_id)
        parent = parents[parent_id]
        components = by_parent.get(parent_id, [])
        _reconcile_component(
            observation,
            parent,
            components,
            parent_digest,
            allow_missing_value=writer is not None,
        )
        for component in components:
            state = (
                _boolean_state(component["value"])
                if "value" in component
                else "missing"
            )
            counts[state] += 1
            displays[_canonical(parent["analysis_value"])] += 1
            class_counts[parent["value_class_id"]] += 1
            groups[
                (
                    parent["value_class_id"],
                    state,
                    _canonical(parent["analysis_value"]),
                )
            ] += 1
            if writer is not None:
                value_class = tables["tbl_value_classes"].get(parent["value_class_id"])
                value_type = (
                    None
                    if value_class is None
                    else tables["tbl_value_types"].get(value_class["value_type_id"])
                )
                entity = entities[observation["entity_relation_id"]]
                site = tables["tbl_sites"].get(entity["site_id"])
                if value_class is None or value_type is None or site is None:
                    raise ValueError(
                        "SEAD Boolean staging missing class, type or site parent"
                    )
                writer.append(
                    project_row(
                        component,
                        parent,
                        observation,
                        entity,
                        site,
                        value_class,
                        value_type,
                        tables["tbl_units"],
                    )
                )
    if seen != set(parents) or total != manifest["observation_count"]:
        raise ValueError("SEAD boolean observation population differs")
    if sum(counts.values()) != len(booleans):
        raise ValueError("SEAD boolean component population differs")
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
    for table in ("tbl_analysis_boolean_values", "tbl_analysis_values"):
        readset[(raw / f"payloads/{table}.json").relative_to(data_root).as_posix()] = (
            digests[table]
        )
    for part in native["partitioned_fields"]["observations"]["parts"]:
        readset[(normalized / part["path"]).relative_to(data_root).as_posix()] = part[
            "sha256"
        ]
    report = {
        "schema_version": "sead-analysis-boolean-value-lineage.v1",
        "source_run_id": SEAD_GOVERNED_EVIDENCE_RUN_ID,
        "build_id": SEAD_GOVERNED_BUILD_ID,
        "raw_admission_sha256": SEAD_GOVERNED_ADMISSION_SHA256,
        "acquisition_manifest_sha256": SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256,
        "evidence_manifest_sha256": SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256,
        "raw_table_sha256": {
            name: digests[name]
            for name in ("tbl_analysis_boolean_values", "tbl_analysis_values")
        },
        "source_observation_denominator": total,
        "parent_analysis_value_count": len(parents),
        "boolean_value_count": len(booleans),
        "boolean_parent_count": len(by_parent),
        "boolean_value_states": dict(sorted(counts.items())),
        "parent_display_counts": dict(sorted(displays.items())),
        "value_class_counts": {str(k): v for k, v in sorted(class_counts.items())},
        "value_groups": [
            {
                "value_class_id": class_id,
                "boolean_state": state,
                "parent_value": json.loads(display),
                "row_count": count,
            }
            for (class_id, state, display), count in sorted(groups.items())
        ],
        "source_readset_sha256": dict(sorted(readset.items())),
        "event_admission_status": "refused",
        "eligible_event_count": 0,
        "interpretation": "Typed source flags and parent display text remain distinct; no ecological, presence/absence, chronology or route interpretation is admitted.",
    }
    if writer is not None:
        if len(writer.identities) != len(booleans):
            raise ValueError("SEAD Boolean staging component population differs")
        readset.update(extra_readset)
        report["source_readset_sha256"] = dict(sorted(readset.items()))
        report["typed_staging"] = writer.account()
    return report


def run(repository: Path, output: Path, *, rows_output: Path | None = None) -> None:
    """Write one compact account to an absent repository artifact file."""
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
        raise ValueError("SEAD boolean account output already exists")
    if rows_output is not None:
        if (
            rows_output.parent != output.parent
            or rows_output == output
            or rows_output.suffix != ".csv"
            or rows_output.resolve() != rows_output
            or any(path.is_symlink() for path in (rows_output, *rows_output.parents))
        ):
            raise ValueError(
                "SEAD Boolean rows must be a distinct real sibling CSV artifact"
            )
        if rows_output.exists():
            raise ValueError("SEAD Boolean rows output already exists")
    staged_csv = io.StringIO(newline="")
    report = (
        build_report(repository / "data", staging_stream=staged_csv)
        if rows_output is not None
        else build_report(repository / "data")
    )
    for relative, digest in report["source_readset_sha256"].items():
        source = repository / "data" / relative
        if source.resolve(strict=True) != source or not source.is_file():
            raise ValueError("SEAD boolean source must remain a real regular file")
        with source.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != digest:
                raise ValueError("SEAD boolean source changed before publication")
    output.parent.mkdir(parents=True, exist_ok=True)
    if rows_output is not None:
        report["typed_staging"]["rows_file"] = rows_output.name
        with rows_output.open("x", encoding="utf-8", newline="") as rows:
            rows.write(staged_csv.getvalue())
    with output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    """Parse command-line inputs and reconcile native SEAD boolean components without admitting events."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rows-output", type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output, rows_output=args.rows_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
