"""Numbered calendar year zero must not become a date or an absent endpoint."""

from __future__ import annotations

import pytest

from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.temporal import (
    _interval_from_relative_age_label,
    sead_dating_interval,
)
from bijux_pollenomics.core.temporal_semantics import admit_bp_interval


@pytest.mark.parametrize(
    "age_type",
    (
        "AD",
        "CE",
        "anno domini",
        "common era",
        "BC",
        "BCE",
        "before christ",
        "before common era",
    ),
)
@pytest.mark.parametrize("year", (0, "0", 0.0, 0.4, -0.4))
@pytest.mark.parametrize("other", (None, 1, 1950))
def test_year_zero_refuses_the_whole_calendar_interval(
    age_type: str, year: object, other: object
) -> None:
    for low, high in ((year, other), (other, year)):
        assert (
            sead_dating_interval(
                {"low_value": low, "high_value": high}, age_type=age_type
            )
            is None
        )


@pytest.mark.parametrize(
    "label",
    (
        "CAL_0_AD",
        "CAL_0_BC",
        "CAL_0_AD-",
        "CAL_0_BC-",
        "CAL_0-1_AD",
        "CAL_1-0_BC",
        "CAL_1-0_AD-",
        "CAL_1-0_BC-",
    ),
)
def test_encoded_calendar_year_zero_is_not_replaced_by_zero_bp(label: str) -> None:
    assert _interval_from_relative_age_label(label) is None


@pytest.mark.parametrize(
    "era,year,bp",
    (("CE", 1, 1949), ("BCE", 1, 1950), ("CE", 1950, 0), ("CE", 2000, -50)),
)
def test_valid_calendar_spacing_native_modern_dates_and_missing_bounds_remain(
    era: str, year: int, bp: int
) -> None:
    for low, high in ((year, year), (None, year), (year, None)):
        assert sead_dating_interval(
            {"low_value": low, "high_value": high}, age_type=era
        ) == (bp, bp)
    assert admit_bp_interval(bp, bp).refusal_reason_code == (
        "negative_bp" if bp < 0 else ""
    )


def test_bp_zero_and_valid_encoded_dates_are_unchanged() -> None:
    assert sead_dating_interval(
        {"low_value": 0, "high_value": None}, age_type="cal BP"
    ) == (0, 0)
    assert _interval_from_relative_age_label("CAL_PERIOD_0_0_BP") == (0, 0)
    assert _interval_from_relative_age_label("CAL_1950_AD") == (0, 0)
    assert _interval_from_relative_age_label("CAL_2000_AD") == (-50, -50)
    assert _interval_from_relative_age_label("CAL_1_BC") == (1950, 1950)
    assert _interval_from_relative_age_label("CAL_1242_AD-") == (0, 708)
