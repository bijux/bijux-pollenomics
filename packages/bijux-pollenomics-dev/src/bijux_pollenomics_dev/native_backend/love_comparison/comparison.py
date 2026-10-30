"""Strict labels, native missingness and fixed-candidate output comparison."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ...lra_validation.reference_replay import numeric_vector_values
from .inputs import NAMES, frame

SHAPES = {"cover": (10, 10), "pollen": (10, 10), "objective": (10, 2), "k": (36, 10)}
ATOL, RTOL = 3e-10, 1e-10


def numeric(path: Path, *, python: bool = False) -> tuple[tuple[str, ...], np.ndarray]:
    """Admit only original writer missing tokens; malformed cells cannot disappear."""
    with path.open(newline="") as stream:
        records = list(csv.reader(stream))
    if not records or not records[0] or len(set(records[0])) != len(records[0]):
        raise ValueError("LOVE output headers are absent or duplicated")
    width = len(records[0])
    if any(len(row) != width for row in records[1:]):
        raise ValueError("LOVE output row width differs")
    tokens = [token for row in records[1:] for token in row]
    missing = {""} if python else {"NaN"}
    if any(
        token != token.strip() or (not token and not python) or token in {"NA", "nan"}
        for token in tokens
    ):
        raise ValueError("LOVE output missing token differs")
    values = numeric_vector_values(pd.Series(tokens, dtype=str)).reshape(-1, width)
    if any(
        not np.isfinite(value) and token not in missing
        for value, token in zip(values.ravel(), tokens, strict=True)
    ):
        raise ValueError("LOVE output contains unsupported nonfinite value")
    return tuple(records[0]), values


def compare(output: Path, input_dir: Path) -> dict[str, Any]:
    """Compare all four source products and every exact parsed input value."""
    for name in NAMES:
        expected = frame(input_dir / f"{name}-hex.csv")
        actual = [
            float.fromhex(token)
            for token in (output / f"r-input-{name}-hex.txt").read_text().splitlines()
        ]
        reference = [
            float.fromhex(token) for token in expected.to_numpy().ravel(order="F")
        ]
        if actual != reference:
            raise ValueError("R parsed LOVE input binary64 values differ")
        if name != "candidates":
            original = frame(input_dir / f"{name}.csv")
            parsed = frame(output / f"r-input-{name}.csv")
            if list(parsed.columns) != list(original.columns):
                raise ValueError("R parsed LOVE input labels differ")
            labels = original.select_dtypes(exclude="number").columns
            if not original[labels].equals(parsed[labels]):
                raise ValueError("R parsed LOVE taxon/row identities differ")
    comparisons = {}
    for name, shape in SHAPES.items():
        r_labels, r = numeric(output / f"r-{name}.csv")
        py_labels, py = numeric(output / f"python-{name}.csv", python=True)
        if r_labels != py_labels or r.shape != shape or py.shape != shape:
            raise ValueError("LOVE product labels or shapes differ")
        if not np.array_equal(np.isnan(r), np.isnan(py)):
            raise ValueError("LOVE product missing masks differ")
        finite = np.isfinite(r) & np.isfinite(py)
        expected_finite = {"cover": 40, "pollen": 40, "objective": 8, "k": 360}[name]
        if int(finite.sum()) != expected_finite:
            raise ValueError("LOVE source-valid/undefined ring population differs")
        absolute = np.abs(r[finite] - py[finite])
        nonzero = py[finite] != 0
        relative = absolute[nonzero] / np.abs(py[finite][nonzero])
        comparisons[name] = {
            "shape": shape,
            "finite_pairs": int(finite.sum()),
            "missing_pairs": int(np.isnan(r).sum()),
            "different_finite_entries": int(np.sum(r[finite] != py[finite])),
            "max_absolute_error": float(absolute.max()),
            "max_relative_error_nonzero_python": float(relative.max())
            if len(relative)
            else None,
            "passed": bool(np.allclose(r, py, atol=ATOL, rtol=RTOL, equal_nan=True)),
        }
    rtrace, pytrace = frame(output / "r-trace.csv"), frame(output / "python-trace.csv")
    if (
        len(rtrace) != 8
        or len(pytrace) != 8
        or not (rtrace.nfev == 32).all()
        or not (pytrace.nfev == 32).all()
        or rtrace.best_index.tolist() != pytrace.best_index.tolist()
    ):
        raise ValueError("LOVE candidate indices/search return populations differ")
    return {
        "products": comparisons,
        "selected_indices_one_based": rtrace.best_index.tolist(),
        "passed": all(row["passed"] for row in comparisons.values()),
    }
