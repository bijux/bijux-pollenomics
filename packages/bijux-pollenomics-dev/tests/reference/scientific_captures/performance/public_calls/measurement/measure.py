"""Retain first/warm public-call observations without a compiled candidate."""

from __future__ import annotations

import argparse
import cProfile
import importlib
import json
import os
from pathlib import Path
import pstats
import resource
import sys
import time
from typing import Any
import warnings

PROCESS_ENTRY = time.perf_counter()


def boundary_measurement(
    workload: Any, target: tuple[str, str], expected: str
) -> dict[str, Any]:
    from boundary import assess
    from workloads import digest, normalized

    module = importlib.import_module(target[0])
    original = getattr(module, target[1])
    initial = workload.original_input_digest()
    groups: dict[str, list[float]] = {
        k: []
        for k in ("baseline", "passthrough", "instrumented", "inside", "clock_cost")
    }
    count = 0
    inside = 0.0

    def passthrough(*args: Any, **kwargs: Any) -> Any:
        return original(*args, **kwargs)

    def instrumented(*args: Any, **kwargs: Any) -> Any:
        nonlocal count, inside
        start = time.perf_counter()
        value = original(*args, **kwargs)
        inside += time.perf_counter() - start
        count += 1
        return value

    try:
        for mode, function in (
            ("baseline", original),
            ("passthrough", passthrough),
            ("instrumented", instrumented),
        ):
            setattr(module, target[1], function)
            for _ in range(3):
                inside = 0.0
                count = 0
                began = time.perf_counter()
                value = workload.public_call()
                elapsed = time.perf_counter() - began
                assert digest(normalized(workload.project(value))) == expected
                groups[mode].append(elapsed)
                if mode == "instrumented":
                    assert count > 0
                    groups["inside"].append(inside)
                    cost = 0.0
                    for _ in range(count):
                        tick = time.perf_counter()
                        cost += time.perf_counter() - tick
                    groups["clock_cost"].append(cost)
    finally:
        setattr(module, target[1], original)
    assert initial == workload.original_input_digest()
    return {
        "module": target[0],
        "attribute": target[1],
        "call_count_per_instrumented_public_call": count,
        "timings_seconds": groups,
        "assessment": assess(**groups, outputs_exact=True, inputs_exact=True),
        "scope": "Separate otherwise unprofiled complete public calls; one boundary at a time, never summed nested costs. Conservative min/max spread and empty clock correction are descriptive measurements, not a confidence interval or sourceR parity.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--worker", type=int, required=True)
    parser.add_argument(
        "--workload",
        choices=("author-conditional-joint-draws", "love-larger-fixed-candidate-batch"),
        required=True,
    )
    parser.add_argument("--samples", type=int, choices=(1, 8), default=8)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_bytes())
    root = Path(plan["repository"])
    sys.path[:0] = [str(root / "packages" / n / "src") for n in plan["packages"]]
    from storage import write_json
    from workloads import build, digest, normalized

    directory = Path(plan["output"]) / args.workload / f"worker-{args.worker}"
    assert directory.resolve() == directory and not any(
        p.is_symlink() for p in (directory, *directory.parents)
    )
    directory.parent.mkdir(exist_ok=True)
    directory.mkdir(exist_ok=False)
    rows = []
    for name in (args.workload,):
        loading = time.perf_counter()
        workload = build(root, Path(plan["private_root"]), name)
        construction_seconds = time.perf_counter() - loading
        before = workload.original_input_digest()
        timings = []
        identities = []
        serialization = []
        output = None
        with warnings.catch_warnings(record=True) as warning_records:
            warnings.simplefilter("always")
            for _ in range(args.samples):
                started = time.perf_counter()
                value = workload.public_call()
                timings.append(time.perf_counter() - started)
                projection = time.perf_counter()
                current = normalized(workload.project(value))
                identities.append(digest(current))
                serialization.append(time.perf_counter() - projection)
                if output is None:
                    output = current
            profiler = cProfile.Profile()
            if args.samples == 8:
                profiler.enable()
                value = workload.public_call()
                profiler.disable()
                assert digest(normalized(workload.project(value))) == identities[0]
        assert len(set(identities)) == 1 and before == workload.original_input_digest()
        output_path = directory / (name + ".json")
        write_json(Path(plan["output"]), output_path, output)
        statistics: Any = pstats.Stats(profiler) if args.samples == 8 else None
        costs = [
            {
                "file": key[0],
                "line": key[1],
                "function": key[2],
                "calls": v[1],
                "self_seconds": v[2],
                "cumulative_seconds": v[3],
            }
            for key, v in (statistics.stats.items() if statistics is not None else [])
        ]
        rows.append(
            {
                "workload": name,
                "contract": workload.contract,
                "input_identity": before,
                "construction_loading_conversion_seconds": construction_seconds,
                "first_public_call_seconds": timings[0],
                "warm_public_call_seconds": timings[1:],
                "output_projection_seconds": serialization,
                "scientific_output_sha256": identities[0],
                "scientific_output_path": str(output_path),
                "diagnostic_profile_total_seconds": statistics.total_tt
                if statistics is not None
                else None,
                "diagnostic_top_self": sorted(
                    costs, key=lambda x: x["self_seconds"], reverse=True
                )[:20],
                "diagnostic_top_cumulative": sorted(
                    costs, key=lambda x: x["cumulative_seconds"], reverse=True
                )[:20],
                "profile_is_unprofiled_hotspot_evidence": False,
                "warnings": sorted({str(w.message) for w in warning_records}),
            }
        )
        if args.samples == 8:
            targets = (
                [
                    (
                        "bijux_pollenomics_lra.reconstruction.uncertainty.joint_site_draws",
                        "_closed_joint_draws",
                    )
                ]
                if name == "author-conditional-joint-draws"
                else [
                    ("bijux_pollenomics_lra.reconstruction.optimized", n)
                    for n in ("tf", "calK")
                ]
            )
            rows[-1]["measured_unprofiled_boundaries"] = [
                boundary_measurement(workload, target, identities[0])
                for target in targets
            ]
    origins = {}
    for name in ("bijux_pollenomics_lra", "bijux_pollenomics_dev"):
        module_file = importlib.import_module(name).__file__
        assert module_file is not None
        origins[name] = str(Path(module_file).absolute())

    result = {
        "candidate": plan["candidate"],
        "worker": args.worker,
        "rows": rows,
        "worker_body_seconds": time.perf_counter() - PROCESS_ENTRY,
        "peak_RSS_native": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "rss_units": "bytes" if sys.platform == "darwin" else "KiB",
        "thread_limits": {
            key: os.environ[key]
            for key in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
                "BLIS_NUM_THREADS",
            )
        },
        "native_thread_counters_observed": False,
        "R_or_compiler_executed": False,
        "source_origins": origins,
        "limits": "Fresh process first call is not guaranteed OS-cold. Seven warm observations include all repeats; profiles are diagnostic only. Full public calls exclude separately measured input construction/projection; no compiled adoption or sourceR parity claim.",
    }
    write_json(Path(plan["output"]), directory / "measurement.json", result)
    print(json.dumps({"worker": args.worker, "workloads": len(rows), "native_exit": 0}))


if __name__ == "__main__":
    main()
