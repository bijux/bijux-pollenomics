"""Models configuration for the LRA engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, StrEnum

import numpy as np

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.validation import finite_number, integer


class BasinType(StrEnum):
    """Supported pollen-basin deposition geometries."""

    LAKE = "lake"
    PEATLAND = "peatland"


class DistanceWeighting(StrEnum):
    """Distance-weighting models available in the source implementation."""

    LSM_UNSTABLE = "lsm unstable"
    LSM_UNSTABLE_LOW = "lsm unstable low"
    GPM_NEUTRAL = "gpm neutral"
    GPM_UNSTABLE = "gpm unstable"
    ONE_OVER_D = "1overd"


class LoveMethod(StrEnum):
    """Available LOVE reconstruction formulations."""

    ANALYTICAL = "analytical"
    OPTIMIZED = "optimized"


def _enum_value(value: str | Enum, enum: type[Enum], name: str) -> str:
    raw = value.value if isinstance(value, Enum) else str(value).strip().lower()
    allowed = {member.value for member in enum}
    if raw not in allowed:
        raise ValidationError(f"{name} must be one of {sorted(allowed)}")
    return raw


def _boolean(value: object, name: str) -> bool:
    if not isinstance(value, (bool, np.bool_)):
        raise ValidationError(f"{name} must be boolean")
    return bool(value)


@dataclass(frozen=True, slots=True)
class RevealsConfig:
    """Configuration for a regional REVEALS reconstruction."""

    basin_type: BasinType | str
    basin_diameter_m: int
    distance_weighting: DistanceWeighting | str = DistanceWeighting.LSM_UNSTABLE
    iterations: int = 1000
    region_cutoff_m: float = 100_000
    stochastic: bool = True
    seed: int | None = None
    retain_samples: bool = False

    def __post_init__(self) -> None:
        basin_type = _enum_value(self.basin_type, BasinType, "basin_type")
        method = _enum_value(
            self.distance_weighting, DistanceWeighting, "distance_weighting"
        )
        diameter = integer(self.basin_diameter_m, "basin_diameter_m", minimum=10)
        iterations = integer(self.iterations, "iterations")
        cutoff = finite_number(
            self.region_cutoff_m,
            "region_cutoff_m",
            minimum=0,
            strict_minimum=True,
        )
        if diameter / 2 > cutoff:
            raise ValidationError("Basin radius cannot exceed region_cutoff_m")
        if self.seed is not None:
            integer(self.seed, "seed", minimum=0)
        stochastic = _boolean(self.stochastic, "stochastic")
        retain_samples = _boolean(self.retain_samples, "retain_samples")
        object.__setattr__(self, "basin_type", basin_type)
        object.__setattr__(self, "distance_weighting", method)
        object.__setattr__(self, "basin_diameter_m", diameter)
        object.__setattr__(self, "iterations", iterations)
        object.__setattr__(self, "region_cutoff_m", cutoff)
        object.__setattr__(self, "stochastic", stochastic)
        object.__setattr__(self, "retain_samples", retain_samples)

    def as_dict(self) -> dict[str, object]:
        """Return JSON-compatible settings."""
        return {
            "basin_type": self.basin_type,
            "basin_diameter_m": self.basin_diameter_m,
            "distance_weighting": self.distance_weighting,
            "iterations": self.iterations,
            "region_cutoff_m": self.region_cutoff_m,
            "stochastic": self.stochastic,
            "seed": self.seed,
            "retain_samples": self.retain_samples,
        }


@dataclass(frozen=True, slots=True)
class LoveConfig:
    """Configuration for analytical or optimized local reconstruction."""

    method: LoveMethod | str
    regional_basin_type: BasinType | str
    regional_basin_diameter_m: int
    local_basin_diameter_m: float
    max_ring: int
    distance_weighting: DistanceWeighting | str = DistanceWeighting.LSM_UNSTABLE
    repeats: int = 100
    stochastic: bool = True
    seed: int | None = None
    retain_samples: bool = False
    ppe_error: bool = True
    optimizer_iterations: int = 200
    optimizer_max_evaluations: int | None = None
    optimizer_tolerance: float = 0.01

    def __post_init__(self) -> None:
        method = _enum_value(self.method, LoveMethod, "method")
        basin_type = _enum_value(
            self.regional_basin_type, BasinType, "regional_basin_type"
        )
        distance_weighting = _enum_value(
            self.distance_weighting, DistanceWeighting, "distance_weighting"
        )
        regional_diameter = integer(
            self.regional_basin_diameter_m,
            "regional_basin_diameter_m",
            minimum=10,
        )
        local_diameter = finite_number(
            self.local_basin_diameter_m,
            "local_basin_diameter_m",
            minimum=0,
            strict_minimum=True,
        )
        maximum_ring = integer(self.max_ring, "max_ring")
        repeats = integer(self.repeats, "repeats")
        optimizer_iterations = integer(
            self.optimizer_iterations, "optimizer_iterations"
        )
        max_evaluations = self.optimizer_max_evaluations
        if max_evaluations is not None:
            max_evaluations = integer(max_evaluations, "optimizer_max_evaluations")
        tolerance = finite_number(
            self.optimizer_tolerance,
            "optimizer_tolerance",
            minimum=0,
        )
        if self.seed is not None:
            integer(self.seed, "seed", minimum=0)
        stochastic = _boolean(self.stochastic, "stochastic")
        retain_samples = _boolean(self.retain_samples, "retain_samples")
        ppe_error = _boolean(self.ppe_error, "ppe_error")
        object.__setattr__(self, "method", method)
        object.__setattr__(self, "regional_basin_type", basin_type)
        object.__setattr__(self, "distance_weighting", distance_weighting)
        object.__setattr__(self, "regional_basin_diameter_m", regional_diameter)
        object.__setattr__(self, "local_basin_diameter_m", local_diameter)
        object.__setattr__(self, "max_ring", maximum_ring)
        object.__setattr__(self, "repeats", repeats)
        object.__setattr__(self, "optimizer_iterations", optimizer_iterations)
        object.__setattr__(self, "optimizer_max_evaluations", max_evaluations)
        object.__setattr__(self, "optimizer_tolerance", tolerance)
        object.__setattr__(self, "stochastic", stochastic)
        object.__setattr__(self, "retain_samples", retain_samples)
        object.__setattr__(self, "ppe_error", ppe_error)

    def as_dict(self) -> dict[str, object]:
        """Return JSON-compatible settings."""
        return {
            "method": self.method,
            "regional_basin_type": self.regional_basin_type,
            "regional_basin_diameter_m": self.regional_basin_diameter_m,
            "local_basin_diameter_m": self.local_basin_diameter_m,
            "max_ring": self.max_ring,
            "distance_weighting": self.distance_weighting,
            "repeats": self.repeats,
            "stochastic": self.stochastic,
            "seed": self.seed,
            "retain_samples": self.retain_samples,
            "ppe_error": self.ppe_error,
            "optimizer_iterations": self.optimizer_iterations,
            "optimizer_max_evaluations": self.optimizer_max_evaluations,
            "optimizer_tolerance": self.optimizer_tolerance,
        }


@dataclass(frozen=True, slots=True)
class LRAConfig:
    """Configuration for the two-stage REVEALS then LOVE workflow."""

    reveals: RevealsConfig
    love: LoveConfig
    seed: int | None = None
    couple_regional_draws: bool = True

    def __post_init__(self) -> None:
        if self.seed is not None:
            integer(self.seed, "seed", minimum=0)
        if not isinstance(self.couple_regional_draws, (bool, np.bool_)):
            raise ValidationError("couple_regional_draws must be boolean")
        if self.couple_regional_draws and self.reveals.iterations < self.love.repeats:
            raise ValidationError(
                "Coupled LRA requires REVEALS iterations >= LOVE repeats"
            )
        if self.reveals.basin_type != self.love.regional_basin_type:
            raise ValidationError("REVEALS and LOVE regional basin types must agree")
        if self.reveals.basin_diameter_m != self.love.regional_basin_diameter_m:
            raise ValidationError(
                "REVEALS and LOVE regional basin diameters must agree"
            )
        if self.reveals.distance_weighting != self.love.distance_weighting:
            raise ValidationError(
                "REVEALS and LOVE distance-weighting methods must agree"
            )

    def as_dict(self) -> dict[str, object]:
        return {
            "reveals": self.reveals.as_dict(),
            "love": self.love.as_dict(),
            "seed": self.seed,
            "couple_regional_draws": self.couple_regional_draws,
        }
