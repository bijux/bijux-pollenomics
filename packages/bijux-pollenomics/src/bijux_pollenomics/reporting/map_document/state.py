from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math

from ...core.geospatial.geojson import JsonObject, as_mapping, feature_list
from ..map_publication import MapScopePolicy
from .coordinates import point_coordinate_pair
from .temporal_admission import calendar_profile_metadata, feature_interval


@dataclass(frozen=True)
class MapDocumentState:
    bounds: list[list[float]]
    has_time_data: bool
    initial_diameter_km: int
    initial_time_end_bp: int | float
    initial_time_interval_years: int | float
    initial_time_start_bp: int | float
    max_time_span: int | float
    time_max_bp: int | float
    time_min_bp: int | float
    source_time_bounds_bp: tuple[float, float] | None = None


def collect_feature_time_candidates(
    time_candidates: set[float],
    feature: JsonObject,
    *,
    temporal_profile: str | None = None,
) -> None:
    """Collect only chronology admitted by the shared static/browser contract."""
    interval = feature_interval(feature, temporal_profile=temporal_profile)
    if interval is not None:
        time_candidates.update(interval)


def build_map_document_state(
    *,
    policy: MapScopePolicy,
    point_layers: Sequence[JsonObject],
    polygon_layers: Sequence[JsonObject],
    temporal_profile: str | None = None,
) -> MapDocumentState:
    """Build the shared derived state needed by the standalone map document."""
    calendar_profile_metadata(temporal_profile)
    initial_diameter_km = policy.initial_diameter_km
    time_candidates: set[float] = set()
    map_points = [feature for layer in point_layers for feature in feature_list(layer)]
    for layer in point_layers:
        for feature in feature_list(layer):
            collect_feature_time_candidates(
                time_candidates, feature, temporal_profile=temporal_profile
            )
    for layer in polygon_layers:
        geojson = as_mapping(layer.get("geojson"))
        if geojson is None:
            continue
        for feature in feature_list(geojson):
            properties = as_mapping(feature.get("properties"))
            if properties is not None:
                collect_feature_time_candidates(
                    time_candidates, properties, temporal_profile=temporal_profile
                )

    time_values = sorted(time_candidates)
    has_time_data = bool(time_values)
    source_time_bounds = (min(time_values), max(time_values)) if time_values else None
    if temporal_profile is not None and time_values:
        time_min_bp, time_max_bp = min(time_values), max(time_values)
        max_time_span = time_max_bp - time_min_bp
        if not math.isfinite(max_time_span) or abs(max_time_span) > 2**53 - 1:
            raise ValueError("Signed calendar display span is not finite")
        initial_time_interval_years = max_time_span
        initial_time_start_bp = time_min_bp
    elif time_values:
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
    initial_time_end_bp = (
        time_max_bp
        if temporal_profile is not None
        else min(time_max_bp, initial_time_start_bp + initial_time_interval_years)
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
        source_time_bounds_bp=source_time_bounds,
    )
