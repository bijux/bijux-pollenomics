"""Preserve native point support and missing/boundary age semantics."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

PRODUCER = (
    Path(__file__).resolve().parents[5]
    / "reports/science/nordic-chronology-admission/qualify.py"
)


def module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "nordic_chronology_admission", PRODUCER
    )
    assert spec is not None and spec.loader is not None
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


@pytest.mark.parametrize(
    "point,index", [(0, 0), (99.999, 0), (100, 1), (200, None), (-1, None)]
)
def test_half_open_source_windows(point: float, index: int | None) -> None:
    assert module().window(point, [0, 100, 200]) == index


@pytest.mark.parametrize("point", [True, "100", float("nan"), float("inf")])
def test_nonnumeric_and_nonfinite_ages_are_refused(point: object) -> None:
    with pytest.raises(ValueError):
        module().window(point, [0, 100, 200])


@pytest.mark.parametrize(
    "lower,upper,status",
    [
        (None, None, "reported_bounds_missing"),
        (None, 90, "reported_bounds_missing"),
        (-41, 60, "reported_bounds_extend_outside_point_domain"),
        (0, 99, "reported_bounds_wholly_within_point_window"),
        (0, 100, "reported_bounds_cross_point_window_boundary"),
        (0, 200, "reported_bounds_extend_outside_point_domain"),
        (8, 10, "reported_bounds_inconsistent_with_point"),
    ],
)
def test_source_bounds_remain_separate_from_point_admission(
    lower: float | None, upper: float | None, status: str
) -> None:
    age: dict[str, Any] = {"age": 7, "ageyounger": lower, "ageolder": upper}
    assert module().bound_support(age, 0, [0, 100, 200]) == status
    assert module().window(age["age"], [0, 100, 200]) == 0
    assert age["ageyounger"] == lower


def test_source_custody_refusal_before_output(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="custody differs"):
        module().qualify(tmp_path)
