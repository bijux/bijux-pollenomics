"""Retain the measured native forward comparison without local build paths."""

from __future__ import annotations

import argparse
import hashlib
from io import StringIO
import json
import math
from pathlib import Path
from statistics import median
from typing import Any

import numpy as np

from bijux_pollenomics_dev.native_backend.forward_compare import inputs


SHAPES = ((1, 8, 3), (32, 128, 32), (512, 256, 64))
METHODS = (
    "numpy_compute",
    "native_compute_with_native_validation",
    "numpy_validated_facade",
    "native_validated_facade",
    "conversion_and_shared_validation",
)
INPUTS = ("cover", "regional", "kernels", "fractions", "productivity")


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _array_sha(value: object) -> str:
    return _sha(json.dumps(value, allow_nan=False).encode())


def _input_sha(value: np.ndarray) -> str:
    destination = StringIO()
    np.savetxt(destination, value, delimiter=",", fmt="%.17g")
    return _sha(destination.getvalue().encode())


def build(raw_bytes: bytes, reference_root: Path) -> dict[str, Any]:
    """Check every scientific comparison and retain its measurable decision."""
    raw = json.loads(raw_bytes)
    gate = raw["prospective_gate"]
    command = raw["build"]["command"]
    if (
        raw.get("schema_version") != "lra-forward-native-comparison.v1"
        or [(c["rows"], c["rings"], c["taxa"]) for c in raw["cases"]] != list(SHAPES)
        or set(raw["thread_settings"].values()) != {"1"}
        or gate
        != {
            "minimum_validated_facade_speedup": 2.0,
            "maximum_peak_rss_ratio": 1.25,
            "rtol": 1e-10,
            "atol": 1e-12,
        }
        or command[1:4] != ["-std=c++17", "-O3", "-fPIC"]
        or command[4] not in ("-dynamiclib", "-shared")
        or not command[0].endswith("/clang++")
        or not command[5].endswith("/forward_kernel.cpp")
        or command[6] != "-o"
        or not command[7].endswith("/forward-library.so")
        or raw["build"]["stdout"]
        or raw["build"]["stderr"]
    ):
        raise ValueError("Native forward workload, gate or build contract changed")
    cases = []
    for case in raw["cases"]:
        rows, rings, taxa = (case[field] for field in ("rows", "rings", "taxa"))
        arrays = inputs(rows, rings, taxa)
        identities = {
            f"{name}.csv": _input_sha(value)
            for name, value in zip(INPUTS, arrays, strict=True)
        }
        reference = f"reference/rows-{rows}-rings-{rings}-taxa-{taxa}/R-output.csv"
        reference_path = reference_root / reference
        reference_bytes = reference_path.read_bytes()
        r_output = np.loadtxt(reference_path, delimiter=",", ndmin=2)
        native = np.asarray(case["native_output"], dtype=np.float64)
        public = np.asarray(case["public_output"], dtype=np.float64)
        if (
            case["source"] != "synthetic finite numerical stress, no observed pollen"
            or case["inputs_unchanged"] is not True
            or case["input_sha256"] != identities
            or case["retained_R_output"] != reference
            or case["R_stdout"]
            or case["R_stderr"]
            or not case["R_version"].startswith("R version ")
            or any(value.shape != (rows, taxa) for value in (native, public, r_output))
            or any(not np.isfinite(value).all() for value in (native, public, r_output))
            or any(
                not np.allclose(value.sum(axis=1), 1, rtol=0, atol=1e-12)
                for value in (native, public, r_output)
            )
        ):
            raise ValueError(f"Native forward input or output changed: {rows}")
        cover, regional, kernels, fractions, productivity = arrays
        weights = fractions @ kernels
        total = cover * (weights * productivity) + regional
        optimized = total / total.sum(axis=1)[:, None]
        for name, candidate in (
            ("native", native),
            ("optimized_numpy", optimized),
            ("R_equation", r_output),
        ):
            observed = case["comparisons"][name]
            difference = float(np.max(np.abs(candidate - public)))
            if (
                not math.isclose(
                    observed["maximum_absolute_error"],
                    difference,
                    rel_tol=0,
                    abs_tol=1e-16,
                )
                or observed["passed"]
                is not bool(np.allclose(candidate, public, rtol=1e-10, atol=1e-12))
                or observed["passed"] is not True
            ):
                raise ValueError(f"Native forward parity changed: {rows}/{name}")
        measurements = case["measurements"]
        if set(measurements) != set(METHODS):
            raise ValueError(f"Native forward method denominator changed: {rows}")
        for name in METHODS:
            item = measurements[name]
            observations = item["seconds_per_call"]
            if (
                item["calls_per_block"] != (40 if rows == 512 else 200)
                or item["repetitions"] != 9
                or len(observations) != 9
                or any(not math.isfinite(value) or value <= 0 for value in observations)
                or item["median_seconds_per_call"] != median(observations)
            ):
                raise ValueError(f"Native forward timing changed: {rows}/{name}")
        ratio = (
            measurements["numpy_validated_facade"]["median_seconds_per_call"]
            / measurements["native_validated_facade"]["median_seconds_per_call"]
        )
        if not math.isclose(
            case["validated_facade_speedup"], ratio, rel_tol=0, abs_tol=1e-15
        ):
            raise ValueError(f"Native forward benefit ratio changed: {rows}")
        cases.append(
            {
                "source": case["source"],
                "rows": rows,
                "rings": rings,
                "taxa": taxa,
                "input_sha256": identities,
                "reference_R_output": reference,
                "reference_R_output_sha256": _sha(reference_bytes),
                "public_output_sha256": _array_sha(case["public_output"]),
                "native_output_sha256": _array_sha(case["native_output"]),
                "comparisons": case["comparisons"],
                "inputs_unchanged": True,
                "measurements": measurements,
                "validated_facade_speedup": ratio,
                "R_startup_loading_equation_export_seconds": case[
                    "R_startup_loading_equation_export_seconds"
                ],
                "R_version": case["R_version"],
            }
        )
    return {
        "schema_version": "lra-forward-native-measurement.v1",
        "summary_producer_sha256": _sha(Path(__file__).read_bytes()),
        "raw_measurement_sha256": _sha(raw_bytes),
        "raw_measurement_bytes": len(raw_bytes),
        "source_sha256": raw["source_sha256"],
        "build": {
            "flags": command[1:5],
            "compiler": raw["build"]["compiler"],
            "elapsed_seconds": raw["build"]["elapsed_seconds"],
            "binary_sha256": raw["build"]["binary_sha256"],
        },
        "platform": raw["platform"],
        "thread_settings": raw["thread_settings"],
        "cases": cases,
        "prospective_gate": gate,
        "decision_scope": raw["decision_scope"],
        "limits": raw["limits"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-report", required=True, type=Path)
    parser.add_argument("--reference-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Compact native measurement destination must be absent")
    summary = build(args.raw_report.read_bytes(), args.reference_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
