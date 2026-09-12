"""Reconstruction draws for the LRA engine."""

from __future__ import annotations

import numpy as np

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import (
    integer,
    rng_from,
    vector,
)


def rnorm_reveals(
    n: int,
    mean: object | None = None,
    sds: object | None = None,
    *,
    rng: None | int | np.random.Generator = None,
    max_attempts: int = 100_000,
) -> np.ndarray:
    """Draw a whole normal vector repeatedly until every PPE is nonnegative.

    This reproduces the source's *whole-vector* rejection rule.  A finite
    attempt cap prevents an accidental infinite loop for pathological inputs.
    """
    n = integer(n, "n")
    generator = rng_from(rng)
    means = np.broadcast_to(
        np.asarray(np.ones(n) if mean is None else mean, dtype=float),
        (n,),
    )
    errors = np.broadcast_to(
        np.asarray(np.ones(n) if sds is None else sds, dtype=float),
        (n,),
    )
    if not np.isfinite(means).all() or not np.isfinite(errors).all():
        raise ValidationError("PPE normal parameters must be finite")
    if np.any(errors < 0):
        raise ValidationError("PPE standard deviations cannot be negative")
    if np.any((means < 0) & (errors == 0)):
        raise ValidationError(
            "Positive PPE sampling is impossible for a negative mean and zero SD"
        )
    for _ in range(integer(max_attempts, "max_attempts")):
        draw = generator.normal(means, errors)
        if np.all(draw >= 0):
            return draw
    raise ValidationError("Positive-PPE rejection sampler exceeded max_attempts")


def multidraw(
    counts: object,
    *,
    rng: None | int | np.random.Generator = None,
) -> np.ndarray:
    """Return one multinomial pollen-count draw."""
    values = vector(counts, "counts", nonnegative=True)
    total = float(values.sum())
    if total <= 0 or not np.isclose(total, round(total), rtol=0, atol=1e-8):
        raise ValidationError("A multinomial pollen total must be a positive integer")
    return rng_from(rng).multinomial(int(round(total)), values / total)


def rmultinom_reveals(
    n: int = 1,
    pollen: object | None = None,
    *,
    rng: None | int | np.random.Generator = None,
) -> np.ndarray:
    """Draw pollen percentages in the source taxa-by-replicates orientation."""
    n = integer(n, "n")
    values = vector(pollen, "pollen", nonnegative=True)
    total = float(values.sum())
    if total <= 0 or not np.isclose(total, round(total), rtol=0, atol=1e-8):
        raise ValidationError("A multinomial pollen total must be a positive integer")
    draws = rng_from(rng).multinomial(int(round(total)), values / total, size=n)
    return 100 * draws.T / total


def maher_counts(
    n: int = 1,
    pollen: object | None = None,
    *,
    rng: None | int | np.random.Generator = None,
) -> np.ndarray:
    """Apply the Maher uncertainty equation to a counts-only vector."""
    del n  # retained for callback compatibility
    values = vector(pollen, "pollen", nonnegative=True)
    total = float(values.sum())
    if total <= 0:
        raise ValidationError("Pollen total must be positive")
    normal = rng_from(rng).normal(size=len(values))
    proportions = values / total
    numerator = (
        proportions
        + normal**2 / (2 * total)
        + normal
        * np.sqrt(proportions * (1 - proportions) / total + normal**2 / (4 * total**2))
    )
    return 100 * numerator / (1 + normal**2 / total)


def rMaher(
    n: int = 1,
    pollen: object | None = None,
    *,
    rng: None | int | np.random.Generator = None,
) -> np.ndarray:
    """Literal upstream helper, which discards its first pollen entry.

    The R helper expects a metadata-prefixed vector even though REVEALS passes a
    counts-only vector.  This mismatch is retained and documented.  Use
    ``maher_counts`` for an explicit counts-only callback.
    """
    values = vector(pollen, "pollen")
    if len(values) < 2:
        raise ValidationError("rMaher expects metadata followed by pollen counts")
    return maher_counts(n=n, pollen=values[1:], rng=rng)
