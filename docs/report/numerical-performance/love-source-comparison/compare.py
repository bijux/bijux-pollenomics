"""Compare the published fixed-candidate LOVE workload with native source R."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import warnings

import numpy as np
import pandas as pd

from bijux_pollenomics_dev.native_backend.profiling import workloads
from bijux_pollenomics_lra.api import LoveConfig, run_love
from bijux_pollenomics_lra.resources.examples import load_love_example

ROOT = Path(__file__).resolve().parents[4]
INPUT_NAMES = ("local", "regional", "ppes", "rings", "candidates")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frame(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, float_precision="round_trip")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--rscript", type=Path, default=Path("/usr/local/bin/Rscript"))
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    input_dir = output / "input"
    input_dir.mkdir()

    local, regional, params, rings = load_love_example()
    workload = workloads("love-optimized-replay")[0]
    candidates = np.asarray(workload.contract["candidates"], dtype=float)
    config = LoveConfig(
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
    contract_sha = hashlib.sha256(
        json.dumps(workload.contract, sort_keys=True).encode()
    ).hexdigest()
    profile = json.loads(
        (
            ROOT / "docs/report/numerical-performance/love-source-profile/report.json"
        ).read_text()
    )
    source_closure = profile["measurement"]["source_sha256"]
    assert all(sha256(ROOT / name) == digest for name, digest in source_closure.items())
    assert profile["workload"]["contract_sha256"] == contract_sha
    assert config.as_dict() == workload.contract["config"]
    assert candidates.shape == (32, 10)

    original = {
        "local": local,
        "regional": regional,
        "ppes": params["ppes"],
        "rings": rings,
    }
    for name, table in original.items():
        table.to_csv(input_dir / f"{name}.csv", index=False, float_format="%.17g")
        numeric = table.select_dtypes(include="number")
        pd.DataFrame(
            {
                column: [float(value).hex() for value in numeric[column]]
                for column in numeric
            }
        ).to_csv(input_dir / f"{name}-hex.csv", index=False)
    pd.DataFrame(candidates).to_csv(
        input_dir / "candidates.csv", index=False, float_format="%.17g"
    )
    pd.DataFrame([[float(value).hex() for value in row] for row in candidates]).to_csv(
        input_dir / "candidates-hex.csv", index=False
    )
    for name, table in original.items():
        restored = frame(input_dir / f"{name}.csv")
        assert list(restored.columns) == list(table.columns)
        assert np.array_equal(
            restored.select_dtypes(include="number").to_numpy(),
            table.select_dtypes(include="number").to_numpy(),
        )
    assert np.array_equal(frame(input_dir / "candidates.csv").to_numpy(), candidates)
    for name in INPUT_NAMES:
        decimal = frame(input_dir / f"{name}.csv").select_dtypes(include="number")
        exact = frame(input_dir / f"{name}-hex.csv")
        assert list(decimal.columns) == list(exact.columns)
        assert np.array_equal(
            decimal.to_numpy(dtype=float),
            np.asarray(
                [[float.fromhex(value) for value in row] for row in exact.to_numpy()]
            ),
        )

    # Python consumes the exported files that native R reads, including candidates.
    local = frame(input_dir / "local.csv")
    regional = frame(input_dir / "regional.csv")
    ppes = frame(input_dir / "ppes.csv")
    rings = frame(input_dir / "rings.csv")
    candidates = frame(input_dir / "candidates.csv").to_numpy(dtype=float)
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", message="Terrestrial area exceeds geometric ring area"
        )
        python = run_love(
            local, regional, ppes, rings, config, replay_candidates=candidates
        )
        assert np.allclose(
            np.asarray(workload.consume(), dtype=float),
            python.cover["mean"].to_numpy(dtype=float),
            rtol=0,
            atol=0,
            equal_nan=True,
        )
    python.cover["mean"].to_csv(output / "python-cover.csv", index=False)
    python.pollen_percentages["mean"].to_csv(output / "python-pollen.csv", index=False)
    assert python.objective_values is not None
    python.objective_values.to_csv(output / "python-objective.csv", index=False)
    python.auxiliary["K"].to_csv(output / "python-k.csv", index=False)

    support = (
        ROOT / "packages/bijux-pollenomics-lra/tests/reference/lra_oracle/r_support.R"
    )
    archive = ROOT / "packages/bijux-pollenomics-lra/vendor/disqover_0.9.14.tar.gz"
    replay = Path(__file__).with_name("replay.R")
    command = [
        str(args.rscript),
        "--vanilla",
        str(replay),
        str(input_dir),
        str(output),
        str(args.library.resolve()),
        sha256(archive),
        str(support),
    ]
    process = subprocess.run(
        command, text=True, capture_output=True, check=False, timeout=180
    )
    (output / "r-stdout.log").write_text(process.stdout)
    (output / "r-stderr.log").write_text(process.stderr)
    report: dict[str, object] = {
        "schema_version": "love-identical-input-source-comparison.v1",
        "workload": "love-optimized-replay",
        "contract_sha256": contract_sha,
        "source_archive_sha256": sha256(archive),
        "profile_source_files_verified": len(source_closure),
        "producer_sha256": {
            name: sha256(path)
            for name, path in (
                ("compare.py", Path(__file__)),
                ("replay.R", replay),
                ("r_support.R", support),
            )
        },
        "input_sha256": {
            filename: sha256(input_dir / filename)
            for filename in sorted(path.name for path in input_dir.iterdir())
        },
        "command": command,
        "r_exit_code": process.returncode,
    }
    if process.returncode == 0:
        parsed_input_agrees = True
        for name in INPUT_NAMES:
            py_input = frame(input_dir / f"{name}.csv")
            numeric = py_input.select_dtypes(include="number")
            py_parsed_values = numeric.to_numpy(dtype=float).ravel(order="F")
            r_parsed_values = np.asarray(
                [
                    float.fromhex(line)
                    for line in (output / f"r-input-{name}-hex.txt")
                    .read_text()
                    .splitlines()
                ]
            )
            parsed_input_agrees &= np.array_equal(py_parsed_values, r_parsed_values)
            if name != "candidates":
                r_input = frame(output / f"r-input-{name}.csv")
                text_columns = py_input.select_dtypes(exclude="number").columns
                parsed_input_agrees &= list(r_input.columns) == list(
                    py_input.columns
                ) and r_input[text_columns].equals(py_input[text_columns])
        report["parsed_input_agrees"] = bool(parsed_input_agrees)
        comparisons = {}
        for name in ("cover", "pollen", "objective", "k"):
            r_table = frame(output / f"r-{name}.csv")
            py_table = frame(output / f"python-{name}.csv")
            r_values = r_table.to_numpy(dtype=float)
            py_values = py_table.to_numpy(dtype=float)
            same_shape = r_values.shape == py_values.shape
            same_columns = list(r_table.columns) == list(py_table.columns)
            difference = np.abs(r_values - py_values) if same_shape else np.array([])
            comparisons[name] = {
                "shape": list(py_values.shape),
                "same_columns": same_columns,
                "finite_pairs": int(
                    np.sum(np.isfinite(r_values) & np.isfinite(py_values))
                )
                if same_shape
                else 0,
                "max_abs_difference": float(np.nanmax(difference))
                if np.isfinite(difference).any()
                else None,
                "passed": bool(
                    same_shape
                    and same_columns
                    and np.allclose(
                        r_values, py_values, atol=3e-10, rtol=1e-10, equal_nan=True
                    )
                ),
            }
        r_trace = frame(output / "r-trace.csv")
        python_indices = [
            int(np.flatnonzero(np.all(candidates == diagnostic.x, axis=1))[0]) + 1
            for diagnostic in python.diagnostics
        ]
        selection_agrees = (
            len(r_trace) == len(python_indices) == 8
            and r_trace["best_index"].to_list() == python_indices
            and bool((r_trace["nfev"] == 32).all())
            and all(diagnostic.nfev == 32 for diagnostic in python.diagnostics)
        )
        report["selected_candidate_indices"] = python_indices
        report["selected_candidates_agree"] = selection_agrees
        report["comparisons"] = comparisons
        report["trace_calls"] = len(r_trace)
        report["status"] = (
            "passed"
            if parsed_input_agrees
            and selection_agrees
            and all(item["passed"] for item in comparisons.values())
            else "failed"
        )
    else:
        report["status"] = "r_execution_failed"
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
