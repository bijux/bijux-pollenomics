"""Workflows local for the LRA engine."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.models.configuration import (
    LoveConfig,
    LoveMethod,
)
from bijux_pollenomics_lra.models.errors import ConvergenceError, ValidationError
from bijux_pollenomics_lra.models.results import (
    LoveResult,
)
from bijux_pollenomics_lra.models.validation import (
    frame,
    normalise_parameters,
    sample_counts,
)
from bijux_pollenomics_lra.optimization.solver import ReplayOptimizer
from bijux_pollenomics_lra.provenance.manifest import build_manifest
from bijux_pollenomics_lra.reconstruction.analytical import LOVEr
from bijux_pollenomics_lra.reconstruction.optimized import LOVEoptim


def _prepare_love_params(
    params: pd.DataFrame,
    taxa: list[str],
    config: LoveConfig,
) -> dict[str, Any]:
    table = normalise_parameters(params, taxa)
    ppes = table.reset_index().rename(columns={table.index.name or "index": "Taxon"})
    # reset_index uses "index" if the index had no explicit name.
    if "Taxon" not in ppes.columns:
        ppes = ppes.rename(columns={ppes.columns[0]: "Taxon"})
    fallspeed = ppes[["Taxon", "fallspeed"]].copy(deep=True)
    return {
        "ppes": ppes,
        "fallspeed": fallspeed,
        "dBasinRegional": config.regional_basin_diameter_m,
        "dBasinLocal": config.local_basin_diameter_m,
        "tBasinRegional": config.regional_basin_type,
        "tBasin": config.regional_basin_type,
        "tBasinLocal": "lake",
        "dwm": config.distance_weighting,
        "repeats": config.repeats,
        "error": bool(config.ppe_error),
    }


def run_love(
    local_pollen: pd.DataFrame,
    regional_pollen: pd.DataFrame,
    params: pd.DataFrame,
    rings: pd.DataFrame,
    config: LoveConfig,
    *,
    replay_candidates: object | None = None,
    regional_cover_draws: object | None = None,
    local_ppe_draws: object | None = None,
    local_count_draws: object | None = None,
) -> LoveResult:
    """Run analytical or optimized Python LOVE for one paired sample."""
    local_table = frame(local_pollen, "local_pollen")
    regional_table = frame(regional_pollen, "regional_pollen")
    _, taxa, _ = sample_counts(local_table, "local_pollen")
    _, regional_taxa, _ = sample_counts(regional_table, "regional_pollen")
    if taxa != regional_taxa:
        raise ValidationError(
            "Local and regional pollen taxa must agree exactly in name and order"
        )
    if regional_cover_draws is not None:
        draws = np.asarray(regional_cover_draws, dtype=float)
        if draws.shape != (config.repeats, len(taxa)):
            raise ValidationError(
                "regional_cover_draws must have shape (repeats, taxa)"
            )
        # REVEALS rounds each percentage to .001 before conversion to fractions.
        rounding_bound = len(taxa) * 0.000005 + 1e-12
        if (
            not np.isfinite(draws).all()
            or np.any(draws < 0)
            or np.any(draws > 1)
            or not np.allclose(draws.sum(axis=1), 1, rtol=0, atol=rounding_bound)
        ):
            raise ValidationError(
                "regional_cover_draws must be closed fractions, not percentages"
            )
    love_params = _prepare_love_params(params, taxa, config)

    if config.method == LoveMethod.ANALYTICAL.value:
        if replay_candidates is not None:
            raise ValidationError(
                "Analytical LOVE does not consume optimizer candidates"
            )
        analytical_raw = LOVEr(
            local_table,
            regional_table,
            love_params,
            rings,
            config.max_ring,
            repeats=config.repeats,
            rng=config.seed,
            stochastic=config.stochastic,
            regional_cover_draws=regional_cover_draws,
            local_ppe_draws=local_ppe_draws,
            local_count_draws=local_count_draws,
            return_samples=config.retain_samples,
        )
        if not bool(analytical_raw["valid_ring"].any()):
            raise ValidationError(
                "No requested local ring is supported by analytical LOVE geometry",
                reason_code="no_valid_local_rings",
            )
        cover = {
            "mean": analytical_raw["Mean"],
            "q10": analytical_raw["Q10"],
            "q90": analytical_raw["Q90"],
            "sd": analytical_raw["SD"],
        }
        analytical_samples: dict[str, np.ndarray] = (
            {"cover": analytical_raw["samples"]}
            if config.retain_samples and "samples" in analytical_raw
            else {}
        )
        return LoveResult(
            method=config.method,
            cover=cover,
            outlier=analytical_raw["Outlier"],
            outlier_quantile=analytical_raw["OutlierQant"],
            auxiliary={
                "Kreg": analytical_raw["Kreg"],
                "Kloc": analytical_raw["Kloc"],
                "valid_ring": analytical_raw["valid_ring"],
            },
            samples=analytical_samples,
            manifest=build_manifest(
                "LOVE-analytical",
                {
                    **config.as_dict(),
                    "paired_regional_cover_draws": regional_cover_draws is not None,
                    "paired_local_ppe_draws": local_ppe_draws is not None,
                    "paired_local_count_draws": local_count_draws is not None,
                    "equations": ["Sugita-2007-6", "Sugita-2007-7"],
                    "source_geometry": "disqover-0.9.14",
                },
                {
                    "local_pollen": local_table,
                    "regional_pollen": regional_table,
                    "params": params,
                    "rings": rings,
                    **(
                        {"regional_cover_draws": regional_cover_draws}
                        if regional_cover_draws is not None
                        else {}
                    ),
                    **(
                        {"local_ppe_draws": local_ppe_draws}
                        if local_ppe_draws is not None
                        else {}
                    ),
                    **(
                        {"local_count_draws": local_count_draws}
                        if local_count_draws is not None
                        else {}
                    ),
                },
                stochastic=config.stochastic,
                seed=config.seed,
            ),
        )

    if local_ppe_draws is not None:
        raise ValidationError(
            "Optimized LOVE does not consume local_ppe_draws in this profile"
        )
    optimizer = (
        ReplayOptimizer(np.asarray(replay_candidates, dtype=float))
        if replay_candidates is not None
        else None
    )
    raw = LOVEoptim(
        local_table,
        regional_table,
        love_params,
        rings,
        config.max_ring,
        repeats=config.repeats,
        rng=config.seed,
        stochastic=config.stochastic,
        regional_cover_draws=regional_cover_draws,
        local_count_draws=local_count_draws,
        optimizer=optimizer,
        itermax=config.optimizer_iterations,
        max_evaluations=config.optimizer_max_evaluations,
        tolerance=config.optimizer_tolerance,
        return_samples=config.retain_samples,
    )
    if not raw["optimizers"]:
        raise ValidationError(
            "No requested local ring has usable terrestrial area",
            reason_code="no_valid_local_rings",
        )
    if any(not diagnostic.success for diagnostic in raw["optimizers"]):
        raise ConvergenceError(
            [diagnostic.as_dict() for diagnostic in raw["optimizers"]]
        )
    cover = {
        "mean": raw["cover"]["mean"],
        "q10": raw["cover"]["Q10"],
        "q90": raw["cover"]["Q90"],
    }
    pollen_percentages = {
        "mean": raw["pollenpercentages"]["mean"],
        "q10": raw["pollenpercentages"]["Q10"],
        "q90": raw["pollenpercentages"]["Q90"],
    }
    samples: dict[str, np.ndarray] = {}
    if config.retain_samples:
        samples = {
            "cover": raw["cover_samples"],
            "pollen_percentages": raw["pollen_samples"],
        }
    return LoveResult(
        method=config.method,
        cover=cover,
        pollen_percentages=pollen_percentages,
        objective_values=raw["mBestValue"],
        diagnostics=raw["optimizers"],
        auxiliary={
            "K": raw["K"],
            "terrestrial_fraction": raw["terrestrial_fraction"],
        },
        samples=samples,
        manifest=build_manifest(
            "LOVE-optimized",
            {
                **config.as_dict(),
                "optimizer_backend": (
                    "candidate-replay"
                    if replay_candidates is not None
                    else "scipy.differential_evolution"
                ),
                "candidate_count": (
                    len(np.asarray(replay_candidates))
                    if replay_candidates is not None
                    else None
                ),
                "paired_regional_cover_draws": regional_cover_draws is not None,
                "paired_local_count_draws": local_count_draws is not None,
                "source_quirks": [
                    "calK_forces_peatland",
                    "sampled_PPE_vector_is_not_used_by_reference_objective",
                ],
            },
            {
                "local_pollen": local_table,
                "regional_pollen": regional_table,
                "params": params,
                "rings": rings,
                **(
                    {"regional_cover_draws": regional_cover_draws}
                    if regional_cover_draws is not None
                    else {}
                ),
                **(
                    {"local_count_draws": local_count_draws}
                    if local_count_draws is not None
                    else {}
                ),
                **(
                    {"replay_candidates": replay_candidates}
                    if replay_candidates is not None
                    else {}
                ),
            },
            stochastic=config.stochastic,
            seed=config.seed,
        ),
    )
