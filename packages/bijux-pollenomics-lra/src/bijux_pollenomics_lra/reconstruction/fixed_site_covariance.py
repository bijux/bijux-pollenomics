"""Fixed-site REVEALS delta covariance with full PPE dependence."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from bijux_pollenomics_lra.models.errors import ValidationError

PROFILE = "reveals-fixed-site-delta-covariance-v1"


@dataclass(frozen=True, slots=True)
class FixedSiteCovariance:
    """Conditional cover and separate counting/PPE covariance components."""

    cover: np.ndarray
    counting_covariance: np.ndarray
    ppe_covariance: np.ndarray
    total_covariance: np.ndarray
    standard_error: np.ndarray
    profile: str = PROFILE


def fixed_site_cover_covariance(
    counts: np.ndarray,
    deposition: np.ndarray,
    ppe: np.ndarray,
    ppe_covariance: np.ndarray,
) -> FixedSiteCovariance:
    """Propagate conditional multinomial counts and independent PPE uncertainty.

    For site s and taxon i, the unclosed weight is
    ``w_i = sum_s counts[s,i] / (deposition[s,i] * ppe[i])``. The delta method
    uses independent fixed-total multinomial counts at each site and the full
    covariance of the shared PPE vector. Sites and PPE are assumed independent.
    Site selection, chronology, geometry and transport uncertainty are held
    fixed; no site bootstrap or empirical vegetation accuracy is represented.
    """
    raw_counts = np.asarray(counts)
    if raw_counts.dtype.kind not in "iuf" or (
        raw_counts.dtype.kind in "iu"
        and np.any(np.abs(raw_counts.astype(object)) > 2**53 - 1)
    ):
        raise ValidationError("Fixed-site counts must be numeric, not coerced")
    for value in (deposition, ppe, ppe_covariance):
        if np.asarray(value).dtype.kind not in "iuf":
            raise ValidationError("Fixed-site parameters must be numeric, not coerced")
    n = np.asarray(raw_counts, dtype=float)
    k = np.asarray(deposition, dtype=float)
    p = np.asarray(ppe, dtype=float)
    cp = np.asarray(ppe_covariance, dtype=float)
    if (
        n.ndim != 2
        or n.shape[0] < 1
        or n.shape[1] < 2
        or k.shape != n.shape
        or p.shape != (n.shape[1],)
        or cp.shape != (n.shape[1], n.shape[1])
    ):
        raise ValidationError("Fixed-site REVEALS input axes are inconsistent")
    if (
        not np.isfinite(n).all()
        or np.any(n < 0)
        or np.any(n > 2**53 - 1)
        or np.any(n != np.floor(n))
        or np.any(n.sum(axis=1) <= 0)
        or not np.isfinite(k).all()
        or np.any(k <= 0)
        or not np.isfinite(p).all()
        or np.any(p <= 0)
        or not np.isfinite(cp).all()
        or not np.allclose(cp, cp.T, rtol=0, atol=1e-12)
        or np.linalg.eigvalsh(cp).min() < -1e-12
    ):
        raise ValidationError("Invalid fixed-site counts, deposition or PPE covariance")

    factors = 1 / (k * p[None, :])
    weights = (n * factors).sum(axis=0)
    total = weights.sum()
    if not np.isfinite(total) or total <= 0:
        raise ValidationError("Fixed-site corrected total is invalid")
    cover = weights / total
    closure_jacobian = np.eye(len(p)) - cover[:, None]
    counting = np.zeros_like(cp)
    for site_counts, site_factors in zip(n, factors, strict=True):
        site_total = site_counts.sum()
        fraction = site_counts / site_total
        count_covariance = site_total * (
            np.diag(fraction) - np.outer(fraction, fraction)
        )
        jacobian = closure_jacobian * site_factors[None, :] / total
        counting += jacobian @ count_covariance @ jacobian.T
    ppe_jacobian = -closure_jacobian * (cover / p)[None, :]
    ppe_part = ppe_jacobian @ cp @ ppe_jacobian.T
    combined = counting + ppe_part
    if not np.isfinite(combined).all() or np.linalg.eigvalsh(combined).min() < -1e-12:
        raise ValidationError("Fixed-site propagated covariance is invalid")
    standard_error = np.sqrt(np.maximum(np.diag(combined), 0))
    for value in (cover, counting, ppe_part, combined, standard_error):
        value.setflags(write=False)
    return FixedSiteCovariance(cover, counting, ppe_part, combined, standard_error)
