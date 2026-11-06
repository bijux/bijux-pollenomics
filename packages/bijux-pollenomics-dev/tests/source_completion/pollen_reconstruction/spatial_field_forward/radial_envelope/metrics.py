"""Sign-aware finite deposition, closure and nonclosed-observation loss bounds."""

from __future__ import annotations

from fractions import Fraction

from .exact_arithmetic import (
    Interval,
    add,
    require,
    root_difference_square,
    root_interval,
)

METRICS = (
    "mean_absolute_fraction_error",
    "total_variation",
    "hellinger_distance",
)


def deposition(
    total: Fraction,
    first_bounds: Interval,
    first_cover: Fraction,
    second_cover: Fraction,
    ppe: Fraction,
) -> Interval:
    """Bound affine deposition with complementary mass coefficients."""
    require(
        total > 0 and ppe > 0 and min(first_cover, second_cover) >= 0,
        "positive mass/PPE and nonnegative covers required",
    )
    require(
        0 <= first_bounds[0] <= first_bounds[1] <= total, "inconsistent partition total"
    )
    values = tuple(
        ppe * (total * second_cover + (first_cover - second_cover) * endpoint)
        for endpoint in first_bounds
    )
    result = min(values), max(values)
    require(result[0] >= 0, "negative deposition")
    return result


def closure(first: Interval, second: Interval) -> tuple[Interval, Interval]:
    """Return complementary fraction intervals for two deposition ranges."""
    require(
        0 <= first[0] <= first[1] and 0 <= second[0] <= second[1],
        "nonnegative deposition intervals required",
    )
    require(
        first[0] + second[1] > 0 and first[1] + second[0] > 0,
        "undefined positive closure",
    )
    lo = first[0] / (first[0] + second[1])
    hi = first[1] / (first[1] + second[0])
    return (lo, hi), (1 - hi, 1 - lo)


def absolute_error(
    first: Fraction, observations: tuple[Fraction, Fraction]
) -> Fraction:
    """Compute mean absolute error for a two-component closed prediction."""
    return (abs(first - observations[0]) + abs(1 - first - observations[1])) / 2


def hellinger(first: Fraction, observations: tuple[Fraction, Fraction]) -> Interval:
    """Enclose Hellinger distance using root-difference intervals."""
    squared = add(
        root_difference_square(first, observations[0]),
        root_difference_square(1 - first, observations[1]),
    )
    return root_interval((squared[0] / 2, squared[1] / 2))


def metric_bounds(
    prediction: Interval, observations: tuple[Fraction, Fraction]
) -> dict[str, Interval]:
    """Bound the three metrics over a closed prediction interval."""
    require(
        0 <= prediction[0] <= prediction[1] <= 1, "closed prediction bounds required"
    )
    require(
        all(0 <= value <= 1 for value in observations) and sum(observations) > 0,
        "finite observed components required",
    )
    lo, hi = prediction
    candidates = {lo, hi}
    candidates.update(
        knot for knot in (observations[0], 1 - observations[1]) if lo <= knot <= hi
    )
    absolute = [absolute_error(value, observations) for value in candidates]
    error_range = (
        min(absolute),
        max(absolute_error(value, observations) for value in (lo, hi)),
    )
    stationary = observations[0] / sum(observations)
    minimum_at = min(hi, max(lo, stationary))
    low = hellinger(minimum_at, observations)[0]
    high = max(hellinger(value, observations)[1] for value in (lo, hi))
    return {METRICS[0]: error_range, METRICS[1]: error_range, METRICS[2]: (low, high)}
