"""Verify source-owned clock records without observing or replacing a current clock."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.country_reports.sweden.clock import (
    certify,
)


def observations() -> tuple[dict[str, Any], dict[str, Any]]:
    before = {
        "TZ": "UTC0",
        "timezone": 0,
        "daylight": 0,
        "utc": "2000-01-01T12:00:00+00:00",
        "local_date_today": "2000-01-01",
        "tzname": ["UTC", "UTC"],
        "time_ns": 1000000000,
        "monotonic_ns": 1000000000,
    }
    after = deepcopy(before)
    after["time_ns"] += 2000000000
    after["monotonic_ns"] += 2000000000
    return before, after


def test_saved_same_day_UTC_clock_is_not_historical_date_recovery() -> None:
    before, after = observations()
    result = certify(before, after, "2000-01-01")
    assert result["actual_monotonic_elapsed_seconds"] == 2.0
    assert result["date_today_monkeypatched_or_overridden"] is False
    assert result["historical_generated_date_recovered"] is False


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("TZ", "local"),
        ("timezone", False),
        ("daylight", 1),
        ("tzname", ["UTC"]),
        ("utc", "2000-01-01T12:00:00+01:00"),
        ("utc", "2000-01-01T12:00:00"),
        ("time_ns", True),
        ("monotonic_ns", 0),
    ],
)
def test_untyped_or_nonUTC_native_clock_refuses(key: str, value: Any) -> None:
    before, after = observations()
    before[key] = value
    with pytest.raises(ValueError):
        certify(before, after, "2000-01-01")


@pytest.mark.parametrize("field", ["time_ns", "monotonic_ns"])
def test_reversed_or_over_budget_saved_clock_refuses(field: str) -> None:
    before, after = observations()
    after[field] = before[field] - 1
    with pytest.raises(ValueError):
        certify(before, after, "2000-01-01")
    after[field] = before[field] + 601000000000
    with pytest.raises(ValueError):
        certify(before, after, "2000-01-01")


def test_midnight_change_or_changed_timezone_names_refuses() -> None:
    before, after = observations()
    after["utc"] = "2000-01-02T00:00:01+00:00"
    after["local_date_today"] = "2000-01-02"
    with pytest.raises(ValueError):
        certify(before, after, "2000-01-01")
    before, after = observations()
    after["tzname"] = ["GMT", "GMT"]
    with pytest.raises(ValueError):
        certify(before, after, "2000-01-01")
