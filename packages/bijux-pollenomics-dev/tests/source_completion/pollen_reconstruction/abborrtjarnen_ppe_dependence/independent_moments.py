"""Independent exact scalar fixed-panel derivatives and covariance contractions."""

from __future__ import annotations

from fractions import Fraction
import math
from typing import Any

import numpy as np

Rational = tuple[Fraction, ...]
ATOL, RTOL = 2e-14, 2e-12


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _close(actual: Any, expected: Any, label: str) -> float:
    _fraction(actual)
    expected = float(expected)
    gap = abs(actual - expected)
    _require(gap <= ATOL + RTOL * abs(expected), f"{label} differs from scalar oracle")
    return float(gap)


def _array_close(actual: Any, expected: Any, label: str) -> float:
    left, right = np.asarray(actual), np.asarray(expected, dtype=float)
    _require(
        left.shape == right.shape and left.dtype.kind in "iuf", f"{label} axis differs"
    )
    return max(
        (
            _close(a.item(), b.item(), label)
            for a, b in zip(left.flat, right.flat, strict=True)
        ),
        default=0.0,
    )


def _fraction(value: Any) -> Fraction:
    """Interpret a saved finite binary64 value without decimal-token rounding."""
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("A finite native number is required")
    return Fraction(value)


def _window(
    counts: tuple[int, ...], deposition: Rational, ppe: Rational
) -> tuple[Rational, tuple[Rational, ...], Rational]:
    """Differentiate scalar inverse/closure with exact source-number arithmetic."""
    if (
        not counts
        or len(counts) != len(deposition)
        or len(counts) != len(ppe)
        or any(type(n) is not int or n < 0 for n in counts)
        or not sum(counts)
        or any(x <= 0 for x in (*deposition, *ppe))
    ):
        raise ValueError("Invalid scalar fixed-panel input")
    factors = tuple(1 / (k * p) for k, p in zip(deposition, ppe, strict=True))
    weights = tuple(n * a for n, a in zip(counts, factors, strict=True))
    total = sum(weights, Fraction())
    cover = tuple(w / total for w in weights)
    gradients = []
    count_variances = []
    for i, q in enumerate(cover):
        gradients.append(
            tuple(q * (cover[j] - int(i == j)) / ppe[j] for j in range(len(ppe)))
        )
        derivative = tuple(
            (int(i == j) - q) * factors[j] / total for j in range(len(ppe))
        )
        # diag(n) - nn'/N is contracted as independent scalar sums.
        count_variances.append(
            sum(
                (n * d * d for n, d in zip(counts, derivative, strict=True)), Fraction()
            )
            - sum((n * d for n, d in zip(counts, derivative, strict=True)), Fraction())
            ** 2
            / sum(counts)
        )
    return cover, tuple(gradients), tuple(count_variances)


def _count_matrix(
    counts: tuple[int, ...], factors: Rational, cover: Rational
) -> tuple[Rational, ...]:
    normalizer = sum((n * a for n, a in zip(counts, factors, strict=True)), Fraction())
    derivatives = tuple(
        tuple((int(i == j) - q) * a / normalizer for j, a in enumerate(factors))
        for i, q in enumerate(cover)
    )
    projected = tuple(
        sum((n * d for n, d in zip(counts, row, strict=True)), Fraction())
        for row in derivatives
    )
    return tuple(
        tuple(
            sum(
                (n * a * b for n, a, b in zip(counts, left, right, strict=True)),
                Fraction(),
            )
            - projected[i] * projected[j] / sum(counts)
            for j, right in enumerate(derivatives)
        )
        for i, left in enumerate(derivatives)
    )
