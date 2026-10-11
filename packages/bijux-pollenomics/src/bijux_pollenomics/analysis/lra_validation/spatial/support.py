"""One full-precision geographic support separation shared by experiments and evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ....core.geospatial.distance import wgs84_inverse_geodesic
from ..contracts import ValidationRefusal, finite_number


class GeographicSupport(Protocol):
    """Read-only bounded footprint interface; chronology remains a separate contract."""

    @property
    def latitude(self) -> float: ...

    @property
    def longitude(self) -> float: ...

    @property
    def radius_m(self) -> float: ...

    @property
    def coordinate_uncertainty_m(self) -> float: ...


@dataclass(frozen=True)
class SupportSeparation:
    """Every measured term of the conservative footprint-distance lower bound."""

    centre_distance_m: float
    target_radius_m: float
    training_radius_m: float
    target_coordinate_uncertainty_m: float
    training_coordinate_uncertainty_m: float
    lower_bound_m: float


def support_separation(
    target: GeographicSupport, training: GeographicSupport
) -> SupportSeparation:
    """Preserve evaluator arithmetic: unrounded geodesic minus both radii/uncertainties."""
    target_radius = finite_number(target.radius_m)
    training_radius = finite_number(training.radius_m)
    target_uncertainty = finite_number(target.coordinate_uncertainty_m)
    training_uncertainty = finite_number(training.coordinate_uncertainty_m)
    if (
        min(target_radius, training_radius, target_uncertainty, training_uncertainty)
        < 0
    ):
        raise ValidationRefusal(
            "invalid_spatial_support",
            "Footprint radii and coordinate uncertainties must be nonnegative metres",
        )
    distance = wgs84_inverse_geodesic(
        latitude_a=finite_number(target.latitude),
        longitude_a=finite_number(target.longitude),
        latitude_b=finite_number(training.latitude),
        longitude_b=finite_number(training.longitude),
    )
    centre_distance = distance.distance_km_unrounded * 1000
    lower = max(
        0.0,
        centre_distance
        - target_radius
        - training_radius
        - target_uncertainty
        - training_uncertainty,
    )
    return SupportSeparation(
        centre_distance,
        target_radius,
        training_radius,
        target_uncertainty,
        training_uncertainty,
        lower,
    )


def support_distance_lower_bound_m(
    target: GeographicSupport, training: GeographicSupport
) -> float:
    """Return the same scalar buffer quantity used by the governed final evaluator."""
    return support_separation(target, training).lower_bound_m
