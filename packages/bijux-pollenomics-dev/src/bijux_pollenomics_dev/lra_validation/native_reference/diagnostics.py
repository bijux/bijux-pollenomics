"""Describe retained R/Python vector residuals without executing either model."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .annulus_capture import _file
from .finite_covariance_capture import validated_finite_covariance_capture

PETR_TAXA_PATH = "docs/report/method-certification/petrkunes-r-comparison/taxa.csv"
PETR_TAXA_SHA256 = "b37211fda3a692d1b903501a14323ab14820950d434f8a2953b9ea25a269b915"


def _number(value: float) -> float | str:
    if math.isnan(value):
        return "NaN"
    if math.isinf(value):
        return "Infinity" if value > 0 else "-Infinity"
    return value


def vector_diagnostics(
    actual: NDArray[Any],
    expected: NDArray[Any],
    *,
    rtol: float,
    atol: float,
    exact_indices: tuple[int, ...] = (),
) -> dict[str, Any]:
    """Report every unequal entry; relative residuals use nonzero reference values.

    Matching NaNs and matching signed infinities are equal for this comparison.
    A nonzero residual at a zero reference has no finite relative residual; its
    index and absolute residual remain explicit. Original tolerances are used
    asymmetrically against the reference, as in the original NumPy comparison.
    """
    if not math.isfinite(rtol) or not math.isfinite(atol) or rtol < 0 or atol < 0:
        raise ValueError("Finite nonnegative original tolerances required")
    if actual.ndim != 1 or expected.ndim != 1 or actual.shape != expected.shape:
        raise ValueError("Matched one-dimensional retained vectors required")
    if len(set(exact_indices)) != len(exact_indices) or any(
        type(index) is not int or index < 0 or index >= len(expected)
        for index in exact_indices
    ):
        raise ValueError("Unique in-range exact coordinates required")
    strings = expected.dtype.kind in "USO"
    differences: list[dict[str, Any]] = []
    failures: list[int] = []
    absolute: list[float] = []
    relative: list[float] = []
    zero_reference_differences: list[int] = []
    nonfinite_mismatches: list[int] = []
    for index in range(len(expected)):
        if strings:
            left, right = str(actual[index]), str(expected[index])
            if left != right:
                failures.append(index)
                differences.append({"index": index, "actual": left, "expected": right})
            continue
        a, b = float(actual[index]), float(expected[index])
        same = a == b or (math.isnan(a) and math.isnan(b))
        finite = math.isfinite(a) and math.isfinite(b)
        accepted = same or (
            finite
            and index not in exact_indices
            and bool(np.isclose(a, b, rtol=rtol, atol=atol, equal_nan=True))
        )
        if not accepted:
            failures.append(index)
        if finite:
            delta = abs(a - b)
            absolute.append(delta)
            if b != 0:
                relative.append(delta / abs(b))
        if not same:
            row: dict[str, Any] = {
                "index": index,
                "actual": _number(a),
                "expected": _number(b),
                "within_original_tolerance": accepted,
            }
            if finite:
                row["absolute_error"] = _number(abs(a - b))
                row["relative_error"] = _number(abs(a - b) / abs(b)) if b else None
                if b == 0:
                    zero_reference_differences.append(index)
            else:
                nonfinite_mismatches.append(index)
            differences.append(row)
    return {
        "status": "passed" if not failures else "failed",
        "values": len(expected),
        "comparison_kind": "exact_strings" if strings else "numeric",
        "rtol": rtol,
        "atol": atol,
        "exact_indices": list(exact_indices),
        "max_absolute_error": _number(max(absolute, default=0.0))
        if not strings
        else None,
        "max_relative_error": _number(max(relative, default=0.0))
        if not strings
        else None,
        "relative_error_denominator": "abs(expected), excluding zero and nonfinite reference values",
        "zero_reference_difference_indices": zero_reference_differences,
        "nonfinite_mismatch_indices": nonfinite_mismatches,
        "expected_nonfinite_entries": []
        if strings
        else [
            {"index": i, "value": _number(float(value))}
            for i, value in enumerate(expected)
            if not math.isfinite(float(value))
        ],
        "actual_nonfinite_entries": []
        if strings
        else [
            {"index": i, "value": _number(float(value))}
            for i, value in enumerate(actual)
            if not math.isfinite(float(value))
        ],
        "differing_entry_count": len(differences),
        "differing_entries": differences,
        "out_of_tolerance_indices": failures,
    }


def _csv_vector(path: Path, *, strings: bool) -> NDArray[Any]:
    rows = list(csv.DictReader(io.StringIO(path.read_text())))
    values = [row["value"] for row in rows]
    if strings:
        return np.asarray(values, dtype=str)
    return np.asarray(
        [float("nan") if value in {"NA", "NaN"} else float(value) for value in values]
    )


def build_diagnostics(repository: Path, protocol_path: Path) -> dict[str, Any]:
    """Authenticate original packets, then compare only their retained arrays."""
    capture = validated_finite_covariance_capture(repository)
    root = capture.directory
    core = json.loads((root / "oracle/case_manifest.json").read_bytes())
    domains = json.loads((root / "source-domains/case_manifest.json").read_bytes())
    protocol_raw = protocol_path.read_bytes()
    protocol = json.loads(protocol_raw)
    expected_core = [
        {key: row[key] for key in ("id", "rtol", "atol", "exact_indices", "values")}
        for row in core
    ]
    if (
        protocol["schema_version"] != "retained-oracle-residual-protocol.v1"
        or protocol["core_cases"] != expected_core
        or protocol["domain_tolerance"]["rtol"] != 1e-10
        or protocol["domain_tolerance"]["atol"] != 3e-10
        or protocol["domain_tolerance"]["cases"] != 23
        or protocol["petrkunes_serialized_comparison"]["rtol"] != 0
        or protocol["petrkunes_serialized_comparison"]["atol"] != 0
    ):
        raise ValueError(
            "Frozen original case tolerances differ from diagnostics protocol"
        )
    results: list[dict[str, Any]] = []
    with np.load(
        root / "oracle/python_expected_not_R_goldens.npz", allow_pickle=False
    ) as saved:
        if set(saved.files) != {row["id"] for row in core} or len(core) != 43:
            raise ValueError("Exact retained core population required")
        for row in core:
            expected = saved[row["id"]]
            actual = _csv_vector(
                root / "oracle" / (row["id"] + ".csv"),
                strings=expected.dtype.kind in "USO",
            )
            results.append(
                {
                    "profile": "core",
                    "id": row["id"],
                    "name": row["name"],
                    "mode": row["mode"],
                    **vector_diagnostics(
                        actual,
                        expected,
                        rtol=row["rtol"],
                        atol=row["atol"],
                        exact_indices=tuple(row["exact_indices"]),
                    ),
                }
            )
    if len(domains) != 23:
        raise ValueError("Exact retained domain population required")
    for row in domains:
        expected = np.load(
            root
            / "source-domains/python_expected_not_R_goldens"
            / (row["id"] + ".npy"),
            allow_pickle=False,
        )
        actual = _csv_vector(
            root / "source-domains" / (row["id"] + "-R.csv"), strings=False
        )
        results.append(
            {
                "profile": "source-domains",
                "id": row["id"],
                "semantics": row["semantics"],
                **vector_diagnostics(actual, expected, rtol=1e-10, atol=3e-10),
            }
        )
    petr_raw = _file(repository, PETR_TAXA_PATH)
    if hashlib.sha256(petr_raw).hexdigest() != PETR_TAXA_SHA256:
        raise ValueError("Original selected Petr Kunes retained table changed")
    petr = list(csv.DictReader(io.StringIO(petr_raw.decode())))
    scenarios = ("single", "unequal_pair", "six_sites", "full_grid")
    if len(petr) != 124 or {row["scenario"] for row in petr} != set(scenarios):
        raise ValueError("Four retained 31-taxon Petr Kunes cases required")
    for scenario in scenarios:
        selected = [row for row in petr if row["scenario"] == scenario]
        if len(selected) != 31 or len({row["taxon"] for row in selected}) != 31:
            raise ValueError("Exact selected Petr Kunes taxon population required")
        for quantity in ("cover", "se"):
            results.append(
                {
                    "profile": "petrkunes_original_vs_tagged_R_retained_precision",
                    "id": scenario + "_" + quantity,
                    "taxon_axis": [row["taxon"] for row in selected],
                    **vector_diagnostics(
                        np.asarray(
                            [float(row["secondary_" + quantity]) for row in selected]
                        ),
                        np.asarray(
                            [float(row["original_" + quantity]) for row in selected]
                        ),
                        rtol=0.0,
                        atol=0.0,
                    ),
                }
            )
    inputs = {**capture.input_sha256, PETR_TAXA_PATH: PETR_TAXA_SHA256}
    for relative, digest in inputs.items():
        body = (
            capture.read_input(relative)
            if relative in capture.input_sha256
            else _file(repository, relative)
        )
        if hashlib.sha256(body).hexdigest() != digest:
            raise ValueError("Retained native input changed during diagnostics")
    return {
        "schema_version": "retained-native-oracle-vector-diagnostics.v1",
        "protocol_sha256": hashlib.sha256(protocol_raw).hexdigest(),
        "status": "passed"
        if all(row["status"] == "passed" for row in results)
        else "failed",
        "native_source_revision": capture.source_revision,
        "native_capture_manifest_sha256": capture.manifest_sha256,
        "captured_core_cases": 43,
        "captured_domain_cases": 23,
        "petrkunes_retained_mean_pairs": 124,
        "petrkunes_retained_standard_error_pairs": 124,
        "retained_input_sha256": inputs,
        "fresh_R_executed": False,
        "python_expectations_regenerated": False,
        "tolerances_modified": False,
        "release_certificate": False,
        "cases": results,
        "scope": "Post-execution diagnostics of authenticated saved R vectors and original saved Python expectations. Original execution timing, source, case population and tolerances remain unchanged. No model, optimizer, R, ecological or covariance-R certification.",
    }


def main(argv: list[str] | None = None) -> int:
    """Write retained-vector diagnostics to a confined artifact file."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    args = parser.parse_args(argv)
    repository = args.repository.resolve(strict=True)
    output = (
        args.output if args.output.is_absolute() else repository / args.output
    ).absolute()
    artifacts = repository / "artifacts"
    if ".." in args.output.parts or not output.is_relative_to(artifacts):
        raise ValueError(
            "Diagnostics output must be confined below repository artifacts"
        )
    current = output.parent
    while current != repository:
        if current.is_symlink():
            raise ValueError("Diagnostics output ancestor alias refused")
        current = current.parent
    if output.exists() or output.is_symlink():
        raise ValueError("Diagnostics output must be absent")
    result = build_diagnostics(repository, args.protocol)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
