"""Qualify bounded literal native points and extents without inventing locations."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import math
from typing import Any

from bijux_pollenomics.collection.sources.neotoma.client import (
    decode_neotoma_json_object,
)

MAX_EXTENT_POSITIONS = 20000
MAX_SITE_EXTENT_VARIANTS = 128


def native_point(native: Mapping[str, Any]) -> tuple[tuple[float, float] | None, str]:
    if "siteid" not in native:
        return None, "native_site_id_missing"
    if "geography" not in native:
        return None, "native_geography_missing"
    value = native["geography"]
    if isinstance(value, str):
        try:
            value = decode_neotoma_json_object(value)
        except ValueError:
            return None, "native_geography_invalid_json"
    if not isinstance(value, Mapping) or value.get("type") != "Point":
        return None, "native_geography_not_explicit_point"
    coordinates = value.get("coordinates")
    if (
        not isinstance(coordinates, list)
        or len(coordinates) != 2
        or any(type(v) not in (int, float) for v in coordinates)
    ):
        return None, "native_point_coordinates_invalid"
    try:
        longitude, latitude = (float(v) for v in coordinates)
    except (OverflowError, ValueError):
        return None, "native_point_coordinates_invalid"
    if (
        not math.isfinite(longitude)
        or not math.isfinite(latitude)
        or not -180 <= longitude <= 180
        or not -90 <= latitude <= 90
    ):
        return None, "native_point_coordinates_invalid"
    return (longitude, latitude), "explicit_native_point"


def native_extent(native: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str]:
    """Retain only explicit bounded Polygon/MultiPolygon rings and native positions."""
    if "siteid" not in native:
        return None, "native_site_id_missing"
    value = native.get("geography")
    if isinstance(value, str):
        try:
            value = decode_neotoma_json_object(value)
        except (ValueError, UnicodeError, RecursionError):
            return None, "native_extent_invalid_json"
    if not isinstance(value, Mapping) or value.get("type") not in {
        "Polygon",
        "MultiPolygon",
    }:
        return None, "native_geography_not_explicit_extent"
    coordinates = value.get("coordinates")
    polygons = [coordinates] if value["type"] == "Polygon" else coordinates
    if (
        not isinstance(polygons, list)
        or not polygons
        or len(polygons) > MAX_EXTENT_POSITIONS
    ):
        return None, "native_extent_coordinates_invalid"
    count = 0
    for polygon in polygons:
        if (
            not isinstance(polygon, list)
            or not polygon
            or len(polygon) > MAX_EXTENT_POSITIONS
        ):
            return None, "native_extent_coordinates_invalid"
        for ring in polygon:
            if not isinstance(ring, list) or not 4 <= len(ring) <= MAX_EXTENT_POSITIONS:
                return None, "native_extent_coordinates_invalid"
            for position in ring:
                count += 1
                if count > MAX_EXTENT_POSITIONS:
                    return None, "native_extent_coordinate_budget_exceeded"
                if not isinstance(position, list) or len(position) != 2:
                    return None, "native_extent_coordinates_invalid"
                if any(type(v) not in (int, float) for v in position):
                    return None, "native_extent_coordinates_invalid"
                try:
                    longitude, latitude = (float(v) for v in position)
                except (OverflowError, ValueError):
                    return None, "native_extent_coordinates_invalid"
                if (
                    not math.isfinite(longitude)
                    or not math.isfinite(latitude)
                    or not -180 <= longitude <= 180
                    or not -90 <= latitude <= 90
                ):
                    return None, "native_extent_coordinates_invalid"
            if ring[0] != ring[-1]:
                return None, "native_extent_ring_not_closed"
    return {
        "type": value["type"],
        "coordinates": deepcopy(coordinates),
    }, "explicit_native_extent"


def qualify_site_extents(variants: list[dict[str, Any]]) -> None:
    """Bound the whole site display while retaining every raw source variant."""
    if len(variants) > MAX_SITE_EXTENT_VARIANTS:
        for variant in variants:
            variant.update(
                extent_geometry=None,
                extent_status="native_extent_site_display_budget_exceeded",
            )
        return
    count = 0
    for variant in variants:
        geometry, status = native_extent(variant["native_site"])
        variant.update(extent_geometry=geometry, extent_status=status)
        if geometry is not None:
            polygons = (
                [geometry["coordinates"]]
                if geometry["type"] == "Polygon"
                else geometry["coordinates"]
            )
            count += sum(len(ring) for polygon in polygons for ring in polygon)
            if count > MAX_EXTENT_POSITIONS:
                for member in variants:
                    member.update(
                        extent_geometry=None,
                        extent_status="native_extent_site_display_budget_exceeded",
                    )
                return
