"""Exact source counts and explicit missing-value counterexamples."""

from __future__ import annotations

import pytest

from bijux_pollenomics.analysis.lra.materialization.counts import assess_count

from .support import observation


@pytest.mark.parametrize("value", (0, 1.0, 9007199254740993, 10**100))
def test_counts_never_round_through_binary64(value: int | float) -> None:
    row = observation(value)
    assessment = assess_count(row)
    assert assessment.status == "count_candidate"
    assert assessment.exact_count == int(value)
    assert type(row["source_value"]) is type(value)


@pytest.mark.parametrize(
    "value,reason",
    (
        (True, "count_is_not_numeric"),
        ("3", "count_is_not_numeric"),
        (1.5, "count_is_not_finite_integer"),
        (-1, "negative_count"),
    ),
)
def test_invalid_counts_cannot_become_matrix_entries(
    value: object, reason: str
) -> None:
    assessment = assess_count(observation(value))
    assert assessment.exact_count is None
    assert assessment.reason == reason


def test_absent_null_zero_and_percent_remain_separate() -> None:
    null = observation(None)
    absent = {
        **null,
        "detection_status": "not_provided_by_source",
        "source_payload": {"units": "NISP"},
    }
    assert assess_count(null).reason == "source_null"
    assert assess_count(absent).reason == "not_provided_by_source"
    assert assess_count(observation(0)).exact_count == 0
    assert (
        assess_count(observation(20, unit="percent", family="percentage")).exact_count
        is None
    )
    assert (
        assess_count(observation(20, unit="percent", family="count")).reason
        == "inconsistent_unit_family"
    )


def test_normalized_scalar_type_must_match_its_source_payload() -> None:
    row = observation(1)
    row["source_value"] = True
    assert assess_count(row).reason == "inconsistent_source_projection"
    row["source_value"] = 1.0
    assert assess_count(row).reason == "inconsistent_source_projection"
