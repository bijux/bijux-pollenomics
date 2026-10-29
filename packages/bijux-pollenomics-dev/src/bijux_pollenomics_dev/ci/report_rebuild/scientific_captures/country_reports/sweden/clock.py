"""Validate the saved source-owned clock without reading a current clock."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def certify(
    before: dict[str, Any], after: dict[str, Any], generated_on: str
) -> dict[str, Any]:
    """Check recorded clock identities and the declared native time zone."""
    for row in (before, after):
        if (
            row.get("TZ") != "UTC0"
            or type(row.get("timezone")) is not int
            or type(row.get("daylight")) is not int
            or (row["timezone"] != 0)
            or (row["daylight"] != 0)
        ):
            raise ValueError("Actual native UTC clock configuration differs")
        if (
            type(row.get("TZ")) is not str
            or type(row.get("utc")) is not str
            or type(row.get("local_date_today")) is not str
            or (type(row.get("tzname")) is not list)
            or (len(row["tzname"]) != 2)
            or any(type(value) is not str or not value for value in row["tzname"])
        ):
            raise ValueError(
                "Typed native clock strings and complete timezone names required"
            )
        utc = datetime.fromisoformat(row["utc"])
        if (
            utc.utcoffset() != UTC.utcoffset(utc)
            or str(utc.date()) != row["local_date_today"]
        ):
            raise ValueError("Actual UTC and source-owned local date disagree")
        for key in ("time_ns", "monotonic_ns"):
            if type(row[key]) is not int or row[key] <= 0:
                raise ValueError("Typed native clock scalar required")
    if (
        type(generated_on) is not str
        or generated_on != before["local_date_today"]
        or generated_on != after["local_date_today"]
    ):
        raise ValueError("Producer day changed or crossed native UTC midnight")
    if before["tzname"] != after["tzname"]:
        raise ValueError("Native timezone observation changed during producer")
    elapsed = (after["monotonic_ns"] - before["monotonic_ns"]) / 1000000000.0
    wall = (after["time_ns"] - before["time_ns"]) / 1000000000.0
    if not 0 <= elapsed <= 600 or not 0 <= wall <= 600:
        raise ValueError("Actual clock interval exceeds source stage bound")
    return {
        "native_UTC_day": generated_on,
        "actual_before": before,
        "actual_after": after,
        "actual_monotonic_elapsed_seconds": elapsed,
        "date_today_monkeypatched_or_overridden": False,
        "historical_generated_date_recovered": False,
    }
