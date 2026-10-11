"""Exhaustive count-subset oracles and closed/half-open age boundary cases."""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from itertools import product
import random
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_age_support.interval_fraction import (
    interval_bin_membership,
    pooled_fraction_outer_bounds,
)


def test_threshold_extrema_match_exhaustive_integer_subset_oracle() -> None:
    rng = random.Random(20261002)
    for _ in range(100):
        denominator = rng.randrange(100)
        numerator = rng.randrange(denominator + 1)
        optional = []
        for _ in range(8):
            total = rng.randrange(1, 100)
            optional.append((rng.randrange(total + 1), total))
        enumerated = []
        for bits in product((False, True), repeat=8):
            n, d = numerator, denominator
            for include, counts in zip(bits, optional, strict=True):
                if include:
                    n += counts[0]
                    d += counts[1]
            if d:
                enumerated.append(Fraction(n, d))
        bounds = pooled_fraction_outer_bounds(numerator, denominator, optional)
        assert bounds.lower == min(enumerated)
        assert bounds.upper == max(enumerated)
        assert bounds.empty_bin_possible == (denominator == 0)


def test_count_ordering_remains_exact_above_float_precision() -> None:
    total = 10**400
    bounds = pooled_fraction_outer_bounds(0, 0, [(total - 1, total), (total, total)])
    assert bounds.lower == Fraction(total - 1, total)
    assert bounds.upper == 1
    assert bounds.empty_bin_possible


def test_absent_optional_samples_preserve_fixed_or_empty_population() -> None:
    fixed = pooled_fraction_outer_bounds(2, 5, [])
    assert fixed.lower == fixed.upper == Fraction(2, 5)
    assert not fixed.empty_bin_possible
    empty = pooled_fraction_outer_bounds(0, 0, [])
    assert empty.lower is empty.upper is None
    assert empty.empty_bin_possible


@pytest.mark.parametrize(
    "mandatory,optional",
    [
        ((True, 1), []),
        ((1.0, 2), []),
        ((-1, 2), []),
        ((3, 2), []),
        ((0, -1), []),
        ((0, 0), [(0, 0)]),
        ((0, 0), [(1, 0)]),
        ((0, 0), [(2, 1)]),
        ((0, 0), [(0, 1.0)]),
    ],
)
def test_noninteger_or_inconsistent_masses_refuse(
    mandatory: tuple[Any, Any], optional: list[tuple[Any, Any]]
) -> None:
    with pytest.raises(ValueError):
        pooled_fraction_outer_bounds(*mandatory, optional)


@pytest.mark.parametrize(
    "younger,older,expected",
    [
        ("1499", "1499", "outside"),
        ("1499", "1500", "optional"),
        ("1500", "1500", "mandatory"),
        ("1500", "1999.999999999999999999", "mandatory"),
        ("1500", "2000", "optional"),
        ("2000", "2000", "outside"),
        ("2000", "2001", "outside"),
        ("1000", "2500", "optional"),
    ],
)
def test_closed_interval_and_half_open_bin_endpoints(
    younger: str, older: str, expected: str
) -> None:
    assert (
        interval_bin_membership(
            Decimal(younger), Decimal(older), Decimal(1500), Decimal(2000)
        )
        == expected
    )


@pytest.mark.parametrize(
    "endpoints",
    [
        ("NaN", "2", "0", "3"),
        ("1", "Infinity", "0", "3"),
        ("2", "1", "0", "3"),
        ("1", "2", "3", "3"),
        ("1", "2", "4", "3"),
    ],
)
def test_invalid_age_interval_or_bin_refuses(endpoints: tuple[str, ...]) -> None:
    with pytest.raises(ValueError):
        interval_bin_membership(*map(Decimal, endpoints))
