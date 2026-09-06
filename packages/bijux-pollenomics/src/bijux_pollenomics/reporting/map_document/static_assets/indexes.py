"""Selection indexes for point-layer atlas records."""

from collections.abc import Sequence
import math

from ....core.geospatial.geojson import JsonObject
from ..coordinates import point_coordinate_pair


def build_indexes(point_layers: Sequence[JsonObject]) -> dict[str, object]:
    """Build deterministic country, spatial, temporal, and signal indexes."""
    countries: dict[str, dict[str, list[int]]] = {}
    spatial_cells: dict[str, dict[str, list[int]]] = {}
    time_intervals: list[list[object]] = []
    signals: dict[str, list[str]] = {}
    for layer in point_layers:
        layer_key = str(layer.get("key", "")).strip()
        group = str(layer.get("group", "")).strip()
        species = str(layer.get("species_latin_name", "")).strip()
        for signal in (layer_key, group, species):
            if signal:
                signals.setdefault(signal, []).append(layer_key)
        raw_features = layer.get("features")
        if not isinstance(raw_features, list):
            continue
        for feature_index, feature in enumerate(raw_features):
            if not isinstance(feature, dict):
                continue
            country = str(feature.get("country", "")).strip() or "UNASSIGNED"
            countries.setdefault(country, {}).setdefault(layer_key, []).append(
                feature_index
            )
            coordinate_pair = point_coordinate_pair(feature)
            if coordinate_pair is not None:
                latitude, longitude = coordinate_pair
                cell = f"{math.floor(latitude)}:{math.floor(longitude)}"
                spatial_cells.setdefault(cell, {}).setdefault(layer_key, []).append(
                    feature_index
                )
            interval = feature_interval(feature)
            if interval is not None:
                time_intervals.append(
                    [interval[0], interval[1], layer_key, feature_index]
                )
    return {
        "schema_version": "atlas-static-indexes.v2",
        "country_feature_indexes": _sorted_nested_indexes(countries),
        "spatial_degree_feature_indexes": _sorted_nested_indexes(spatial_cells),
        "time_interval_feature_indexes": sorted(
            time_intervals, key=lambda row: (row[0], row[1], row[2], row[3])
        ),
        "signal_layer_indexes": {
            key: sorted(set(value)) for key, value in sorted(signals.items())
        },
    }


def feature_interval(feature: dict[str, object]) -> tuple[float, float] | None:
    """Return a valid signed-BP point or interval age for a feature."""
    if "time_start_bp" in feature or "time_end_bp" in feature:
        raw_start = feature.get("time_start_bp")
        raw_end = feature.get("time_end_bp")
        if raw_start is not None or raw_end is not None:
            start = finite_number(raw_start)
            end = finite_number(raw_end)
            return (
                (start, end)
                if start is not None and end is not None and start <= end
                else None
            )
    for key in ("time_mean_bp", "time_year_bp"):
        if key not in feature or feature.get(key) is None:
            continue
        point = finite_number(feature.get(key))
        return (point, point) if point is not None else None
    return None


def finite_number(value: object) -> float | None:
    """Normalize a finite scalar without treating booleans as numbers."""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value) if isinstance(value, (int, float, str)) else math.nan
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def index_reference_count(payload: dict[str, object]) -> int:
    """Count point and detail references represented by an index payload."""
    country_rows = payload.get("country_feature_indexes")
    if not isinstance(country_rows, dict):
        return 0
    feature_reference_count = sum(
        len(indexes)
        for layers in country_rows.values()
        if isinstance(layers, dict)
        for indexes in layers.values()
        if isinstance(indexes, list)
    )
    detail_rows = payload.get("detail_record_asset_keys")
    detail_reference_count = len(detail_rows) if isinstance(detail_rows, dict) else 0
    return feature_reference_count + detail_reference_count


def _sorted_nested_indexes(
    rows: dict[str, dict[str, list[int]]],
) -> dict[str, dict[str, list[int]]]:
    return {
        outer_key: dict(sorted(inner_rows.items()))
        for outer_key, inner_rows in sorted(rows.items())
    }


__all__ = [
    "build_indexes",
    "feature_interval",
    "finite_number",
    "index_reference_count",
]
