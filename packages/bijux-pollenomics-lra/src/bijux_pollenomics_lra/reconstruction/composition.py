"""Declared nonnegative compositions derived from raw analytical LOVE draws."""

from __future__ import annotations

import numpy as np

from bijux_pollenomics_lra.models.errors import ValidationError


def close_love_cover(samples: np.ndarray, valid_rings: np.ndarray) -> np.ndarray:
    """Clip negatives and close each supported draw, retaining the taxon axis.

    Scaling by the largest surviving cover avoids overflow in the positive sum
    and permits subnormal positive mass. Unsupported rings remain missing.
    Raw equation values are never modified or used to impute absent support.
    """
    supported = samples[:, valid_rings, :]
    if not np.isfinite(supported).all():
        raise ValidationError(
            "Supported LOVE cover must be finite before clipping",
            reason_code="nonfinite_love_cover",
        )
    positive = np.maximum(supported, 0)
    scale = positive.max(axis=2, keepdims=True)
    if np.any(scale == 0):
        raise ValidationError(
            "LOVE cover has zero positive mass after clipping",
            reason_code="zero_positive_love_cover",
        )
    scaled = positive / scale
    result = np.full_like(samples, np.nan, dtype=float)
    result[:, valid_rings, :] = scaled / scaled.sum(axis=2, keepdims=True)
    return result
