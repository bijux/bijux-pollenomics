"""Retain the measured numerical result without publishing profiler stacks."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
from typing import Any

WORKLOADS = (
    "reveals-interactive",
    "reveals-reference-series",
    "love-analytical",
    "love-optimized-replay",
    "lra-replicated-series",
    "forward-validated",
    "forward-dot-compute",
)
MEASUREMENT_SCOPE = (
    "Seven repeated single-thread workloads on the same recorded machine; "
    "independent timing runs, no noise-free performance guarantee."
)


def _sha_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha_value(value: object) -> str:
    return _sha_bytes(json.dumps(value, sort_keys=True).encode())


def build(
    raw_bytes: bytes, reference_bytes: bytes
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Check exact scientific support and select only enduring measurement fields."""
    raw = json.loads(raw_bytes)
    reference = json.loads(reference_bytes)
    if (
        raw.get("schema_version") != "lra-python-performance-baseline.v1"
        or reference.get("schema_version")
        != "lra-runtime-metadata-reference-baseline.v1"
        or raw.get("repetitions") != 7
        or [row["name"] for row in raw["workloads"]] != list(WORKLOADS)
        or [row["name"] for row in reference["workloads"]] != list(WORKLOADS)
    ):
        raise ValueError("Runtime measurement or baseline support changed")
    environment = raw["environment"]
    if environment != reference["environment"] or set(
        environment["threads"].values()
    ) != {"1"}:
        raise ValueError("Measured environment differs from source baseline")
    selected = []
    comparisons = []
    for observation, baseline in zip(
        raw["workloads"], reference["workloads"], strict=True
    ):
        if (
            observation["status"] != "measured"
            or observation["attempted"] != 8
            or observation["identical_scientific_outputs"] is not True
            or len(observation["warm_seconds"]) != 7
            or not math.isclose(
                observation["warm_median_seconds"],
                statistics.median(observation["warm_seconds"]),
                rel_tol=0,
                abs_tol=1e-15,
            )
            or _sha_value(observation["contract"]) != baseline["contract_sha256"]
            or _sha_value(observation["scientific_output"])
            != baseline["scientific_output_sha256"]
            or _sha_value(observation["nonfinite_output_semantics"])
            != baseline["nonfinite_semantics_sha256"]
        ):
            raise ValueError(
                f"Scientific or timing support changed: {baseline['name']}"
            )
        timing = observation["warm_median_seconds"]
        selected.append(
            {
                "name": observation["name"],
                "contract": observation["contract"],
                "contract_sha256": baseline["contract_sha256"],
                "scientific_output_sha256": baseline["scientific_output_sha256"],
                "nonfinite_semantics_sha256": baseline["nonfinite_semantics_sha256"],
                "first_call_seconds": observation["first_call_seconds"],
                "warm_seconds": observation["warm_seconds"],
                "warm_median_seconds": timing,
                "warm_min_seconds": observation["warm_min_seconds"],
                "warm_max_seconds": observation["warm_max_seconds"],
                "profile_total_seconds": observation["profile_total_seconds"],
            }
        )
        comparisons.append(
            {
                "workload": observation["name"],
                "baseline_median_seconds": baseline["warm_median_seconds"],
                "optimized_median_seconds": timing,
                "latency_ratio": baseline["warm_median_seconds"] / timing,
                "same_config": True,
                "same_scientific_outputs": True,
                "same_native_missingness": True,
            }
        )
    summary = {
        "schema_version": "lra-runtime-metadata-measurement.v1",
        "summary_producer_sha256": _sha_bytes(Path(__file__).read_bytes()),
        "raw_measurement_sha256": _sha_bytes(raw_bytes),
        "raw_measurement_bytes": len(raw_bytes),
        "source_sha256": raw["source_sha256"],
        "environment": environment,
        "repetitions": raw["repetitions"],
        "elapsed_seconds": raw["elapsed_seconds"],
        "process_peak_rss_native_units": raw["process_peak_rss_native_units"],
        "rss_semantics": raw["rss_semantics"],
        "cache_semantics": raw["cache_semantics"],
        "workloads": selected,
        "limits": raw["limits"],
    }
    comparison = {
        "schema_version": "lra-runtime-metadata-comparison.v1",
        "baseline_report": "reference-baseline.json",
        "reference_baseline_sha256": _sha_bytes(reference_bytes),
        "reference_baseline_source_sha256": reference["source_report_sha256"],
        "optimized_report": "report.json",
        "baseline_commit": reference["source_commit"][:8],
        "comparisons": comparisons,
        "same_dependency_versions": True,
        "measurement_scope": MEASUREMENT_SCOPE,
    }
    return summary, comparison


def main() -> None:
    """Write compact native profile measurements and their comparison."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-report", required=True, type=Path)
    parser.add_argument("--reference-baseline", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    if args.output_root.exists():
        raise ValueError("Compact measurement destination must be absent")
    summary, comparison = build(
        args.raw_report.read_bytes(), args.reference_baseline.read_bytes()
    )
    args.output_root.mkdir(parents=True)
    for name, value in (("report.json", summary), ("comparison.json", comparison)):
        (args.output_root / name).write_text(json.dumps(value, indent=2) + "\n")


if __name__ == "__main__":
    main()
