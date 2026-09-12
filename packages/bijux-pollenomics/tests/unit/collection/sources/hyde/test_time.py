from __future__ import annotations

import pytest

from bijux_pollenomics.collection.sources.hyde import CalendarYear, TimeSupport
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal


def test_ce_bce_conversion_counts_year_starts_without_year_zero() -> None:
    assert CalendarYear(2, "BCE").signed_bp == 1951
    assert CalendarYear(1, "BCE").signed_bp == 1950
    assert CalendarYear(1, "CE").signed_bp == 1949
    assert CalendarYear(1950, "CE").signed_bp == 0
    assert CalendarYear(2000, "CE").signed_bp == -50
    assert CalendarYear(10000, "BCE").signed_bp == 11949
    with pytest.raises(IntakeRefusal, match="calendar_year_invalid"):
        CalendarYear(0, "BCE")


def test_interval_endpoint_order_and_closure_are_explicit() -> None:
    support = TimeSupport(CalendarYear(1, "BCE"), CalendarYear(1, "CE"), "interval")
    assert support.signed_bp_endpoints == (1950, 1949)
    with pytest.raises(IntakeRefusal, match="time_support_invalid"):
        TimeSupport(CalendarYear(2000, "CE"), CalendarYear(1900, "CE"), "interval")
    with pytest.raises(IntakeRefusal, match="time_support_invalid"):
        TimeSupport(CalendarYear(2000, "CE"), CalendarYear(2000, "CE"), "interval")
