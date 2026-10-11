"""Workflows regional for the LRA engine."""

from __future__ import annotations

import pandas as pd

from bijux_pollenomics_lra.models.configuration import (
    RevealsConfig,
)
from bijux_pollenomics_lra.models.results import (
    RevealsResult,
)
from bijux_pollenomics_lra.provenance.manifest import build_manifest
from bijux_pollenomics_lra.reconstruction.regional import _reconstruct_frame


def run_reveals(
    pollen: pd.DataFrame,
    params: pd.DataFrame,
    config: RevealsConfig,
    *,
    ppe_draws: object | None = None,
    pollen_draws: object | None = None,
) -> RevealsResult:
    """Run a Python regional REVEALS reconstruction."""
    table, deposition, samples = _reconstruct_frame(
        pollen,
        params,
        config.basin_type,
        config.basin_diameter_m,
        config.distance_weighting,
        config.iterations,
        config.region_cutoff_m,
        None,
        None,
        False,
        False,
        rng=config.seed,
        stochastic=config.stochastic,
        ppe_draws=ppe_draws,
        pollen_draws=pollen_draws,
        output_dir=".",
        collect_samples=config.retain_samples,
    )
    manifest = build_manifest(
        "REVEALS",
        {
            **config.as_dict(),
            "paired_ppe_draws": ppe_draws is not None,
            "paired_pollen_draws": pollen_draws is not None,
            "equation": "Sugita-2007-B1",
        },
        {
            "pollen": pollen,
            "params": params,
            **({"ppe_draws": ppe_draws} if ppe_draws is not None else {}),
            **({"pollen_draws": pollen_draws} if pollen_draws is not None else {}),
        },
        stochastic=config.stochastic,
        seed=config.seed,
    )
    return RevealsResult(table, deposition, manifest, samples)
