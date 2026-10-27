"""Literal rational and integer-square-root checks, without producer imports."""

from __future__ import annotations

from fractions import Fraction
from math import isfinite, isqrt
from typing import Any

Interval = tuple[Fraction, Fraction]
BITS = 96


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError("Independent radial envelope: " + message)


def finite(value: object) -> Fraction:
    """Interpret a serialized finite binary64 quantity as its exact rational."""
    require(type(value) in {int, float}, "finite numeric value required")
    assert isinstance(value, int | float)
    number = float(value)
    require(isfinite(number), "nonfinite binary64 input")
    return Fraction.from_float(number)


def rational(value: Any) -> Fraction:
    require(type(value) is str, "canonical rational string required")
    result = Fraction(value)
    require(
        str(result) == value, "rational must be reduced with a positive denominator"
    )
    return result


def interval(value: Any) -> Interval:
    require(
        isinstance(value, list) and len(value) == 2, "two interval endpoints required"
    )
    low, high = rational(value[0]), rational(value[1])
    require(low <= high, "reversed interval")
    return low, high


def sqrt_bounds(value: Fraction, bits: int = BITS) -> Interval:
    """Bound the principal root on a fixed binary lattice by integer inequalities."""
    require(value >= 0 and bits > 0, "nonnegative root and positive precision required")
    scale = 1 << bits
    floor = isqrt((value.numerator * scale * scale) // value.denominator)
    low = Fraction(floor, scale)
    high = low if low * low == value else Fraction(floor + 1, scale)
    require(low * low <= value <= high * high, "integer root certificate failed")
    return low, high


def outward(bounds: Interval, bits: int = BITS) -> Interval:
    scale = 1 << bits
    low, high = bounds
    require(low <= high, "reversed outward interval")
    return Fraction((low * scale).__floor__(), scale), Fraction(
        (high * scale).__ceil__(), scale
    )


def add(first: Interval, second: Interval) -> Interval:
    return first[0] + second[0], first[1] + second[1]


def squared(bounds: Interval) -> Interval:
    low, high = bounds
    require(low <= high, "reversed square interval")
    ends = low * low, high * high
    return (Fraction(0) if low <= 0 <= high else min(ends), max(ends))


def root_interval(bounds: Interval) -> Interval:
    require(0 <= bounds[0] <= bounds[1], "nonnegative root interval required")
    return sqrt_bounds(bounds[0])[0], sqrt_bounds(bounds[1])[1]


def root_difference_square(first: Fraction, second: Fraction) -> Interval:
    a, b = sqrt_bounds(first), sqrt_bounds(second)
    return squared((a[0] - b[1], a[1] - b[0]))
