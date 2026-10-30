"""Conditional common-cover likelihood with distinct fixed site responses."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import logsumexp

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import finite_number, integer, matrix

PROFILE = "heterogeneous-fixed-response-multinomial-likelihood-v1"


@dataclass(frozen=True, slots=True)
class MultisiteLikelihoodFit:
    """A conditional point fit with numerical stationarity and effort accounting."""

    cover: np.ndarray
    predicted: np.ndarray
    site_totals: np.ndarray
    observed_taxon_totals: np.ndarray
    site_used: np.ndarray
    active_taxa: np.ndarray
    excluded_zero_total_site_indices: tuple[int, ...]
    gauge_taxon_index: int
    mean_negative_log_likelihood: float
    score_residual: float
    score_tolerance: float
    relative_count_residual: float
    relative_count_tolerance: float
    hessian_condition_number: float
    minimum_relative_information: float
    information_resolution_floor: float
    converged: bool
    steps: int
    stop_reason: str
    profile: str = PROFILE


def _require_unmasked(value: object, name: str) -> None:
    """Keep unresolved masks visible before common-cover numeric conversion."""
    if np.ma.isMaskedArray(value) and np.ma.is_masked(value):
        raise ValidationError(f"{name} contains masked values")


def _require_numeric_measurements(value: object, name: str) -> None:
    """Preserve raw Boolean provenance before common-cover numeric coercion."""
    _require_unmasked(value, name)
    try:
        original = np.asarray(value, dtype=object)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValidationError(f"{name} must contain numerical measurements") from exc
    if any(isinstance(item, (bool, np.bool_)) for item in original.flat):
        raise ValidationError(f"{name} cannot contain Boolean measurements")
    if any(isinstance(item, (complex, np.complexfloating)) for item in original.flat):
        raise ValidationError(f"{name} cannot contain complex measurements")


def _input_matrix(value: object, name: str, *, nonnegative: bool = False) -> np.ndarray:
    """Refuse Boolean or unresolved masked common-cover matrices before conversion."""
    _require_numeric_measurements(value, name)
    try:
        return matrix(value, name, nonnegative=nonnegative)
    except ValidationError:
        raise
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValidationError(f"{name} must be a numerical matrix") from exc


def _measured(value: object, shape: tuple[int, ...]) -> None:
    if np.ma.isMaskedArray(value) and np.ma.is_masked(value):
        raise ValidationError("taxon_measured contains unresolved missing metadata")
    try:
        mask = np.asarray(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValidationError(
            "An explicit common measured taxon matrix required"
        ) from exc
    if mask.dtype.kind != "b" or mask.shape != shape or not mask.all():
        raise ValidationError(
            "Every site/taxon cell must be explicitly measured on the same axis; missing taxa are not zero counts"
        )


def _owned(value: np.ndarray) -> np.ndarray:
    result = value.copy()
    result.setflags(write=False)
    return result


def fit_multisite_likelihood(
    counts: object,
    responses: object,
    *,
    taxon_measured: object,
    score_tolerance: float = 1e-10,
    relative_count_tolerance: float = 1e-8,
    max_steps: int = 200,
) -> MultisiteLikelihoodFit:
    """Fit one common composition under distinct fixed multinomial responses.

    Site s has p_si=a_si*v_i/sum_j(a_sj*v_j), with supplied positive response
    a_si=PPE_i*K_si and common closed cover v. Each site's actual grain count
    supplies its likelihood effort; sites are not assigned equal weight or
    pooled before correcting geometry. This is a distinct estimator from the
    historical Qa-ratio/site-bootstrap and geometry-correct-then-pool profiles.

    With theta_i=log(v_i/v_g), the per-grain negative log likelihood is a sum
    of logsumexp(theta+log(a_s)) minus the pooled observed log-ratio term.
    Its Hessian is sum_s(N_s/N)[diag(p_s)-p_s*p_s.T]. On a fully measured
    common axis with positive responses it is positive definite after fixing
    one active taxon gauge. Positive pooled counts make this reduced objective
    coercive; hence its finite minimizer is unique. Globally unobserved taxa
    have exact boundary cover zero: deleting their mass and reclosing raises
    every observed probability. No pseudocount or artificial cover floor is
    introduced. One active taxon therefore has an exact degenerate solution.

    Counts are nonnegative integer-valued numbers with aggregate mass below
    2**53, retaining exact integer admission in binary64. Missing/masked values,
    booleans, fractional counts, unmeasured cells and invalid responses refuse.
    Zero-effort rows contribute no information and are explicitly returned as
    excluded; an entirely empty cohort refuses. Predictions retain every row.

    Damped Newton solves the fixed-gauge objective in log space. Convergence
    requires both a full normalized score and a positive-taxon relative
    expected-count balance. These floating-point checks are not an interval proof,
    objective-gap bound, cover-error bound or uncertainty interval. Exhaustion,
    singular curvature and failed line searches remain visible. Physical
    common-cover applicability, source identities, matching time/units and
    omitted geometry/PPE/site-heterogeneity uncertainty belong to the caller.

    Before convergence, the reduced Hessian is scaled on each axis by the
    square root of its pooled positive taxon frequency. A minimum eigenvalue
    at or below machine epsilon gives an explicit floating-information refusal,
    even if a saturated score rounds to zero and the scalar condition number
    is one. This conservative arithmetic-resolution rule preserves count-scale
    differences; it neither removes exact identifiability nor certifies cover
    error. Information and stationarity are rechecked on the returned cover.
    """
    n = _input_matrix(counts, "counts", nonnegative=True).copy()
    a = _input_matrix(responses, "responses").copy()
    _measured(taxon_measured, n.shape)
    if a.shape != n.shape or np.any(a <= 0):
        raise ValidationError(
            "Fixed positive responses must match the site/taxon count matrix"
        )
    if np.any(n >= 2**53) or np.any(n != np.floor(n)):
        raise ValidationError("Exact nonnegative integer counts below 2**53 required")
    total = float(n.sum())
    if total >= 2**53:
        raise ValidationError("Aggregate integer count must be below 2**53")
    if total == 0:
        raise ValidationError(
            "No positive-count site is available", reason_code="no_positive_count_site"
        )
    _require_numeric_measurements(score_tolerance, "score_tolerance")
    _require_numeric_measurements(relative_count_tolerance, "relative_count_tolerance")
    _require_unmasked(max_steps, "max_steps")
    tolerance = finite_number(
        score_tolerance, "score_tolerance", minimum=0, strict_minimum=True
    )
    relative_tolerance = finite_number(
        relative_count_tolerance,
        "relative_count_tolerance",
        minimum=0,
        strict_minimum=True,
    )
    limit = integer(max_steps, "max_steps", minimum=0)
    site_totals = n.sum(axis=1)
    taxon_totals = n.sum(axis=0)
    used, active = site_totals > 0, taxon_totals > 0
    indices = np.flatnonzero(active)
    gauge = int(indices[np.argmax(taxon_totals[indices])])
    # Put a largest-count taxon in the gauge. Reduced scores then retain rare
    # expected counts directly, avoiding subtraction of two values near one.
    indices = np.append(indices[indices != gauge], gauge)
    weights = site_totals[used] / total
    observed = n[used][:, indices] / total
    observed_taxa = taxon_totals[indices] / total
    offsets = np.log(a[:, indices])
    offsets -= offsets[:, -1:]
    theta = (
        np.log(observed_taxa[:-1])
        - np.log(observed_taxa[-1])
        - weights @ offsets[used, :-1]
    )

    def evaluate(point: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
        logits = offsets + np.append(point, 0.0)[None, :]
        logp = logits - logsumexp(logits, axis=1, keepdims=True)
        probabilities = np.exp(logp)
        objective = float(-np.sum(observed * logp[used]))
        score = weights @ probabilities[used] - observed_taxa
        return objective, score, probabilities

    def relative_balance(score: np.ndarray) -> float:
        return float(np.max(np.abs(score) / observed_taxa))

    def curvature(probabilities: np.ndarray) -> np.ndarray:
        p = probabilities[used]
        reduced = p[:, :-1]
        hessian = -(reduced.T @ (weights[:, None] * reduced))
        # Sum the other probabilities directly: 1-p_i loses curvature when a
        # dominant probability rounds to one while smaller taxa remain positive.
        np.fill_diagonal(
            hessian,
            [
                float(weights @ (p[:, i] * np.sum(np.delete(p, i, axis=1), axis=1)))
                for i in range(reduced.shape[1])
            ],
        )
        return np.asarray(hessian)

    objective, score, probabilities = evaluate(theta)
    steps, stop = 0, "step_limit"
    condition = 1.0
    information_floor = float(np.finfo(float).eps)

    def relative_information(hessian: np.ndarray) -> float:
        if hessian.size == 0:
            return 1.0
        scale = np.sqrt(observed_taxa[:-1])
        normalized = hessian / scale[:, None] / scale[None, :]
        try:
            return float(np.linalg.eigvalsh(normalized)[0])
        except np.linalg.LinAlgError:
            return float("nan")

    for _ in range(limit):
        hessian = curvature(probabilities)
        information = relative_information(hessian)
        if not np.isfinite(information) or information <= information_floor:
            stop = "floating_information_unresolved"
            break
        if (
            float(np.max(np.abs(score))) <= tolerance
            and relative_balance(score) <= relative_tolerance
        ):
            stop = "count_balance_tolerances"
            break
        try:
            direction = np.linalg.solve(hessian, -score[:-1])
        except np.linalg.LinAlgError:
            stop = "singular_hessian"
            break
        descent = float(score[:-1] @ direction)
        if not np.isfinite(direction).all() or not np.isfinite(descent) or descent >= 0:
            stop = "invalid_newton_direction"
            break
        accepted = False
        for reduction in range(60):
            step = 2.0**-reduction
            # Only the trial addition may overflow; reject that candidate
            # before evaluating logits rather than emitting invalid-logit noise.
            with np.errstate(over="ignore"):
                candidate = theta + step * direction
            if not np.isfinite(candidate).all():
                continue
            next_objective, next_score, next_probabilities = evaluate(candidate)
            if (
                np.isfinite(next_objective)
                and next_objective <= objective + 1e-4 * step * descent
            ):
                theta, objective, score, probabilities = (
                    candidate,
                    next_objective,
                    next_score,
                    next_probabilities,
                )
                accepted = True
                steps += 1
                break
        if not accepted:
            stop = "line_search_failed"
            break
    logits = np.append(theta, 0.0)
    active_cover = np.exp(logits - logsumexp(logits))
    if not np.isfinite(active_cover).all() or np.any(active_cover <= 0):
        raise ValidationError(
            "Positive active cover is not numerically representable",
            reason_code="active_cover_not_representable",
        )
    # Report probabilities, the full NLL and stationarity for the returned
    # binary64 cover, rather than an unreturned higher-resolution log parameter.
    returned_point = np.log(active_cover[:-1]) - np.log(active_cover[-1])
    objective, score, probabilities = evaluate(returned_point)
    residual = float(np.max(np.abs(score)))
    relative_residual = relative_balance(score)
    hessian = curvature(probabilities)
    information = relative_information(hessian)
    resolved = np.isfinite(information) and information > information_floor
    converged = bool(
        resolved and residual <= tolerance and relative_residual <= relative_tolerance
    )
    if indices.size == 1:
        stop = "single_active_taxon"
    elif not resolved:
        stop = "floating_information_unresolved"
    elif converged:
        stop = "count_balance_tolerances"
    elif stop == "count_balance_tolerances":
        stop = "returned_cover_stationarity_lost"
    if (
        not np.isfinite(objective)
        or not np.isfinite(probabilities).all()
        or np.any(probabilities <= 0)
    ):
        raise ValidationError(
            "Active predicted probability or objective is not numerically representable",
            reason_code="active_probability_not_representable",
        )
    if indices.size > 1:
        condition = float(np.linalg.cond(hessian))
    cover = np.zeros(n.shape[1])
    cover[indices] = active_cover
    predicted = np.zeros_like(n)
    predicted[:, indices] = probabilities
    return MultisiteLikelihoodFit(
        _owned(cover),
        _owned(predicted),
        _owned(site_totals),
        _owned(taxon_totals),
        _owned(used),
        _owned(active),
        tuple(map(int, np.flatnonzero(~used))),
        gauge,
        objective,
        residual,
        tolerance,
        relative_residual,
        relative_tolerance,
        condition,
        information,
        information_floor,
        converged,
        steps,
        stop,
    )
