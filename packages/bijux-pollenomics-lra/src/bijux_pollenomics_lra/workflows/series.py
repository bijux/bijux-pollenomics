"""Workflows series for the LRA engine."""

from __future__ import annotations

from dataclasses import replace
from numbers import Integral, Real

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.models.configuration import (
    LRAConfig,
)
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.results import (
    LRAResult,
    LRASeriesResult,
)
from bijux_pollenomics_lra.models.validation import (
    frame,
)
from bijux_pollenomics_lra.provenance.identity import sha256_object
from bijux_pollenomics_lra.provenance.manifest import build_manifest
from bijux_pollenomics_lra.workflows.paired import _seed_from_sequence, run_lra


def _pairing_coordinates(values: pd.Series) -> np.ndarray:
    """Validate coordinates before constructing binary64 lookup identities."""
    coordinates_list: list[float] = []
    # Preserve original object scalars: pandas numeric coercion can round a large
    # integer when another row is a fractional float, before any later check.
    for original in values.tolist():
        if isinstance(original, (bool, np.bool_)) or not isinstance(original, Real):
            raise ValidationError(
                "LRA series coordinates must be numeric scalars, excluding booleans",
                reason_code="invalid_coordinate_type",
            )
        try:
            converted = float(original)
        except (OverflowError, ValueError) as error:
            raise ValidationError("LRA series coordinates must be finite") from error
        if not np.isfinite(converted):
            raise ValidationError("LRA series coordinates must be finite")
        # Python integer comparison avoids NumPy implicitly promoting both sides.
        if isinstance(original, Integral) and int(converted) != int(original):
            raise ValidationError(
                "LRA series integer coordinates must be exactly representable as binary64",
                reason_code="coordinate_precision_loss",
            )
        coordinates_list.append(converted)
    coordinates = np.asarray(coordinates_list, dtype=float)
    if len(np.unique(coordinates)) != len(coordinates):
        raise ValidationError(
            "LRA series coordinates must be unique after binary64 conversion",
            reason_code="duplicate_coordinate",
        )
    return coordinates


def run_lra_series(
    local_pollen: pd.DataFrame,
    regional_pollen: pd.DataFrame,
    params: pd.DataFrame,
    rings: pd.DataFrame,
    config: LRAConfig,
    *,
    replay_candidates: object | None = None,
) -> LRASeriesResult:
    """Run paired LRA reconstructions for all exactly matching coordinates.

    The first column of each pollen table is the pairing key.  Duplicate keys,
    missing counterparts, and differing taxon order are rejected rather than
    implicitly interpolated or re-ordered.
    """
    local = frame(local_pollen, "local_pollen")
    regional = frame(regional_pollen, "regional_pollen")
    if list(map(str, local.columns[1:])) != list(map(str, regional.columns[1:])):
        raise ValidationError(
            "Local and regional series must have identical taxon columns"
        )
    local_coordinates = _pairing_coordinates(local.iloc[:, 0])
    regional_coordinates = _pairing_coordinates(regional.iloc[:, 0])
    local_keys = set(local_coordinates)
    regional_keys = set(regional_coordinates)
    if local_keys != regional_keys:
        missing_local = sorted(regional_keys - local_keys)
        missing_regional = sorted(local_keys - regional_keys)
        raise ValidationError(
            "Local/regional coordinates do not match; "
            f"missing local={missing_local}, missing regional={missing_regional}"
        )

    regional_lookup = {
        float(value): position for position, value in enumerate(regional_coordinates)
    }
    parent_sequences = (
        np.random.SeedSequence(config.seed).spawn(len(local))
        if config.seed is not None
        else [None] * len(local)
    )
    runs: dict[str, LRAResult] = {}
    for position, coordinate in enumerate(local_coordinates):
        numeric_coordinate = float(coordinate)
        regional_index = regional_lookup[numeric_coordinate]
        child_config = config
        parent_sequence = parent_sequences[position]
        if parent_sequence is not None:
            child_config = replace(
                config,
                seed=_seed_from_sequence(parent_sequence),
            )
        # Seventeen significant digits preserve distinct binary64 coordinates.
        key = format(numeric_coordinate, ".17g")
        runs[key] = run_lra(
            local.iloc[[position]],
            regional.iloc[[regional_index]],
            params,
            rings,
            child_config,
            replay_candidates=replay_candidates,
        )

    manifest = build_manifest(
        "LRA-series",
        {
            **config.as_dict(),
            "coordinates": list(runs),
            "run_manifest_sha256": {
                key: sha256_object(run.manifest.scientific_identity())
                for key, run in runs.items()
            },
        },
        {
            "local_pollen": local,
            "regional_pollen": regional,
            "params": params,
            "rings": rings,
        },
        stochastic=bool(config.reveals.stochastic or config.love.stochastic),
        seed=config.seed,
    )
    return LRASeriesResult(runs, manifest)
