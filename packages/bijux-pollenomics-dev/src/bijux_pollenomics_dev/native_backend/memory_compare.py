"""Measure isolated worker memory for the scoped NumPy/C++ forward boundary."""

from __future__ import annotations

import argparse
import ctypes
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

import numpy as np

from bijux_pollenomics_dev.native_backend.forward_compare import (
    ForwardBatch,
    compile_library,
    inputs,
)
from bijux_pollenomics_dev.native_backend.profiling import THREAD_VARIABLES

SHAPES = ((1, 8, 3), (32, 128, 32), (512, 256, 64), (8192, 256, 512))
METHODS = ("numpy", "native")
REPETITIONS = 5


def _peak_bytes() -> int:
    """Platform resource units are bytes on macOS and KiB on Linux."""
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if platform.system() == "Darwin" else value * 1024)


def child(
    method: str, shape: tuple[int, int, int], library_path: Path, destination: Path
) -> dict[str, Any]:
    if method not in METHODS or shape not in SHAPES:
        raise ValueError("Undeclared memory case")
    arrays = inputs(*shape)
    digest = hashlib.sha256(b"".join(value.tobytes() for value in arrays)).hexdigest()
    batch = ForwardBatch(*arrays)
    library: ctypes.CDLL | None = None
    if method == "native":
        library = ctypes.CDLL(str(library_path))
        function = library.pollen_forward_batch
        function.argtypes = [ctypes.c_size_t] * 3 + [
            ctypes.POINTER(ctypes.c_double)
        ] * 6
        function.restype = ctypes.c_int
    baseline = _peak_bytes()
    started = time.perf_counter()
    result = batch.numpy() if library is None else batch.native(library)
    seconds = time.perf_counter() - started
    peak = _peak_bytes()
    if (
        digest
        != hashlib.sha256(b"".join(value.tobytes() for value in arrays)).hexdigest()
    ):
        raise ValueError("Input buffer changed during memory run")
    np.save(destination, result)
    return {
        "method": method,
        "shape": list(shape),
        "pre_call_process_peak_rss_bytes": baseline,
        "post_call_process_peak_rss_bytes": peak,
        "observed_peak_increment_bytes": max(0, peak - baseline),
        "single_call_seconds": seconds,
        "input_sha256": digest,
        "output_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "output_shape": list(result.shape),
    }


def run(repository: Path, output: Path, compiler: Path) -> dict[str, Any]:
    repository, output = repository.resolve(), output.resolve()
    if output.exists() or not output.is_relative_to(repository / "artifacts"):
        raise ValueError("Absent output root under repository artifacts required")
    if any(os.environ.get(name) != "1" for name in THREAD_VARIABLES):
        raise ValueError("All numerical thread budgets must be one")
    output.mkdir(parents=True)
    source_root = Path(__file__).parent
    sources = [
        Path(__file__),
        source_root / "forward_compare.py",
        source_root / "forward_kernel.cpp",
        source_root / "profiling.py",
        source_root.parent / "trusted_process.py",
    ]
    source_sha256 = {
        p.relative_to(repository).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sources
    }
    library_path = output / "forward-library.so"
    _, build = compile_library(
        source_root / "forward_kernel.cpp", library_path, compiler
    )
    cases = []
    for shape in SHAPES:
        observations: dict[str, list[dict[str, Any]]] = {mode: [] for mode in METHODS}
        for iteration in range(REPETITIONS):
            for method in METHODS:
                stem = f"rows-{shape[0]}-rings-{shape[1]}-taxa-{shape[2]}-{method}-{iteration}"
                path = output / (stem + ".npy")
                started = time.perf_counter()
                complete = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "bijux_pollenomics_dev.native_backend.memory_compare",
                        "--child",
                        method,
                        "--rows",
                        str(shape[0]),
                        "--rings",
                        str(shape[1]),
                        "--taxa",
                        str(shape[2]),
                        "--library",
                        str(library_path),
                        "--destination",
                        str(path),
                    ],
                    cwd=repository,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=True,
                )
                elapsed = time.perf_counter() - started
                result = json.loads(complete.stdout)
                if (
                    result["method"] != method
                    or result["shape"] != list(shape)
                    or hashlib.sha256(path.read_bytes()).hexdigest()
                    != result["output_sha256"]
                ):
                    raise ValueError("Child memory receipt/output differs")
                result["whole_worker_seconds_including_import_and_export"] = elapsed
                observations[method].append(result)
        reference = np.load(
            output / f"rows-{shape[0]}-rings-{shape[1]}-taxa-{shape[2]}-numpy-0.npy"
        )
        for method in METHODS:
            for iteration in range(REPETITIONS):
                candidate = np.load(
                    output
                    / f"rows-{shape[0]}-rings-{shape[1]}-taxa-{shape[2]}-{method}-{iteration}.npy"
                )
                np.testing.assert_allclose(candidate, reference, rtol=1e-10, atol=1e-12)
        if (
            len(
                {
                    row["input_sha256"]
                    for group in observations.values()
                    for row in group
                }
            )
            != 1
        ):
            raise ValueError("Memory workers received different input arrays")
        metrics = {
            mode: {
                "median_process_peak_rss_bytes": median(
                    row["post_call_process_peak_rss_bytes"]
                    for row in observations[mode]
                ),
                "median_single_call_seconds": median(
                    row["single_call_seconds"] for row in observations[mode]
                ),
                "median_whole_worker_seconds_including_import_and_export": median(
                    row["whole_worker_seconds_including_import_and_export"]
                    for row in observations[mode]
                ),
            }
            for mode in METHODS
        }
        cases.append(
            {
                "shape": list(shape),
                "observations": observations,
                "metrics": metrics,
                "native_to_numpy_peak_rss_ratio": metrics["native"][
                    "median_process_peak_rss_bytes"
                ]
                / metrics["numpy"]["median_process_peak_rss_bytes"],
                "numpy_to_native_whole_worker_latency_ratio": metrics["numpy"][
                    "median_whole_worker_seconds_including_import_and_export"
                ]
                / metrics["native"][
                    "median_whole_worker_seconds_including_import_and_export"
                ],
                "numerical_parity": True,
            }
        )
    if any(
        hashlib.sha256((repository / p).read_bytes()).hexdigest() != digest
        for p, digest in source_sha256.items()
    ):
        raise ValueError("Memory comparison source changed")
    report = {
        "schema_version": "native-forward-isolated-worker-memory.1",
        "status": "passed",
        "platform": platform.platform(),
        "thread_settings": {name: os.environ[name] for name in THREAD_VARIABLES},
        "source_sha256": source_sha256,
        "build": build,
        "cases": cases,
        "repetitions_per_method_shape": REPETITIONS,
        "memory_metric": "per-process high-water RSS; NumPy/import/input baseline common, macOS ru_maxrss bytes, Linux KiB converted to bytes",
        "limitation": "Whole worker includes imports and NPY export; high-water increments can be zero after import transients. The large stress shape probes that high-water blind spot but remains a synthetic standalone forward batch, not full LOVE/REVEALS throughput.",
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--compiler", type=Path)
    parser.add_argument("--child", choices=METHODS)
    parser.add_argument("--rows", type=int)
    parser.add_argument("--rings", type=int)
    parser.add_argument("--taxa", type=int)
    parser.add_argument("--library", type=Path)
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    if args.child is not None:
        if None in (args.rows, args.rings, args.taxa, args.library, args.destination):
            parser.error("Child measurement requires shape, library and destination")
        assert (
            args.rows is not None and args.rings is not None and args.taxa is not None
        )
        assert args.library is not None and args.destination is not None
        print(
            json.dumps(
                child(
                    args.child,
                    (args.rows, args.rings, args.taxa),
                    args.library,
                    args.destination,
                ),
                allow_nan=False,
            )
        )
        return 0
    if args.repository is None or args.output is None or args.compiler is None:
        parser.error("Producer requires repository, output and compiler")
    run(args.repository, args.output, args.compiler)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
