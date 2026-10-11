"""Owned analytical inputs prepared once before repeat and ring calculations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.dispersal.kernels import DispersalFactorK
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import (
    integer,
    parameter_value,
    sample_counts,
)
from bijux_pollenomics_lra.reconstruction.regional import checkREVEALS


def _owned(values: object) -> np.ndarray:
    result = np.array(values, dtype=float, copy=True)
    result.setflags(write=False)
    return result


@dataclass(frozen=True, slots=True)
class PreparedAnalyticalInputs:
    """Private numerical inputs; no references to caller-owned labeled tables."""

    local_counts: np.ndarray
    regional_counts: np.ndarray | None
    ppe_means: np.ndarray
    ppe_errors: np.ndarray
    regional_deposition: np.ndarray | None
    local_error: bool


def prepare_analytical_inputs(
    local: pd.DataFrame,
    regional: pd.DataFrame | None,
    ppe_table: pd.DataFrame,
    params: Mapping[str, object],
    *,
    stochastic: bool,
    needs_regional_deposition: bool,
) -> PreparedAnalyticalInputs:
    """Extract validated arrays and, when needed, regional deposition factors."""
    local_counts, _, _ = sample_counts(local, "vSampleLoc")
    if regional is None and needs_regional_deposition:
        raise ValidationError("Regional pollen is required for regional deposition")
    regional_counts = (
        None if regional is None else sample_counts(regional, "pollenReg")[0]
    )
    deposition = None
    if needs_regional_deposition:
        assert regional is not None
        basin_type = str(parameter_value(params, "tBasinRegional", "lake")).lower()
        diameter = integer(
            parameter_value(params, "dBasinRegional"), "dBasinRegional", minimum=10
        )
        method = str(parameter_value(params, "dwm", "lsm unstable")).lower()
        checkREVEALS(
            regional,
            ppe_table,
            basin_type,
            diameter,
            method,
            1,
            100_000,
            verbose=False,
        )
        deposition = _owned(
            [
                DispersalFactorK(speed, basin_type, diameter, method, 100_000)
                for speed in ppe_table["fallspeed"]
            ]
        )
        if not np.isfinite(deposition).all() or np.any(deposition <= 0):
            raise ValidationError(
                "Deposition factors are undefined or nonpositive; check model domain, "
                "basin geometry, and regionCutoff"
            )
    return PreparedAnalyticalInputs(
        _owned(local_counts),
        None if regional_counts is None else _owned(regional_counts),
        _owned(ppe_table["ppe"]),
        _owned(ppe_table["ppe.error"]),
        deposition,
        bool(parameter_value(params, "error", True)) and bool(stochastic),
    )
