"""Compare bounded Python and source R LOVE objective solution quality."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess

import numpy as np

from bijux_pollenomics_lra.optimization.solver import OptimizationResult, optimize_box
from bijux_pollenomics_lra.reconstruction.optimized import tf


REFERENCE_SHA256 = "ea496ae82807b52c9dd3d4b39b4dfa294bfac4068e20184ce56187bff70caf5c"
MAX_OPTIMUM_GAP = 1e-4
MAX_CROSS_EVALUATION_GAP = 1e-10


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _known_optimum(name: str) -> float:
    if name == "symmetric-interior":
        return math.sqrt(2) * abs(math.log(0.5 / 0.501))
    if name == "constrained-boundary":
        return math.hypot(math.log(0.75 / 1.001), math.log(0.25 / 0.001))
    lower, upper = 1 / 3, 3 / 5
    for _ in range(80):
        p = (lower + upper) / 2
        derivative = -4 * math.log((1 - p) / 0.502) / (1 - p)
        derivative += 2 * math.log(p / 0.501) / p
        if derivative > 0:
            upper = p
        else:
            lower = p
    p = (lower + upper) / 2
    return math.sqrt(2 * math.log((1 - p) / 0.502) ** 2 + math.log(p / 0.501) ** 2)


def _arrays(case: dict[str, object]) -> tuple[np.ndarray, ...]:
    return tuple(
        np.asarray(case[key], dtype=float)
        for key in ("regional", "local_k", "local_fraction", "observed", "ppe")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--rscript", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository = args.repository.resolve()
    library = args.library.resolve()
    rscript = args.rscript.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    here = Path(__file__).resolve().parent
    config = json.loads((here / "cases.json").read_text(encoding="utf-8"))
    assert config["schema_version"] == "love-objective-cases.1"
    source = repository / "packages/bijux-pollenomics-lra/vendor/disqover_0.9.14.tar.gz"
    marker = library / "disqover/SOURCE_SHA256"
    assert (
        _sha(source) == marker.read_text(encoding="utf-8").strip() == REFERENCE_SHA256
    )

    fits: dict[str, OptimizationResult] = {}
    python_rows: list[dict[str, object]] = []
    for case in config["cases"]:
        inputs = _arrays(case)
        n = len(inputs[0])

        def objective(candidate: np.ndarray) -> float:
            return tf(candidate, *inputs)

        fit = optimize_box(
            objective,
            np.zeros(n),
            np.ones(n),
            rng=config["optimizer_seed"],
            maxiter=config["iterations"],
            tolerance=1e-7,
            max_evaluations=20_000,
        )
        fits[case["name"]] = fit
        python_rows.append(
            {
                "case": case["name"],
                "bestval": format(fit.fun, ".17g"),
                "iter": fit.nit,
                "nfeval": fit.nfev,
                "success": str(fit.success).lower(),
                **{
                    f"c{i + 1}": format(fit.x[i], ".17g") if i < n else ""
                    for i in range(3)
                },
            }
        )
    python_path = output / "python-fits.csv"
    with python_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=list(python_rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(python_rows)

    r_path = output / "r-fits.csv"
    environment = dict(
        os.environ, R_LIBS_USER=str(library), TZ="UTC", LANG="C", LC_ALL="C"
    )
    for key in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ):
        environment[key] = "1"
    completed = subprocess.run(
        [
            str(rscript),
            "--vanilla",
            str(here / "solver.R"),
            str(here / "cases.json"),
            str(python_path),
            str(r_path),
            str(output / "r-session.txt"),
        ],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    (output / "r-stdout.log").write_text(completed.stdout, encoding="utf-8")
    (output / "r-stderr.log").write_text(completed.stderr, encoding="utf-8")
    if completed.returncode:
        raise RuntimeError(
            f"Source R optimizer exited {completed.returncode}; see retained logs"
        )

    r_rows = {row["case"]: row for row in csv.DictReader(r_path.open(encoding="utf-8"))}
    summary: list[dict[str, object]] = []
    for case in config["cases"]:
        name = case["name"]
        inputs = _arrays(case)
        n = len(inputs[0])
        py = fits[name]
        row = r_rows[name]
        r_candidate = np.array([float(row[f"c{i + 1}"]) for i in range(n)])
        r_objective = float(row["bestval"])
        py_at_r = tf(r_candidate, *inputs)
        r_at_py = float(row["r_at_python"])
        optimum = _known_optimum(name)
        assert py.success and -1e-12 <= py.fun - optimum <= MAX_OPTIMUM_GAP
        assert -1e-12 <= r_objective - optimum <= MAX_OPTIMUM_GAP
        assert abs(py_at_r - r_objective) <= MAX_CROSS_EVALUATION_GAP
        assert abs(r_at_py - py.fun) <= MAX_CROSS_EVALUATION_GAP
        summary.append(
            {
                "case": name,
                "known_optimum": optimum,
                "python_best": py.fun,
                "r_best": r_objective,
                "python_gap": py.fun - optimum,
                "r_gap": r_objective - optimum,
                "python_at_r_gap": py_at_r - r_objective,
                "r_at_python_gap": r_at_py - py.fun,
                "python_success": py.success,
                "python_iterations": py.nit,
                "python_evaluations": py.nfev,
                "r_iterations": int(row["iter"]),
                "r_evaluations": int(row["nfeval"]),
            }
        )
    with (output / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=list(summary[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(summary)
    paths = [
        here / "cases.json",
        here / "solver.R",
        here / "replay.py",
        source,
        repository
        / "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/optimized.py",
        repository
        / "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/optimization/solver.py",
    ]
    report = {
        "schema_version": "love-optimizer-solution-quality.1",
        "status": "passed",
        "source_package": "disqover 0.9.14",
        "rscript_sha256": _sha(rscript),
        "input_sha256": {
            str(path.relative_to(repository)): _sha(path) for path in paths
        },
        "maximum_optimum_gap": MAX_OPTIMUM_GAP,
        "maximum_cross_evaluation_gap": MAX_CROSS_EVALUATION_GAP,
        "case_count": len(summary),
        "output_sha256": {
            name: _sha(output / name)
            for name in (
                "python-fits.csv",
                "r-fits.csv",
                "summary.csv",
                "r-session.txt",
            )
        },
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
