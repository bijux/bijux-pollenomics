"""Challenge simultaneous allocation, heterogeneous weights and direction claims."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.literal_pair_trajectory.arithmetic import (
    family_confidence,
    outward,
    transition,
    weighted_bin,
)


@pytest.mark.parametrize("population", [1, 2, 15, 101, 10000])
def test_error_allocation_uses_original_population(population: int) -> None:
    confidence = Fraction.from_float(family_confidence(population))
    assert confidence >= 1 - Fraction(1, 20 * population)
    assert population * (1 - confidence) <= Fraction(1, 20)


@pytest.mark.parametrize("value", [-1, True, 0])
def test_invalid_family_population_refused(value: int) -> None:
    with pytest.raises(ValueError):
        family_confidence(value)


@pytest.mark.parametrize(
    "value", [Fraction(1, 3), Fraction(-1, 3), Fraction(0), Fraction(1), Fraction(-1)]
)
def test_directed_binary64_encloses_signed_exact_value(value: Fraction) -> None:
    assert (
        Fraction.from_float(outward(value, upper=False))
        <= value
        <= Fraction.from_float(outward(value, upper=True))
    )


def test_individual_bounds_are_count_weighted_without_pooled_refitting() -> None:
    rows = [
        {
            "pair_total": 1,
            "counts": [0, 1],
            "source_pointer": "a",
            "interval": {"cover_lower": [0.0, 0.2], "cover_upper": [0.8, 1.0]},
        },
        {
            "pair_total": 3,
            "counts": [3, 0],
            "source_pointer": "b",
            "interval": {"cover_lower": [0.4, 0.0], "cover_upper": [1.0, 0.6]},
        },
    ]
    result = weighted_bin(rows)
    assert result["point"] == [0.75, 0.25] and result["pair_total"] == 4
    expected = 3 * Fraction.from_float(0.4) / 4
    assert Fraction.from_float(result["lower"][0]) <= expected
    assert result["lower"][0] > 0.29 and result["upper"][0] >= 0.95
    assert result["source_pointers"] == ["a", "b"]


@pytest.mark.parametrize(
    "a,b,direction",
    [(0.1, 0.8, "positive"), (0.8, 0.1, "negative"), (0.3, 0.3, "indeterminate")],
)
def test_transition_requires_strictly_separated_intervals(
    a: float, b: float, direction: str
) -> None:
    def item(value: float) -> dict[str, Any]:
        return {
            "available": True,
            "lower": [value, 0],
            "upper": [value + 0.1, 1],
            "point": [value + 0.05, 0],
        }

    assert transition(item(a), item(b))["direction"] == direction


def test_empty_bins_are_unavailable_not_zero() -> None:
    empty = weighted_bin([])
    assert not empty["available"] and transition(empty, empty) == {
        "available": False,
        "direction": "unavailable",
    }
