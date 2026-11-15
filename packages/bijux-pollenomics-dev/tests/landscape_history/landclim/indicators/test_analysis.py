"""Literal support and component checks for agricultural-context indicators."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import math
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.landscape_history.landclim.inputs import CellWindow

from ..support import means


def cells() -> tuple[CellWindow, ...]:
    a = means(
        Pinus=85,
        **{"Cerealia.t": 10, "Secale": 0, "Plantago.lanceolata.type": 2, "Poaceae": 3},
    )
    b = means(
        Pinus=75,
        **{"Cerealia.t": 0, "Secale": 20, "Plantago.lanceolata.type": 0, "Poaceae": 5},
    )
    return (
        CellWindow("a", 15.5, 55.5, 0, 100, "high", a, {}, "eligible", ""),
        CellWindow("b", 15.5, 57.5, 0, 100, "low", b, {}, "eligible", ""),
    )


def base_row(*, weighting: str = "area") -> Any:
    a, b = (
        (math.cos(math.radians(55.5)), math.cos(math.radians(57.5)))
        if weighting == "area"
        else (1, 1)
    )
    return {
        "band_count": 5,
        "band_index": 0,
        "south_latitude": 55.0,
        "north_latitude": 58.0,
        "younger_bp": 0,
        "older_bp": 100,
        "source_window": "0-100 BP",
        "policy": "available",
        "weighting": weighting,
        "count": 2,
        "grid_ids": ["a", "b"],
        "status": "available",
        "reason": "",
        "coverage": {
            "total": 2,
            "eligible": 2,
            "high": 1,
            "low": 1,
            "no_data": 0,
            "invalid": 0,
            "excluded": 0,
        },
        "metrics": {
            "source_OL": {
                "mean": (a * 15 + b * 25) / (a + b),
                "minimum": 15,
                "maximum": 25,
            },
            "cereals": {
                "mean": (a * 10 + b * 20) / (a + b),
                "minimum": 10,
                "maximum": 20,
            },
            "non_cereal_herbs": {"mean": 5.0, "minimum": 5.0, "maximum": 5.0},
        },
    }


@pytest.mark.parametrize("weighting", ["area", "equal"])
def test_components_use_literal_weights_and_not_sums_of_extrema(weighting: str) -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.indicators import derive_rows

    row = derive_rows(cells(), [base_row(weighting=weighting)])[0]
    a, b = (
        (math.cos(math.radians(55.5)), math.cos(math.radians(57.5)))
        if weighting == "area"
        else (1, 1)
    )
    assert row["metrics"]["rye"] == pytest.approx(
        {"mean": b * 20 / (a + b), "minimum": 0, "maximum": 20}
    )
    assert row["metrics"]["other_cereals"] == pytest.approx(
        {"mean": a * 10 / (a + b), "minimum": 0, "maximum": 10}
    )
    assert row["metrics"]["plantain"] == pytest.approx(
        {"mean": a * 2 / (a + b), "minimum": 0, "maximum": 2}
    )
    assert row["metrics"]["cereals"]["minimum"] == 10
    assert row["metrics"]["cereals"]["maximum"] == 20
    assert row["metrics"]["non_cereal_herbs"] == pytest.approx(
        {"mean": 5, "minimum": 5, "maximum": 5}
    )
    assert row["grid_ids"] == ["a", "b"]
    assert "standard_errors" not in row


@pytest.mark.parametrize("metric", ["source_OL", "cereals", "non_cereal_herbs"])
@pytest.mark.parametrize("stat", ["mean", "minimum", "maximum"])
def test_each_base_statistic_mismatch_is_refused(metric: str, stat: str) -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.indicators import derive_rows

    row = base_row()
    row["metrics"][metric][stat] += 0.01
    with pytest.raises(ValueError, match="baseline statistic"):
        derive_rows(cells(), [row])


@pytest.mark.parametrize(
    "failure", ["duplicate", "missing", "count", "ineligible", "band", "policy"]
)
def test_inconsistent_selected_support_is_refused(failure: str) -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.indicators import derive_rows

    row, source = base_row(), cells()
    if failure == "duplicate":
        row["grid_ids"] = ["a", "a"]
    elif failure == "missing":
        row["grid_ids"] = ["a", "missing"]
    elif failure == "count":
        row["count"] = 1
    elif failure == "ineligible":
        source = (replace(source[0], status="invalid"), source[1])
    elif failure == "band":
        row["band_index"] = 1
    else:
        row["policy"] = "high_quality"
    with pytest.raises(ValueError):
        derive_rows(source, [row])


def test_empty_fixed_gap_stays_unavailable_and_true_zero_stays_numeric() -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.indicators import derive_rows

    row = base_row()
    row.update(
        band_index=3,
        south_latitude=64.0,
        north_latitude=67.0,
        policy="fixed_recent",
        count=0,
        grid_ids=[],
        status="unavailable",
        reason="no_eligible_cells",
    )
    row["coverage"] = dict.fromkeys(row["coverage"], 0)
    row["metrics"] = {
        key: dict.fromkeys(("mean", "minimum", "maximum")) for key in row["metrics"]
    }
    result = derive_rows(cells(), [row])[0]
    assert result["reason"] == "no_eligible_cells"
    assert all(
        x is None for stats in result["metrics"].values() for x in stats.values()
    )
    zero_source = tuple(replace(c, estimates=means(Pinus=100)) for c in cells())
    row = base_row()
    row["metrics"] = {
        key: dict.fromkeys(("mean", "minimum", "maximum"), 0.0)
        for key in row["metrics"]
    }
    result = derive_rows(zero_source, [row])[0]
    assert all(x == 0 for stats in result["metrics"].values() for x in stats.values())


def test_per_cell_cereal_overlap_guard_cannot_be_hidden_by_cancellation() -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.indicators import derive_rows

    source = deepcopy(cells())
    source[0].estimates["AL"] += 1
    source[1].estimates["AL"] -= 1
    with pytest.raises(ValueError, match="cereal_source_mismatch"):
        derive_rows(source, [base_row(weighting="equal")])


def test_source_reader_retains_all_frozen_public_cohorts() -> None:
    from bijux_pollenomics_dev.landscape_history.landclim.indicators import (
        read_base_rows,
    )

    repository = Path(__file__).resolve().parents[6]
    rows = read_base_rows(
        repository / "reports/science/swedish-landscape-history/trajectories.csv"
    )
    assert len(rows) == 2250
    row = next(
        r
        for r in rows
        if r["policy"] == "fixed_recent"
        and r["band_count"] == 5
        and r["band_index"] == 3
        and r["younger_bp"] == 0
    )
    assert row["count"] == 0
    assert row["metrics"]["source_OL"]["mean"] is None
