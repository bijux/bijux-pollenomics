"""Conditional likelihood inversion of fixed homogeneous local deposition."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import finite_number, integer, vector

PROFILE = "homogeneous-fixed-input-likelihood-v1"
CLOSURE_TOLERANCE = 1e-12


@dataclass(frozen=True, slots=True)
class HomogeneousLikelihoodFit:
    """Point fit and floating-point diagnostics, without ecological acceptance."""

    cover: np.ndarray
    predicted: np.ndarray
    mixture: np.ndarray
    mean_negative_log_likelihood: float
    optimality_gap: float
    converged: bool
    exact_composition_fit: bool
    steps: int
    stop_reason: str
    vertex_condition_number: float
    observed_mass: float
    gap_tolerance: float
    profile: str = PROFILE


def _mass(values: np.ndarray, name: str) -> float:
    with np.errstate(over="ignore", invalid="ignore"):
        mass = float(values.sum())
    if not np.isfinite(mass) or mass <= 0:
        raise ValidationError(f"{name} must have finite positive aggregate mass")
    return mass


def _composition(values: object, name: str) -> np.ndarray:
    result = vector(values, name, nonnegative=True).copy()
    if abs(_mass(result, name) - 1.0) > CLOSURE_TOLERANCE:
        raise ValidationError(f"{name} must sum to one within absolute 1e-12")
    return result


def homogeneous_vertices(
    local_coefficients: object, regional_deposition: object
) -> tuple[np.ndarray, np.ndarray]:
    """Return pure-taxon pollen columns and scaled positive mixture denominators.

    For cover v, p_i=(a_i*v_i+b_i)/sum_j(a_j*v_j+b_j). The host
    binds a_i=PPE_i*sum_r(K_ri*terrestrial_fraction_r), fixed b_i, and their
    common units and taxon order. Each ring has the same local cover.
    Common coefficient scaling leaves pollen fractions and cover unchanged.
    """
    a = vector(local_coefficients, "local_coefficients", positive=True).copy()
    b = vector(regional_deposition, "regional_deposition", nonnegative=True).copy()
    if a.shape != b.shape:
        raise ValidationError("Local and regional coefficients must match taxa")
    scale = max(float(a.max()), float(b.max()))
    a /= scale
    b /= scale
    if np.any(a <= 0):
        raise ValidationError("Local coefficients underflow under common scaling")
    background = float(b.sum())
    d = a + background
    y = (np.diag(a) + b[:, None]) / d[None, :]
    if (
        not np.isfinite(d).all()
        or np.any(d <= 0)
        or not np.isfinite(y).all()
        or np.any(y < 0)
        or not np.allclose(y.sum(axis=0), 1.0, rtol=0, atol=CLOSURE_TOLERANCE)
    ):
        raise ValidationError("Invalid normalized homogeneous vertices")
    return y, d


def homogeneous_cover_to_mixture(
    cover: object, local_coefficients: object, regional_deposition: object
) -> np.ndarray:
    """Apply the closed-composition change of variables without mutating inputs."""
    v = _composition(cover, "cover")
    _, d = homogeneous_vertices(local_coefficients, regional_deposition)
    if v.shape != d.shape:
        raise ValidationError("Cover and coefficient dimensions must match")
    mixture = v * d
    return np.asarray(mixture / _mass(mixture, "mixture"))


def _cover(mixture: np.ndarray, denominators: np.ndarray) -> np.ndarray:
    # Zero-mixture taxa have zero cover and must not set reciprocal scale.
    # Evaluate only active entries: dividing by an inactive tiny denominator
    # can overflow before multiplication by its zero mixture weight.
    active = mixture > 0
    weights = np.zeros_like(mixture)
    weights[active] = mixture[active] * (
        float(denominators[active].min()) / denominators[active]
    )
    return weights / _mass(weights, "cover")


def fit_homogeneous_likelihood(
    observed_weights: object,
    local_coefficients: object,
    regional_deposition: object,
    *,
    gap_tolerance: float = 1e-7,
    max_steps: int = 10000,
    max_condition_number: float = 1e12,
) -> HomogeneousLikelihoodFit:
    """Fit the convex mean negative log likelihood over pure-taxon mixtures.

    Weights must be finite, nonnegative and have finite positive total mass.
    They represent a multinomial sampling likelihood only when they are actual
    integer counts; fractions give the same point objective but no count
    uncertainty. Zero-weight taxa use no pseudocount. This is a new estimator,
    separate from the source-compatible log-Euclidean LOVE profile.

    The simplex first-order gap bounds objective suboptimality in exact
    arithmetic. ``converged`` records a floating-point check, not a rigorous
    interval certificate or a bound on vegetation error. Dominant background
    can obscure cover even when this check passes. Numerically ill-conditioned
    vertices are refused under the declared condition limit. Geometry, PPE,
    regional deposition and taxon eligibility are fixed, not inferred here.

    Each pairwise simplex step uses at most 100 scalar root iterations. The
    returned stop reason and actual steps preserve exhaustion/nonconvergence.
    """
    n = vector(observed_weights, "observed_weights", nonnegative=True).copy()
    mass = _mass(n, "observed_weights")
    tolerance = finite_number(
        gap_tolerance, "gap_tolerance", minimum=0, strict_minimum=True
    )
    limit = integer(max_steps, "max_steps", minimum=0)
    condition_limit = finite_number(
        max_condition_number, "max_condition_number", minimum=1
    )
    y, d = homogeneous_vertices(local_coefficients, regional_deposition)
    if n.shape != d.shape:
        raise ValidationError("Observed weights and coefficients must match taxa")
    condition = float(np.linalg.cond(y))
    if not np.isfinite(condition) or condition > condition_limit:
        raise ValidationError(
            "Homogeneous vertices exceed the numerical condition limit",
            reason_code="homogeneous_likelihood_ill_conditioned",
        )
    q = n / mass
    keep = n > 0
    if np.any(q[keep] <= 0) or not np.isclose(
        q.sum(), 1.0, rtol=0, atol=CLOSURE_TOLERANCE
    ):
        raise ValidationError("Observed positive weights underflow on normalization")
    try:
        inverse = np.linalg.solve(y, q)
    except np.linalg.LinAlgError as exc:
        raise ValidationError(
            "Homogeneous vertex inversion is numerically singular",
            reason_code="homogeneous_likelihood_ill_conditioned",
        ) from exc
    if (
        np.isfinite(inverse).all()
        and np.all(inverse >= 0)
        and abs(float(inverse.sum()) - 1.0) <= CLOSURE_TOLERANCE
    ):
        mixture = inverse / _mass(inverse, "inverse mixture")
    else:
        mixture = np.full(n.size, 1.0 / n.size)

    def gradient(point: np.ndarray) -> np.ndarray:
        pollen = y @ point
        if not np.isfinite(pollen).all() or np.any(pollen[keep] <= 0):
            raise ValidationError(
                "Positive-weight taxon has invalid fitted probability"
            )
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            result = -(y[keep].T @ (q[keep] / pollen[keep]))
        if not np.isfinite(result).all():
            raise ValidationError("Homogeneous likelihood gradient is nonfinite")
        return np.asarray(result)

    steps = 0
    stop = "step_limit"
    for _ in range(limit):
        g = gradient(mixture)
        current_gap = float(g @ mixture - g.min())
        if not np.isfinite(current_gap) or current_gap < -CLOSURE_TOLERANCE:
            raise ValidationError("Invalid homogeneous likelihood optimality gap")
        if current_gap <= tolerance:
            stop = "gap_tolerance"
            break
        toward = int(np.argmin(g))
        active = np.flatnonzero(mixture > 0)
        away = int(active[np.argmax(g[active])])
        maximum = float(mixture[away])
        pollen = y @ mixture
        direction = y[:, toward] - y[:, away]

        def derivative(
            step: float,
            pollen: np.ndarray = pollen,
            direction: np.ndarray = direction,
        ) -> float:
            p = pollen + step * direction
            if np.any(p[keep] <= 0):
                return float("inf")
            return float(-q[keep] @ (direction[keep] / p[keep]))

        if derivative(maximum) <= 0:
            step = maximum
        else:
            try:
                step = float(
                    brentq(
                        derivative,
                        0.0,
                        maximum,
                        # Line precision scales with the available mass. The
                        # final objective gap still controls convergence.
                        xtol=max(np.finfo(float).eps * maximum, np.finfo(float).tiny),
                        rtol=4 * np.finfo(float).eps,
                        maxiter=100,
                    )
                )
            except (ValueError, RuntimeError):
                stop = "line_search_failed"
                break
        if step <= 0 or not np.isfinite(step):
            stop = "line_search_stalled"
            break
        mixture[toward] += step
        mixture[away] -= step
        steps += 1

    mixture = _composition(mixture, "fitted mixture")
    predicted = _composition(y @ mixture, "fitted pollen")
    cover = _composition(_cover(mixture, d), "fitted cover")
    if not np.allclose(
        homogeneous_cover_to_mixture(cover, local_coefficients, regional_deposition),
        mixture,
        rtol=0,
        atol=CLOSURE_TOLERANCE,
    ):
        raise ValidationError("Homogeneous mixture/cover round trip is unstable")
    g = gradient(mixture)
    raw_gap = float(g @ mixture - g.min())
    nll = float(-q[keep] @ np.log(predicted[keep]))
    if not np.isfinite(raw_gap) or raw_gap < -CLOSURE_TOLERANCE or not np.isfinite(nll):
        raise ValidationError("Invalid final homogeneous likelihood diagnostics")
    gap = max(0.0, raw_gap)
    converged = gap <= tolerance
    if converged:
        stop = "gap_tolerance"
    exact = bool(np.allclose(predicted, q, rtol=0, atol=CLOSURE_TOLERANCE))
    for value in (cover, predicted, mixture):
        value.setflags(write=False)
    return HomogeneousLikelihoodFit(
        cover,
        predicted,
        mixture,
        nll,
        gap,
        converged,
        exact,
        steps,
        stop,
        condition,
        mass,
        tolerance,
    )
