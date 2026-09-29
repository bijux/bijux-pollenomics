"""Freeze public LRA workloads and retain repeated Python baseline measurements."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import cProfile
from dataclasses import dataclass
import hashlib
from importlib.metadata import version
import json
from math import isfinite
import os
from pathlib import Path
import platform
import pstats
import resource
from statistics import median
import time
from typing import Any, Protocol, cast

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.api import (
    LoveConfig,
    LRAConfig,
    LRAError,
    RevealsConfig,
    forward_deposition,
    run_love,
    run_lra_series,
    run_reveals,
)
from bijux_pollenomics_lra.resources.examples import load_dataset, load_love_example

THREAD_VARIABLES = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)


class ProfileStatistics(Protocol):
    """Public runtime statistics fields absent from the installed pstats stubs."""

    stats: dict[tuple[str, int, str], tuple[int, int, float, float, object]]
    total_tt: float


@dataclass
class Workload:
    """An immutable recipe whose callable returns only scientific numeric outputs."""

    name: str
    contract: dict[str, Any]
    consume: Callable[[], object]


WORKLOAD_NAMES = (
    "reveals-interactive",
    "reveals-reference-series",
    "love-analytical",
    "love-optimized-replay",
    "lra-replicated-series",
    "forward-validated",
    "forward-dot-compute",
)


def workloads(name: str | None = None) -> list[Workload]:
    """Construct only the named fixture in an isolated worker."""
    if name is not None and name not in WORKLOAD_NAMES:
        raise ValueError(f"Undeclared Python baseline workload: {name}")
    return [_workload(item) for item in (WORKLOAD_NAMES if name is None else (name,))]


def _workload(name: str) -> Workload:
    if name.startswith("reveals-"):
        tiefer = load_dataset("Tiefer_See")
        reveals_config = RevealsConfig("lake", 300, iterations=8, stochastic=False)
        rows = 1 if name == "reveals-interactive" else 45
        pollen = tiefer["pollenTS"].iloc[[0]] if rows == 1 else tiefer["pollenTS"]
        return Workload(
            name,
            {
                "source": "Tiefer_See",
                "rows": rows,
                "taxa": 21,
                "config": reveals_config.as_dict(),
            },
            lambda: (
                run_reveals(pollen, tiefer["paramsTS"], reveals_config)
                .table.to_numpy()
                .tolist()
            ),
        )

    if name.startswith("love-") or name == "lra-replicated-series":
        local, regional, parameters, rings = load_love_example()
        params = parameters["ppes"]
        analytical = LoveConfig(
            "analytical", "lake", 300, 12.9, 10, repeats=8, stochastic=False, seed=7
        )
        if name == "love-analytical":
            return Workload(
                name,
                {
                    "source": "LOVEexample",
                    "rows": 1,
                    "taxa": 10,
                    "rings": 36,
                    "config": analytical.as_dict(),
                },
                lambda: (
                    run_love(local, regional, params, rings, analytical)
                    .cover["mean"]
                    .to_numpy()
                    .tolist()
                ),
            )
        if name == "love-optimized-replay":
            optimized_config = LoveConfig(
                "optimized",
                "lake",
                300,
                12.9,
                10,
                repeats=2,
                stochastic=False,
                seed=7,
                optimizer_max_evaluations=32,
            )
            candidates = np.linspace(0.1, 0.9, 320).reshape(32, 10)
            return Workload(
                name,
                {
                    "source": "LOVEexample",
                    "rows": 1,
                    "taxa": 10,
                    "rings": 36,
                    "config": optimized_config.as_dict(),
                    "candidates": candidates.tolist(),
                    "search": "bounded fixed candidate replay; no convergence benchmark",
                },
                lambda: (
                    run_love(
                        local,
                        regional,
                        params,
                        rings,
                        optimized_config,
                        replay_candidates=candidates,
                    )
                    .cover["mean"]
                    .to_numpy()
                    .tolist()
                ),
            )
        reveals = RevealsConfig("lake", 300, iterations=8, stochastic=False)
        series_local = pd.concat([local] * 8, ignore_index=True)
        series_regional = pd.concat([regional] * 8, ignore_index=True)
        series_local.iloc[:, 0] = np.arange(8)
        series_regional.iloc[:, 0] = np.arange(8)
        series_config = LRAConfig(reveals, analytical, seed=7)

        def series() -> list[object]:
            result = run_lra_series(
                series_local, series_regional, params, rings, series_config
            )
            return [
                run.local.cover["mean"].to_numpy().tolist()
                for run in result.runs.values()
            ]

        return Workload(
            name,
            {
                "source": "eight synthetic coordinate replicas of LOVEexample; no independent sites",
                "rows": 8,
                "taxa": 10,
                "rings": 36,
                "config": series_config.as_dict(),
            },
            series,
        )

    cover = np.arange(1, 33, dtype=float)
    cover /= cover.sum()
    kernels = np.linspace(0.001, 1.0, 128 * 32).reshape(128, 32)
    fractions = np.linspace(0.1, 1.0, 128)
    productivity = np.linspace(0.5, 5.0, 32)
    regional_term = np.linspace(0.01, 0.1, 32)
    if name == "forward-validated":
        return Workload(
            name,
            {"source": "synthetic numerical stress arrays", "rings": 128, "taxa": 32},
            lambda: forward_deposition(
                cover, regional_term, kernels, fractions, productivity
            ).pollen_fraction.tolist(),
        )

    def dot_kernel() -> list[float]:
        total = (fractions @ kernels) * (cover * productivity) + regional_term
        return [float(value) for value in total / total.sum()]

    return Workload(
        name,
        {
            "source": "same synthetic arrays",
            "rings": 128,
            "taxa": 32,
            "validation": "compute only; inputs already frozen and validated; not equivalent facade latency",
        },
        dot_kernel,
    )


def normalize_output(
    value: object, path: str = "output"
) -> tuple[object, list[dict[str, str]]]:
    """Preserve undefined scientific values as null with explicit original semantics."""
    if isinstance(value, float) and not isfinite(value):
        return None, [{"path": path, "source_value": str(value)}]
    if isinstance(value, list):
        output = []
        nonfinite = []
        for index, child in enumerate(value):
            normalized, reasons = normalize_output(child, f"{path}[{index}]")
            output.append(normalized)
            nonfinite.extend(reasons)
        return output, nonfinite
    return value, []


def measure(workload: Workload, repetitions: int) -> dict[str, Any]:
    """Retain failures and every unprofiled timing; profiling is a separate sample."""
    if repetitions < 2:
        raise ValueError("At least two timing repetitions are required")
    timings = []
    outputs = []
    failure = None
    nonfinite_outputs = []
    for _ in range(repetitions + 1):
        started = time.perf_counter()
        try:
            output = workload.consume()
        except LRAError as error:
            failure = {"type": type(error).__name__, "detail": str(error)}
            output = None
        timings.append(time.perf_counter() - started)
        normalized, missing = normalize_output(output)
        outputs.append(normalized)
        nonfinite_outputs.append(missing)
    profiler = cProfile.Profile()
    profiler.enable()
    try:
        workload.consume()
    except LRAError:
        pass
    finally:
        profiler.disable()
    stats = cast(ProfileStatistics, pstats.Stats(profiler))
    costs = []
    for (filename, line, name), (
        primitive,
        calls,
        own,
        cumulative,
        _,
    ) in stats.stats.items():
        costs.append(
            {
                "file": filename,
                "line": line,
                "function": name,
                "primitive_calls": primitive,
                "calls": calls,
                "self_seconds": own,
                "cumulative_seconds": cumulative,
            }
        )
    stable = all(value == outputs[0] for value in outputs)
    return {
        "name": workload.name,
        "contract": workload.contract,
        "status": "refused" if failure else "measured",
        "failure": failure,
        "attempted": repetitions + 1,
        "first_call_seconds": timings[0],
        "warm_seconds": timings[1:],
        "warm_median_seconds": median(timings[1:]),
        "warm_min_seconds": min(timings[1:]),
        "warm_max_seconds": max(timings[1:]),
        "identical_scientific_outputs": stable,
        "scientific_output": outputs[0],
        "nonfinite_output_semantics": nonfinite_outputs,
        "profile_total_seconds": stats.total_tt,
        "profile_top_self_costs": sorted(
            costs, key=lambda row: cast(float, row["self_seconds"]), reverse=True
        )[:30],
        "profile_top_cumulative_costs": sorted(
            costs, key=lambda row: cast(float, row["cumulative_seconds"]), reverse=True
        )[:30],
    }


def run(repository: Path, repetitions: int = 7) -> dict[str, Any]:
    """Bind input/producer bytes and the single-thread contract before measurement."""
    if any(os.environ.get(name) != "1" for name in THREAD_VARIABLES):
        raise ValueError("All numerical thread variables must be explicitly one")
    engine = repository / "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra"
    paths = sorted(
        path
        for path in engine.rglob("*")
        if path.is_file() and path.suffix in {".py", ".json", ".npz"}
    )
    paths.append(Path(__file__).resolve())
    identities = {
        str(path.relative_to(repository)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }
    started = time.perf_counter()
    results = [measure(workload, repetitions) for workload in workloads()]
    if any(
        hashlib.sha256((repository / path).read_bytes()).hexdigest() != digest
        for path, digest in identities.items()
    ):
        raise ValueError("Consumed input/producer closure changed during measurement")
    return {
        "schema_version": "lra-python-performance-baseline.v1",
        "prospective_native_gate": {
            "minimum_end_to_end_speedup": 2.0,
            "maximum_peak_rss_ratio": 1.25,
            "absolute_numeric_tolerance": 1e-12,
            "relative_numeric_tolerance": 1e-10,
            "scope": "future identical-input native comparison; this baseline does not decide adoption",
        },
        "environment": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python": platform.python_version(),
            "threads": {name: os.environ[name] for name in THREAD_VARIABLES},
            "versions": {name: version(name) for name in ("numpy", "scipy", "pandas")},
        },
        "source_sha256": identities,
        "repetitions": repetitions,
        "elapsed_seconds": time.perf_counter() - started,
        "process_peak_rss_native_units": resource.getrusage(
            resource.RUSAGE_SELF
        ).ru_maxrss,
        "rss_semantics": "whole process high-water mark including imports; bytes on macOS, KiB on Linux; not a per-workload incremental measurement",
        "cache_semantics": "first call and repeated warm calls in one process; first calls may share kernels warmed by earlier workloads; no claim of isolated cold cache",
        "workloads": results,
        "limits": [
            "No compiled implementation measured",
            "No native adoption decision",
            "No R performance comparison",
            "No parallel scaling or isolated startup/RSS comparison",
            "Replay candidates do not establish optimizer convergence",
            "Compute-only dot alternative excludes facade validation and output ownership",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    report = run(arguments.repository.resolve())
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
