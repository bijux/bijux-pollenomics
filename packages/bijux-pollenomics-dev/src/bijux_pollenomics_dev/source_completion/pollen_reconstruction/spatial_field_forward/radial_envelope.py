"""Exact conditional envelopes for finite ring masses and planar geometry."""

from __future__ import annotations

from fractions import Fraction
import math
from typing import Any

BITS = 96
Bounds = tuple[Fraction, Fraction]
METRICS = (
    "mean_absolute_fraction_error",
    "total_variation",
    "hellinger_distance",
)


def require(condition: bool, reason: str) -> None:
    """Refuse a conditional-envelope input when its required condition fails."""
    if not condition:
        raise ValueError(reason)


def rational(value: float | int) -> Fraction:
    """Convert an allowed finite integer or float to its rational value."""
    require(
        type(value) in (int, float) and math.isfinite(value),
        "Finite numeric value required",
    )
    return Fraction(value)


def encoded(interval: Bounds) -> list[str]:
    """Serialize ordered rational interval endpoints as strings."""
    require(interval[0] <= interval[1], "Reversed exact interval")
    return [str(interval[0]), str(interval[1])]


def decoded(interval: list[str]) -> Bounds:
    """Read two rational endpoints and reject reversed order."""
    require(len(interval) == 2, "Two exact interval endpoints required")
    values = Fraction(interval[0]), Fraction(interval[1])
    require(values[0] <= values[1], "Reversed exact interval")
    return values


def root_bounds(value: Fraction) -> Bounds:
    """Outward square-root lattice bounds verified by exact integer inequalities."""
    require(value >= 0, "Negative square-root domain; no clipping")
    lattice = 1 << BITS
    scaled = value.numerator << (2 * BITS)
    lower = math.isqrt(scaled // value.denominator)
    upper = lower if lower * lower * value.denominator == scaled else lower + 1
    return Fraction(lower, lattice), Fraction(upper, lattice)


def lattice_bounds(interval: Bounds) -> Bounds:
    """Enclose a rational interval on the fixed binary lattice."""
    lattice = 1 << BITS
    left, right = interval
    require(left <= right, "Reversed rational lattice domain")
    lower = left.numerator * lattice // left.denominator
    upper = -((-right.numerator * lattice) // right.denominator)
    return Fraction(lower, lattice), Fraction(upper, lattice)


def angular_certificate(
    radius: float, first: list[float], second: list[float]
) -> dict[str, Any]:
    """Bound the exact circle mean at the supplied finite geometry, not a projection."""
    require(len(first) == len(second) == 2, "Two planar coordinates required")
    r = rational(radius)
    a, b = [rational(v) for v in first], [rational(v) for v in second]
    require(r >= 0 and a != b, "Distinct anchors and nonnegative radius required")
    delta = sum((y * y - x * x for x, y in zip(a, b, strict=True)), Fraction(0))
    if delta == 0:
        return {
            "radius_m": radius,
            "symmetry": True,
            "sqrt_radicand_exact": None,
            "sqrt_bounds_exact": None,
            "weight_bounds_exact": encoded((Fraction(1, 2), Fraction(1, 2))),
        }
    norm_sum = sum(((x + y) ** 2 for x, y in zip(a, b, strict=True)), Fraction(0))
    norm_difference = sum(
        ((y - x) ** 2 for x, y in zip(a, b, strict=True)), Fraction(0)
    )
    u = 2 * (r * r - sum((x * y for x, y in zip(a, b, strict=True)), Fraction(0)))
    radicand = u * u + norm_sum * norm_difference
    root = root_bounds(radicand)
    require(
        norm_sum > 0 and root[0] > 0,
        "Fixed algebraic resolution does not resolve angular denominator",
    )
    values = [Fraction(1, 2) + delta / (2 * norm_sum) * (1 - u / d) for d in root]
    bounds = lattice_bounds((min(values), max(values)))
    require(
        0 <= bounds[0] <= bounds[1] <= 1,
        "Fixed angular enclosure leaves the weight domain",
    )
    return {
        "radius_m": radius,
        "symmetry": False,
        "sqrt_radicand_exact": str(radicand),
        "sqrt_bounds_exact": encoded(root),
        "weight_bounds_exact": encoded(bounds),
    }


def coefficients(
    masses: list[float], certificates: list[dict[str, Any]]
) -> tuple[Fraction, tuple[Bounds, Bounds]]:
    """Use one consistent refined K, keeping the two anchor factors complementary."""
    require(
        len(certificates) == len(masses) + 1 and len(masses) > 0,
        "Ring/endpoint populations differ",
    )
    weights = [decoded(row["weight_bounds_exact"]) for row in certificates]
    require(
        all(0 <= lo <= hi <= 1 for lo, hi in weights), "Angular weight domain differs"
    )
    exact = [rational(mass) for mass in masses]
    require(
        all(mass > 0 for mass in exact), "Every conditional ring mass must be positive"
    )
    total = sum(exact, Fraction(0))
    lower = sum(
        (mass * min(weights[i][0], weights[i + 1][0]) for i, mass in enumerate(exact)),
        Fraction(0),
    )
    upper = sum(
        (mass * max(weights[i][1], weights[i + 1][1]) for i, mass in enumerate(exact)),
        Fraction(0),
    )
    return total, ((lower, upper), (total - upper, total - lower))


def deposition(
    total: Fraction, first: Bounds, cover: list[float], ppe: float
) -> Bounds:
    """Bound deposition with complementary coefficients and fixed cover and PPE."""
    require(
        len(cover) == 2 and total > 0 and 0 <= first[0] <= first[1] <= total,
        "Invalid complementary coefficient domain",
    )
    a, b = [rational(value) for value in cover]
    productivity = rational(ppe)
    require(
        0 <= a <= 1 and 0 <= b <= 1 and productivity > 0,
        "Invalid fixed cover/PPE domain",
    )
    endpoints = [
        productivity * (total * b + (a - b) * coefficient) for coefficient in first
    ]
    return min(endpoints), max(endpoints)


def normalized(masses: tuple[Bounds, Bounds]) -> Bounds:
    """Bound the first closed component of two nonnegative mass intervals."""
    first, second = masses
    require(
        0 <= first[0] <= first[1] and 0 <= second[0] <= second[1],
        "Invalid positive deposition range",
    )
    require(
        first[0] + second[1] > 0 and first[1] + second[0] > 0,
        "Undefined positive normalization",
    )
    return first[0] / (first[0] + second[1]), first[1] / (first[1] + second[0])


def squared(interval: Bounds) -> Bounds:
    """Bound an interval square while retaining any zero crossing."""
    lower, upper = interval
    require(lower <= upper, "Reversed square interval")
    endpoints = lower * lower, upper * upper
    return (Fraction(0) if lower <= 0 <= upper else min(endpoints)), max(endpoints)


def hellinger_at(probability: Fraction, observed: tuple[Fraction, Fraction]) -> Bounds:
    """Construct the norm from root differences, avoiding subtractive cancellation."""
    require(
        0 <= probability <= 1 and all(value >= 0 for value in observed),
        "Invalid Hellinger domain",
    )
    norms = []
    for predicted, actual in zip((probability, 1 - probability), observed, strict=True):
        a, b = root_bounds(predicted), root_bounds(actual)
        norms.append(squared((a[0] - b[1], a[1] - b[0])))
    lower = sum((norm[0] for norm in norms), Fraction(0)) / 2
    upper = sum((norm[1] for norm in norms), Fraction(0)) / 2
    return root_bounds(lower)[0], root_bounds(upper)[1]


def metric_ranges(
    probability: Bounds, observation: list[float]
) -> dict[str, list[str]]:
    """Keep both observed finite components; neither is silently reclosed."""
    lo, hi = probability
    require(
        0 <= lo <= hi <= 1 and len(observation) == 2,
        "Invalid probability/observation axes",
    )
    observed = rational(observation[0]), rational(observation[1])
    require(
        all(0 <= value <= 1 for value in observed) and sum(observed) > 0,
        "Invalid observed finite pair",
    )

    def absolute(p: Fraction) -> Fraction:
        return (abs(p - observed[0]) + abs(1 - p - observed[1])) / 2

    nearest_absolute = min(hi, max(lo, observed[0]))
    absolute_bounds = absolute(nearest_absolute), max(absolute(lo), absolute(hi))
    nearest_hellinger = min(hi, max(lo, observed[0] / sum(observed)))
    hellinger_bounds = (
        hellinger_at(nearest_hellinger, observed)[0],
        max(hellinger_at(p, observed)[1] for p in (lo, hi)),
    )
    return {
        METRICS[0]: encoded(absolute_bounds),
        METRICS[1]: encoded(absolute_bounds),
        METRICS[2]: encoded(hellinger_bounds),
    }
