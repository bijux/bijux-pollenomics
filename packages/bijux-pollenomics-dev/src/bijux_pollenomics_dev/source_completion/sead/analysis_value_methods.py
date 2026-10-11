"""Project source-declared methods and types onto governed SEAD component counts."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
from typing import Any

from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_ADMISSION_SHA256,
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
)
from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from .analysis_value_components import CSV_FIELDS, _read

CENSUS_ROOT = Path("docs/report/source-relations/sead/analysis-value-components")
CENSUS_REPORT_SHA256 = (
    "b7c62ea8f3552f0e50e5d55aa0091a8485eafb5ad0c012641e8f1b53f92b784f"
)
CENSUS_ROWS_SHA256 = "c935541d8da42d7cdfd9308ec6343349380ef3b8e682912eed32f67ab2a92cce"
METHODS_MEMBER = "payloads/tbl_methods.json"
METHODS_SHA256 = "a47ab8d9d2952945e5e9ba64173ae31e85497f2a99702ae87b7752c0b3724da6"
GROUP_FIELDS = (
    "country_code",
    "parent_value_state",
    "component_kind",
    "source_method_id",
    "source_method_name",
    "value_class_id",
    "value_class_name",
    "value_type_id",
    "value_type_name",
    "declared_base_type",
    "source_unit_id",
    "parent_count",
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _index(document: dict[str, Any], key: str, table: str) -> dict[int, dict[str, Any]]:
    if document.get("table") != table or not isinstance(document.get("rows"), list):
        raise ValueError(f"invalid source definition table: {table}")
    result: dict[int, dict[str, Any]] = {}
    for row in document["rows"]:
        if not isinstance(row, dict) or type(row.get(key)) is not int:
            raise ValueError(f"invalid {table} identity")
        identity = row[key]
        if identity in result:
            raise ValueError(f"duplicate {table} identity: {identity}")
        result[identity] = row
    return result


def _require_methods_member(
    admission: dict[str, Any], manifest: dict[str, Any]
) -> None:
    """Authenticate the method table against both admission and capture manifest."""
    copied = {row["path"]: row for row in admission["copied_files"]}
    captured = {row["path"]: row for row in manifest["files"]}
    member = copied.get(METHODS_MEMBER)
    if (
        len(copied) != len(admission["copied_files"])
        or len(captured) != len(manifest["files"])
        or member is None
        or captured.get(METHODS_MEMBER) != member
        or member
        != {"path": METHODS_MEMBER, "sha256": METHODS_SHA256, "byte_count": 10954}
    ):
        raise ValueError("raw method table custody differs")


def project(
    census: dict[str, Any],
    census_rows: list[dict[str, str]],
    classes_doc: dict[str, Any],
    types_doc: dict[str, Any],
    methods_doc: dict[str, Any],
    units_doc: dict[str, Any],
) -> dict[str, Any]:
    """Refuse incomplete class/type/method/unit joins and return count-only groups."""
    if census.get("schema_version") != "sead-analysis-value-component-closure.v1":
        raise ValueError("unexpected upstream census schema")
    classes = _index(classes_doc, "value_class_id", "tbl_value_classes")
    types = _index(types_doc, "value_type_id", "tbl_value_types")
    methods = _index(methods_doc, "method_id", "tbl_methods")
    units = _index(units_doc, "unit_id", "tbl_units")
    expected_columns = {
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
    }
    counts: Counter[
        tuple[str, str, str, int, str, int, str, int, str, str, int | None]
    ] = Counter()
    seen: set[tuple[str, ...]] = set()
    component_counts: Counter[str] = Counter()
    unit_counts: Counter[str] = Counter()
    country_counts: Counter[str] = Counter()
    method_counts: Counter[int] = Counter()
    linked_untyped_count = 0
    for row in census_rows:
        if set(row) != expected_columns:
            raise ValueError("upstream census columns differ")
        identity = tuple(
            row[column] for column in sorted(expected_columns - {"parent_count"})
        )
        if identity in seen:
            raise ValueError("duplicate upstream census group")
        seen.add(identity)
        try:
            count = int(row["parent_count"])
            class_id = int(row["value_class_id"])
            type_id = int(row["value_type_id"])
        except ValueError as exc:
            raise ValueError("noninteger census count or identity") from exc
        if (
            count <= 0
            or str(count) != row["parent_count"]
            or str(class_id) != row["value_class_id"]
            or str(type_id) != row["value_type_id"]
        ):
            raise ValueError("noncanonical upstream count or identity")
        value_class = classes.get(class_id)
        value_type = types.get(type_id)
        if value_class is None or value_type is None:
            raise ValueError("missing declared value class or type")
        if (
            type(value_class.get("value_type_id")) is not int
            or value_class["value_type_id"] != type_id
            or value_class.get("name") != row["value_class_name"]
            or value_type.get("name") != row["value_type_name"]
        ):
            raise ValueError("upstream class/type declaration differs")
        method_id = value_class.get("method_id")
        if type(method_id) is not int or method_id not in methods:
            raise ValueError("missing source method definition")
        source_unit_id = value_type.get("unit_id")
        if source_unit_id is None:
            if (
                row["source_unit_id"]
                or row["source_unit_name"]
                or row["unit_status"] != "not_exposed_by_relation"
            ):
                raise ValueError("unit absence differs from source definition")
        elif (
            type(source_unit_id) is not int
            or source_unit_id not in units
            or row["source_unit_id"] != str(source_unit_id)
            or row["source_unit_name"] != units[source_unit_id]["unit_name"]
            or row["unit_status"] != "source_native_linked"
        ):
            raise ValueError("source unit definition differs")
        if row["parent_value_state"] not in {"reported", "source_null"}:
            raise ValueError("invalid source value state")
        kind = row["component_kind"]
        if kind not in {
            "boolean",
            "categorical",
            "integer",
            "numerical",
            "untyped_source_text",
        }:
            raise ValueError("invalid typed component state")
        base_type = value_type.get("base_type")
        if not isinstance(base_type, str) or not base_type:
            raise ValueError("missing declared base type")
        country = row["country_code"]
        if country != "SE":
            raise ValueError("unexpected country in governed census")
        component_counts[kind] += count
        unit_counts[row["unit_status"]] += count
        country_counts[country] += count
        if kind == "untyped_source_text":
            method_counts[method_id] += count
            if source_unit_id is not None:
                linked_untyped_count += count
            counts[
                (
                    country,
                    row["parent_value_state"],
                    kind,
                    method_id,
                    methods[method_id]["method_name"],
                    class_id,
                    value_class["name"],
                    type_id,
                    value_type["name"],
                    base_type,
                    source_unit_id,
                )
            ] += count
    summary = census.get("summary")
    if not isinstance(summary, dict) or (
        dict(component_counts) != summary.get("component_counts")
        or dict(unit_counts) != summary.get("unit_status_counts")
        or dict(country_counts) != summary.get("country_parent_counts")
        or sum(component_counts.values()) != summary.get("parent_count")
        or component_counts["untyped_source_text"]
        != summary.get("untyped_parent_count")
        or sum(
            count
            for kind, count in component_counts.items()
            if kind != "untyped_source_text"
        )
        != summary.get("typed_parent_count")
        or len(census_rows) != census.get("row_count")
    ):
        raise ValueError("upstream census totals differ")
    groups = [
        {
            "country_code": country,
            "parent_value_state": state,
            "component_kind": kind,
            "source_method_id": method_id,
            "source_method_name": method_name,
            "value_class_id": class_id,
            "value_class_name": class_name,
            "value_type_id": type_id,
            "value_type_name": type_name,
            "declared_base_type": base_type,
            "source_unit_id": unit_id,
            "parent_count": count,
        }
        for (
            country,
            state,
            kind,
            method_id,
            method_name,
            class_id,
            class_name,
            type_id,
            type_name,
            base_type,
            unit_id,
        ), count in sorted(counts.items())
    ]
    return {
        "schema_version": "sead-untyped-method-coverage.v1",
        "upstream_parent_count": summary["parent_count"],
        "untyped_parent_count": summary["untyped_parent_count"],
        "source_method_counts": {
            str(k): count for k, count in sorted(method_counts.items())
        },
        "source_unit_linked_untyped_count": linked_untyped_count,
        "groups": groups,
        "interpretation": "Absent typed component, with source-declared class/type/method preserved; no measurement or ecological eligibility inferred.",
        "eligible_event_count": 0,
    }


def build_report(repository: Path) -> tuple[dict[str, Any], bytes]:
    """Bind a compact upstream census to raw method, class, type and unit definitions."""
    raw = Path("data/sead/raw/acquisitions") / SEAD_GOVERNED_EVIDENCE_RUN_ID
    report = _read(
        repository, (CENSUS_ROOT / "report.json").as_posix(), CENSUS_REPORT_SHA256
    )
    csv_path = CENSUS_ROOT / "rows.csv"
    if (repository / csv_path).resolve(strict=True) != repository / csv_path:
        raise ValueError("upstream census CSV escapes repository")
    census_bytes = (repository / csv_path).read_bytes()
    if (
        _sha(census_bytes) != CENSUS_ROWS_SHA256
        or report.get("rows_csv_sha256") != CENSUS_ROWS_SHA256
    ):
        raise ValueError("upstream census CSV identity differs")
    if (
        report.get("source_run_id") != SEAD_GOVERNED_EVIDENCE_RUN_ID
        or report.get("raw_admission_sha256") != SEAD_GOVERNED_ADMISSION_SHA256
    ):
        raise ValueError("upstream census source admission differs")
    readset = report.get("source_readset_sha256")
    if not isinstance(readset, dict):
        raise ValueError("upstream census source readset is missing")
    admission_relative = (raw / "admission.json").as_posix()
    manifest_relative = (raw / "manifest.json").as_posix()
    if readset.get(admission_relative) != SEAD_GOVERNED_ADMISSION_SHA256:
        raise ValueError("upstream source admission readset differs")
    admission = _read(repository, admission_relative, SEAD_GOVERNED_ADMISSION_SHA256)
    manifest = _read(repository, manifest_relative, readset[manifest_relative])
    if (
        admission.get("run_id") != SEAD_GOVERNED_EVIDENCE_RUN_ID
        or admission.get("acquisition_manifest_sha256") != readset[manifest_relative]
        or manifest.get("status") != "complete"
    ):
        raise ValueError("raw source custody differs")
    _require_methods_member(admission, manifest)
    source_readset = {
        (CENSUS_ROOT / "report.json").as_posix(): CENSUS_REPORT_SHA256,
        csv_path.as_posix(): CENSUS_ROWS_SHA256,
        admission_relative: SEAD_GOVERNED_ADMISSION_SHA256,
        manifest_relative: readset[manifest_relative],
    }
    definitions: dict[str, dict[str, Any]] = {}
    for label in ("tbl_value_classes", "tbl_value_types", "tbl_units", "tbl_methods"):
        relative = (raw / f"payloads/{label}.json").as_posix()
        expected = METHODS_SHA256 if label == "tbl_methods" else readset.get(relative)
        if not isinstance(expected, str):
            raise ValueError(f"upstream definition absent from readset: {label}")
        source_readset[relative] = expected
        definitions[label] = _read(repository, relative, expected)
    rows = list(csv.DictReader(io.StringIO(census_bytes.decode("utf-8"))))
    if not rows or set(rows[0]) != set(CSV_FIELDS):
        raise ValueError("upstream census CSV columns differ")
    result = project(
        report,
        rows,
        definitions["tbl_value_classes"],
        definitions["tbl_value_types"],
        definitions["tbl_methods"],
        definitions["tbl_units"],
    )
    if (
        result["source_method_counts"] != {"10": 27451, "175": 90}
        or result["source_unit_linked_untyped_count"] != 12508
    ):
        raise ValueError("source method or unit population differs")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=GROUP_FIELDS, lineterminator="\n")
    writer.writeheader()
    grouped_rows = result.pop("groups")
    writer.writerows(grouped_rows)
    grouped_bytes = stream.getvalue().encode()
    result.update(
        {
            "source_run_id": SEAD_GOVERNED_EVIDENCE_RUN_ID,
            "raw_admission_sha256": SEAD_GOVERNED_ADMISSION_SHA256,
            "upstream_census_report_sha256": CENSUS_REPORT_SHA256,
            "upstream_census_rows_sha256": CENSUS_ROWS_SHA256,
            "source_readset_sha256": dict(sorted(source_readset.items())),
            "upstream_row_count": len(rows),
            "grouped_row_count": len(grouped_rows),
            "grouped_rows_sha256": _sha(grouped_bytes),
            "event_admission_status": "refused",
        }
    )
    return result, grouped_bytes


def run(repository: Path, output: Path) -> dict[str, Any]:
    """Publish two compact artifacts only after source identities survive postread."""
    if not repository.is_absolute() or repository.resolve(strict=True) != repository:
        raise ValueError("A real absolute repository root is required")
    destination = require_absent_artifact_output(repository, output)
    stage = require_absent_artifact_output(
        repository, output.with_name(output.name + ".stage")
    )
    report, rows_bytes = build_report(repository)
    stage.mkdir()
    try:
        (stage / "report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n"
        )
        (stage / "rows.csv").write_bytes(rows_bytes)
        for relative, expected in report["source_readset_sha256"].items():
            source = repository / relative
            if (
                source.resolve(strict=True) != source
                or not source.is_file()
                or _sha(source.read_bytes()) != expected
            ):
                raise ValueError(
                    f"SEAD source changed before method publication: {relative}"
                )
        require_absent_artifact_output(repository, destination)
        stage.rename(destination)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return report


def main(argv: list[str] | None = None) -> int:
    """Write one source-bound SEAD method/type coverage report under artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    main()
