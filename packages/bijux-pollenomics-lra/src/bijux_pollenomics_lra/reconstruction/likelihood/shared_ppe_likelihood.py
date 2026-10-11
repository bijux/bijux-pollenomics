"""Conditional local likelihood fits with one PPE vector shared across regions."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from bijux_pollenomics_lra.dispersal.rounding import r_round
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.draws import rnorm_reveals
from bijux_pollenomics_lra.reconstruction.forward import forward_deposition
from bijux_pollenomics_lra.reconstruction.likelihood.homogeneous_likelihood import (
    HomogeneousLikelihoodFit,
    fit_homogeneous_likelihood,
)


@dataclass(frozen=True, slots=True)
class SharedPpeLikelihoodResult:
    """Nominal row followed by stochastic rows on one fixed taxon axis."""

    ppe_draws: np.ndarray
    regional_cover: np.ndarray
    local_cover: np.ndarray
    fits: tuple[HomogeneousLikelihoodFit, ...]
    forward_max_abs: np.ndarray


def _vector(value: object, name: str, size: int | None = None) -> np.ndarray:
    try:
        result = np.asarray(value, dtype=float)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValidationError(f"{name} must be numeric") from exc
    if result.ndim != 1 or not np.isfinite(result).all():
        raise ValidationError(f"{name} must be a finite vector")
    if size is not None and result.size != size:
        raise ValidationError(f"{name} differs from the taxon axis")
    return result.copy()


def fit_shared_ppe_likelihood(
    regional_counts: object,
    local_counts: object,
    ppe_mean: object,
    ppe_sd: object,
    ppe_covariance: object,
    regional_kernel: object,
    local_kernels: object,
    terrestrial_fractions: object,
    *,
    draws: int,
    seed: int,
    max_attempts: int = 100_000,
    gap_tolerance: float = 1e-7,
    max_steps: int = 10_000,
    max_condition_number: float = 1e12,
) -> SharedPpeLikelihoodResult:
    """Propagate diagonal PPE uncertainty through fixed regional and local inputs.

    The first row is the nominal mean, never a random draw. Stochastic rows use
    source-compatible whole-vector normal rejection under a declared diagonal
    covariance. The supplied SD must agree with that diagonal; this function
    cannot represent cross-taxon PPE covariance. Regional percentages use three
    decimal places before conversion to fractions, so their row sums may differ
    slightly from one. Every draw uses its own PPE vector for both regional
    cover and local/background deposition. The first local kernel row defines
    the homogeneous local domain; all remaining rows define background. The
    caller owns source identity, time support, geometry and taxon alignment.
    """
    if (
        type(draws) is not int
        or not 2 <= draws <= 10_000
        or type(seed) is not int
        or seed < 0
        or type(max_attempts) is not int
        or not 1 <= max_attempts <= 100_000
    ):
        raise ValidationError(
            "Shared-PPE draws, nonnegative seed and positive capped attempts "
            "must be explicit integers"
        )
    means = _vector(ppe_mean, "ppe_mean")
    size = means.size
    if size < 2 or np.any(means <= 0):
        raise ValidationError("Nominal PPE must be positive on at least two taxa")
    sds = _vector(ppe_sd, "ppe_sd", size)
    if np.any(sds < 0):
        raise ValidationError("PPE standard deviations cannot be negative")
    with np.errstate(over="ignore", invalid="ignore"):
        variances = sds * sds
    if not np.isfinite(variances).all():
        raise ValidationError("PPE variances must be finite")
    try:
        covariance = np.asarray(ppe_covariance, dtype=float)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValidationError("ppe_covariance must be numeric") from exc
    if (
        covariance.shape != (size, size)
        or not np.isfinite(covariance).all()
        or not np.array_equal(covariance, covariance.T)
        or np.any(np.diag(covariance) < 0)
        or np.count_nonzero(covariance - np.diag(np.diag(covariance))) != 0
        or not np.allclose(np.diag(covariance), variances, rtol=1e-12, atol=0)
    ):
        raise ValidationError("Shared-PPE helper requires declared diagonal covariance")
    regional_n = _vector(regional_counts, "regional_counts", size)
    local_n = _vector(local_counts, "local_counts", size)
    for name, counts in (("regional_counts", regional_n), ("local_counts", local_n)):
        with np.errstate(over="ignore", invalid="ignore"):
            mass = float(counts.sum())
        if (
            np.any(counts < 0)
            or not np.array_equal(counts, np.floor(counts))
            or not np.isfinite(mass)
            or mass <= 0
        ):
            raise ValidationError(f"{name} must have finite positive integer mass")
    regional_k = _vector(regional_kernel, "regional_kernel", size)
    try:
        local_k = np.asarray(local_kernels, dtype=float)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValidationError("local_kernels must be numeric") from exc
    fractions = _vector(terrestrial_fractions, "terrestrial_fractions")
    if (
        np.any(regional_k <= 0)
        or local_k.ndim != 2
        or local_k.shape != (fractions.size, size)
        or fractions.size < 2
        or not np.isfinite(local_k).all()
        or np.any(local_k < 0)
        or np.any(fractions < 0)
        or np.any(fractions > 1)
    ):
        raise ValidationError("Shared-PPE kernels or terrestrial fractions differ")
    local_weight = np.sum(local_k[:1] * fractions[:1, None], axis=0)
    background_weight = np.sum(local_k[1:] * fractions[1:, None], axis=0)
    if (
        not np.isfinite(local_weight).all()
        or not np.isfinite(background_weight).all()
        or np.any(local_weight <= 0)
        or np.any(background_weight < 0)
    ):
        raise ValidationError("Shared-PPE local/background kernel sums are invalid")

    generator = np.random.default_rng(seed)
    ppe = np.empty((draws, size), dtype=float)
    ppe[0] = means
    for index in range(1, draws):
        ppe[index] = rnorm_reveals(
            size, mean=means, sds=sds, rng=generator, max_attempts=max_attempts
        )
    if not np.isfinite(ppe).all() or np.any(ppe <= 0):
        raise ValidationError("A shared-PPE vector is not strictly positive")

    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        raw_regional = regional_n[None, :] / (ppe * regional_k[None, :])
        raw_mass = raw_regional.sum(axis=1)
        regional = (
            np.asarray(r_round(100 * raw_regional / raw_mass[:, None], 3), dtype=float)
            / 100
        )
    if (
        not np.isfinite(raw_regional).all()
        or not np.isfinite(raw_mass).all()
        or np.any(raw_mass <= 0)
        or not np.isfinite(regional).all()
        or np.any(regional < 0)
        or np.any(regional.sum(axis=1) <= 0)
    ):
        raise ValidationError("Shared-PPE regional cover is invalid")

    local_cover = np.empty_like(ppe)
    residual = np.empty(draws, dtype=float)
    fits: list[HomogeneousLikelihoodFit] = []
    for index, draw in enumerate(ppe):
        a = draw * local_weight
        b = draw * regional[index] * background_weight
        if not np.isfinite(a).all() or not np.isfinite(b).all():
            raise ValidationError("Shared-PPE local/background deposition is nonfinite")
        fit = fit_homogeneous_likelihood(
            local_n,
            a,
            b,
            gap_tolerance=gap_tolerance,
            max_steps=max_steps,
            max_condition_number=max_condition_number,
        )
        if not fit.converged or fit.optimality_gap > gap_tolerance:
            raise ValidationError(f"Shared-PPE draw {index} did not converge")
        forward = forward_deposition(fit.cover, b, local_k[:1], fractions[:1], draw)
        error = float(np.max(np.abs(forward.pollen_fraction - fit.predicted)))
        if not np.isfinite(error) or error > 1e-12:
            raise ValidationError(f"Shared-PPE draw {index} failed forward equality")
        local_cover[index] = fit.cover
        residual[index] = error
        fits.append(fit)
    for array in (ppe, regional, local_cover, residual):
        array.setflags(write=False)
    return SharedPpeLikelihoodResult(
        ppe_draws=ppe,
        regional_cover=regional,
        local_cover=local_cover,
        fits=tuple(fits),
        forward_max_abs=residual,
    )
