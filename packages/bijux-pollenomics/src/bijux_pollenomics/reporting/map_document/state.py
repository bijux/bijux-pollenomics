from __future__ import annotations

from dataclasses import dataclass
import math

from ...core.geospatial.geojson import JsonObject, as_mapping, feature_list
from ..map_publication import MapScopePolicy
from .coordinates import point_coordinate_pair


@dataclass(frozen=True)
class MapDocumentState:
    bounds: list[list[float]]
    has_time_data: bool
    initial_diameter_km: int
    initial_time_end_bp: int
    initial_time_interval_years: int
    initial_time_start_bp: int
    max_time_span: int
    time_max_bp: int
    time_min_bp: int


def _finite_bp_value(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if not isinstance(value, (int, float, str)):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(numeric) or numeric < 0:
        return None
    return numeric


def collect_feature_time_candidates(
    time_candidates: set[float], feature: JsonObject
) -> None:
    """Collect only complete canonical intervals or standalone point ages."""
    interval_declared = "time_start_bp" in feature or "time_end_bp" in feature
    if interval_declared:
        raw_start = feature.get("time_start_bp")
        raw_end = feature.get("time_end_bp")
        if raw_start is None and raw_end is None:
            interval_declared = False
        else:
            start = _finite_bp_value(raw_start)
            end = _finite_bp_value(raw_end)
            if start is not None and end is not None and start <= end:
                time_candidates.update((start, end))
            return
    if not interval_declared:
        for key in ("time_mean_bp", "time_year_bp"):
            if key not in feature or feature.get(key) is None:
                continue
            point_age = _finite_bp_value(feature.get(key))
            if point_age is None:
                return
            time_candidates.add(point_age)
            return


def build_map_document_state(
    *,
    policy: MapScopePolicy,
    point_layers: list[JsonObject],
    polygon_layers: list[JsonObject],
) -> MapDocumentState:
    """Build the shared derived state needed by the standalone map document."""
    initial_diameter_km = policy.initial_diameter_km
    time_candidates: set[float] = set()
    map_points = [feature for layer in point_layers for feature in feature_list(layer)]
    for layer in point_layers:
        for feature in feature_list(layer):
            collect_feature_time_candidates(time_candidates, feature)
    for layer in polygon_layers:
        geojson = as_mapping(layer.get("geojson"))
        if geojson is None:
            continue
        for feature in feature_list(geojson):
            properties = as_mapping(feature.get("properties"))
            if properties is not None:
                collect_feature_time_candidates(time_candidates, properties)

    time_values = sorted(time_candidates)
    has_time_data = bool(time_values)
    if time_values:
        time_min_bp = math.floor(min(time_values))
        time_max_bp = math.ceil(max(time_values))
        max_time_span = max(1, time_max_bp - time_min_bp)
        initial_time_interval_years = max_time_span
        initial_time_start_bp = time_min_bp
    else:
        time_min_bp = 0
        time_max_bp = 0
        initial_time_interval_years = 100
        max_time_span = initial_time_interval_years
        initial_time_start_bp = 0
    initial_time_end_bp = min(
        time_max_bp, initial_time_start_bp + initial_time_interval_years
    )
    if map_points:
        coordinate_pairs = [
            pair
            for feature in map_points
            if (pair := point_coordinate_pair(feature)) is not None
        ]
        if coordinate_pairs:
            latitude_values = [latitude for latitude, _longitude in coordinate_pairs]
            longitude_values = [longitude for _latitude, longitude in coordinate_pairs]
            data_bounds = [
                [min(latitude_values), min(longitude_values)],
                [max(latitude_values), max(longitude_values)],
            ]
            bounds = [
                [
                    min(data_bounds[0][0], policy.minimum_bounds[0][0]),
                    min(data_bounds[0][1], policy.minimum_bounds[0][1]),
                ],
                [
                    max(data_bounds[1][0], policy.minimum_bounds[1][0]),
                    max(data_bounds[1][1], policy.minimum_bounds[1][1]),
                ],
            ]
        else:
            bounds = [
                [policy.minimum_bounds[0][0], policy.minimum_bounds[0][1]],
                [policy.minimum_bounds[1][0], policy.minimum_bounds[1][1]],
            ]
    else:
        bounds = [
            [policy.minimum_bounds[0][0], policy.minimum_bounds[0][1]],
            [policy.minimum_bounds[1][0], policy.minimum_bounds[1][1]],
        ]
    return MapDocumentState(
        bounds=bounds,
        has_time_data=has_time_data,
        initial_diameter_km=initial_diameter_km,
        initial_time_end_bp=initial_time_end_bp,
        initial_time_interval_years=initial_time_interval_years,
        initial_time_start_bp=initial_time_start_bp,
        max_time_span=max_time_span,
        time_max_bp=time_max_bp,
        time_min_bp=time_min_bp,
    )
