"""Reconstruction optimized for the LRA engine."""

from __future__ import annotations

from collections.abc import Mapping
from typing import NotRequired, TypedDict
import warnings

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.dispersal.kernels import DispersalFactorK
from bijux_pollenomics_lra.dispersal.rounding import r_round
from bijux_pollenomics_lra.models.configuration import OptimizedLoveProfile
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import (
    frame,
    parameter_value,
    rng_from,
    sample_counts,
    vector,
)
from bijux_pollenomics_lra.optimization.solver import (
    OptimizationResult,
    ReplayOptimizer,
    optimize_box,
)
from bijux_pollenomics_lra.reconstruction.draws import multidraw, rnorm_reveals
from bijux_pollenomics_lra.reconstruction.forward import _deposition_components
from bijux_pollenomics_lra.reconstruction.inputs import (
    _fallspeeds,
    _prepare_inputs,
    _regional_cover,
    _summary_frames,
)


class OptimizedOutput(TypedDict):
    """Validated numerical intermediates consumed by the optimized workflow."""

    cover: dict[str, pd.DataFrame]
    pollenpercentages: dict[str, pd.DataFrame]
    mBestValue: pd.DataFrame
    optimizers: list[OptimizationResult]
    K: pd.DataFrame
    terrestrial_fraction: pd.Series
    cover_samples: NotRequired[np.ndarray]
    pollen_samples: NotRequired[np.ndarray]


def logeuclidean(a: object, b: object) -> float:
    """Return the source log-Euclidean distance."""
    first = vector(a, "a", finite=False)
    second = vector(b, "b", finite=False)
    if first.shape != second.shape:
        raise ValidationError("logeuclidean vectors must have equal dimensions")
    with np.errstate(divide="ignore", invalid="ignore"):
        return float(np.sqrt(np.sum((np.log(first) - np.log(second)) ** 2)))


def love_pollen(
    a: object,
    vPoldepRegio: object,
    mKlocal: object,
    vFlocal: object,
    ppes: object,
) -> np.ndarray:
    """Forward-model local plus regional pollen deposition."""
    cover = vector(a, "a", nonnegative=True)
    regional = vector(vPoldepRegio, "vPoldepRegio", finite=False)
    local_k = np.atleast_2d(np.asarray(mKlocal, dtype=float))
    local_fraction = vector(vFlocal, "vFlocal", finite=False)
    productivity = vector(ppes, "ppes", positive=True)
    if (
        local_k.shape != (len(local_fraction), len(cover))
        or regional.shape != cover.shape
        or productivity.shape != cover.shape
    ):
        raise ValidationError("LOVE forward-model dimensions disagree")
    if cover.sum() <= 0:
        return np.full_like(cover, np.nan, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        _, total = _deposition_components(
            cover / cover.sum(),
            regional,
            local_k,
            local_fraction,
            productivity,
        )
        return np.asarray(total / total.sum())


def tf(
    a: object,
    vPoldepRegio: object,
    mKlocal: object,
    vFlocal: object,
    vSampleLocPro: object,
    ppes: object,
) -> float:
    """LOVEoptim objective function."""
    predicted = love_pollen(a, vPoldepRegio, mKlocal, vFlocal, ppes)
    observed = np.asarray(vSampleLocPro, dtype=float) + 0.001
    return logeuclidean(predicted, observed)


def calK(
    dfRadii: pd.DataFrame,
    lParams: Mapping[str, object],
) -> pd.DataFrame:
    """Calculate ring-specific K factors for LOVEoptim.

    DISQOVER 0.9.14 forcibly uses the peatland deposition path here because its
    own source marks the ring lake path as unresolved.  That behaviour is kept
    for parity and explicitly represented in result provenance.
    """
    radii = frame(dfRadii, "dfRadii")
    if not {"inner", "outer", "mean"} <= set(radii.columns):
        raise ValidationError("dfRadii requires inner, outer, and mean columns")
    fall_speeds, taxa = _fallspeeds(lParams)
    method = str(parameter_value(lParams, "dwm", "lsm unstable"))
    values = np.asarray(
        [
            [
                DispersalFactorK(
                    fall_speed,
                    "peatland",
                    2 * float(inner),
                    method,
                    float(outer),
                )
                for fall_speed in fall_speeds
            ]
            for inner, outer in radii[["inner", "outer"]].to_numpy(dtype=float)
        ],
        dtype=float,
    )
    return pd.DataFrame(
        values,
        index=radii["mean"].to_numpy(dtype=float),
        columns=taxa,
    )


def LOVEoptim(
    pollenLoc: pd.DataFrame,
    pollenReg: pd.DataFrame,
    lParams: Mapping[str, object],
    dfRadii: pd.DataFrame,
    maxRingLove: int,
    repeats: int = 10,
    *,
    rng: None | int | np.random.Generator = None,
    stochastic: bool = True,
    regional_cover_draws: object | None = None,
    local_count_draws: object | None = None,
    optimizer: ReplayOptimizer | object | None = None,
    itermax: int = 200,
    max_evaluations: int | None = None,
    tolerance: float = 0.01,
    return_samples: bool = False,
    optimized_profile: OptimizedLoveProfile
    | str = OptimizedLoveProfile.DISQOVER_SOURCE,
) -> OptimizedOutput:
    """Run the complete native forward-optimization LOVE workflow.

    The source draws a PPE vector on each repeat but then uses nominal PPEs in
    both the target and final pollen calculation.  The unused draw is preserved
    for source-compatible random-consumption semantics.
    """
    try:
        profile = OptimizedLoveProfile(optimized_profile)
    except ValueError as error:
        raise ValidationError("Unknown optimized_profile") from error
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
        require_remaining_regional_ring=True,
    )
    if not {"ring", "terrestrial"} <= set(radii.columns):
        raise ValidationError("LOVEoptim requires ring and terrestrial columns")
    ring_area = vector(radii["ring"], "ring", positive=True)
    terrestrial_area = vector(radii["terrestrial"], "terrestrial", nonnegative=True)
    if np.any(terrestrial_area > ring_area * (1 + 1e-8)):
        warnings.warn(
            "Terrestrial area exceeds geometric ring area; the source ratio is "
            "retained rather than clipped",
            UserWarning,
            stacklevel=2,
        )

    terrestrial_fraction = terrestrial_area / ring_area
    if (
        profile == OptimizedLoveProfile.DISQOVER_SOURCE
        and len(taxa) > 1
        and (
            terrestrial_fraction[0] > 0
            or (
                maximum_ring == len(radii) - 1
                and terrestrial_fraction[-1] > 0
                and np.any(terrestrial_fraction[:maximum_ring] > 0)
            )
        )
    ):
        raise ValidationError(
            "DISQOVER 0.9.14 drops ring-matrix dimensions for evaluated "
            "single-local or nonzero single-regional rings with multiple taxa; "
            "this source-compatible profile refuses those requests",
            reason_code="unsupported_source_ring_dimensions",
        )

    local_params = dict(lParams)
    local_params["fallspeed"] = pd.DataFrame({"Taxon": taxa, "fallspeed": fall_speeds})
    k_matrix = calK(radii, local_params).to_numpy(dtype=float)
    local_counts, _, _ = sample_counts(local, "pollenLoc")
    generator = rng_from(rng)
    nominal_ppe = ppe_table["ppe"].to_numpy(dtype=float)

    cover_samples = np.full(
        (repeat_count, maximum_ring, len(taxa)), np.nan, dtype=float
    )
    pollen_samples = np.full_like(cover_samples, np.nan)
    best_values = np.full((maximum_ring, repeat_count), np.nan, dtype=float)
    if local_count_draws is not None and np.asarray(local_count_draws).shape != (
        repeat_count,
        len(taxa),
    ):
        raise ValidationError("local_count_draws must have shape (repeats, taxa)")

    diagnostics: list[OptimizationResult] = []
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
        if stochastic:
            # Deliberately unused downstream, matching the reference source.
            rnorm_reveals(
                len(ppe_table),
                nominal_ppe,
                ppe_table["ppe.error"],
                rng=generator,
            )
        counts = (
            np.asarray(local_count_draws, dtype=float)[repeat_index]
            if local_count_draws is not None
            else multidraw(local_counts, rng=generator)
            if stochastic
            else local_counts
        )
        counts = vector(counts, "local counts", nonnegative=True)
        if counts.sum() <= 0:
            raise ValidationError("Local pollen draw has zero total")
        observed = counts / counts.sum()

        for ring_index in range(maximum_ring):
            local_fraction = terrestrial_fraction[: ring_index + 1]
            if local_fraction.sum() <= 0:
                continue
            regional_fraction = terrestrial_fraction[ring_index + 1 :]
            regional_deposition = np.sum(
                k_matrix[ring_index + 1 :]
                * (regional_cover * nominal_ppe)[None, :]
                * regional_fraction[:, None],
                axis=0,
            )
            local_k = k_matrix[: ring_index + 1]

            def objective(
                candidate: np.ndarray,
                regional_deposition: np.ndarray = regional_deposition,
                local_k: np.ndarray = local_k,
                local_fraction: np.ndarray = local_fraction,
                observed: np.ndarray = observed,
            ) -> float:
                return tf(
                    candidate,
                    regional_deposition,
                    local_k,
                    local_fraction,
                    observed,
                    nominal_ppe,
                )

            optimization_result = optimize_box(
                objective,
                np.zeros(len(taxa)),
                np.ones(len(taxa)),
                maxiter=itermax,
                popsize=10,
                tolerance=tolerance,
                max_evaluations=max_evaluations,
                rng=generator,
                optimizer=optimizer,
            )
            if optimization_result.x.sum() <= 0:
                raise ValidationError("Optimizer returned an all-zero cover vector")
            proportions = optimization_result.x / optimization_result.x.sum()
            cover_samples[repeat_index, ring_index] = r_round(proportions, 4)
            pollen_samples[repeat_index, ring_index] = r_round(
                100
                * love_pollen(
                    optimization_result.x,
                    regional_deposition,
                    local_k,
                    local_fraction,
                    nominal_ppe,
                ),
                2,
            )
            best_values[ring_index, repeat_index] = optimization_result.fun
            diagnostics.append(optimization_result)

    ring_index_values = radii["mean"].iloc[:maximum_ring].to_numpy(dtype=float)
    result: OptimizedOutput = {
        "cover": _summary_frames(
            cover_samples,
            ring_index_values,
            taxa,
            mean_na_rm=False,
        ),
        "pollenpercentages": _summary_frames(
            pollen_samples,
            ring_index_values,
            taxa,
            mean_na_rm=False,
        ),
        "mBestValue": pd.DataFrame(
            best_values,
            index=ring_index_values,
            columns=np.arange(1, repeat_count + 1),
        ),
        "optimizers": diagnostics,
        "K": pd.DataFrame(k_matrix, index=radii["mean"], columns=taxa),
        "terrestrial_fraction": pd.Series(terrestrial_fraction, index=radii["mean"]),
    }
    if return_samples:
        result["cover_samples"] = cover_samples
        result["pollen_samples"] = pollen_samples
    return result
