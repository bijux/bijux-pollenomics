from __future__ import annotations

from collections.abc import Callable
import json

from ...core.geojson import JsonObject
from .state import build_map_document_state


def build_map_document_payload(
    *,
    title: str,
    version: str,
    generated_on: str,
    countries: tuple[str, ...],
    point_layers: list[JsonObject],
    polygon_layers: list[JsonObject],
    asset_base_path: str,
    escape_html_fn: Callable[[str], str],
) -> dict[str, str]:
    """Build placeholder replacements for the standalone map document template."""
    state = build_map_document_state(
        point_layers=point_layers, polygon_layers=polygon_layers
    )
    return {
        "__TITLE__": escape_html_fn(title),
        "__VERSION__": escape_html_fn(version),
        "__GENERATED_ON__": escape_html_fn(generated_on),
        "__COUNTRIES_JSON__": json.dumps(list(countries), ensure_ascii=False),
        "__POINT_LAYERS_JSON__": json.dumps(point_layers, ensure_ascii=False),
        "__POLYGON_LAYERS_JSON__": json.dumps(polygon_layers, ensure_ascii=False),
        "__BOUNDS_JSON__": json.dumps(state.bounds),
        "__ASSET_BASE_PATH__": asset_base_path,
        "__INITIAL_DIAMETER__": str(state.initial_diameter_km),
        "__INITIAL_RADIUS__": f"{state.initial_diameter_km / 2:.1f}",
        "__TIME_MIN_BP__": str(state.time_min_bp),
        "__TIME_MAX_BP__": str(state.time_max_bp),
        "__TIME_HAS_DATA__": str(state.has_time_data).lower(),
        "__INITIAL_TIME_START_BP__": str(state.initial_time_start_bp),
        "__INITIAL_TIME_END_BP__": str(state.initial_time_end_bp),
        "__INITIAL_TIME_INTERVAL__": str(state.initial_time_interval_years),
        "__TIME_INTERVAL_MAX__": str(state.max_time_span),
    }
