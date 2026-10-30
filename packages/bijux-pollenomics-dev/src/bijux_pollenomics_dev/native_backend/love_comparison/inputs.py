"""One shared binary64 input set for the existing fixed-candidate LOVE contract."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.api import LoveConfig
from bijux_pollenomics_lra.resources.examples import load_love_example

from ..profiling import workloads

NAMES = ("local", "regional", "ppes", "rings", "candidates")
REPLAY = Path("docs/report/numerical-performance/love-source-comparison/replay.R")
SUPPORT = Path("packages/bijux-pollenomics-lra/tests/reference/lra_oracle/r_support.R")
ARCHIVE = Path("packages/bijux-pollenomics-lra/vendor/disqover_0.9.14.tar.gz")
CONFIG = LoveConfig(
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


def frame(path: Path) -> pd.DataFrame:
    """Retain correctly rounded numeric tokens and original labels."""
    return pd.read_csv(path, float_precision="round_trip", keep_default_na=False)


def write(directory: Path) -> dict[str, str]:
    """Export the packaged fixture once, with exact numeric hexadecimal sidecars."""
    local, regional, parameters, rings = load_love_example()
    contract = workloads("love-optimized-replay")[0].contract
    if contract["config"] != CONFIG.as_dict():
        raise ValueError("Declared LOVE public-call contract changed")
    candidates = np.asarray(contract["candidates"], dtype=float)
    if candidates.shape != (32, 10):
        raise ValueError("Declared LOVE candidate population changed")
    tables = {
        "local": local,
        "regional": regional,
        "ppes": parameters["ppes"],
        "rings": rings,
        "candidates": pd.DataFrame(candidates),
    }
    directory.mkdir()
    for name, table in tables.items():
        table.to_csv(directory / f"{name}.csv", index=False, float_format="%.17g")
        numeric = table.select_dtypes(include="number")
        exact = pd.DataFrame(
            {column: [float(v).hex() for v in numeric[column]] for column in numeric}
        )
        exact.to_csv(directory / f"{name}-hex.csv", index=False)
        restored = frame(directory / f"{name}.csv")
        if list(map(str, table.columns)) != list(
            restored.columns
        ) or not np.array_equal(
            restored[numeric.columns.astype(str)].to_numpy(float),
            numeric.to_numpy(float),
        ):
            raise ValueError("Shared LOVE decimal export changed binary64 inputs")
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(directory.iterdir())
    }


def read(directory: Path) -> dict[str, pd.DataFrame]:
    """Require every sidecar to agree with the decimal input, without coercion repair."""
    tables = {name: frame(directory / f"{name}.csv") for name in NAMES}
    for name, table in tables.items():
        numeric = table.select_dtypes(include="number")
        exact = frame(directory / f"{name}-hex.csv")
        if list(numeric.columns) != list(exact.columns):
            raise ValueError("Shared LOVE numeric labels differ")
        hex_values = np.asarray(
            [[float.fromhex(value) for value in row] for row in exact.to_numpy()]
        )
        if not np.array_equal(numeric.to_numpy(float), hex_values):
            raise ValueError("Shared LOVE hexadecimal input differs")
    return tables
