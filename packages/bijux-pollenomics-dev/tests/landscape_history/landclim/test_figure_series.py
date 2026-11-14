"""Protect scientific ranges and missing support at the plotting boundary."""

from __future__ import annotations

import math
from pathlib import Path
import runpy
from typing import Any

import pytest


@pytest.fixture
def series() -> dict[str, Any]:
    repository = Path(__file__).resolve().parents[5]
    return runpy.run_path(
        str(repository / "reports/science/swedish-landscape-history/figure_series.py")
    )


def row(
    younger: int,
    older: int,
    mean: float | None,
    low: float | None,
    high: float | None,
    count: int = 2,
) -> dict[str, Any]:
    return {
        "younger_bp": younger,
        "older_bp": older,
        "count": count,
        "metrics": {"cereals": {"mean": mean, "minimum": low, "maximum": high}},
    }


def test_midpoints_keep_saved_means_and_full_extrema(series: dict[str, Any]) -> None:
    x, mean, low, high = series["envelope"](
        [row(0, 100, 3.0, 0.0, 12.0), row(100, 350, 6.0, 1.0, 22.0)], "cereals"
    )
    assert x == [50.0, 225.0]
    assert mean == [3.0, 6.0]
    assert low == [0.0, 1.0]
    assert high == [12.0, 22.0]


def test_missing_window_does_not_become_zero_or_bridge(series: dict[str, Any]) -> None:
    x, mean, low, high = series["envelope"](
        [
            row(0, 100, 3.0, 0.0, 12.0),
            row(100, 350, None, None, None, 0),
            row(350, 700, 6.0, 1.0, 22.0),
        ],
        "cereals",
    )
    assert x == [50.0, 225.0, 525.0]
    assert all(math.isnan(values[1]) for values in (mean, low, high))
    assert mean[0] == 3.0 and mean[2] == 6.0


def test_absent_source_interval_inserts_a_break(series: dict[str, Any]) -> None:
    x, mean, low, high = series["envelope"](
        [row(0, 100, 3.0, 0.0, 12.0), row(350, 700, 6.0, 1.0, 22.0)], "cereals"
    )
    assert x[0] == 50.0 and x[2] == 525.0
    assert all(math.isnan(values[1]) for values in (x, mean, low, high))


def test_zero_and_single_grid_ranges_stay_degenerate(series: dict[str, Any]) -> None:
    _, mean, low, high = series["envelope"](
        [row(0, 100, 0.0, 0.0, 0.0, 1), row(100, 350, 12.0, 12.0, 12.0, 1)], "cereals"
    )
    assert mean == low == high == [0.0, 12.0]


@pytest.mark.parametrize(
    "sample",
    [
        row(0, 100, 6.0, 7.0, 22.0),
        row(0, 100, 6.0, None, 22.0),
        row(0, 100, 6.0, 0.0, float("nan")),
        row(0, 100, None, None, None, 2),
        row(0, 100, 6.0, 0.0, 22.0, 0),
    ],
)
def test_unsupported_range_panels_refuse(
    series: dict[str, Any], sample: dict[str, Any]
) -> None:
    with pytest.raises(ValueError):
        series["envelope"]([sample], "cereals")


def test_right_axis_includes_extrema_beyond_the_mean(series: dict[str, Any]) -> None:
    assert series["range_ceiling"]([row(0, 100, 6.0, 0.0, 22.14)], "cereals") == 25.0
    assert series["range_ceiling"]([row(0, 100, 6.0, 0.0, 35.0)], "cereals") == 35.0
    assert series["range_ceiling"]([row(0, 100, 0.0, 0.0, 0.0)], "cereals") == 5.0
