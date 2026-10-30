"""Measure complete public Python LOVE calls on the shared input files."""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
from importlib.metadata import version
import io
import json
from pathlib import Path
import time
from typing import Any

import numpy as np
import pandas as pd

import bijux_pollenomics_lra
from bijux_pollenomics_lra.api import LRAError, run_love

from .inputs import CONFIG, read

WARM_CALLS = 5


def products(result: object) -> dict[str, pd.DataFrame]:
    """Select numerical public products, preserving source undefined cells."""
    from typing import Any, cast

    value = cast(Any, result)
    if value.objective_values is None:
        raise ValueError("Optimized LOVE objective output is missing")
    return {
        "cover": value.cover["mean"],
        "pollen": value.pollen_percentages["mean"],
        "objective": value.objective_values,
        "k": value.auxiliary["K"],
    }


def selection(result: object, candidates: np.ndarray) -> pd.DataFrame:
    """Expose first-min candidate identities without asserting search convergence."""
    from typing import Any, cast

    diagnostics = cast(Any, result).diagnostics
    rows = []
    for item in diagnostics:
        matches = np.flatnonzero(np.all(candidates == item.x, axis=1))
        if len(matches) != 1 or item.nfev != 32:
            raise ValueError("LOVE candidate selection or search budget differs")
        rows.append({"best_index": int(matches[0]) + 1, "nfev": item.nfev})
    if len(rows) != 8:
        raise ValueError("LOVE active ring/repeat population differs")
    return pd.DataFrame(rows)


def run(input_dir: Path, output: Path) -> dict[str, Any]:
    """Keep parsing/export separate from one first plus five warm public calls."""
    started = time.perf_counter()
    tables = read(input_dir)
    candidates = tables["candidates"].to_numpy(float)
    setup = time.perf_counter() - started
    times = []
    reference = None
    reference_trace = None
    for _ in range(WARM_CALLS + 1):
        before = time.perf_counter()
        result = run_love(
            tables["local"],
            tables["regional"],
            tables["ppes"],
            tables["rings"],
            CONFIG,
            replay_candidates=candidates,
        )
        times.append(time.perf_counter() - before)
        current = products(result)
        trace = selection(result, candidates)
        if reference is None:
            reference, reference_trace = current, trace
        elif (
            reference_trace is None
            or any(not table.equals(reference[name]) for name, table in current.items())
            or not trace.equals(reference_trace)
        ):
            raise ValueError("Repeated Python LOVE products or selections differ")
    export_started = time.perf_counter()
    assert reference is not None and reference_trace is not None
    for name, table in reference.items():
        table.to_csv(output / f"python-{name}.csv", index=False, float_format="%.17g")
    reference_trace.to_csv(output / "python-trace.csv", index=False)
    export_seconds = time.perf_counter() - export_started
    try:
        run_love(
            tables["local"],
            tables["regional"],
            tables["ppes"],
            tables["rings"],
            CONFIG,
            replay_candidates=np.zeros((32, 10)),
        )
    except LRAError as exc:
        refusal = str(exc)
        if "Every replay candidate has an undefined objective" not in refusal:
            raise
    else:
        raise ValueError("All-undefined LOVE replay did not refuse")
    configuration = io.StringIO()
    with redirect_stdout(configuration):
        np.show_config()
    return {
        "setup_seconds_excluding_imports": setup,
        "call_seconds": times,
        "export_seconds": export_seconds,
        "all_undefined_refusal": refusal,
        "dependency_versions": {
            name: version(name) for name in ("numpy", "pandas", "scipy")
        },
        "numpy_build_configuration": configuration.getvalue(),
        "lra_distribution_version": version("bijux-pollenomics-lra"),
        "lra_imported_version": bijux_pollenomics_lra.__version__,
        "search_returns_per_call": 256,
        "mandatory_certifications_per_call": 8,
    }


def main() -> int:
    """Write the declared Python wrapper values and timing records."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output), allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
