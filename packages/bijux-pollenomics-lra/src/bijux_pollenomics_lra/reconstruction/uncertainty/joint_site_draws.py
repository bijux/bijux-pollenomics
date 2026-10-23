"""Explicit shared site, count and PPE draws for multi-site REVEALS."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import _reject_masked_values

PROFILE = "reveals-joint-site-count-ppe-draws-v1"


@dataclass(frozen=True, slots=True)
class JointSiteDrawResult:
    """Closed draw rows and sample covariance on fixed geometry and chronology."""

    cover_draws: np.ndarray
    mean_cover: np.ndarray
    covariance: np.ndarray
    standard_error: np.ndarray
    profile: str = PROFILE


def _closed_joint_draws(
    sampled_counts: np.ndarray,
    deposition: np.ndarray,
    ppe: np.ndarray,
) -> np.ndarray:
    """Preserve ordinary pooled arithmetic and cancel unresolved common scales."""
    calculation_dtype = np.result_type(
        sampled_counts.dtype, deposition.dtype, ppe.dtype, np.float64
    )
    with np.errstate(over="ignore", under="ignore", divide="ignore", invalid="ignore"):
        weights = (sampled_counts / deposition).sum(axis=1) / ppe
        totals = weights.sum(axis=1)
        closed = weights / totals[:, None]
        unresolved = (
            ~np.isfinite(weights).all(axis=1)
            | ~np.isfinite(totals)
            | (totals <= 0)
            | np.any(
                np.any(sampled_counts > 0, axis=1)
                & (weights < np.finfo(weights.dtype).tiny),
                axis=1,
            )
        )
        if np.any(unresolved):
            # A duplicated site retains the same count draw and geometry. Sum
            # its positive contributions before applying the shared PPE draw.
            closed = np.asarray(closed, dtype=calculation_dtype)
            corrected = np.log(
                np.asarray(sampled_counts[unresolved], dtype=calculation_dtype)
            ) - np.log(np.asarray(deposition[unresolved], dtype=calculation_dtype))
            logged = np.logaddexp.reduce(corrected, axis=1) - np.log(
                np.asarray(ppe[unresolved], dtype=calculation_dtype)
            )
            scaled = np.exp(logged - logged.max(axis=1, keepdims=True))
            closed[unresolved] = scaled / scaled.sum(axis=1, keepdims=True)
    tolerance = max(1e-12, np.finfo(closed.dtype).eps * closed.shape[1])
    if not np.isfinite(closed).all() or not np.allclose(
        closed.sum(axis=1), 1, rtol=0, atol=tolerance
    ):
        raise ValidationError("Joint REVEALS corrected draw is numerically unresolved")
    return np.asarray(closed)


def joint_site_cover_draws(
    counts: np.ndarray,
    deposition: np.ndarray,
    site_indices: np.ndarray,
    count_draws: np.ndarray,
    ppe_draws: np.ndarray,
    *,
    taxon_measured: np.ndarray,
) -> JointSiteDrawResult:
    """Close supplied joint draws after correcting each sampled site's geometry.

    Each row of ``site_indices`` samples original site positions with replacement.
    Count draws are indexed by original site so a duplicated site uses the same
    count draw twice. One PPE vector is shared across all sites in a replicate.
    The producer of draws owns their stochastic model and provenance; this
    calculation neither infers a random seed nor treats site rows as independent
    when the same site was selected twice.
    """
    for value, name in (
        (counts, "counts"),
        (deposition, "deposition"),
        (site_indices, "site_indices"),
        (count_draws, "count_draws"),
        (ppe_draws, "ppe_draws"),
        (taxon_measured, "taxon_measured"),
    ):
        _reject_masked_values(value, name)
    raw = [
        np.asarray(value)
        for value in (counts, deposition, site_indices, count_draws, ppe_draws)
    ]
    n, k, indices, sampled, ppe = raw
    measured = np.asarray(taxon_measured)
    if measured.dtype != bool or measured.shape != n.shape:
        raise ValidationError(
            "Measured-taxon mask must be boolean with site/taxon axes"
        )
    if not measured.all():
        raise ValidationError(
            "Unmeasured source taxa cannot be treated as observed zero counts",
            reason_code="taxon_measurement_unresolved",
        )
    if (
        any(value.dtype.kind not in "iuf" for value in (n, k, sampled, ppe))
        or indices.dtype.kind not in "iu"
    ):
        raise ValidationError(
            "Joint REVEALS draws require numeric arrays and integer site indices"
        )
    if (
        n.ndim != 2
        or n.shape[0] < 2
        or n.shape[1] < 2
        or k.shape != n.shape
        or indices.ndim != 2
        or indices.shape[1] != n.shape[0]
        or not 2 <= indices.shape[0] <= 10_000
        or sampled.shape != (indices.shape[0], *n.shape)
        or ppe.shape != (indices.shape[0], n.shape[1])
    ):
        raise ValidationError("Joint REVEALS draw axes are inconsistent")
    if (
        not np.isfinite(n).all()
        or np.any(n < 0)
        or np.any(n != np.floor(n))
        or np.any(n > 2**53 - 1)
        or np.any(np.sum(n, axis=1, dtype=float) >= 2**53)
        or np.any(n.sum(axis=1) <= 0)
        or not np.isfinite(k).all()
        or np.any(k <= 0)
        or not np.isfinite(sampled).all()
        or np.any(sampled < 0)
        or np.any(sampled != np.floor(sampled))
        or np.any(sampled > 2**53 - 1)
        or np.any(np.sum(sampled, axis=2, dtype=float) >= 2**53)
        or not np.array_equal(
            sampled.sum(axis=2), np.broadcast_to(n.sum(axis=1), sampled.shape[:2])
        )
        or not np.isfinite(ppe).all()
        or np.any(ppe <= 0)
        or np.any(indices < 0)
        or np.any(indices >= n.shape[0])
    ):
        raise ValidationError(
            "Joint REVEALS count totals, PPE or site identities are invalid"
        )
    rows = np.arange(indices.shape[0])[:, None]
    closed = _closed_joint_draws(sampled[rows, indices], k[indices], ppe)
    mean = closed.mean(axis=0)
    covariance = np.cov(closed, rowvar=False, ddof=1)
    standard_error = np.sqrt(np.maximum(np.diag(covariance), 0))
    for value in (closed, mean, covariance, standard_error):
        value.setflags(write=False)
    return JointSiteDrawResult(closed, mean, covariance, standard_error)
