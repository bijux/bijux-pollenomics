"""Export Nordic conditional inputs and compare independent R window calculations."""

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
import stat
from typing import Any


def _columns(names: str) -> tuple[str, ...]:
    return tuple(names.split())


CASE_SIZES = {
    "52082.metadata_static_radius": (2, 24),
    "52082.reported_25_5_ha_static_circle": (2, 24),
    "20034.metadata_static_radius": (3, 22),
    "20034.reported_7_2_ha_static_circle": (3, 22),
    "20034.reported_8_0_ha_static_circle": (3, 22),
    "4445.metadata_static_radius": (2, 23),
    "4445.reported_2_5_ha_static_circle": (2, 23),
    "4446.metadata_static_radius": (6, 11),
    "4446.reported_2_5_ha_static_circle": (6, 11),
}
TUPLE_COLUMNS = _columns(
    "tuple_id receiver_radius_m source_inner_radius_m regional_extent_m fall_speed_m_s empirical_diffusion_coefficient turbulence_parameter wind_speed_m_s"
)
SCENARIO_COLUMNS = _columns(
    "case_id taxon_index taxon tuple_id ppe ppe_sd saved_factor"
)
WINDOW_COLUMNS = _columns(
    "case_id window_id younger_cal_bp older_cal_bp_exclusive taxon_index count panel_count_denominator"
)
FACTOR_COLUMNS = _columns(
    "tuple_id factor raw_factor estimated_absolute_error tail_mass_bound subdivisions_used"
)
VALUE_COLUMNS = _columns("case_id window_id track quantity i j value")
VECTORS = _columns(
    "conditional_cover direct_pollen_panel_fraction conditional_standard_error"
)
MATRICES = _columns(
    "counting_covariance assumed_ppe_covariance total_conditional_covariance"
)
TRACKS = {"fresh_factor": 1e-8, "saved_factor": 2e-12}
MAX_BYTES = 8 * 1024 * 1024


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


def _integer(value: Any) -> int:
    if type(value) is not int or not 0 <= value < 2**53:
        raise ValueError("Counts must be exact nonnegative integers below 2**53")
    return value


def _label(value: Any) -> str:
    if not isinstance(value, str) or not value or any(c in value for c in "\t\n\r"):
        raise ValueError("Expected an explicit single-line source identity")
    return value


def _tsv(columns: tuple[str, ...], rows: list[list[Any]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
    writer.writerow(columns)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def population(report: dict[str, Any], tuples: list[dict[str, Any]]) -> dict[str, Any]:
    """Reconcile the complete saved population without evaluating an LRA model."""
    cases = report["cases"]
    if [c["case_id"] for c in cases] != list(CASE_SIZES) or len(tuples) != 23:
        raise ValueError("Expected the exact ordered nine-case/23-tuple population")
    if (report["unique_physical_tuples"], report["physical_tuple_case_uses"]) != (
        23,
        29,
    ):
        raise ValueError("Declared physical population differs")
    _identity(report["candidate"], 40)
    uses: dict[tuple[str, str], tuple[str, dict[str, Any]]] = {}
    tuple_rows: list[list[Any]] = []
    geometry_keys: set[tuple[float, ...]] = set()
    factors: dict[str, float] = {}
    for index, item in enumerate(tuples, 1):
        tid = f"t{index:03d}"
        values = [_number(item[k], positive=True) for k in TUPLE_COLUMNS[1:]]
        if tuple(values) in geometry_keys or not values[0] <= values[1] < values[2]:
            raise ValueError("Duplicate or unsupported physical tuple")
        geometry_keys.add(tuple(values))
        factor = _number(item["factor"], positive=True)
        if (
            factor > 1
            or _number(item["estimated_absolute_error"]) < 0
            or item["rigorous_error_bound"] is not False
        ):
            raise ValueError("Invalid source-qualified response diagnostic")
        factors[tid] = factor
        tuple_rows.append([tid, *values])
        if not item["uses"]:
            raise ValueError("Unused physical tuple")
        for use in item["uses"]:
            key = (_label(use["case_id"]), _label(use["parameter_taxon"]))
            if key in uses:
                raise ValueError("Duplicate case/taxon tuple membership")
            uses[key] = (tid, item)
    scenarios: list[list[Any]] = []
    windows: list[list[Any]] = []
    expected: dict[tuple[str, int, str, int, int], float] = {}
    window_ids: list[tuple[str, int]] = []
    used: set[tuple[str, str]] = set()
    for case in cases:
        cid = case["case_id"]
        size, n_windows = CASE_SIZES[cid]
        taxa = case["parameter_taxa"]
        if len(taxa) != size or len(set(map(_label, taxa))) != size:
            raise ValueError("Invalid or duplicate taxon axis")
        for field in ("PPE", "PPE_SD", "fall_speed_m_s"):
            if len(case[field]) != size:
                raise ValueError("Parameter axis shape differs")
        if (
            case["panel_N_not_full_NISP"] is not True
            or case["source_present_not_hypothesized_zero"] is not True
        ):
            raise ValueError("Source measurement/denominator declaration absent")
        saved = case["physical_response"]["factors"]
        if len(saved) != 1 or len(saved[0]) != size:
            raise ValueError("Expected one pooled site response per taxon")
        for j, taxon in enumerate(taxa):
            key = (cid, taxon)
            if key not in uses:
                raise ValueError("Missing case/taxon physical membership")
            used.add(key)
            tid, item = uses[key]
            protocol = report["protocol"]
            pairs = (
                (item["receiver_radius_m"], case["static_geometry"]["radius_m"]),
                (item["source_inner_radius_m"], case["static_geometry"]["radius_m"]),
                (item["fall_speed_m_s"], case["fall_speed_m_s"][j]),
                (item["regional_extent_m"], protocol["regional_extent_m"]),
                (
                    item["empirical_diffusion_coefficient"],
                    protocol["diffusion_coefficient"],
                ),
                (item["turbulence_parameter"], protocol["turbulence_parameter"]),
                (item["wind_speed_m_s"], protocol["wind_speed_m_s"]),
            )
            if (
                any(
                    _number(a, positive=True) != _number(b, positive=True)
                    for a, b in pairs
                )
                or _number(saved[0][j]) != factors[tid]
            ):
                raise ValueError("Physical parameters or saved response do not join")
            ppe, sd = _number(case["PPE"][j], positive=True), _number(case["PPE_SD"][j])
            if sd < 0:
                raise ValueError("Negative PPE standard deviation")
            scenarios.append([cid, j + 1, taxon, tid, ppe, sd, factors[tid]])
        results = case["results"]
        if len(results) != n_windows or case["occupied_windows"] != n_windows:
            raise ValueError("Window population differs")
        seen: set[tuple[float, float]] = set()
        last_older = -math.inf
        edges = protocol["age_window_edges_cal_bp"]
        for wid, row in enumerate(results, 1):
            younger, older = (
                _number(row["younger_cal_bp"]),
                _number(row["older_cal_bp_exclusive"]),
            )
            interval = (younger, older)
            if (
                interval in seen
                or younger < last_older
                or interval not in list(zip(edges, edges[1:], strict=False))
            ):
                raise ValueError("Duplicate, foreign or overlapping source window")
            seen.add(interval)
            last_older = older
            counts = row["counts"]
            if (
                len(counts) != 1
                or len(counts[0]) != size
                or row["actual_source_panel_presence"] is not True
            ):
                raise ValueError("Source count axes or measured support differ")
            panel = _integer(row["panel_count_denominator"])
            if panel == 0 or sum(map(_integer, counts[0])) != panel:
                raise ValueError("Panel denominator does not equal exact counts")
            window_ids.append((cid, wid))
            for j, count in enumerate(counts[0], 1):
                windows.append([cid, wid, younger, older, j, count, panel])
            for quantity in VECTORS + MATRICES:
                cells = row[quantity]
                if len(cells) != size:
                    raise ValueError("Expected moment axis differs")
                for i in range(size):
                    if quantity in VECTORS:
                        expected[cid, wid, quantity, i + 1, 0] = _number(cells[i])
                    else:
                        if len(cells[i]) != size:
                            raise ValueError("Expected covariance shape differs")
                        for j in range(size):
                            expected[cid, wid, quantity, i + 1, j + 1] = _number(
                                cells[i][j]
                            )
    if (
        used != set(uses)
        or len(uses) != 29
        or len(windows) != 518
        or len(expected) != 6840
        or len(window_ids) != 182
    ):
        raise ValueError("Complete tuple/use/window/cell bijection failed")
    return {
        "files": {
            "tuples.tsv": _tsv(TUPLE_COLUMNS, tuple_rows),
            "scenarios.tsv": _tsv(SCENARIO_COLUMNS, scenarios),
            "windows.tsv": _tsv(WINDOW_COLUMNS, windows),
        },
        "expected": expected,
        "factors": factors,
        "windows": window_ids,
    }


def _load(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    report_body, rp = _read(args.report, args.report_sha256)
    tuple_body, tp = _read(args.tuples, args.tuples_sha256)
    report, tuples = _json(report_body), _json(tuple_body)
    if report["physical_response_tuples_sha256"] != tp["sha256"]:
        raise ValueError("Report does not bind the exact physical tuple buffer")
    data = population(report, tuples)
    return data, [rp, tp], report


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


def export(args: argparse.Namespace) -> int:
    data, sources, report = _load(args)
    output = _output_path(args.output_root, args.output)
    manifest = {
        "schema": "nordic-physical-window-inputs.v1",
        "sources": sources,
        "source_epoch": report["candidate"],
        "execution_epoch": _identity(args.execution_epoch, 40),
        "python_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "population": {
            "cases": 9,
            "tuples": 23,
            "uses": 29,
            "windows": 182,
            "components": 518,
            "matrix_cells": 1762,
        },
        "scope": report["scope"],
        "chronology_scope": report["protocol"]["chronology_scope"],
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


def compare(args: argparse.Namespace) -> int:
    data, sources, report = _load(args)
    output = _output_path(args.output_root, args.output)
    directory = _directory(args.input_directory, {*data["files"], "manifest.json"})
    manifest_body, mp = _read(directory / "manifest.json")
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
        manifest["schema"] != "nordic-physical-window-inputs.v1"
        or manifest["sources"] != sources
        or manifest["inputs"] != expected_inputs
        or manifest["source_epoch"] != report["candidate"]
        or manifest["execution_epoch"] != _identity(args.execution_epoch, 40)
        or manifest["python_source_sha256"]
        != hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
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
            or numbers["tail_mass_bound"] != 0
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
        if track not in TRACKS or key not in data["expected"] or unique in seen_values:
            raise ValueError("Duplicate or foreign R moment cell")
        seen_values.add(unique)
        actual, expected = _finite(row["value"], "value"), data["expected"][key]
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
    if len(seen_values) != 2 * len(data["expected"]):
        raise ValueError("Missing R moment cells")
    result = {
        "schema": "nordic-physical-window-comparison.v1",
        "passed": not mismatches,
        "sources": sources,
        "export_manifest": mp,
        "r_outputs": [fp, vp],
        "source_epoch": report["candidate"],
        "execution_epoch": args.execution_epoch,
        "python_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "physical_factors": diagnostics,
        "windows": list(summaries.values()),
        "values_per_track": 6840,
        "tolerances": TRACKS,
        "factor_absolute_tolerance": 1e-8,
        "mismatches": mismatches,
        "limits": "Conditional numerical parity; source-qualified Python K and assumed diagonal PPE SD. No original-author/historical identity, calibrated chronology/uncertainty, field accuracy or complete scientific validation.",
    }
    _write(output, _json_bytes(result))
    return 0 if not mismatches else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("export", "compare"))
    for name in ("report", "tuples", "output-root", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    for name in ("report-sha256", "tuples-sha256", "execution-epoch"):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument("--input-directory", type=Path)
    parser.add_argument("--r-directory", type=Path)
    args = parser.parse_args(argv)
    if args.mode == "compare" and (
        args.input_directory is None or args.r_directory is None
    ):
        parser.error("compare requires --input-directory and --r-directory")
    try:
        return export(args) if args.mode == "export" else compare(args)
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        parser.exit(2, f"physical-window reference refused: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
