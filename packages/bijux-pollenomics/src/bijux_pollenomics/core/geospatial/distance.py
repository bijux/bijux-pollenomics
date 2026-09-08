from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, isfinite, radians, sin, sqrt

from pyproj import Geod
from pyproj import __version__ as pyproj_version

EARTH_RADIUS_KM = 6371.0088
WGS84_DISTANCE_ALGORITHM = "WGS84 inverse geodesic"
WGS84_DISTANCE_LIBRARY = "pyproj"
WGS84_GEODESIC = Geod(ellps="WGS84")

__all__ = [
    "EARTH_RADIUS_KM",
    "WGS84_DISTANCE_ALGORITHM",
    "WGS84_DISTANCE_LIBRARY",
    "GeodesicDistance",
    "InvalidCoordinateError",
    "haversine_km",
    "wgs84_inverse_geodesic",
]


class InvalidCoordinateError(ValueError):
    """Raised when an endpoint cannot participate in geodesic calculation."""


@dataclass(frozen=True)
class GeodesicDistance:
    """Full-precision eligibility distance plus separate display metadata."""

    distance_km_unrounded: float
    distance_km_display: float
    distance_algorithm: str = WGS84_DISTANCE_ALGORITHM
    distance_library: str = WGS84_DISTANCE_LIBRARY
    distance_library_version: str = pyproj_version


def wgs84_inverse_geodesic(
    *,
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> GeodesicDistance:
    """Calculate the WGS84 inverse-geodesic distance between two endpoints."""
    latitude_a = _validated_coordinate(
        latitude_a, field_name="latitude_a", minimum=-90.0, maximum=90.0
    )
    longitude_a = _validated_coordinate(
        longitude_a, field_name="longitude_a", minimum=-180.0, maximum=180.0
    )
    latitude_b = _validated_coordinate(
        latitude_b, field_name="latitude_b", minimum=-90.0, maximum=90.0
    )
    longitude_b = _validated_coordinate(
        longitude_b, field_name="longitude_b", minimum=-180.0, maximum=180.0
    )
    _, _, distance_metres = WGS84_GEODESIC.inv(
        longitude_a,
        latitude_a,
        longitude_b,
        latitude_b,
    )
    distance_km = abs(float(distance_metres)) / 1000.0
    return GeodesicDistance(
        distance_km_unrounded=distance_km,
        distance_km_display=round(distance_km, 3),
    )


def _validated_coordinate(
    value: object,
    *,
    field_name: str,
    minimum: float,
    maximum: float,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidCoordinateError(f"{field_name} must be a finite number")
    coordinate = float(value)
    if not isfinite(coordinate):
        raise InvalidCoordinateError(f"{field_name} must be finite")
    if coordinate < minimum or coordinate > maximum:
        raise InvalidCoordinateError(
            f"{field_name} must be between {minimum} and {maximum}"
        )
    return coordinate


def haversine_km(
    *,
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    """Return the great-circle distance between two latitude/longitude points."""
    latitude_delta = radians(latitude_b - latitude_a)
    longitude_delta = radians(longitude_b - longitude_a)
    latitude_a_radians = radians(latitude_a)
    latitude_b_radians = radians(latitude_b)
    sin_latitude = sin(latitude_delta / 2.0)
    sin_longitude = sin(longitude_delta / 2.0)
    arc = (
        sin_latitude * sin_latitude
        + cos(latitude_a_radians)
        * cos(latitude_b_radians)
        * sin_longitude
        * sin_longitude
    )
    return 2.0 * EARTH_RADIUS_KM * asin(sqrt(arc))
