"""Export Swedish fixed-basin inputs and compare independent R conditional moments."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import runpy
import stat
from typing import Any


def _columns(names: str) -> tuple[str, ...]:
    return tuple(names.split())


FACTOR_COLUMNS = _columns(
    "tuple_id factor raw_factor estimated_absolute_error tail_mass_bound subdivisions_used"
)
VALUE_COLUMNS = _columns("case_id window_id track quantity i j value")
TRACKS = {"fresh_factor": 1e-8, "saved_factor": 2e-12}
MAX_BYTES = 8 * 1024 * 1024
POPULATION_SHA256 = "3d1769d49d07fc65c3b67a68eca99c89560383111958fe15a2f5f641cd841c12"


def _finite(value: str, name: str) -> float:
    if not re.fullmatch(
        r"[-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][-+]?[0-9]+)?", value
    ):
        raise ValueError(f"Invalid R numeric field {name}")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"Nonfinite R numeric field {name}")
    return number


def _identity(value: str, length: int) -> str:
    if not re.fullmatch(rf"[0-9a-f]{{{length}}}", value):
        raise ValueError("Expected a lowercase hexadecimal source identity")
    return value


def _physical_path(path: Path) -> Path:
    if ".." in path.parts:
        raise ValueError("Reference paths cannot traverse parent directories")
    absolute = path.absolute()
    for parent in reversed(absolute.parents):
        if not stat.S_ISDIR(parent.lstat().st_mode):
            raise ValueError("Reference paths require physical directory ancestors")
    return absolute


def _output_path(root: Path, path: Path) -> Path:
    owned = _physical_path(root)
    if not stat.S_ISDIR(owned.lstat().st_mode):
        raise ValueError("Output root must be a physical directory")
    output = _physical_path(path)
    if not output.is_relative_to(owned) or output.exists() or output.is_symlink():
        raise ValueError("Output must be absent and inside its explicit output root")
    return output


def _read(path: Path, checksum: str | None = None) -> tuple[bytes, dict[str, Any]]:
    path = _physical_path(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_BYTES:
            raise ValueError("Input must be a bounded regular file")
        body = stream.read(MAX_BYTES + 1)
    digest = hashlib.sha256(body).hexdigest()
    if len(body) > MAX_BYTES or (
        checksum is not None and digest != _identity(checksum, 64)
    ):
        raise ValueError("Input byte identity changed")
    return body, {"path": str(path), "sha256": digest, "bytes": len(body)}


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise ValueError("Duplicate JSON member")
        result[key] = value
    return result


def _json(body: bytes) -> Any:
    return json.loads(body, object_pairs_hook=_pairs, parse_constant=_number)


def _number(value: Any, *, positive: bool = False) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("Expected a finite numeric source value")
    if positive and value <= 0:
        raise ValueError("Expected a positive source value")
    return float(value)


def _load(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    raw, identity = _read(args.report, args.report_sha256)
    report = _json(raw)
    if report["schema_version"] != "swedish-static-basin-maintained-producer.v1":
        raise ValueError("Expected exact maintained Swedish report schema")
    support = Path(__file__).with_name("swedish_population.py")
    _read(support, POPULATION_SHA256)
    # Qualified adjacent reference source; no package or script-parent import is needed.
    api = runpy.run_path(str(support))
    return api["population"](report), [identity], report


def _write(path: Path, body: bytes) -> None:
    if len(body) > MAX_BYTES:
        raise ValueError("Output exceeds the bounded reference role")
    with path.open("xb") as target:
        target.write(body)


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, allow_nan=False) + "\n").encode()


def _directory(path: Path, names: set[str]) -> Path:
    path = _physical_path(path)
    if (
        not stat.S_ISDIR(path.lstat().st_mode)
        or {p.name for p in path.iterdir()} != names
    ):
        raise ValueError("Reference directory has missing or foreign members")
    return path


def _rows(body: bytes, columns: tuple[str, ...]) -> list[dict[str, str]]:
    reader = csv.DictReader(
        io.StringIO(body.decode("utf-8"), newline=""), delimiter="\t", strict=True
    )
    if reader.fieldnames != list(columns):
        raise ValueError("R result columns differ")
    rows = list(reader)
    if any(
        set(row) != set(columns) or any(v is None for v in row.values()) for row in rows
    ):
        raise ValueError("R result row shape differs")
    return rows


def _axis(value: str) -> int:
    if not re.fullmatch(r"0|[1-9][0-9]*", value):
        raise ValueError("R axis requires canonical nonnegative integer")
    return int(value)


def export(args: argparse.Namespace) -> int:
    """Export admitted reference tuples with their original source identities."""
    data, sources, report = _load(args)
    output = _output_path(args.output_root, args.output)
    manifest = {
        "schema": "swedish-physical-window-inputs.v1",
        "sources": sources,
        "source_epoch": report["producer_candidate"],
        "execution_epoch": _identity(args.execution_epoch, 40),
        "python_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "population": {
            "cores": 4,
            "cases": 24,
            "tuples": 45,
            "uses": 54,
            "windows": 462,
            "components": 1002,
            "matrix_cells": 2238,
            "saved_cells_per_track": 8434,
            "computed_cells_per_track": 9720,
            "r_only_control_cells_per_track": 1286,
        },
        "scope": {
            key: report[key]
            for key in (
                "historical_reproduction_claimed",
                "full_31_target_reconstruction_claimed",
                "vegetation_accuracy_claimed",
                "chronology_or_geometry_uncertainty_quantified",
                "source_lake_algorithm_parity_claimed",
                "distribution_of_raw_source_counts_authorized",
            )
        },
        "chronology_scope": report["protocol"]["age_support"],
        "inputs": [
            {
                "name": name,
                "sha256": hashlib.sha256(body).hexdigest(),
                "bytes": len(body),
            }
            for name, body in data["files"].items()
        ],
    }
    output.mkdir()
    for name, body in data["files"].items():
        _write(output / name, body)
    _write(output / "manifest.json", _json_bytes(manifest))
    return 0


def compare(args: argparse.Namespace) -> int:
    """Compare admitted responses with exact independent numerical outputs."""
    comparison_epoch = _identity(args.execution_epoch, 40)
    data, sources, report = _load(args)
    output = _output_path(args.output_root, args.output)
    directory = _directory(args.input_directory, {*data["files"], "manifest.json"})
    manifest_body, mp = _read(
        directory / "manifest.json", _identity(args.input_export_manifest_sha256, 64)
    )
    _, exporter_source = _read(
        args.input_exporter_source, _identity(args.input_exporter_source_sha256, 64)
    )
    export_epoch = _identity(args.input_export_execution_epoch, 40)
    manifest = _json(manifest_body)
    expected_inputs = []
    for name, expected_body in data["files"].items():
        body, identity = _read(directory / name)
        if body != expected_body:
            raise ValueError(
                "Exported input differs from authenticated source population"
            )
        expected_inputs.append(
            {"name": name, "sha256": identity["sha256"], "bytes": identity["bytes"]}
        )
    if (
        manifest["schema"] != "swedish-physical-window-inputs.v1"
        or manifest["sources"] != sources
        or manifest["inputs"] != expected_inputs
        or manifest["source_epoch"] != report["producer_candidate"]
        or manifest["execution_epoch"] != export_epoch
        or manifest["python_source_sha256"] != exporter_source["sha256"]
    ):
        raise ValueError("Export manifest identity differs")
    rd = _directory(args.r_directory, {"factors.tsv", "values.tsv"})
    fb, fp = _read(rd / "factors.tsv")
    vb, vp = _read(rd / "values.tsv")
    factor_rows = _rows(fb, FACTOR_COLUMNS)
    diagnostics: list[dict[str, Any]] = []
    seen_factors: set[str] = set()
    mismatches: list[dict[str, Any]] = []
    for row in factor_rows:
        tid = row["tuple_id"]
        if tid not in data["factors"] or tid in seen_factors:
            raise ValueError("Duplicate or foreign R physical tuple")
        seen_factors.add(tid)
        numbers = {k: _finite(row[k], k) for k in FACTOR_COLUMNS[1:]}
        if (
            not 0 <= numbers["factor"] <= 1
            or not -1e-11 <= numbers["raw_factor"] <= 1 + 1e-11
            or numbers["factor"] != min(1, max(0, numbers["raw_factor"]))
            or numbers["estimated_absolute_error"] < 0
            or not 0 <= numbers["tail_mass_bound"] <= math.exp(-700)
            or not 1 <= _axis(row["subdivisions_used"]) <= 3000
        ):
            raise ValueError("Invalid R physical diagnostic")
        difference = abs(numbers["factor"] - data["factors"][tid])
        diagnostics.append(
            {"tuple_id": tid, **numbers, "absolute_difference": difference}
        )
        if difference > 1e-8:
            mismatches.append({"tuple_id": tid, "absolute_difference": difference})
    if seen_factors != set(data["factors"]):
        raise ValueError("Missing R physical tuple")
    seen_values: set[tuple[str, int, str, str, int, int]] = set()
    actual_values: dict[tuple[str, int, str, str, int, int], float] = {}
    summaries = {
        (cid, wid): {
            "case_id": cid,
            "window_id": wid,
            "tracks": {
                track: {"cells": 0, "maximum_absolute_difference": 0.0, "passed": True}
                for track in TRACKS
            },
        }
        for cid, wid in data["windows"]
    }
    for row in _rows(vb, VALUE_COLUMNS):
        cid, wid, track, quantity = (
            row["case_id"],
            _axis(row["window_id"]),
            row["track"],
            row["quantity"],
        )
        key = (cid, wid, quantity, _axis(row["i"]), _axis(row["j"]))
        unique = (cid, wid, track, quantity, key[3], key[4])
        if (
            track not in TRACKS
            or (key not in data["expected"] and key not in data["r_only"])
            or unique in seen_values
        ):
            raise ValueError("Duplicate or foreign R moment cell")
        seen_values.add(unique)
        actual = _finite(row["value"], "value")
        actual_values[unique] = actual
        if key in data["r_only"]:
            continue
        expected = data["expected"][key]
        difference = abs(actual - expected)
        passed = math.isclose(
            actual, expected, abs_tol=TRACKS[track], rel_tol=TRACKS[track]
        )
        summary = summaries[cid, wid]["tracks"][track]
        summary["cells"] += 1
        summary["maximum_absolute_difference"] = max(
            summary["maximum_absolute_difference"], difference
        )
        summary["passed"] = summary["passed"] and passed
        if not passed:
            mismatches.append(
                {
                    "key": unique,
                    "r_value": actual,
                    "saved_python_value": expected,
                    "absolute_difference": difference,
                }
            )
    if len(seen_values) != 2 * (len(data["expected"]) + len(data["r_only"])):
        raise ValueError("Missing R moment cells")
    controls = []
    for cid, wid, quantity, i, j in sorted(data["r_only"]):
        baseline = cid.split(".", 1)[0] + ".metadata_radius_wind_3"
        for track in TRACKS:
            control_key = (cid, wid, track, quantity, i, j)
            value = actual_values[control_key]
            if quantity == "assumed_ppe_covariance":
                target = 0.0
                passed = value == 0
            else:
                target_quantity = (
                    "counting_covariance"
                    if quantity == "total_conditional_covariance"
                    else quantity
                )
                target = actual_values[baseline, wid, track, target_quantity, i, j]
                passed = math.isclose(value, target, abs_tol=2e-12, rel_tol=2e-12)
            control = {
                "key": control_key,
                "r_value": value,
                "baseline_or_exact_zero": target,
                "passed": passed,
                "saved_zero_ppe_array_present": False,
            }
            controls.append(control)
            if not passed:
                mismatches.append(control)
    if len(controls) != 2572:
        raise ValueError("Exact independent reduced-row control population required")
    result = {
        "schema": "swedish-physical-window-comparison.v1",
        "passed": not mismatches,
        "sources": sources,
        "export_manifest": mp,
        "input_export_execution_epoch": export_epoch,
        "input_exporter_source": exporter_source,
        "r_outputs": [fp, vp],
        "source_epoch": report["producer_candidate"],
        "execution_epoch": comparison_epoch,
        "python_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "physical_factors": diagnostics,
        "windows": list(summaries.values()),
        "values_per_track": 9720,
        "saved_comparisons_per_track": 8434,
        "independently_computed_zero_ppe_controls": controls,
        "tolerances": TRACKS,
        "factor_absolute_tolerance": 1e-8,
        "mismatches": mismatches,
        "limits": "Conditional numerical parity; source-qualified Python K and assumed diagonal PPE SD. No original-author/historical identity, calibrated chronology/uncertainty, field accuracy or complete scientific validation.",
    }
    _write(output, _json_bytes(result))
    return 0 if not mismatches else 1


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch the declared reference export or comparison."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("export", "compare"))
    for name in ("report", "output-root", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    for name in ("report-sha256", "execution-epoch"):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument("--input-directory", type=Path)
    parser.add_argument("--r-directory", type=Path)
    parser.add_argument("--input-exporter-source", type=Path)
    for name in (
        "input-export-manifest-sha256",
        "input-exporter-source-sha256",
        "input-export-execution-epoch",
    ):
        parser.add_argument(f"--{name}")
    args = parser.parse_args(argv)
    if args.mode == "compare" and (
        any(
            getattr(args, name) is None
            for name in (
                "input_directory",
                "r_directory",
                "input_exporter_source",
                "input_export_manifest_sha256",
                "input_exporter_source_sha256",
                "input_export_execution_epoch",
            )
        )
    ):
        parser.error(
            "compare requires input/R directories and explicit retained export manifest/source/epoch bindings"
        )
    try:
        return export(args) if args.mode == "export" else compare(args)
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        parser.exit(2, f"physical-window reference refused: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
