"""Scientific temporal-semantics tests."""

from __future__ import annotations

import pytest

from bijux_pollenomics.evidence.scientific_review import (
    _locality_overlaps_point,
    _period_label_for,
    _validated_interval,
)

from .support import context_point, locality


@pytest.mark.parametrize(
    ("mean_bp", "expected"),
    [
        (0, "0-1000 BP"),
        (1000, "0-1000 BP"),
        (1001, "1001-3000 BP"),
        (3000, "1001-3000 BP"),
        (3001, "3001-6000 BP"),
        (6000, "3001-6000 BP"),
        (6001, "6001+ BP"),
        (None, "project_level_or_unresolved"),
    ],
)
def test_period_bins_preserve_zero_and_exact_boundaries(
    mean_bp: int | None,
    expected: str,
) -> None:
    assert _period_label_for(locality(mean_bp=mean_bp)) == expected


def test_closed_bp_intervals_overlap_at_a_shared_endpoint() -> None:
    assert _locality_overlaps_point(
        locality(younger_bp=0, older_bp=100),
        context_point(younger_bp=100, older_bp=200),
    )


@pytest.mark.parametrize(
    ("younger_bp", "older_bp"),
    [
        (None, None),
        (0, None),
        (None, 100),
        (-1, 100),
        (100, 0),
    ],
)
def test_invalid_or_incomplete_intervals_remain_noncomparable(
    younger_bp: int | None,
    older_bp: int | None,
) -> None:
    assert _validated_interval(younger_bp, older_bp) is None


def test_zero_is_a_valid_bp_value_not_missing_data() -> None:
    interval = _validated_interval(0, 100)
    assert interval is not None
    assert (interval.younger_bp, interval.older_bp) == (0, 100)
