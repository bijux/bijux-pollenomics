"""Behavioral checks for published-model landscape history."""

from __future__ import annotations

from dataclasses import replace
import math

import pytest

from .support import cell, means


def test_band_edges_have_single_assignment() -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.aggregation import band_index

    for n in (4, 5, 6):
        for i in range(n + 1):
            assert band_index(55 + 15 * i / n, n) == min(i, n - 1)
    assert band_index(54.999, 5) is None
    assert band_index(70.001, 5) is None
    with pytest.raises(ValueError):
        band_index(60, 3)


def test_area_weights_and_cereal_ratio_use_same_support() -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.aggregation import aggregate

    rows = aggregate(
        (
            replace(cell("a", 55.5), estimates=means(Pinus=80, **{"Cerealia.t": 20})),
            cell("b", 57.5, Pinus=20, Poaceae=80),
        )
    )
    row = next(
        r
        for r in rows
        if (r["band_count"], r["band_index"], r["policy"], r["weighting"])
        == (5, 0, "available", "area")
    )
    wa, wb = math.cos(math.radians(55.5)), math.cos(math.radians(57.5))
    forest = (wa * 80 + wb * 20) / (wa + wb)
    cereal = wa * 20 / (wa + wb)
    assert row["metrics"]["tree_assigned"]["mean"] == pytest.approx(forest)
    assert row["metrics"]["cereal_share_non_tree"]["mean"] == pytest.approx(
        100 * cereal / (100 - forest)
    )
    assert row["metrics"]["tree_assigned"]["minimum"] == 20
    assert row["metrics"]["tree_assigned"]["maximum"] == 80
    assert row["grid_ids"] == ["a", "b"]
    assert row["source_standard_error_ranges"]["OL"] == {"minimum": 2, "maximum": 2}
    assert not any("confidence" in k for k in row)


def test_empty_high_quality_band_retains_nulls_and_exclusion_ids() -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.aggregation import aggregate

    rows = aggregate(
        (cell("a", 56, Pinus=100), cell("b", 57, status="no_data", Pinus=100))
    )
    row = next(
        r
        for r in rows
        if (r["band_count"], r["band_index"], r["policy"], r["weighting"])
        == (5, 0, "high_quality", "equal")
    )
    assert row["count"] == 0
    assert row["status"] == "unavailable"
    assert row["reason"] == "no_high_quality_cells"
    assert row["metrics"]["tree_assigned"]["mean"] is None
    assert row["coverage"] == {
        "total": 2,
        "high": 0,
        "low": 1,
        "no_data": 1,
        "invalid": 0,
        "eligible": 1,
        "excluded": 2,
    }
    assert row["excluded_grid_ids"] == ["a", "b"]
    assert len(rows) == (4 + 5 + 6) * 3 * 2


def test_fixed_recent_requires_all_eight_windows_not_just_latest() -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.aggregation import aggregate
    from bijux_pollenomics_dev.landscape_history.landclim.inputs import WINDOWS

    cells = []
    for younger, older in WINDOWS[:8]:
        for grid in ("a", "b"):
            x = cell(grid, 56, Pinus=100)
            cells.append(
                replace(
                    x,
                    younger_bp=younger,
                    older_bp=older,
                    status="invalid" if grid == "b" and younger == 100 else "eligible",
                )
            )
    rows = aggregate(tuple(cells))
    fixed = [
        r
        for r in rows
        if r["policy"] == "fixed_recent"
        and r["band_count"] == 5
        and r["band_index"] == 0
    ]
    assert len(fixed) == 16
    assert all(r["grid_ids"] == ["a"] for r in fixed)


def test_duplicate_grid_window_is_refused() -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.aggregation import aggregate

    x = cell("a", 56, Pinus=100)
    with pytest.raises(ValueError, match="duplicate"):
        aggregate((x, x))


def test_aggregate_rejects_inconsistent_grid_centers() -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.aggregation import aggregate

    first = cell("a", 56, Pinus=100)
    other = replace(first, latitude=60, younger_bp=100, older_bp=350)
    with pytest.raises(ValueError, match="center"):
        aggregate((first, other))


def test_area_denominator_reports_selected_and_full_support() -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.aggregation import aggregate

    rows = aggregate(
        (cell("a", 55.5, high=True, Pinus=100), cell("b", 57.5, Pinus=100))
    )
    row = next(
        r
        for r in rows
        if (r["band_count"], r["band_index"], r["policy"], r["weighting"])
        == (5, 0, "high_quality", "area")
    )
    expected = math.cos(math.radians(55.5)) / (
        math.cos(math.radians(55.5)) + math.cos(math.radians(57.5))
    )
    assert row["eligible_area_fraction"] == 1
    assert row["selected_area_fraction"] == pytest.approx(expected)
    assert row["area_weight_denominator_km2"] == row["selected_area_km2"]
    assert row["selected_area_km2"] < row["total_area_km2"]
    assert row["source_quality_counts"] == {"high": 1, "low": 1}


def test_fixed_support_omission_is_not_reported_as_missing_source_data() -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.aggregation import aggregate

    rows = aggregate((cell("a", 56, older=3700, Pinus=100),))
    outside = next(
        r
        for r in rows
        if r["policy"] == "fixed_recent"
        and r["band_count"] == 5
        and r["band_index"] == 0
    )
    assert outside["reason"] == "outside_fixed_recent_windows"
    assert outside["coverage"]["eligible"] == 1
    assert outside["eligible_area_fraction"] == 1
    assert outside["selected_area_fraction"] == 0
    rows = aggregate((cell("a", 56, Pinus=100),))
    missing_cohort = next(
        r
        for r in rows
        if r["policy"] == "fixed_recent"
        and r["band_count"] == 5
        and r["band_index"] == 0
    )
    assert missing_cohort["reason"] == "no_common_valid_cohort"
