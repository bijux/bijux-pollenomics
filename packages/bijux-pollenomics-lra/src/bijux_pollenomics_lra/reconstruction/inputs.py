"""Reconstruction inputs for the LRA engine."""

from __future__ import annotations

from collections.abc import Mapping
import warnings

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import (
    DEFAULT_FALL_SPEED_PROFILE,
    fall_speed_bounds,
    frame,
    integer,
    normalise_parameters,
    parameter_value,
    sample_counts,
    validate_fall_speeds,
    vector,
)
from bijux_pollenomics_lra.reconstruction.regional import REVEALSinR


def _fallspeeds(
    params: Mapping[str, object],
    taxa: list[str] | None = None,
    *,
    fall_speed_profile: str = DEFAULT_FALL_SPEED_PROFILE,
    distance_weighting: str = "lsm unstable",
) -> tuple[np.ndarray, list[str]]:
    """Return positive fall speeds aligned with the requested pollen taxa.

    Values may come from a separate fall-speed input or the PPE table. A table
    must identify each taxon exactly once; an unnamed vector retains the given
    taxon order or receives positional names when no taxa were supplied.
    """
    value = params.get("fallspeed")
    if value is None and "ppes" in params and isinstance(params["ppes"], pd.DataFrame):
        ppe_table = params["ppes"]
        lowered = {str(column).lower(): column for column in ppe_table.columns}
        if "fallspeed" in lowered:
            value = ppe_table
    if value is None:
        raise ValidationError("LOVE parameters require fall-speed values")

    if isinstance(value, pd.DataFrame):
        table = value.copy(deep=True)
        table.columns = [str(column).strip().lower() for column in table.columns]
        if "fallspeed" not in table.columns:
            raise ValidationError("Fall-speed table lacks a fallspeed column")
        first = table.columns[0]
        if first != "fallspeed":
            table = table.set_index(first)
        table.index = table.index.map(str)
        if table.index.has_duplicates:
            raise ValidationError("Fall-speed table contains duplicate taxa")
        if taxa is not None:
            missing = sorted(set(taxa) - set(table.index))
            if missing:
                raise ValidationError(f"Fall-speed table is missing taxa: {missing}")
            table = table.loc[taxa]
        values = validate_fall_speeds(
            table["fallspeed"], fall_speed_profile, distance_weighting
        )
        names = list(table.index)
    else:
        values = validate_fall_speeds(value, fall_speed_profile, distance_weighting)
        names = (
            list(taxa)
            if taxa is not None
            else [f"taxon_{index + 1}" for index in range(len(values))]
        )
    return values, names


def _prepare_inputs(
    pollenLoc: pd.DataFrame,
    pollenReg: pd.DataFrame,
    lParams: Mapping[str, object],
    dfRadii: pd.DataFrame,
    maxRingLove: int,
    repeats: int,
    *,
    require_remaining_regional_ring: bool = False,
    allow_publication_profile: bool = False,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    np.ndarray,
    pd.DataFrame,
    list[str],
    int,
    int,
]:
    """Validate LOVE pollen, PPE, fall speeds, ring geometry and repeat counts.

    Local and regional counts must share the exact taxon names and order.
    Rings are ordered, nonoverlapping radial intervals in the supplied table;
    optimized LOVE can require a remaining regional ring. Return the validated
    inputs and aligned taxon axis without inferring chronology or vegetation.
    """
    local = frame(pollenLoc, "pollenLoc")
    regional = frame(pollenReg, "pollenReg")
    _, taxa, _ = sample_counts(local, "pollenLoc")
    _, regional_taxa, _ = sample_counts(regional, "pollenReg")
    if regional_taxa != taxa:
        raise ValidationError(
            "Local and regional pollen taxa must agree exactly in name and order"
        )
    if "ppes" not in lParams:
        raise ValidationError("LOVE parameters require a ppes table")
    fall_speed_profile = str(
        parameter_value(lParams, "fall_speed_profile", DEFAULT_FALL_SPEED_PROFILE)
    )
    distance_weighting = str(parameter_value(lParams, "dwm", "lsm unstable")).lower()
    fall_speed_bounds(fall_speed_profile, distance_weighting)
    if (
        fall_speed_profile != DEFAULT_FALL_SPEED_PROFILE
        and not allow_publication_profile
    ):
        raise ValidationError(
            "The LandClim II fall-speed profile requires analytical LOVE"
        )
    ppe_table = normalise_parameters(
        frame(lParams["ppes"], "ppes"),
        taxa,
        fall_speed_profile=fall_speed_profile,
        distance_weighting=distance_weighting,
    )
    fall_speeds, _ = _fallspeeds(
        lParams,
        taxa,
        fall_speed_profile=fall_speed_profile,
        distance_weighting=distance_weighting,
    )
    if fall_speeds.shape != (len(taxa),):
        raise ValidationError("Fall-speed and pollen dimensions disagree")
    if fall_speed_profile != DEFAULT_FALL_SPEED_PROFILE and not np.array_equal(
        fall_speeds, ppe_table["fallspeed"].to_numpy(dtype=float)
    ):
        raise ValidationError(
            "LandClim II fall speeds must agree between PPE and fall-speed tables"
        )

    radii = frame(dfRadii, "dfRadii")
    required = {"inner", "outer", "mean"}
    missing = required - set(radii.columns)
    if missing:
        raise ValidationError(f"Ring table is missing columns: {sorted(missing)}")
    inner = radii["inner"].to_numpy(dtype=float)
    outer = radii["outer"].to_numpy(dtype=float)
    mean = radii["mean"].to_numpy(dtype=float)
    if not (
        np.isfinite(inner).all()
        and np.isfinite(outer).all()
        and np.isfinite(mean).all()
    ):
        raise ValidationError("Ring radii must be finite")
    if np.any(inner < 0) or np.any(outer <= inner):
        raise ValidationError("Every ring needs inner >= 0 and outer > inner")
    if np.any(inner[1:] < outer[:-1]):
        raise ValidationError("Rings must not overlap", reason_code="overlapping_rings")
    if np.any(mean < inner) or np.any(mean > outer):
        raise ValidationError(
            "Ring mean must lie within its interval", reason_code="invalid_ring_mean"
        )
    if np.any(np.diff(inner) < 0) or np.any(np.diff(outer) <= 0):
        raise ValidationError("Rings must be ordered outward without overlap reversal")

    maximum_ring = integer(maxRingLove, "maxRingLove")
    repeat_count = integer(repeats, "repeats")
    if maximum_ring > len(radii):
        raise ValidationError("maxRingLove exceeds the number of available rings")
    if require_remaining_regional_ring and maximum_ring >= len(radii):
        raise ValidationError("LOVEoptim requires at least one ring beyond maxRingLove")
    return (
        local,
        regional,
        ppe_table,
        fall_speeds,
        radii,
        taxa,
        maximum_ring,
        repeat_count,
    )


def _regional_cover(
    regional: pd.DataFrame,
    ppe_table: pd.DataFrame,
    params: Mapping[str, object],
    rng: np.random.Generator,
    stochastic: bool,
    draws: object | None,
    repeat_index: int,
) -> np.ndarray:
    """Select an explicit regional cover draw or estimate it with REVEALS.

    Explicit draws are taxon-aligned nonnegative fractions with positive total.
    The REVEALS path converts its percent means to fractions for the LOVE step.
    """
    if draws is not None:
        values = np.asarray(draws, dtype=float)
        if values.ndim == 1:
            values = values[None, :]
        if repeat_index >= len(values) or values.shape[1] != len(ppe_table):
            raise ValidationError(
                "regional_cover_draws must have shape (repeats, taxa)"
            )
        cover = vector(values[repeat_index], "regional_cover_draw", nonnegative=True)
        if cover.sum() <= 0:
            raise ValidationError("Regional cover draw must have positive total")
        if np.any(cover > 1):
            raise ValidationError("regional_cover_draws must contain fractions")
        return cover

    result = REVEALSinR(
        regional,
        ppe_table,
        tBasin=str(parameter_value(params, "tBasinRegional", "lake")),
        dBasin=integer(
            parameter_value(params, "dBasinRegional"), "dBasinRegional", minimum=10
        ),
        dwm=str(parameter_value(params, "dwm", "lsm unstable")),
        n=1,
        verbose=False,
        rng=rng,
        stochastic=stochastic,
    )
    return result.filter(regex=r"\.mean$").iloc[0].to_numpy(dtype=float) / 100


def _summary_frames(
    values: np.ndarray,
    radii: np.ndarray,
    taxa: list[str],
    *,
    include_sd: bool = False,
    mean_na_rm: bool = True,
) -> dict[str, pd.DataFrame]:
    """Summarize replicate arrays by ring radius and taxon.

    Return mean, linear-interpolated 10th and 90th quantiles, and optional
    sample standard deviation. Missing values are omitted from the mean only
    when ``mean_na_rm`` is true; quantiles and SD omit them in either case.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        mean = np.nanmean(values, axis=0) if mean_na_rm else np.mean(values, axis=0)
        summaries: dict[str, np.ndarray] = {
            "mean": mean,
            "Q10": np.nanquantile(values, 0.1, axis=0, method="linear"),
            "Q90": np.nanquantile(values, 0.9, axis=0, method="linear"),
        }
        if include_sd:
            summaries["SD"] = np.nanstd(values, axis=0, ddof=1)
    return {
        name: pd.DataFrame(array, index=radii, columns=taxa)
        for name, array in summaries.items()
    }
