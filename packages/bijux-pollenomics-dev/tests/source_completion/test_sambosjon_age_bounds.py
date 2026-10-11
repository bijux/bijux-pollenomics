"""Check age-interval overlap at the exact 500-year bin boundaries."""

from __future__ import annotations

import pytest

from bijux_pollenomics_dev.source_completion.sambosjon_age_bounds import (
    _interval_bins,
)


@pytest.mark.parametrize(
    ("point", "younger", "older", "expected"),
    [
        (900, 750, 1000, (1,)),  # An older endpoint touch has no width in bin 2.
        (1000, 900, 1100, (1, 2)),
        (950, 900, 1100, (1, 2)),
        (750, 500, 999, (1,)),
    ],
)
def test_reported_age_interval_uses_positive_width_overlap(
    point: int, younger: int, older: int, expected: tuple[int, ...]
) -> None:
    assert _interval_bins(point, younger, older, 500) == expected


def test_age_interval_refuses_point_outside_source_bounds() -> None:
    with pytest.raises(ValueError, match="invalid or reversed sample age interval"):
        _interval_bins(1100, 750, 1000, 500)
