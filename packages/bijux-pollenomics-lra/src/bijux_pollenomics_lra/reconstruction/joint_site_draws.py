"""Explicit shared site, count and PPE draws for multi-site REVEALS."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from bijux_pollenomics_lra.models.errors import ValidationError

PROFILE = "reveals-joint-site-count-ppe-draws-v1"


@dataclass(frozen=True, slots=True)
class JointSiteDrawResult:
    """Closed draw rows and sample covariance on fixed geometry and chronology."""

    cover_draws: np.ndarray
    mean_cover: np.ndarray
    covariance: np.ndarray
    standard_error: np.ndarray
    profile: str = PROFILE


def joint_site_cover_draws(
    counts: np.ndarray,
    deposition: np.ndarray,
    site_indices: np.ndarray,
    count_draws: np.ndarray,
    ppe_draws: np.ndarray,
) -> JointSiteDrawResult:
    """Close supplied joint draws after correcting each sampled site's geometry.

    Each row of ``site_indices`` samples original site positions with replacement.
    Count draws are indexed by original site so a duplicated site uses the same
    count draw twice. One PPE vector is shared across all sites in a replicate.
    The producer of draws owns their stochastic model and provenance; this
    calculation neither infers a random seed nor treats site rows as independent
    when the same site was selected twice.
    """
    raw = [
        np.asarray(value)
        for value in (counts, deposition, site_indices, count_draws, ppe_draws)
    ]
    n, k, indices, sampled, ppe = raw
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
    weights = (sampled[rows, indices] / k[indices]).sum(axis=1) / ppe
    totals = weights.sum(axis=1)
    if not np.isfinite(weights).all() or np.any(totals <= 0):
        raise ValidationError("Joint REVEALS corrected draw is invalid")
    closed = weights / totals[:, None]
    mean = closed.mean(axis=0)
    covariance = np.cov(closed, rowvar=False, ddof=1)
    standard_error = np.sqrt(np.maximum(np.diag(covariance), 0))
    for value in (closed, mean, covariance, standard_error):
        value.setflags(write=False)
    return JointSiteDrawResult(closed, mean, covariance, standard_error)
