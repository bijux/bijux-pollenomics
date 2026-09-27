"""Compare a private C++ forward batch with validated NumPy and an R equation."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import platform
from statistics import median
import time
from typing import Any

import numpy as np

from bijux_pollenomics_dev.native_backend.profiling import THREAD_VARIABLES
from bijux_pollenomics_dev.trusted_process import run_text
from bijux_pollenomics_lra.api import forward_deposition


class ForwardBatch:
    """Convert input buffers deliberately; both execution paths preserve ownership."""

    def __init__(
        self,
        cover: object,
        regional: object,
        kernels: object,
        fractions: object,
        productivity: object,
    ) -> None:
        values = [
            np.require(value, dtype=np.float64, requirements=("C", "A"))
            for value in (cover, regional, kernels, fractions, productivity)
        ]
        self.cover, self.regional, self.kernels, self.fractions, self.productivity = (
            values
        )
        if self.cover.ndim != 2 or self.kernels.ndim != 2:
            raise ValueError("cover and kernels must be matrices")
        rows, taxa = self.cover.shape
        rings, kernel_taxa = self.kernels.shape
        if (
            not rows
            or not rings
            or not taxa
            or kernel_taxa != taxa
            or self.regional.shape != (taxa,)
            or self.productivity.shape != (taxa,)
            or self.fractions.shape != (rings,)
        ):
            raise ValueError("forward dimensions must agree")
        if any(not np.isfinite(value).all() or np.any(value < 0) for value in values):
            raise ValueError("forward inputs must be finite and nonnegative")
        if (
            np.any(self.fractions > 1)
            or np.any(self.productivity <= 0)
            or not np.allclose(self.cover.sum(axis=1), 1, rtol=0, atol=1e-12)
        ):
            raise ValueError(
                "forward closure, fraction and productivity invariants failed"
            )

    def numpy(self) -> np.ndarray:
        """An optimized matrix batch with validated frozen input arrays."""
        weights = self.fractions @ self.kernels
        total = self.cover * (weights * self.productivity) + self.regional
        mass = total.sum(axis=1)
        if (
            not np.isfinite(total).all()
            or not np.isfinite(mass).all()
            or np.any(mass <= 0)
        ):
            raise ValueError("nonfinite or zero forward mass")
        return np.array(total / mass[:, None], copy=True)

    def native(self, library: ctypes.CDLL) -> np.ndarray:
        """Caller keeps all source buffers alive until the synchronous C call returns."""
        function = library.pollen_forward_batch
        pointer = ctypes.POINTER(ctypes.c_double)
        output = np.empty_like(self.cover)
        status = function(
            self.cover.shape[0],
            self.kernels.shape[0],
            self.cover.shape[1],
            *(
                value.ctypes.data_as(pointer)
                for value in (
                    self.cover,
                    self.regional,
                    self.kernels,
                    self.fractions,
                    self.productivity,
                    output,
                )
            ),
        )
        if status != 0:
            raise ValueError(f"native forward refused input with status {status}")
        return output


def compile_library(
    source: Path, output: Path, compiler: Path
) -> tuple[ctypes.CDLL, dict[str, Any]]:
    """Use the installed compiler; no dependency install or runtime package change."""
    flag = "-dynamiclib" if platform.system() == "Darwin" else "-shared"
    command = [
        str(compiler),
        "-std=c++17",
        "-O3",
        "-fPIC",
        flag,
        str(source),
        "-o",
        str(output),
    ]
    started = time.perf_counter()
    result = run_text(command, check=True, capture_output=True)
    identity = run_text([str(compiler), "--version"], check=True, capture_output=True)
    library = ctypes.CDLL(str(output))
    function = library.pollen_forward_batch
    function.argtypes = [ctypes.c_size_t] * 3 + [ctypes.POINTER(ctypes.c_double)] * 6
    function.restype = ctypes.c_int
    return library, {
        "command": command,
        "elapsed_seconds": time.perf_counter() - started,
        "compiler": identity.stdout,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "binary_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }


def inputs(rows: int, rings: int, taxa: int) -> tuple[np.ndarray, ...]:
    """Deterministic numerical stress inputs; no biological sample interpretation."""
    cover = np.arange(1, rows * taxa + 1, dtype=float).reshape(rows, taxa)
    cover /= cover.sum(axis=1)[:, None]
    return (
        cover,
        np.linspace(0.01, 0.1, taxa),
        np.linspace(0.001, 1, rings * taxa).reshape(rings, taxa),
        np.linspace(0.1, 1, rings),
        np.linspace(0.5, 5, taxa),
    )


def timings(consume: Any, calls: int = 200, repetitions: int = 9) -> dict[str, Any]:
    """Batch timer overhead over repeated blocks; keep every wall-time denominator."""
    consume()
    values = []
    for _ in range(repetitions):
        started = time.perf_counter()
        for _ in range(calls):
            consume()
        values.append((time.perf_counter() - started) / calls)
    return {
        "calls_per_block": calls,
        "repetitions": repetitions,
        "seconds_per_call": values,
        "median_seconds_per_call": median(values),
    }


def run(
    repository: Path, output: Path, compiler: Path, rscript: Path
) -> dict[str, Any]:
    """Measure matching finite inputs and retain genuine failures before any decision."""
    if output.exists() or not output.is_relative_to(repository / "artifacts"):
        raise ValueError("absent output root under repository artifacts required")
    if any(os.environ.get(name) != "1" for name in THREAD_VARIABLES):
        raise ValueError("all numerical thread budgets must be one")
    output.mkdir(parents=True)
    source_root = Path(__file__).parent
    source_files = [
        Path(__file__),
        source_root / "forward_kernel.cpp",
        source_root / "forward_reference.R",
    ]
    engine = repository / "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra"
    source_files.extend(sorted(path for path in engine.rglob("*.py") if path.is_file()))
    source_files.extend(
        [source_root / "profiling.py", source_root.parent / "trusted_process.py"]
    )
    identities = {
        str(path.relative_to(repository)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in source_files
    }
    library, build = compile_library(
        source_root / "forward_kernel.cpp", output / "forward-library.so", compiler
    )
    cases = []
    for rows, rings, taxa in ((1, 8, 3), (32, 128, 32), (512, 256, 64)):
        case_root = output / f"rows-{rows}-rings-{rings}-taxa-{taxa}"
        case_root.mkdir()
        arrays = inputs(rows, rings, taxa)
        before = [value.tobytes() for value in arrays]
        batch = ForwardBatch(*arrays)
        numpy_output = batch.numpy()
        native_output = batch.native(library)
        public_output = np.stack(
            [
                forward_deposition(
                    cover, arrays[1], arrays[2], arrays[3], arrays[4]
                ).pollen_fraction
                for cover in arrays[0]
            ]
        )
        for name, value in zip(
            ("cover", "regional", "kernels", "fractions", "productivity"),
            arrays,
            strict=True,
        ):
            np.savetxt(case_root / f"{name}.csv", value, delimiter=",", fmt="%.17g")
        r_started = time.perf_counter()
        r_result = run_text(
            [
                str(rscript),
                "--vanilla",
                str(source_root / "forward_reference.R"),
                str(case_root),
            ],
            check=True,
            capture_output=True,
        )
        r_seconds = time.perf_counter() - r_started
        r_output = np.loadtxt(case_root / "R-output.csv", delimiter=",", ndmin=2)
        comparisons = {}
        for name, candidate in (
            ("native", native_output),
            ("optimized_numpy", numpy_output),
            ("R_equation", r_output),
        ):
            comparisons[name] = {
                "maximum_absolute_error": float(
                    np.max(np.abs(candidate - public_output))
                ),
                "passed": bool(
                    np.allclose(candidate, public_output, rtol=1e-10, atol=1e-12)
                ),
            }
        calls = 200 if rows < 512 else 40
        measurements = {
            "numpy_compute": timings(batch.numpy, calls),
            "native_compute_with_native_validation": timings(
                lambda batch=batch: batch.native(library), calls
            ),
            "numpy_validated_facade": timings(
                lambda arrays=arrays: ForwardBatch(*arrays).numpy(), calls
            ),
            "native_validated_facade": timings(
                lambda arrays=arrays: ForwardBatch(*arrays).native(library), calls
            ),
            "conversion_and_shared_validation": timings(
                lambda arrays=arrays: ForwardBatch(*arrays), calls
            ),
        }
        cases.append(
            {
                "source": "synthetic finite numerical stress, no observed pollen",
                "rows": rows,
                "rings": rings,
                "taxa": taxa,
                "comparisons": comparisons,
                "inputs_unchanged": all(
                    value.tobytes() == old
                    for value, old in zip(arrays, before, strict=True)
                ),
                "measurements": measurements,
                "validated_facade_speedup": measurements["numpy_validated_facade"][
                    "median_seconds_per_call"
                ]
                / measurements["native_validated_facade"]["median_seconds_per_call"],
                "R_startup_loading_equation_export_seconds": r_seconds,
                "R_stdout": r_result.stdout,
                "R_stderr": r_result.stderr,
                "R_version": (case_root / "R-version.txt").read_text(),
                "input_sha256": {
                    path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in sorted(case_root.glob("*.csv"))
                    if path.name != "R-output.csv"
                },
                "native_output": native_output.tolist(),
                "public_output": public_output.tolist(),
            }
        )
    if any(
        hashlib.sha256((repository / path).read_bytes()).hexdigest() != digest
        for path, digest in identities.items()
    ):
        raise ValueError("producer source changed during comparison")
    report = {
        "schema_version": "lra-forward-native-comparison.v1",
        "source_sha256": identities,
        "build": build,
        "platform": platform.platform(),
        "thread_settings": {name: os.environ[name] for name in THREAD_VARIABLES},
        "cases": cases,
        "prospective_gate": {
            "minimum_validated_facade_speedup": 2.0,
            "maximum_peak_rss_ratio": 1.25,
            "rtol": 1e-10,
            "atol": 1e-12,
        },
        "decision_scope": "Measured forward batch boundary only; no global native adoption or DISQOVER R source parity claim",
        "limits": [
            "R is an independent equation reference; original DISQOVER domain parity remains separate",
            "Native validation is repeated after shared facade validation and counted",
            "Compiled binary/toolchain is artifact-only; no production ABI or package dependency",
            "No isolated peak-RSS ratio, parallel scaling, optimizer convergence or packaging comparison",
        ],
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--compiler", required=True, type=Path)
    parser.add_argument("--rscript", required=True, type=Path)
    args = parser.parse_args()
    run(
        args.repository.resolve(),
        args.output.resolve(),
        args.compiler.resolve(),
        args.rscript.resolve(),
    )


if __name__ == "__main__":
    main()
