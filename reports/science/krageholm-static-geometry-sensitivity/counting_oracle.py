"""Independent exact binomial tails and fixed-response pair transformations."""

from __future__ import annotations

from fractions import Fraction
import math


def binomial_cdf(total: int, count: int, probability: Fraction) -> Fraction:
    """Sum exact integer binomial terms on one common denominator."""
    if not 0 <= probability <= 1 or total < 1:
        raise ValueError("Invalid binomial domain")
    if count < 0:
        return Fraction(0)
    if count >= total or probability == 0:
        return Fraction(1)
    if probability == 1:
        return Fraction(0)
    if count > total // 2:
        return 1 - binomial_cdf(total, total - count - 1, 1 - probability)
    numerator, denominator = probability.numerator, probability.denominator
    other = denominator - numerator
    term = other**total
    summed = term
    for index in range(count):
        dividend = term * (total - index) * numerator
        divisor = (index + 1) * other
        term, remainder = divmod(dividend, divisor)
        if remainder:
            raise ValueError("Exact polynomial recurrence lost integrality")
        summed += term
    return Fraction(summed, denominator**total)


def transformed_pair(
    probability: Fraction, deposition: tuple[float, float], ppe: tuple[float, float]
) -> tuple[Fraction, Fraction]:
    """Apply the quotient to exact binary64 response inputs."""
    if not 0 <= probability <= 1 or any(
        not math.isfinite(value) or value <= 0 for value in (*deposition, *ppe)
    ):
        raise ValueError("Invalid fixed response domain")
    factors = tuple(
        1 / (Fraction.from_float(k) * Fraction.from_float(p))
        for k, p in zip(deposition, ppe, strict=True)
    )
    left, right = factors[0] * probability, factors[1] * (1 - probability)
    cover = left / (left + right)
    return cover, 1 - cover


def verify_interval(
    counts: tuple[int, int],
    deposition: tuple[float, float],
    ppe: tuple[float, float],
    confidence: float,
    interval: tuple[float, float],
    cover: tuple[float, float],
    lower: tuple[float, float],
    upper: tuple[float, float],
    target_lower: str,
    tail_upper: tuple[str | None, str | None],
) -> dict[str, float | int | bool]:
    """Verify certificates and complementary enclosure without inverse beta calls."""
    count, total = counts[0], sum(counts)
    target = (1 - Fraction.from_float(confidence)) / 2
    reported_target = Fraction(target_lower)
    if not 0 < reported_target <= target:
        raise ValueError("Reported tail target is not a lower enclosure")
    left, right = map(Fraction.from_float, interval)
    if not 0 <= left <= right <= 1:
        raise ValueError("Probability bounds are not ordered")
    tails = (
        1 - binomial_cdf(total, count - 1, left) if count else Fraction(0),
        binomial_cdf(total, count, right) if count < total else Fraction(0),
    )
    for index, tail in enumerate(tails):
        if tail > target:
            raise ValueError("Exact binomial endpoint exceeds the confidence tail")
        declared = tail_upper[index]
        active = count > 0 if index == 0 else count < total
        if active != (declared is not None):
            raise ValueError("Missing or unsupported endpoint certificate")
        if declared is not None and not tail <= Fraction(declared) <= reported_target:
            raise ValueError("Directed tail certificate does not enclose exact tail")
    left_cover = transformed_pair(left, deposition, ppe)
    right_cover = transformed_pair(right, deposition, ppe)
    actual_low = (left_cover[0], right_cover[1])
    actual_high = (right_cover[0], left_cover[1])
    for i in range(2):
        if (
            not Fraction.from_float(lower[i])
            <= actual_low[i]
            <= actual_high[i]
            <= Fraction.from_float(upper[i])
        ):
            raise ValueError("Reported pair cover bounds fail exact outward enclosure")
    if not all(lower[i] <= cover[i] <= upper[i] for i in range(2)):
        raise ValueError("Point estimate lies outside reported interval")
    point = transformed_pair(Fraction(count, total), deposition, ppe)
    errors = [abs(float(point[i]) - cover[i]) for i in range(2)]
    if any(error > 2 * math.ulp(float(point[i])) for i, error in enumerate(errors)):
        raise ValueError("Point estimate differs from independent exact quotient")
    return {
        "exact_tail_checks": 2,
        "exact_cover_enclosures": 4,
        "point_checks": 2,
        "maximum_point_absolute_error": max(errors),
        "maximum_exact_tail": float(max(tails)),
        "all_exact_inequalities_passed": True,
    }
