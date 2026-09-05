from __future__ import annotations

from collections.abc import Callable

from .models import _Target as Target


def polygon_contains(geometry, *, longitude: float, latitude: float) -> bool:  # type: ignore[no-untyped-def]
    coordinates = geometry.get("coordinates", [])
    if geometry.get("type") != "Polygon" or not coordinates:
        return False
    ring = coordinates[0]
    longitudes = [float(point[0]) for point in ring]
    latitudes = [float(point[1]) for point in ring]
    return min(longitudes) <= longitude <= max(longitudes) and min(
        latitudes
    ) <= latitude <= max(latitudes)


def within_radius(
    target: Target,
    *,
    latitude: float,
    longitude: float,
    distance_km: Callable[..., float],
    context_radius_km: int,
) -> bool:
    return (
        distance_km(
            latitude_a=target.latitude,
            longitude_a=target.longitude,
            latitude_b=latitude,
            longitude_b=longitude,
        )
        <= context_radius_km
    )
