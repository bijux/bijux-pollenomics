"""Workflows paired for the LRA engine."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.models.configuration import (
    LRAConfig,
)
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.results import (
    LRAResult,
)
from bijux_pollenomics_lra.provenance.identity import sha256_object
from bijux_pollenomics_lra.provenance.manifest import build_manifest
from bijux_pollenomics_lra.workflows.local import love_compatibility_mode, run_love
from bijux_pollenomics_lra.workflows.regional import run_reveals


def _seed_from_sequence(sequence: np.random.SeedSequence) -> int:
    return int(sequence.generate_state(1, dtype=np.uint32)[0])


def run_lra(
    local_pollen: pd.DataFrame,
    regional_pollen: pd.DataFrame,
    params: pd.DataFrame,
    rings: pd.DataFrame,
    config: LRAConfig,
    *,
    replay_candidates: object | None = None,
) -> LRAResult:
    """Run the complete regional REVEALS then local LOVE workflow."""
    reveals_config = config.reveals
    love_config = config.love
    if config.seed is not None:
        regional_sequence, local_sequence = np.random.SeedSequence(config.seed).spawn(2)
        reveals_config = replace(
            reveals_config, seed=_seed_from_sequence(regional_sequence)
        )
        love_config = replace(love_config, seed=_seed_from_sequence(local_sequence))

    # A true two-stage LRA run passes the regional REVEALS realizations into
    # LOVE rather than independently re-running REVEALS inside LOVE.  Samples
    # are retained internally for that hand-off even when the public result is
    # configured not to expose them.
    internal_reveals_config = (
        replace(reveals_config, retain_samples=True)
        if config.couple_regional_draws and not reveals_config.retain_samples
        else reveals_config
    )
    regional_result = run_reveals(regional_pollen, params, internal_reveals_config)
    regional_draws = None
    if config.couple_regional_draws:
        if regional_result.samples is None or regional_result.samples.shape[0] != 1:
            raise ValidationError(
                "Coupled LRA requires exactly one regional pollen sample"
            )
        regional_draws = regional_result.samples[0, : love_config.repeats, :] / 100

    local_result = run_love(
        local_pollen,
        regional_pollen,
        params,
        rings,
        love_config,
        replay_candidates=replay_candidates,
        regional_cover_draws=regional_draws,
    )
    if not reveals_config.retain_samples:
        regional_result.samples = None
    manifest = replace(
        build_manifest(
            "LRA",
            {
                **config.as_dict(),
                "stage_order": ["REVEALS", f"LOVE-{love_config.method}"],
                "regional_draw_handoff": config.couple_regional_draws,
                "regional_child_manifest_sha256": sha256_object(
                    regional_result.manifest.scientific_identity()
                ),
                "local_child_manifest_sha256": sha256_object(
                    local_result.manifest.scientific_identity()
                ),
            },
            {
                "local_pollen": local_pollen,
                "regional_pollen": regional_pollen,
                "params": params,
                "rings": rings,
            },
            stochastic=bool(reveals_config.stochastic or love_config.stochastic),
            seed=config.seed,
        ),
        compatibility_mode=love_compatibility_mode(love_config),
    )
    return LRAResult(regional_result, local_result, manifest)
