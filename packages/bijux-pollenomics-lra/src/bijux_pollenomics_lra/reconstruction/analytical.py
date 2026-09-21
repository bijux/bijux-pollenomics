"""Reconstruction analytical for the LRA engine."""

from __future__ import annotations

from collections.abc import Mapping
from typing import NotRequired, TypedDict
import warnings

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.dispersal.kernels import DispersalFactorK
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.regional_draw_source import RegionalCoverDrawSource
from bijux_pollenomics_lra.models.validation import (
    DEFAULT_FALL_SPEED_PROFILE,
    LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE,
    fall_speed_bounds,
    frame,
    normalise_parameters,
    parameter_value,
    rng_from,
    sample_counts,
    vector,
)
from bijux_pollenomics_lra.reconstruction.draws import (
    multidraw,
    rmultinom_reveals,
    rnorm_reveals,
)
from bijux_pollenomics_lra.reconstruction.inputs import (
    _prepare_inputs,
    _regional_cover,
    _summary_frames,
)
from bijux_pollenomics_lra.reconstruction.preparation import (
    PreparedAnalyticalInputs,
    prepare_analytical_inputs,
)
from bijux_pollenomics_lra.reconstruction.regional import reveals_cover


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

    return _lov_arrays(
        observed,
        ppe_table["ppe"].to_numpy(dtype=float),
        ppe_table["ppe.error"].to_numpy(dtype=float),
        use_error,
        sr,
        generator,
        alpha=alpha,
        counts=counts,
    )


def _lov_arrays(
    observed: np.ndarray,
    means: np.ndarray,
    errors: np.ndarray,
    use_error: bool,
    sr: object,
    generator: np.random.Generator,
    *,
    alpha: object | None,
    counts: object | None,
) -> np.ndarray:
    """Evaluate the existing local draw/equation path with prepared invariants."""
    if alpha is None:
        alpha_values = (
            rnorm_reveals(
                len(means),
                means,
                errors,
                rng=generator,
            )
            if use_error
            else means
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


def _prepared_regional_cover(
    prepared: PreparedAnalyticalInputs,
    generator: np.random.Generator,
    stochastic: bool,
) -> np.ndarray:
    """Preserve one REVEALS draw, percentage rounding, and fraction conversion."""
    if prepared.regional_counts is None or prepared.regional_deposition is None:
        raise ValidationError(
            "Regional pollen is required without supplied cover draws"
        )
    alpha = (
        rnorm_reveals(
            len(prepared.ppe_means),
            prepared.ppe_means,
            prepared.ppe_errors,
            rng=generator,
        )
        if stochastic
        else prepared.ppe_means
    )
    pollen = (
        rmultinom_reveals(n=1, pollen=prepared.regional_counts, rng=generator).reshape(
            -1
        )
        if stochastic
        else prepared.regional_counts
    )
    return reveals_cover(pollen, alpha, prepared.regional_deposition) / 100


def LOVEr(
    pollenLoc: pd.DataFrame,
    pollenReg: pd.DataFrame | None,
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
    draw_source: RegionalCoverDrawSource | None = None,
) -> AnalyticalOutput:
    """Run the complete analytical LOVE workflow.

    Local paired-draw arrays use shape ``(repeats, maxRingLove, taxa)``.
    Regional cover draws use shape ``(repeats, taxa)`` and contain fractions.  These hooks support exact R/Python wrapper comparisons.
    """
    fall_speed_profile = str(
        parameter_value(lParams, "fall_speed_profile", DEFAULT_FALL_SPEED_PROFILE)
    )
    if (
        fall_speed_profile == LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE
        and regional_cover_draws is None
    ):
        raise ValidationError(
            "The LandClim II analytical profile requires supplied regional_cover_draws"
        )
    if pollenReg is None and (
        not isinstance(draw_source, RegionalCoverDrawSource)
        or regional_cover_draws is None
        or fall_speed_profile != LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE
        or regional_cover_draws is not draw_source.values
    ):
        raise ValidationError(
            "Regional pollen is required outside draw-only analytical LOVE"
        )
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
        allow_publication_profile=True,
        allow_draw_only=draw_source is not None,
    )
    if fall_speed_profile == LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE:
        draws = np.asarray(regional_cover_draws, dtype=float)
        rounding_bound = len(taxa) * 0.000005 + 1e-12
        if (
            draws.shape != (repeat_count, len(taxa))
            or not np.isfinite(draws).all()
            or np.any(draws < 0)
            or np.any(draws > 1)
            or not np.allclose(draws.sum(axis=1), 1, rtol=0, atol=rounding_bound)
        ):
            raise ValidationError(
                "regional_cover_draws must be closed fractions, not percentages"
            )
    generator = rng_from(rng)
    local_diameter = float(parameter_value(lParams, "dBasinLocal"))
    if not np.isfinite(local_diameter) or local_diameter <= 0:
        raise ValidationError("dBasinLocal must be positive and finite")
    method = str(parameter_value(lParams, "dwm", "lsm unstable")).lower()
    fall_speed_bounds(fall_speed_profile, method)

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
        if fall_speed_profile != DEFAULT_FALL_SPEED_PROFILE and (
            not np.isfinite(regional_k[ring_index]).all()
            or not np.isfinite(local_k[ring_index]).all()
            or np.any(regional_k[ring_index] <= 0)
            or np.any(local_k[ring_index] <= 0)
        ):
            raise ValidationError(
                "LandClim II analytical deposition must be finite and positive"
            )

    samples = np.full((repeat_count, maximum_ring, len(taxa)), np.nan, dtype=float)
    for supplied, name in (
        (local_ppe_draws, "local_ppe_draws"),
        (local_count_draws, "local_count_draws"),
    ):
        if supplied is not None and np.asarray(supplied).shape != samples.shape:
            raise ValidationError(f"{name} must have shape {samples.shape}")

    prepared = prepare_analytical_inputs(
        local,
        regional,
        ppe_table,
        lParams,
        stochastic=stochastic,
        needs_regional_deposition=regional_cover_draws is None,
    )
    for repeat_index in range(repeat_count):
        regional_cover = (
            _prepared_regional_cover(prepared, generator, stochastic)
            if regional_cover_draws is None
            else _regional_cover(
                regional,
                ppe_table,
                lParams,
                generator,
                stochastic,
                regional_cover_draws,
                repeat_index,
            )
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
            samples[repeat_index, ring_index] = _lov_arrays(
                prepared.local_counts,
                prepared.ppe_means,
                prepared.ppe_errors,
                prepared.local_error,
                regional_correction,
                generator,
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
