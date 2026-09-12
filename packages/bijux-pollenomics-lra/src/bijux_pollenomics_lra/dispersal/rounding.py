"""Dispersal rounding for the LRA engine."""

from __future__ import annotations

import numpy as np

from bijux_pollenomics_lra.models.errors import ValidationError


def r_round(value: object, digits: int = 0) -> float | np.ndarray:
    """Round using R's nearest-even decimal decision for supported digits."""
    if isinstance(digits, bool) or int(digits) != digits or not 0 <= digits <= 15:
        raise ValidationError("r_round supports integer digits from 0 through 15")

    array = np.asarray(value, dtype=float)
    if digits == 0:
        result = np.rint(array)
    else:
        absolute = np.abs(array)
        power = float(10 ** int(digits))
        with np.errstate(invalid="ignore", over="ignore", divide="ignore"):
            scaled = absolute * power
            lower_integer = np.floor(scaled)
            lower = lower_integer / power
            upper = np.ceil(scaled) / power
            distance_up = upper - absolute
            distance_down = absolute - lower
            choose_upper = (distance_up < distance_down) | (
                (np.fmod(lower_integer, 2) == 1) & (distance_up == distance_down)
            )
            result = np.copysign(
                np.where(choose_upper, upper, lower),
                array,
            )
            exponent = np.frexp(absolute)[1] - 1
            unchanged = (
                (np.log10(2) * (0.5 + exponent) + digits > 15)
                | (~np.isfinite(array))
                | (absolute == 0)
            )
            result = np.where(unchanged, array, result)

    return float(result) if result.ndim == 0 else result
