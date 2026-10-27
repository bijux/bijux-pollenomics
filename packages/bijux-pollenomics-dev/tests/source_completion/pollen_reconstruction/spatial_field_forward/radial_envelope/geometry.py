"""Derive circle means separately and check serialized radial mass certificates."""

from __future__ import annotations

from fractions import Fraction
import math
from typing import Any

from .exact_arithmetic import (
    Interval,
    finite,
    interval,
    outward,
    rational,
    require,
    sqrt_bounds,
)

Point = tuple[Fraction, Fraction]


def point(values: Any) -> Point:
    require(
        isinstance(values, list) and len(values) == 2, "two anchor coordinates required"
    )
    return finite(values[0]), finite(values[1])


def circle_bounds(
    first: Point, second: Point, radius: Fraction
) -> tuple[Interval, Fraction, Interval | None]:
    """Use the averaged reciprocal linear-cosine denominator independently."""
    require(
        first != second and radius >= 0,
        "distinct anchors and nonnegative radius required",
    )
    aa = sum((x * x for x in first), Fraction(0))
    bb = sum((x * x for x in second), Fraction(0))
    delta = bb - aa
    s = sum(((x + y) ** 2 for x, y in zip(first, second, strict=True)), Fraction(0))
    a = 2 * radius * radius + aa + bb
    radicand = a * a - 4 * radius * radius * s
    require(radicand > 0, "strictly positive angular denominator required")
    if delta == 0:
        return (Fraction(1, 2), Fraction(1, 2)), radicand, None
    require(s > 0, "non-symmetric anchor sum must be positive")
    roots = sqrt_bounds(radicand)
    require(roots[0] > 0, "root lattice cannot resolve positive denominator")
    constant = Fraction(1, 2) + delta / (2 * s)
    coefficient = delta * (s - a) / (2 * s)
    quotients = coefficient / roots[0], coefficient / roots[1]
    return (
        outward((constant + min(quotients), constant + max(quotients))),
        radicand,
        roots,
    )


def literal_circle_mean(
    first: tuple[float, float], second: tuple[float, float], radius: float, nodes: int
) -> float:
    """Independent angle-node control; this is not a certified radial integral."""
    require(nodes > 0 and first != second and radius >= 0, "invalid circle control")
    weights = []
    for node in range(nodes):
        angle = math.tau * (node + 0.5) / nodes
        x, y = radius * math.cos(angle), radius * math.sin(angle)
        da = (x - first[0]) ** 2 + (y - first[1]) ** 2
        db = (x - second[0]) ** 2 + (y - second[1]) ** 2
        weights.append(db / (da + db))
    return math.fsum(weights) / nodes


def check_angular(first: Point, second: Point, row: dict[str, Any]) -> Interval:
    expected, radicand, roots = circle_bounds(first, second, finite(row["radius_m"]))
    require(type(row["symmetry"]) is bool, "literal symmetry flag required")
    require(row["symmetry"] is (roots is None), "incorrect symmetry branch")
    if roots is None:
        require(
            row["sqrt_radicand_exact"] is None and row["sqrt_bounds_exact"] is None,
            "symmetric branch has no root certificate",
        )
    else:
        require(
            rational(row["sqrt_radicand_exact"]) == radicand, "angular radicand differs"
        )
        require(
            interval(row["sqrt_bounds_exact"]) == roots,
            "angular square-root certificate differs",
        )
    require(
        interval(row["weight_bounds_exact"]) == expected,
        "angular weight certificate differs",
    )
    return expected


def partition_bounds(
    masses: list[Fraction], weights: list[Interval], first: Point, second: Point
) -> tuple[Fraction, tuple[Interval, Interval]]:
    """Bound every nonnegative radial distribution with the given finite ring masses."""
    require(
        len(weights) == len(masses) + 1 and masses, "nested ring population differs"
    )
    require(
        all(value > 0 for value in masses), "positive serialized ring mass required"
    )
    require(first != second, "distinct source anchors required")
    low = high = Fraction(0)
    for mass, inner, outer in zip(masses, weights[:-1], weights[1:], strict=True):
        low += mass * min(inner[0], outer[0])
        high += mass * max(inner[1], outer[1])
    total = sum(masses, Fraction(0))
    require(0 <= low <= high <= total, "finite partition bounds outside total mass")
    return total, ((low, high), (total - high, total - low))
