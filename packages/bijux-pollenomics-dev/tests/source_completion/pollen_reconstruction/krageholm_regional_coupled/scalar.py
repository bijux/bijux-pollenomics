"""Scalar equations conditional on serialized native kernels, with signed LOVE."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from fractions import Fraction
import math

AXIS = ("Betula", "Ulmus")
METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError("Independent KRAG coupled: " + message)


def number(value: object) -> Fraction:
    """Interpret an integer exactly and a decimal token as the native binary64 cell."""
    require(type(value) in (int, float, Decimal), "finite native number required")
    assert isinstance(value, int | float | Decimal)
    try:
        binary = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError("Independent KRAG coupled: unrepresentable number") from exc
    require(math.isfinite(binary), "finite native number required")
    return Fraction(value) if type(value) is int else Fraction.from_float(binary)


def pair(
    values: Sequence[object], *, positive: bool = False
) -> tuple[Fraction, Fraction]:
    require(len(values) == 2, "literal two-taxon axis required")
    first, second = map(number, values)
    require(
        all(value > 0 if positive else value >= 0 for value in (first, second)),
        "nonnegative or positive domain violated",
    )
    return first, second


def close(values: Sequence[Fraction]) -> tuple[Fraction, Fraction]:
    require(
        len(values) == 2 and min(values) >= 0 and sum(values) > 0,
        "positive nonnegative composition required",
    )
    return values[0] / sum(values), values[1] / sum(values)


def percent_round(value: Fraction) -> float:
    """Choose the nearest binary64 decimal-grid endpoint, with even ties at three digits."""
    scalar = float(value)
    magnitude = abs(scalar)
    scaled = magnitude * 1000
    lower_integer = math.floor(scaled)
    lower, upper = lower_integer / 1000, math.ceil(scaled) / 1000
    down, up = magnitude - lower, upper - magnitude
    chosen = upper if up < down or (up == down and lower_integer % 2) else lower
    return math.copysign(chosen, scalar)


def reveals(
    counts: Sequence[object], ppe: Sequence[object], kernel: Sequence[object]
) -> tuple[Fraction, Fraction]:
    n, alpha, k = pair(counts), pair(ppe, positive=True), pair(kernel, positive=True)
    raw = close([n[i] / (alpha[i] * k[i]) for i in range(2)])
    rounded = [Fraction.from_float(percent_round(100 * value)) / 100 for value in raw]
    return rounded[0], rounded[1]


def signed_love(
    counts: Sequence[object],
    ppe: Sequence[object],
    regional: Sequence[object],
    local_kernel: Sequence[object],
    distant_kernel: Sequence[object],
) -> tuple[Fraction, Fraction]:
    n, alpha = pair(counts), pair(ppe, positive=True)
    c, local, distant = pair(regional), pair(local_kernel), pair(distant_kernel)
    relative = close([n[i] / alpha[i] for i in range(2)])
    denominator = sum(c[i] * local[i] for i in range(2))
    require(denominator > 0, "positive LOVE regional denominator required")
    background = [c[i] * distant[i] / denominator for i in range(2)]
    multiplier = 1 + sum(background)
    return relative[0] * multiplier - background[0], relative[
        1
    ] * multiplier - background[1]


def admitted_cover(values: Sequence[Fraction]) -> tuple[Fraction, Fraction]:
    """Retain signed reconstruction evidence; refuse its use as a spatial composition."""
    require(
        len(values) == 2 and min(values) >= 0 and max(values) <= 1,
        "signed LOVE output is inadmissible",
    )
    require(abs(float(sum(values) - 1)) <= 1e-9, "LOVE closure differs")
    return values[0], values[1]


def spatial_weights(
    method: str, distances: Sequence[object]
) -> tuple[Fraction, Fraction]:
    require(method in METHODS, "unknown fixed spatial baseline")
    d = pair(distances)
    if method == "training_mean":
        return Fraction(1, 2), Fraction(1, 2)
    if method == "nearest_site" or min(d) == 0:
        selected = [Fraction(value == min(d)) for value in d]
        return close(selected)
    return close([1 / value**2 for value in d])


def spatial_cover(
    compositions: Sequence[Sequence[Fraction]], weights: Sequence[Fraction]
) -> tuple[Fraction, Fraction]:
    require(
        len(compositions) == 2
        and len(weights) == 2
        and sum(weights) == 1
        and min(weights) >= 0,
        "exactly two weighted local predictors required",
    )
    covers = [admitted_cover(values) for values in compositions]
    first = sum((weights[j] * covers[j][0] for j in range(2)), Fraction())
    second = sum((weights[j] * covers[j][1] for j in range(2)), Fraction())
    return first, second


def forward(
    cover: Sequence[Fraction],
    regional_deposition: Sequence[object],
    local_kernel: Sequence[Sequence[object]],
    terrestrial_fraction: Sequence[object],
    ppe: Sequence[object],
) -> tuple[Fraction, Fraction]:
    admitted_cover(cover)
    require(abs(float(sum(cover) - 1)) <= 1e-12, "forward local cover closure differs")
    regional, alpha = pair(regional_deposition), pair(ppe, positive=True)
    require(
        len(local_kernel) == len(terrestrial_fraction) and bool(local_kernel),
        "matched forward rings required",
    )
    rings = [pair(row) for row in local_kernel]
    fractions = [number(value) for value in terrestrial_fraction]
    require(
        all(0 <= value <= 1 for value in fractions),
        "terrestrial ring fractions must be in [0,1]",
    )
    deposition = [
        regional[i]
        + alpha[i]
        * cover[i]
        * sum(fractions[j] * rings[j][i] for j in range(len(rings)))
        for i in range(2)
    ]
    return close(deposition)


def metrics(
    predicted: Sequence[Fraction], observed_counts: Sequence[object]
) -> dict[str, Fraction]:
    admitted_cover(predicted)
    truth = close(pair(observed_counts))
    error = sum((abs(predicted[i] - truth[i]) for i in range(2)), Fraction())
    return {"mean_absolute_fraction_error": error / 2, "total_variation": error / 2}
