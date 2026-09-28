"""Measure each declared Python LRA workload in a fresh worker process."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
from statistics import median
import subprocess
import sys
import time
from typing import Any

from bijux_pollenomics_dev.native_backend.profiling import (
    THREAD_VARIABLES,
    normalize_output,
    workloads,
)

BASELINE = Path("docs/report/numerical-performance/python-baseline/report.json")
REPETITIONS = 5
MODULE = "bijux_pollenomics_dev.native_backend.isolated_python_baseline"


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _peak_bytes() -> int:
    """Convert ru_maxrss to bytes on the two supported Unix resource units."""
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    system = platform.system()
    if system not in {"Darwin", "Linux"}:
        raise ValueError(f"Unsupported process RSS platform: {system}")
    return int(value if system == "Darwin" else value * 1024)


def _scientific_sha(value: object) -> str:
    return _sha(json.dumps(value, sort_keys=True, allow_nan=False).encode())


def worker(name: str) -> dict[str, Any]:
    """Keep fixture construction and one public call inside one new process."""
    if any(os.environ.get(variable) != "1" for variable in THREAD_VARIABLES):
        raise ValueError("All numerical thread variables must be one")
    selection = {item.name: item for item in workloads()}
    if name not in selection:
        raise ValueError(f"Undeclared Python baseline workload: {name}")
    before = _peak_bytes()
    started = time.perf_counter()
    output = selection[name].consume()
    call_seconds = time.perf_counter() - started
    after = _peak_bytes()
    normalized, nonfinite = normalize_output(output)
    return {
        "name": name,
        "contract_sha256": _scientific_sha(selection[name].contract),
        "pre_call_process_peak_rss_bytes": before,
        "post_call_process_peak_rss_bytes": after,
        "observed_peak_increment_bytes": max(0, after - before),
        "call_seconds": call_seconds,
        "scientific_output_sha256": _scientific_sha(normalized),
        "nonfinite_semantics_sha256": _scientific_sha(nonfinite),
    }


def _summary(
    observations: list[dict[str, Any]],
    expected_sha: str,
    expected_nonfinite_sha: str,
) -> dict[str, Any]:
    """Refuse an incomplete group or scientific output drift."""
    if len(observations) != REPETITIONS or any(
        item["scientific_output_sha256"] != expected_sha
        or item["nonfinite_semantics_sha256"] != expected_nonfinite_sha
        for item in observations
    ):
        raise ValueError("Isolated worker scientific output or denominator changed")
    return {
        "median_process_peak_rss_bytes": median(
            item["post_call_process_peak_rss_bytes"] for item in observations
        ),
        "median_pre_call_process_peak_rss_bytes": median(
            item["pre_call_process_peak_rss_bytes"] for item in observations
        ),
        "median_observed_peak_increment_bytes": median(
            item["observed_peak_increment_bytes"] for item in observations
        ),
        "median_call_seconds": median(item["call_seconds"] for item in observations),
        "median_whole_worker_seconds": median(
            item["whole_worker_seconds"] for item in observations
        ),
    }


def run(repository: Path, output: Path) -> dict[str, Any]:
    """Record repeated independent worker peaks against retained scientific outputs."""
    repository, output = repository.resolve(), output.resolve()
    if output.exists() or not output.is_relative_to(repository / "artifacts"):
        raise ValueError("Absent repository artifact destination required")
    if any(os.environ.get(variable) != "1" for variable in THREAD_VARIABLES):
        raise ValueError("All numerical thread variables must be one")
    baseline_bytes = (repository / BASELINE).read_bytes()
    baseline = json.loads(baseline_bytes)
    names = [row["name"] for row in baseline["workloads"]]
    if (
        baseline["schema_version"] != "lra-python-performance-baseline.v1"
        or len(names) != 7
        or len(set(names)) != 7
        or names != [item.name for item in workloads()]
        or baseline["prospective_native_gate"]["minimum_end_to_end_speedup"] != 2.0
    ):
        raise ValueError("Retained baseline contract changed")
    source_hashes = {
        path: _sha((repository / path).read_bytes())
        for path in baseline["source_sha256"]
    }
    source_hashes[Path(__file__).resolve().relative_to(repository).as_posix()] = _sha(
        Path(__file__).read_bytes()
    )
    changed_since_baseline = sorted(
        path
        for path, digest in baseline["source_sha256"].items()
        if source_hashes[path] != digest
    )
    cases = []
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    for row in baseline["workloads"]:
        name = row["name"]
        expected = _scientific_sha(row["scientific_output"])
        expected_nonfinite_sha = _scientific_sha(row["nonfinite_output_semantics"][0])
        observations = []
        for _ in range(REPETITIONS):
            started = time.perf_counter()
            process = subprocess.run(
                [sys.executable, "-m", MODULE, "--worker", name],
                cwd=repository,
                env=environment,
                capture_output=True,
                text=True,
                timeout=120,
                check=True,
            )
            elapsed = time.perf_counter() - started
            observation = json.loads(process.stdout)
            if observation["name"] != name or observation[
                "contract_sha256"
            ] != _scientific_sha(row["contract"]):
                raise ValueError(f"Worker identity or contract changed: {name}")
            observation["whole_worker_seconds"] = elapsed
            observations.append(observation)
        cases.append(
            {
                "name": name,
                "contract": row["contract"],
                "retained_scientific_output_sha256": expected,
                "observations": observations,
                "retained_nonfinite_semantics_sha256": expected_nonfinite_sha,
                "metrics": _summary(observations, expected, expected_nonfinite_sha),
            }
        )
    if any(
        _sha((repository / path).read_bytes()) != digest
        for path, digest in source_hashes.items()
    ) or _sha((repository / BASELINE).read_bytes()) != _sha(baseline_bytes):
        raise ValueError("Python baseline inputs changed during worker measurements")
    report = {
        "schema_version": "lra-python-isolated-worker-baseline.v1",
        "status": "measured",
        "baseline_path": BASELINE.as_posix(),
        "baseline_sha256": _sha(baseline_bytes),
        "source_sha256": source_hashes,
        "source_paths_changed_since_retained_baseline": changed_since_baseline,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "thread_settings": {name: os.environ[name] for name in THREAD_VARIABLES},
        "repetitions_per_workload": REPETITIONS,
        "cases": cases,
        "rss_semantics": "Fresh process per call. Peak includes imports and construction of all seven retained workload fixtures; pre/post difference is only a high-water increment and may be zero despite allocation.",
        "worker_time_semantics": "Whole worker includes Python startup, imports, all fixture construction, one public call and JSON receipt; call_seconds excludes setup.",
        "adoption_decision": "none; Python-only isolated resource measurement",
    }
    output.mkdir(parents=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker")
    args = parser.parse_args()
    if args.worker is not None:
        print(json.dumps(worker(args.worker), allow_nan=False))
        return
    if args.repository is None or args.output is None:
        parser.error("Parent requires repository and output")
    run(args.repository, args.output)


if __name__ == "__main__":
    main()
