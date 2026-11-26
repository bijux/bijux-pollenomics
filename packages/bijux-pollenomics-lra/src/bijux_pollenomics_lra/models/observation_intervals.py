"""Validate declared binomial endpoints against their numerical profile."""

from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from math import isfinite

import scipy
from scipy.stats import binom

from bijux_pollenomics_lra.models.errors import ValidationError


@lru_cache(maxsize=4096)
def _exact_cdf_at_least(k: int, n: int, p: float, q: float) -> bool:
    """Compare the exact binary64 binomial CDF with q, stopping once decided."""
    if q <= 0:
        return True
    if k < 0:
        return False
    if k >= n:
        return True
    if p == 0:
        return True
    if p == 1 or q == 1:
        return False
    a, b = p.as_integer_ratio()
    c = b - a
    target = Fraction.from_float(q)
    threshold = target.numerator * b**n
    term = c**n
    total = term
    for j in range(k):
        if total * target.denominator >= threshold:
            return True
        term = term * (n - j) * a // ((j + 1) * c)
        total += term
    return bool(total * target.denominator >= threshold)


def validate_interval(
    *,
    effort: int,
    probability: float,
    coverage: float,
    lower: int,
    upper: int,
    scipy_version: str,
) -> None:
    """Check equal-tail boundaries without claiming draw replay or source authority."""
    alpha = (1 - coverage) / 2
    if not 0 < alpha < 0.5:
        raise ValidationError(
            "Observation interval coverage is not numerically resolvable"
        )
    if probability == 0 or probability == 1:
        expected = 0 if probability == 0 else effort
        if lower != expected or upper != expected:
            raise ValidationError("Observation interval contradicts its probability")
        return
    for endpoint, q in ((lower, alpha), (upper, 1 - alpha)):
        if effort <= 256:
            if _exact_cdf_at_least(
                endpoint - 1, effort, probability, q
            ) or not _exact_cdf_at_least(endpoint, effort, probability, q):
                raise ValidationError(
                    "Observation interval does not match equal-tail quantiles"
                )
        else:
            if scipy_version != scipy.__version__:
                raise ValidationError(
                    "Observation interval requires its recorded SciPy version"
                )
            below = float(binom.cdf(endpoint - 1, effort, probability))
            above = float(binom.cdf(endpoint, effort, probability))
            if (
                not isfinite(below)
                or not isfinite(above)
                or not below <= above
                or q - below <= 1e-12
                or above - q <= 1e-12
            ):
                raise ValidationError(
                    "Observation interval boundary is unresolved or differs"
                )
