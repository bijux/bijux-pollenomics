"""Explicit exploratory model parameters and observed geographic coordinates."""

from __future__ import annotations

from dataclasses import dataclass

from ....core.geospatial.distance import wgs84_inverse_geodesic
from ..contracts import ValidationRefusal, finite_number, required_identity

PROFILE = "clr-wgs84-rbf-ridge-v1"


@dataclass(frozen=True)
class SpatialConfig:
    """Fixed declarations, not evidence of tuning or ecological acceptance."""

    length_scale_km: float
    ridge_penalty: float
    support_id: str

    def __post_init__(self) -> None:
        for field in ("length_scale_km", "ridge_penalty"):
            value = finite_number(getattr(self, field))
            if value <= 0:
                raise ValidationRefusal("invalid_spatial_configuration", field)
            object.__setattr__(self, field, value)
        required_identity(self.support_id)

    def as_dict(self) -> dict[str, object]:
        return {
            "profile": PROFILE,
            "length_scale_km": self.length_scale_km,
            "ridge_penalty": self.ridge_penalty,
            "support_id": self.support_id,
            "zero_policy": "strictly_positive_no_replacement",
            "parameter_selection": "caller_declared_not_verified",
        }


@dataclass(frozen=True)
class SiteCoordinate:
    """A declared WGS84 point, independent of pollen and vegetation outcomes."""

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        distance_km(self, self)
        object.__setattr__(self, "latitude", finite_number(self.latitude))
        object.__setattr__(self, "longitude", finite_number(self.longitude))

    def as_dict(self) -> dict[str, float]:
        return {"latitude": self.latitude, "longitude": self.longitude}


def distance_km(left: SiteCoordinate, right: SiteCoordinate) -> float:
    """Delegate validation and full-precision WGS84 distance to the host owner."""
    return wgs84_inverse_geodesic(
        latitude_a=left.latitude,
        longitude_a=left.longitude,
        latitude_b=right.latitude,
        longitude_b=right.longitude,
    ).distance_km_unrounded
