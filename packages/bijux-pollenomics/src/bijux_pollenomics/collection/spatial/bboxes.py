from __future__ import annotations


def point_in_bbox(
    longitude: float,
    latitude: float,
    bbox: tuple[float, float, float, float],
) -> bool:
    """Check whether a lon/lat pair falls inside a bbox."""
    min_longitude, min_latitude, max_longitude, max_latitude = bbox
    return (
        min_longitude <= longitude <= max_longitude
        and min_latitude <= latitude <= max_latitude
    )


__all__ = ["point_in_bbox"]
