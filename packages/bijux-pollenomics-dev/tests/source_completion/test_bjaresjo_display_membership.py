"""Preserve closed source-display membership without changing source admission."""

from __future__ import annotations

from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.bjaresjo_context import (
    _display_interval_members,
)


@pytest.mark.parametrize(
    "bounds,window,expected",
    [
        ((0, 0), (0, 0), True),
        ((0, 1), (1, 2), True),
        ((1, 2), (0, 1), True),
        ((0, 1), (2, 3), False),
        ((2, 3), (0, 1), False),
        ((0.25, 1.5), (1.5, 2.25), True),
        ((0.25, 1.5), (1.75, 2.25), False),
        ((0, 3), (1, 2), True),
    ],
)
def test_source_display_closed_membership(
    bounds: tuple[float, float], window: tuple[float, float], expected: bool
) -> None:
    record: dict[str, Any] = {
        "source_record_id": "native-display-record",
        "site_uuid": "native-site",
        "time_start_bp": bounds[0],
        "time_end_bp": bounds[1],
        "chronology_role": "display_only",
        "ecological_or_event_join": "refused",
    }
    result = _display_interval_members(
        [record], {"time_start_bp": window[0], "time_end_bp": window[1]}
    )
    assert result == ([record] if expected else [])
    if result:
        assert result[0] is record
        assert result[0]["ecological_or_event_join"] == "refused"


def test_display_records_and_distinct_sites_keep_different_denominators() -> None:
    records = [
        {
            "source_record_id": "first",
            "site_uuid": "same-site",
            "time_start_bp": 0,
            "time_end_bp": 1,
        },
        {
            "source_record_id": "second",
            "site_uuid": "same-site",
            "time_start_bp": 1,
            "time_end_bp": 2,
        },
        {
            "source_record_id": "third",
            "site_uuid": "other-site",
            "time_start_bp": 3,
            "time_end_bp": 4,
        },
    ]
    result = _display_interval_members(records, {"time_start_bp": 1, "time_end_bp": 1})
    assert [row["source_record_id"] for row in result] == ["first", "second"]
    assert len(result) == 2 and len({row["site_uuid"] for row in result}) == 1
    assert len(records) == 3
