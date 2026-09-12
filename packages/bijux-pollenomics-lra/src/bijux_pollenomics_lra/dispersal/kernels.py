"""Dispersal kernels for the LRA engine."""

from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
from typing import Final

import numpy as np

from bijux_pollenomics_lra.dispersal.loess import Loess1D
from bijux_pollenomics_lra.dispersal.rounding import r_round
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import finite_number, scalar

METHODS: Final[tuple[str, ...]] = (
    "lsm unstable",
    "lsm unstable low",
    "gpm neutral",
    "gpm unstable",
    "1overd",
)

BASIN_TYPES: Final[tuple[str, ...]] = ("lake", "peatland")


def gpm_values(
    distance_m: object,
    fall_speed_m_s: float,
    diffusion_coefficient: float,
    turbulence_parameter: float,
    wind_speed_m_s: float,
) -> float | np.ndarray:
    """Evaluate the Sutton/Prentice Gaussian plume remaining-airborne curve."""
    distance = np.asarray(distance_m, dtype=float)
    if not np.isfinite(distance).all() or np.any(distance < 0):
        raise ValidationError("GPM distances must be finite and nonnegative")
    values = (
        fall_speed_m_s,
        diffusion_coefficient,
        turbulence_parameter,
        wind_speed_m_s,
    )
    if any(not np.isfinite(value) or value <= 0 for value in values):
        raise ValidationError("GPM parameters must be positive and finite")
    result = np.exp(
        -4
        * fall_speed_m_s
        * distance ** (turbulence_parameter / 2)
        / (
            turbulence_parameter
            * wind_speed_m_s
            * np.sqrt(np.pi)
            * diffusion_coefficient
        )
    )
    return float(result) if result.ndim == 0 else result


@lru_cache(maxsize=256)
def gpm(
    fall_speed_m_s: float,
    diffusion_coefficient: float,
    turbulence_parameter: float,
    wind_speed_m_s: float,
) -> Loess1D:
    """Build the source-compatible GPM LOESS curve."""
    x_values = np.linspace(0, 100, 1001) ** 3
    y_values = gpm_values(
        x_values,
        fall_speed_m_s,
        diffusion_coefficient,
        turbulence_parameter,
        wind_speed_m_s,
    )
    return Loess1D.fit(x_values, y_values)


@lru_cache(maxsize=1)
def one_over_d_model() -> Loess1D:
    """Build the experimental source ``1overd`` distance curve."""
    x_values = (1 + np.arange(661) * 0.15) ** 3
    y_values = 1 / x_values
    y_values /= y_values.sum()
    return Loess1D.fit(x_values, y_values)


@lru_cache(maxsize=1)
def _lsm_data() -> dict[str, np.ndarray]:
    resource = files("bijux_pollenomics_lra").joinpath(
        "resources", "data", "lsm_models.npz"
    )
    with resource.open("rb") as stream, np.load(stream, allow_pickle=False) as data:
        return {key: data[key] for key in data.files}


@lru_cache(maxsize=64)
def lsm_model(fall_speed_m_s: float, *, low_resolution: bool = False) -> Loess1D:
    """Select the source R LSM curve using R-compatible fall-speed rounding."""
    fall_speed_m_s = finite_number(
        fall_speed_m_s, "fall_speed_m_s", minimum=0, strict_minimum=True
    )
    index = int((200 if low_resolution else 100) * r_round(fall_speed_m_s, 2))
    if low_resolution and index == 0:
        index = 1
    maximum = 30 if low_resolution else 15
    if not 1 <= index <= maximum:
        raise ValidationError(
            "Fall speed lies outside the stored Lagrangian stochastic models"
        )
    key = f"lsm_unstable{'_low' if low_resolution else ''}_{index}"
    data = _lsm_data()
    return Loess1D(
        data[f"{key}_vertices"],
        data[f"{key}_values"],
        data[f"{key}_derivatives"],
        tuple(data[f"{key}_domain"]),
    )


def _distance_model(
    fall_speed_m_s: float,
    method: str,
    wind_speed_m_s: float,
) -> Loess1D:
    if method == "gpm neutral":
        return gpm(fall_speed_m_s, 0.12, 0.25, wind_speed_m_s)
    if method == "gpm unstable":
        return gpm(fall_speed_m_s, 0.21, 0.20, wind_speed_m_s)
    if method == "1overd":
        return one_over_d_model()
    return lsm_model(
        fall_speed_m_s,
        low_resolution=method == "lsm unstable low",
    )


def lake_annulus_influx(
    point_radius_m: float,
    basin_diameter_m: float,
    distance_model: Loess1D,
    step_size_m: float,
    region_cutoff_m: float,
) -> float:
    """Calculate one source-compatible annular contribution for a lake basin."""
    point_radius_m = float(point_radius_m)
    basin_radius = float(basin_diameter_m) / 2
    if not (0 < point_radius_m < basin_radius) or step_size_m <= 0:
        raise ValidationError(
            "Lake integration requires 0 < point radius < basin radius and a "
            "positive step"
        )

    radii = np.arange(
        basin_radius - point_radius_m,
        2 * basin_radius + 1e-10,
        2.0,
    )
    clipped_radii = np.minimum(radii, basin_radius + point_radius_m)
    cosine = (clipped_radii**2 + point_radius_m**2 - basin_radius**2) / (
        2 * clipped_radii * point_radius_m
    )
    proportion_outside = 1 - np.arccos(np.clip(cosine, -1, 1)) / np.pi
    midpoint_proportion = (proportion_outside[:-1] + proportion_outside[1:]) / 2
    airborne = np.asarray(distance_model.predict(radii), dtype=float)
    influx = np.sum(np.abs(np.diff(airborne)) * midpoint_proportion)
    influx += float(distance_model.predict(2 * basin_radius))
    influx -= float(distance_model.predict(region_cutoff_m))
    annulus_area = np.pi * (point_radius_m**2 - (point_radius_m - step_size_m) ** 2)
    return float(influx * annulus_area)


@lru_cache(maxsize=16384)
def _factor_scalar(
    fall_speed_m_s: float,
    basin_type: str,
    basin_diameter_m: float,
    method: str,
    region_cutoff_m: float,
    wind_speed_m_s: float,
) -> float:
    basin_radius = basin_diameter_m / 2
    model: Loess1D | None = None

    if method.startswith("gpm"):
        diffusion, turbulence = (
            (0.12, 0.25) if method == "gpm neutral" else (0.21, 0.20)
        )
        # Intentional DISQOVER 0.9.14 behaviour: the GPM peatland path uses
        # basin diameter here, while the other models use basin radius.
        inner = gpm_values(
            basin_diameter_m,
            fall_speed_m_s,
            diffusion,
            turbulence,
            wind_speed_m_s,
        )
        outer = gpm_values(
            region_cutoff_m,
            fall_speed_m_s,
            diffusion,
            turbulence,
            wind_speed_m_s,
        )
    else:
        model = _distance_model(fall_speed_m_s, method, wind_speed_m_s)
        inner = model.predict(basin_radius)
        outer = model.predict(region_cutoff_m)

    if basin_type == "peatland":
        return float(inner - outer if region_cutoff_m <= 1e6 else inner)

    if model is None:
        model = _distance_model(fall_speed_m_s, method, wind_speed_m_s)
    step_size = 10 if basin_diameter_m >= 2000 else 2
    steps = np.arange(step_size, basin_radius - 1 + 1e-10, step_size, dtype=float)
    if len(steps) == 0:
        raise ValidationError(
            "The source lake integration requires a basin diameter of at least 6 m"
        )
    total = sum(
        lake_annulus_influx(
            radius,
            basin_diameter_m,
            model,
            step_size,
            region_cutoff_m,
        )
        for radius in steps
    )
    return float(total / (np.pi * steps[-1] ** 2))


def dispersal_factor(
    fall_speed_m_s: float,
    basin_type: str,
    basin_diameter_m: float | np.ndarray,
    method: str,
    region_cutoff_m: float = 100_000,
    wind_speed_m_s: float = 3,
) -> float | np.ndarray:
    """Calculate the LRA dispersal/deposition factor ``K``.

    Basin diameter may be scalar or array-like.  All other arguments are scalar.
    The return shape follows ``basin_diameter_m``.
    """
    fall_speed = finite_number(
        scalar(fall_speed_m_s, "fall_speed_m_s"),
        "fall_speed_m_s",
        minimum=0,
        strict_minimum=True,
    )
    basin_type = str(scalar(basin_type, "basin_type")).strip().lower()
    method = str(scalar(method, "method")).strip().lower()
    cutoff = finite_number(
        scalar(region_cutoff_m, "region_cutoff_m"),
        "region_cutoff_m",
        minimum=0,
        strict_minimum=True,
    )
    wind_speed = finite_number(
        scalar(wind_speed_m_s, "wind_speed_m_s"),
        "wind_speed_m_s",
        minimum=0,
        strict_minimum=True,
    )
    diameters = np.asarray(basin_diameter_m, dtype=float)
    if not np.isfinite(diameters).all() or np.any(diameters < 0):
        raise ValidationError("Basin diameters must be finite and nonnegative")
    if basin_type not in BASIN_TYPES:
        raise ValidationError(f"basin_type must be one of {BASIN_TYPES}")
    if method not in METHODS:
        raise ValidationError(f"method must be one of {METHODS}")

    result = np.asarray(
        [
            _factor_scalar(
                fall_speed,
                basin_type,
                float(diameter),
                method,
                cutoff,
                wind_speed,
            )
            for diameter in diameters.reshape(-1)
        ]
    ).reshape(diameters.shape)
    return float(result) if result.ndim == 0 else result


def DispersalFactorK(
    vg: float,
    tBasin: str,
    dBasin: float | np.ndarray,
    dwm: str,
    regionCutoff: float,
    u: float = 3,
) -> float | np.ndarray:
    """Compatibility alias for ``dispersal_factor``."""
    return dispersal_factor(vg, tBasin, dBasin, dwm, regionCutoff, u)


def clear_dispersal_cache() -> None:
    """Clear all fitted-model and scalar-factor caches."""
    _factor_scalar.cache_clear()
    gpm.cache_clear()
    lsm_model.cache_clear()
    one_over_d_model.cache_clear()
    _lsm_data.cache_clear()
