"""Reconstruction analytical for the LRA engine."""

from __future__ import annotations

from collections.abc import Mapping
from typing import NotRequired, TypedDict
import warnings

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.dispersal.kernels import DispersalFactorK
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import (
    frame,
    normalise_parameters,
    parameter_value,
    rng_from,
    sample_counts,
    vector,
)
from bijux_pollenomics_lra.reconstruction.draws import multidraw, rnorm_reveals
from bijux_pollenomics_lra.reconstruction.inputs import (
    _prepare_inputs,
    _regional_cover,
    _summary_frames,
)


class AnalyticalOutput(TypedDict):
    """Validated numerical intermediates consumed by the analytical workflow."""

    Mean: pd.DataFrame
    Q10: pd.DataFrame
    Q90: pd.DataFrame
    SD: pd.DataFrame
    Outlier: pd.Series
    OutlierQant: pd.Series
    Kreg: pd.DataFrame
    Kloc: pd.DataFrame
    valid_ring: pd.Series
    samples: NotRequired[np.ndarray]


def lov(
    vSampleLoc: pd.DataFrame | np.ndarray,
    sr: object,
    lParams: Mapping[str, object],
    *,
    rng: None | int | np.random.Generator = None,
    alpha: object | None = None,
    counts: object | None = None,
    stochastic: bool | None = None,
) -> np.ndarray:
    """Evaluate analytical LOVE equation 6 for one local sample.

    As in the source, valid mathematical outputs are not clipped to ``[0, 1]``;
    negative or greater-than-one estimates are diagnostic information.
    """
    observed, taxa, _ = sample_counts(vSampleLoc, "vSampleLoc")
    if "ppes" not in lParams:
        raise ValidationError("LOVE parameters require a ppes table")
    ppe_table = normalise_parameters(frame(lParams["ppes"], "ppes"), taxa)
    generator = rng_from(rng)
    use_error = bool(parameter_value(lParams, "error", True))
    if stochastic is not None:
        use_error = use_error and bool(stochastic)

    if alpha is None:
        alpha_values = (
            rnorm_reveals(
                len(ppe_table),
                ppe_table["ppe"],
                ppe_table["ppe.error"],
                rng=generator,
            )
            if use_error
            else ppe_table["ppe"].to_numpy(dtype=float)
        )
    else:
        alpha_values = vector(alpha, "alpha", positive=True)

    if counts is None:
        count_values = multidraw(observed, rng=generator) if use_error else observed
    else:
        count_values = vector(counts, "counts", nonnegative=True)
    regional_term = vector(np.asarray(sr, dtype=float).reshape(-1), "sr", finite=False)
    if not (
        alpha_values.shape
        == count_values.shape
        == regional_term.shape
        == observed.shape
    ):
        raise ValidationError("LOVE equation vectors have inconsistent dimensions")
    if count_values.sum() <= 0:
        raise ValidationError("Local pollen total must be positive")

    with np.errstate(divide="ignore", invalid="ignore"):
        weighted = count_values / alpha_values
        relative = weighted / weighted.sum()
        return np.asarray(relative * (1 + regional_term.sum()) - regional_term)


def LOVEr(
    pollenLoc: pd.DataFrame,
    pollenReg: pd.DataFrame,
    lParams: Mapping[str, object],
    dfRadii: pd.DataFrame,
    maxRingLove: int,
    repeats: int = 100,
    *,
    rng: None | int | np.random.Generator = None,
    stochastic: bool = True,
    regional_cover_draws: object | None = None,
    local_ppe_draws: object | None = None,
    local_count_draws: object | None = None,
    return_samples: bool = False,
) -> AnalyticalOutput:
    """Run the complete analytical LOVE workflow.

    Local paired-draw arrays use shape ``(repeats, maxRingLove, taxa)``.
    Regional cover draws use shape ``(repeats, taxa)`` and contain fractions.  These hooks support exact R/Python wrapper comparisons.
    """
    (
        local,
        regional,
        ppe_table,
        fall_speeds,
        radii,
        taxa,
        maximum_ring,
        repeat_count,
    ) = _prepare_inputs(
        pollenLoc,
        pollenReg,
        lParams,
        dfRadii,
        maxRingLove,
        repeats,
    )
    generator = rng_from(rng)
    local_diameter = float(parameter_value(lParams, "dBasinLocal"))
    if not np.isfinite(local_diameter) or local_diameter <= 0:
        raise ValidationError("dBasinLocal must be positive and finite")
    method = str(parameter_value(lParams, "dwm", "lsm unstable"))

    regional_k = np.zeros((maximum_ring, len(taxa)), dtype=float)
    local_k = np.zeros_like(regional_k)
    valid_ring = (
        radii["inner"].to_numpy(dtype=float)[:maximum_ring] > local_diameter / 2
    )
    for ring_index in range(maximum_ring):
        if not valid_ring[ring_index]:
            continue
        # Source-compatible geometry: Kreg receives outer radius directly as
        # dBasin, rather than two times the outer radius.
        regional_k[ring_index] = [
            DispersalFactorK(
                fall_speed,
                "peatland",
                radii["outer"].iloc[ring_index],
                method,
                100_000,
            )
            for fall_speed in fall_speeds
        ]
        local_k[ring_index] = [
            DispersalFactorK(
                fall_speed,
                "peatland",
                local_diameter,
                method,
                radii["outer"].iloc[ring_index],
            )
            for fall_speed in fall_speeds
        ]

    samples = np.full((repeat_count, maximum_ring, len(taxa)), np.nan, dtype=float)
    for supplied, name in (
        (local_ppe_draws, "local_ppe_draws"),
        (local_count_draws, "local_count_draws"),
    ):
        if supplied is not None and np.asarray(supplied).shape != samples.shape:
            raise ValidationError(f"{name} must have shape {samples.shape}")

    for repeat_index in range(repeat_count):
        regional_cover = _regional_cover(
            regional,
            ppe_table,
            lParams,
            generator,
            stochastic,
            regional_cover_draws,
            repeat_index,
        )
        for ring_index in range(maximum_ring):
            if not valid_ring[ring_index]:
                continue
            denominator = np.sum(regional_cover * local_k[ring_index])
            if not np.isfinite(denominator) or denominator == 0:
                raise ValidationError(
                    "LOVE regional correction denominator is zero or undefined"
                )
            regional_correction = regional_cover * regional_k[ring_index] / denominator
            samples[repeat_index, ring_index] = lov(
                local,
                regional_correction,
                lParams,
                rng=generator,
                stochastic=stochastic,
                alpha=(
                    None
                    if local_ppe_draws is None
                    else np.asarray(local_ppe_draws)[repeat_index, ring_index]
                ),
                counts=(
                    None
                    if local_count_draws is None
                    else np.asarray(local_count_draws)[repeat_index, ring_index]
                ),
            )

    ring_index_values = radii["mean"].iloc[:maximum_ring].to_numpy(dtype=float)
    summary = _summary_frames(
        samples,
        ring_index_values,
        taxa,
        include_sd=True,
        mean_na_rm=True,
    )
    outlier_count = np.sum((samples < 0) | (samples > 1), axis=2).astype(float)
    outlier_count[:, ~valid_ring] = np.nan
    q10 = summary["Q10"].to_numpy(dtype=float)
    q90 = summary["Q90"].to_numpy(dtype=float)
    inside_q10 = (q10 >= 0) & (q10 <= 1)
    inside_q90 = (q90 >= 0) & (q90 <= 1)
    outside_both = ~inside_q10 & ~inside_q90
    outlier_quantile = outside_both.sum(axis=1).astype(float)
    outlier_quantile[np.isnan(q10).any(axis=1)] = np.nan
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        mean_outlier_count = np.nanmean(outlier_count, axis=0)

    result: AnalyticalOutput = {
        "Mean": summary["mean"],
        "Q10": summary["Q10"],
        "Q90": summary["Q90"],
        "SD": summary["SD"],
        "Outlier": pd.Series(mean_outlier_count, index=ring_index_values),
        # Misspelling preserved because it is part of the source API.
        "OutlierQant": pd.Series(outlier_quantile, index=ring_index_values),
        "Kreg": pd.DataFrame(regional_k, index=ring_index_values, columns=taxa),
        "Kloc": pd.DataFrame(local_k, index=ring_index_values, columns=taxa),
        "valid_ring": pd.Series(valid_ring, index=ring_index_values),
    }
    if return_samples:
        result["samples"] = samples
    return result
