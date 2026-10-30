"""Construct attaining planar Gram matrices and positive PPE moment witnesses."""

from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import product

import numpy as np
from numpy.typing import NDArray

from .independent_moments import Rational

Vector = tuple[Decimal, Decimal]


def _decimal(value: Fraction) -> Decimal:
    return Decimal(value.numerator) / Decimal(value.denominator)


def _range(lengths: Rational) -> tuple[Fraction, Fraction]:
    total = sum(lengths, Fraction())
    return max(Fraction(), 2 * max(lengths, default=Fraction()) - total), total


def _planar_sum(lengths: Rational, target: Fraction) -> tuple[Vector, ...]:
    """Construct prescribed lengths whose sum is (target, 0), without a search.

    The preceding resultant can take any length in its polygon interval.
    Intersect that interval with the triangle interval for the final side,
    then solve the triangle by its exact rational horizontal projection.
    Only the perpendicular square root needs high precision arithmetic.
    """
    lower, upper = _range(lengths)
    if any(a < 0 for a in lengths) or not lower <= target <= upper:
        raise ValueError("Unattainable vector resultant")
    if not lengths:
        return ()
    if len(lengths) == 1:
        return ((_decimal(target), Decimal()),)
    a = lengths[-1]
    lo, hi = _range(lengths[:-1])
    preceding = max(lo, abs(target - a))
    if preceding > min(hi, target + a):
        raise ValueError("Vector triangle does not intersect preceding interval")
    vectors = _planar_sum(lengths[:-1], preceding)
    if not target:
        return (*vectors, (-_decimal(a), Decimal()))
    horizontal = (target * target + preceding * preceding - a * a) / (2 * target)
    perpendicular_squared = preceding * preceding - horizontal * horizontal
    if perpendicular_squared < 0:
        raise ValueError("Negative exact triangle altitude")
    x, y = _decimal(horizontal), _decimal(perpendicular_squared).sqrt()
    if preceding:
        radius = _decimal(preceding)
        vectors = tuple(
            ((u * x - v * y) / radius, (u * y + v * x) / radius) for u, v in vectors
        )
    return (*vectors, (_decimal(target) - x, -y))


def _witness(
    gradient: Rational, sd: Rational, *, upper: bool, ppe: Rational | None = None
) -> tuple[NDArray[np.float64], Decimal, Decimal | None]:
    """Construct a fixed-diagonal PSD Gram witness for one scalar contrast.

    This is a different covariance for each requested extremum/contrast.
    A zero-gradient component retains its declared variance and contributes
    nothing to the scalar. It does not become a zero-variance parameter.
    """
    if len(gradient) != len(sd) or not sd or any(s < 0 for s in sd):
        raise ValueError("Gradient and nonnegative marginal SD axes differ")
    lengths = tuple(abs(g) * s for g, s in zip(gradient, sd, strict=True))
    bounds = _range(lengths)
    with localcontext() as context:
        context.prec = 96
        contributions = _planar_sum(lengths, bounds[int(upper)])
        vectors = tuple(
            (x / _decimal(g), y / _decimal(g)) if g else (_decimal(s), Decimal())
            for g, s, (x, y) in zip(gradient, sd, contributions, strict=True)
        )
        matrix = np.array(
            [[float(x * u + y * v) for u, v in vectors] for x, y in vectors]
        )
        scalar = sum(
            (
                sum(
                    (
                        _decimal(g) * vector[axis]
                        for g, vector in zip(gradient, vectors, strict=True)
                    ),
                    Decimal(),
                )
                ** 2
                for axis in range(2)
            ),
            Decimal(),
        )
        margin = None
        if ppe is not None:
            if len(ppe) != len(vectors):
                raise ValueError("PPE mean axis differs from moment witness")
            # Four equiprobable sign pairs have zero means and identity
            # latent covariance. This is an existence witness, not a fitted
            # or adopted parameter probability law.
            support = tuple(
                tuple(
                    _decimal(p) + a * x + b * y
                    for p, (x, y) in zip(ppe, vectors, strict=True)
                )
                for a, b in product((-1, 1), repeat=2)
            )
            margin = min(min(row) for row in support)
    return matrix, scalar, margin
