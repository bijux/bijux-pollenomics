"""Select reproducible numerical measurements from a raw Python profile."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import median
from typing import Any

from bijux_pollenomics_dev.native_backend.profiling import WORKLOAD_NAMES


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()


def build(raw_bytes: bytes) -> dict[str, Any]:
    """Refuse incomplete profiles and retain the scientific comparison contract."""
    raw = json.loads(raw_bytes)
    if (
        raw.get("schema_version") != "lra-python-performance-baseline.v1"
        or raw.get("repetitions") != 7
        or [row["name"] for row in raw["workloads"]] != list(WORKLOAD_NAMES)
        or raw["prospective_native_gate"]["minimum_end_to_end_speedup"] != 2.0
        or set(raw["environment"]["threads"].values()) != {"1"}
    ):
        raise ValueError("Python baseline workload or measurement contract changed")
    selected = []
    for row in raw["workloads"]:
        missing = row["nonfinite_output_semantics"]
        warm = row["warm_seconds"]
        if (
            row["status"] != "measured"
            or row["failure"] is not None
            or row["attempted"] != 8
            or row["identical_scientific_outputs"] is not True
            or len(warm) != 7
            or len(missing) != 8
            or any(item != missing[0] for item in missing)
            or not math.isclose(
                row["warm_median_seconds"], median(warm), rel_tol=0, abs_tol=1e-15
            )
            or row["warm_min_seconds"] != min(warm)
            or row["warm_max_seconds"] != max(warm)
        ):
            raise ValueError(f"Python baseline evidence changed: {row['name']}")
        selected.append(
            {
                "name": row["name"],
                "contract": row["contract"],
                "contract_sha256": _digest(row["contract"]),
                "scientific_output_sha256": _digest(row["scientific_output"]),
                "nonfinite_single_call_sha256": _digest(missing[0]),
                "nonfinite_semantics_sha256": _digest(missing),
                "first_call_seconds": row["first_call_seconds"],
                "warm_seconds": warm,
                "warm_median_seconds": row["warm_median_seconds"],
                "warm_min_seconds": row["warm_min_seconds"],
                "warm_max_seconds": row["warm_max_seconds"],
                "profile_total_seconds": row["profile_total_seconds"],
            }
        )
    return {
        "schema_version": "lra-python-performance-measurement.v1",
        "summary_producer_sha256": hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest(),
        "raw_measurement_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "raw_measurement_bytes": len(raw_bytes),
        "prospective_native_gate": raw["prospective_native_gate"],
        "environment": raw["environment"],
        "source_sha256": raw["source_sha256"],
        "repetitions": raw["repetitions"],
        "elapsed_seconds": raw["elapsed_seconds"],
        "process_peak_rss_native_units": raw["process_peak_rss_native_units"],
        "rss_semantics": raw["rss_semantics"],
        "cache_semantics": raw["cache_semantics"],
        "workloads": selected,
        "limits": raw["limits"],
    }


def main() -> None:
    """Write a compact summary of the reference workload measurements."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-report", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Compact measurement destination must be absent")
    summary = build(args.raw_report.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
