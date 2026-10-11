"""Literal GPM deposition from the author 2016 REVEALS release."""

from __future__ import annotations

import numpy as np
from scipy.special import gamma, gammainc

from bijux_pollenomics_lra.models.errors import ValidationError


def publication_deposition(
    fall_speed_m_s: np.ndarray,
    radius_m: float,
    basin_type: str,
    wind_speed_m_s: float,
    regional_extent_m: float,
) -> np.ndarray:
    """Evaluate the pinned KPf expression, including its unresolved lake form.

    zipfR Igamma defaults to the lower *unregularized* incomplete gamma. Source
    agreement is not independent confirmation of the author's lake equation.
    """
    if not 0 < radius_m < regional_extent_m:
        raise ValidationError("Basin radius must lie between zero and regional extent")
    b = 75.2 * fall_speed_m_s / wind_speed_m_s
    if basin_type == "peatland":
        deposition = np.exp(-b * radius_m**0.125) - np.exp(
            -b * regional_extent_m**0.125
        )
    elif basin_type == "lake":
        xa = b * (regional_extent_m - radius_m) ** 0.125
        xb = b * (regional_extent_m + radius_m) ** 0.125
        xc = b * (2 * radius_m) ** 0.125
        deposition = (4 * np.pi * radius_m / b**8) * (
            gamma(8) * gammainc(8, xa)
            - gamma(8) * gammainc(8, xb)
            + gamma(8) * gammainc(8, xc)
        )
    else:
        raise ValidationError("Unsupported publication basin type")
    if not np.isfinite(deposition).all() or np.any(deposition <= 0):
        raise ValidationError(
            "Publication deposition factors must be positive and finite"
        )
    return np.asarray(deposition)
