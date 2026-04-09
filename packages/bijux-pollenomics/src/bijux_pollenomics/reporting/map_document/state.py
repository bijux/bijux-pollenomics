from __future__ import annotations

from dataclasses import dataclass


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


def collect_feature_time_candidates(
    time_candidates: set[int], feature: dict[str, object]
) -> None:
    """Collect all numeric BP candidates exposed by one point or polygon feature."""
    for key in ("time_start_bp", "time_end_bp", "time_mean_bp", "time_year_bp"):
        raw = feature.get(key)
        if raw is None:
            continue
        try:
            time_candidates.add(int(round(float(raw))))
        except (TypeError, ValueError):
            continue


def build_map_document_state(
    *,
    point_layers: list[dict[str, object]],
    polygon_layers: list[dict[str, object]],
) -> MapDocumentState:
    """Build the shared derived state needed by the standalone map document."""
    initial_diameter_km = 20
    time_candidates: set[int] = set()
    map_points = [feature for layer in point_layers for feature in layer["features"]]
    for layer in point_layers:
        for feature in layer["features"]:
            if isinstance(feature, dict):
                collect_feature_time_candidates(time_candidates, feature)
    for layer in polygon_layers:
        geojson = layer.get("geojson", {})
        if not isinstance(geojson, dict):
            continue
        for feature in geojson.get("features", []):
            if not isinstance(feature, dict):
                continue
            properties = feature.get("properties", {})
            if isinstance(properties, dict):
                collect_feature_time_candidates(time_candidates, properties)

    time_values = sorted(time_candidates)
    has_time_data = bool(time_values)
    if time_values:
        time_min_bp = min(time_values)
        time_max_bp = max(time_values)
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
        latitude_values = [float(feature["latitude"]) for feature in map_points]
        longitude_values = [float(feature["longitude"]) for feature in map_points]
        bounds = [
            [min(latitude_values), min(longitude_values)],
            [max(latitude_values), max(longitude_values)],
        ]
    else:
        bounds = [[54.0, 4.0], [72.0, 35.0]]
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
