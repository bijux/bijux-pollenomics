"""Source-faithful individual-site and site-bootstrap REVEALS calculations."""

from __future__ import annotations

import numpy as np

from bijux_pollenomics_lra.models.errors import ValidationError


def individual_cover_variance(
    counts: np.ndarray,
    ppe: np.ndarray,
    ppe_covariance: np.ndarray,
    deposition: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Preserve the release's PPE operator order and cumulative covariance bug.

    This function intentionally does not implement a corrected delta method.
    Its taxon-order-sensitive variance is exposed by the named source profile.
    """
    total = counts.sum()
    q = counts / total
    qa = q / ppe
    adjusted = qa / deposition
    adjusted_total = adjusted.sum()
    cover = adjusted / adjusted_total
    variance_qa = np.zeros_like(q)
    positive = q > 0
    variance_qa[positive] = qa[positive] ** 2 * (
        (1 - q[positive]) / (total * q[positive])
        + np.diag(ppe_covariance)[positive] / ppe[positive] * ppe[positive]
    )
    covariance_qa = (
        qa[:, None]
        * qa[None, :]
        * (-1 / total + ppe_covariance / (ppe[:, None] * ppe[None, :]))
    )
    np.fill_diagonal(covariance_qa, 0)
    variance_adjusted = variance_qa / deposition**2
    covariance_adjusted = covariance_qa / (deposition[:, None] * deposition[None, :])
    variance_total = variance_adjusted.sum() + covariance_adjusted.sum()
    # The source does not reset ccc3 for each taxon and does not add its variance.
    accumulated_covariance = np.cumsum(covariance_adjusted.ravel()).reshape(
        covariance_adjusted.shape
    )[:, -1]
    variance = np.zeros_like(cover)
    variance[positive] = cover[positive] ** 2 * (
        variance_adjusted[positive] / adjusted[positive] ** 2
        + variance_total / adjusted_total**2
        - 2 * accumulated_covariance[positive] / (adjusted[positive] * adjusted_total)
    )
    if not np.isfinite(cover).all() or not np.isfinite(variance).all():
        raise ValidationError(
            "Historical individual reconstruction is nonfinite",
            reason_code="nonfinite_reconstruction",
        )
    return np.asarray(cover), np.asarray(variance)


def bootstrap_cover_variance(
    counts: np.ndarray,
    deposition: np.ndarray,
    ppe: np.ndarray,
    site_indices: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Apply the literal 1000-draw, fixed-PPE source bootstrap combination.

    Counts are deposition-corrected separately for every site's geometry before
    pooling. Mean cover is the ratio of accumulated Qa, not mean closed cover.
    """
    corrected_counts = counts / deposition
    pooled = np.sum(corrected_counts[site_indices], axis=1)
    q = pooled / pooled.sum(axis=1, keepdims=True)
    qa = q / ppe
    closed = qa / qa.sum(axis=1, keepdims=True)
    # Match the source's repeated scalar accumulation order, including its
    # cancellation-prone variance and zero result when cancellation is negative.
    taxon_sums = np.cumsum(qa, axis=0)[-1]
    total = np.cumsum(qa.T.ravel())[-1]
    mean = taxon_sums / total
    sx = np.cumsum(closed, axis=0)[-1]
    sxx = np.cumsum(closed**2, axis=0)[-1]
    variance = np.maximum(sxx - sx * sx / 1000, 0) / 999
    if not np.isfinite(mean).all() or not np.isfinite(variance).all():
        raise ValidationError(
            "Historical bootstrap reconstruction is nonfinite",
            reason_code="nonfinite_reconstruction",
        )
    return np.asarray(mean), np.asarray(variance)
