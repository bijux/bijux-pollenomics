"""Interpret saved native innovations and retain complete pollen-score support."""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray


def physical_ages(
    states: NDArray[np.float64], depths: NDArray[np.float64], top: float, thick: float
) -> NDArray[np.float64]:
    """Integrate the no-hiatus native SetThetas recursion on saved decimal states."""
    if (
        states.ndim != 2
        or states.shape[1] < 3
        or depths.ndim != 1
        or not np.all(np.isfinite(states))
        or not np.all(np.isfinite(depths))
    ):
        raise ValueError("Finite native state matrix and depth axis required")
    if (
        not np.isfinite(top)
        or not np.isfinite(thick)
        or thick <= 0
        or np.any(depths < top)
    ):
        raise ValueError("Positive section thickness and supported depths required")
    innovations = states[:, 1:-1]
    memory = states[:, -1]
    if np.any(innovations <= 0) or np.any(memory <= 0) or np.any(memory >= 1):
        raise ValueError("Native innovations and memory are outside model support")
    if np.any(depths > top + innovations.shape[1] * thick):
        raise ValueError("Depth extends beyond the saved model sections")
    rates = innovations.copy()
    for position in range(rates.shape[1] - 2, -1, -1):
        rates[:, position] = (
            memory * rates[:, position + 1] + (1 - memory) * innovations[:, position]
        )
    elbows = top + np.arange(rates.shape[1]) * thick
    overlap = np.minimum(thick, np.maximum(0, depths[None, :] - elbows[:, None]))
    return states[:, :1] + rates @ overlap


def score_draws(
    ages: NDArray[np.float64],
    counts: NDArray[np.int64],
    predictions: NDArray[np.float64],
    bins: tuple[int, ...],
    width: int = 500,
) -> tuple[NDArray[np.float64], dict[str, Any], NDArray[np.int64]]:
    """Score all requested bins per shared draw; preserve incomplete draws as NaN."""
    if (
        ages.ndim != 2
        or counts.ndim != 2
        or ages.shape[1] != counts.shape[0]
        or predictions.ndim != 3
        or predictions.shape[1:] != (len(bins), counts.shape[1])
    ):
        raise ValueError("Draw, sample, bin and taxon axes differ")
    if (
        not np.all(np.isfinite(ages))
        or not np.issubdtype(counts.dtype, np.integer)
        or np.any(counts < 0)
        or not np.all(np.isfinite(predictions))
        or np.any(predictions < 0)
        or np.any(predictions > 1)
        or width <= 0
    ):
        raise ValueError("Finite ages/predictions and nonnegative counts required")
    if not np.allclose(predictions.sum(axis=2), 1, atol=1e-9, rtol=0):
        raise ValueError("Frozen prediction compositions are not closed")
    if len(bins) != len(set(bins)):
        raise ValueError("Requested age bins are repeated")
    per_bin = np.full((ages.shape[0], len(bins), predictions.shape[0]), np.nan)
    empty: dict[str, int] = {}
    zero_mass: dict[str, int] = {}
    support = np.zeros((ages.shape[0], len(bins), 2), dtype=np.int64)
    for position, bin_id in enumerate(bins):
        members = (ages >= bin_id * width) & (ages < (bin_id + 1) * width)
        pooled = members.astype(np.int64) @ counts
        mass = pooled.sum(axis=1)
        support[:, position, 0] = members.sum(axis=1)
        support[:, position, 1] = mass
        eligible = mass > 0
        empty[str(bin_id)] = int(np.sum(~members.any(axis=1)))
        zero_mass[str(bin_id)] = int(np.sum(members.any(axis=1) & ~eligible))
        if np.any(eligible):
            fractions = pooled[eligible] / mass[eligible, None]
            per_bin[eligible, position] = np.mean(
                np.abs(fractions[:, None, :] - predictions[None, :, position, :]),
                axis=2,
            )
    complete = np.all(np.isfinite(per_bin), axis=(1, 2))
    scores = np.full((ages.shape[0], predictions.shape[0]), np.nan)
    scores[complete] = np.mean(per_bin[complete], axis=1)
    return (
        scores,
        {
            "requested_draws": ages.shape[0],
            "complete_four_bin_draws": int(complete.sum()),
            "incomplete_draws": int((~complete).sum()),
            "empty_draw_bins": empty,
            "nonempty_zero_mass_draw_bins": zero_mass,
            "negative_age_cells": int(np.sum(ages < 0)),
            "ages_above_50000_bp": int(np.sum(ages > 50000)),
        },
        support,
    )
