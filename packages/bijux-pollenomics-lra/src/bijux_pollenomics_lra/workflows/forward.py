"""Prepare target-specific deposition geometry without target pollen or fitting."""

from __future__ import annotations

from numbers import Real

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.models.configuration import ForwardConfig
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.results import PreparedForwardInputs
from bijux_pollenomics_lra.models.validation import frame, normalise_parameters
from bijux_pollenomics_lra.reconstruction.forward import _deposition_components
from bijux_pollenomics_lra.reconstruction.optimized import calK


def _numeric(values: object, name: str) -> np.ndarray:
    raw = np.asarray(values, dtype=object)
    if any(
        isinstance(value, (bool, np.bool_)) or not isinstance(value, Real)
        for value in raw.flat
    ):
        raise ValidationError(
            f"{name} requires numerical values, not strings or booleans"
        )
    result = np.asarray(raw, dtype=float)
    if not np.isfinite(result).all():
        raise ValidationError(f"{name} requires finite values")
    return result


def _readonly(values: np.ndarray) -> np.ndarray:
    # The independent bytes backing prevents writeability from being re-enabled.
    return np.frombuffer(values.astype(float).tobytes(), dtype=float).reshape(
        values.shape
    )


def _geometry(
    rings: pd.DataFrame, config: ForwardConfig
) -> tuple[pd.DataFrame, np.ndarray]:
    table = frame(rings, "rings")
    required = ["inner", "outer", "mean", "ring", "terrestrial"]
    if any(name not in table for name in required):
        raise ValidationError(
            "rings requires inner/outer/mean in metres and ring/terrestrial in square metres"
        )
    values = _numeric(table[required].to_numpy(), "rings")
    inner, outer, mean, area, land = values.T
    count = config.local_ring_count
    if count >= len(table):
        raise ValidationError("At least one explicit regional ring is required")
    if np.any(inner < 0) or np.any(outer <= inner) or np.any(inner[1:] < outer[:-1]):
        raise ValidationError("Rings must be ordered and nonoverlapping")
    if np.any(mean < inner) or np.any(mean > outer):
        raise ValidationError("Ring mean must lie within its interval")
    if inner[0] != config.local_basin_diameter_m / 2 or np.any(inner[1:] != outer[:-1]):
        raise ValidationError(
            "This profile requires contiguous circular rings from the declared basin shore"
        )
    if outer[-1] > 100_000:
        raise ValidationError("The source kernel profile is bounded at 100000 metres")
    expected_area = np.pi * (outer**2 - inner**2)
    if np.any(area <= 0) or not np.allclose(area, expected_area, rtol=1e-8, atol=1e-8):
        raise ValidationError("ring must be circular annulus area in square metres")
    if np.any(land < 0) or np.any(land > area):
        raise ValidationError("terrestrial area must lie between zero and ring area")
    fractions = land / area
    if not np.any(fractions[:count] > 0):
        raise ValidationError("Local rings require positive terrestrial support")
    return table, fractions


def prepare_forward_inputs(
    params: pd.DataFrame,
    rings: pd.DataFrame,
    regional_cover: object,
    config: ForwardConfig,
) -> PreparedForwardInputs:
    """Prepare homogeneous-local matrix deposition with nominal PPE.

    Regional cover has exact taxon order and explicit fraction units. Rounded
    DISQOVER fractions are preserved without renormalization only when selected
    in config. No target pollen, total count, random draws or optimization enters
    this calculation. This corrected-matrix profile keeps the taxon axis when
    either side has one ring; it does not reproduce legacy R scalar recycling.
    """
    if not isinstance(config, ForwardConfig):
        raise ValidationError("config must be ForwardConfig")
    parameters = frame(params, "params")
    required = ["Taxon", "fallspeed", "ppe", "ppe.error"]
    if any(name not in parameters for name in required):
        raise ValidationError("params requires Taxon, fallspeed, ppe and ppe.error")
    names = parameters["Taxon"].tolist()
    if any(not isinstance(name, str) or not name.strip() for name in names):
        raise ValidationError("Taxa must be nonempty strings")
    taxa = tuple(str(name) for name in names)
    if len(set(taxa)) != len(taxa):
        raise ValidationError("Taxa must be unique")
    _numeric(parameters[required[1:]].to_numpy(), "params")
    parameters = normalise_parameters(parameters[required], taxa)
    geometry, fractions = _geometry(rings, config)
    cover = _numeric(regional_cover, "regional_cover")
    tolerance = (
        len(taxa) * 0.000005 + 1e-12
        if config.regional_cover_profile == "disqover-rounded-fractions"
        else 1e-12
    )
    if (
        cover.shape != (len(taxa),)
        or np.any(cover < 0)
        or np.any(cover > 1)
        or not np.isclose(cover.sum(), 1.0, rtol=0, atol=tolerance)
    ):
        raise ValidationError(
            "regional_cover must be taxon-aligned fractions with the declared closure"
        )
    kernel_parameters = {
        "fallspeed": pd.DataFrame(
            {"Taxon": taxa, "fallspeed": parameters["fallspeed"].to_numpy()}
        ),
        "dwm": str(config.distance_weighting),
    }
    kernels = calK(geometry, kernel_parameters).to_numpy(dtype=float)
    if not np.isfinite(kernels).all() or np.any(kernels < 0):
        raise ValidationError(
            "Source kernels must be finite and nonnegative for forward deposition",
            reason_code="unsupported_forward_kernel_geometry",
        )
    count = config.local_ring_count
    ppe = parameters["ppe"].to_numpy(dtype=float)
    regional, _ = _deposition_components(
        cover, np.zeros(len(taxa)), kernels[count:], fractions[count:], ppe
    )
    if not np.isfinite(regional).all():
        raise ValidationError("Regional deposition overflowed")
    return PreparedForwardInputs(
        taxa=taxa,
        local_k=_readonly(kernels[:count]),
        terrestrial_fraction=_readonly(fractions[:count]),
        ppe=_readonly(ppe),
        regional_deposition=_readonly(regional),
        regional_cover=_readonly(cover),
        full_k=_readonly(kernels),
        full_terrestrial_fraction=_readonly(fractions),
        ring_bounds_m=_readonly(geometry[["inner", "outer"]].to_numpy(dtype=float)),
        regional_cutoff_m=float(geometry["outer"].iloc[-1]),
        local_basin_diameter_m=config.local_basin_diameter_m,
        distance_weighting=str(config.distance_weighting),
        regional_cover_profile=config.regional_cover_profile,
        preparation_profile=config.preparation_profile,
    )
