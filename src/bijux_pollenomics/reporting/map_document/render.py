from __future__ import annotations

import json

from ..utils import escape_html
from .state import build_map_document_state
from .template import MAP_DOCUMENT_TEMPLATE


def render_multi_country_map_html(
    title: str,
    version: str,
    generated_on: str,
    countries: tuple[str, ...],
    point_layers: list[dict[str, object]],
    polygon_layers: list[dict[str, object]],
    asset_base_path: str,
) -> str:
    """Render the standalone interactive map document."""
    state = build_map_document_state(point_layers=point_layers, polygon_layers=polygon_layers)
    return (
        MAP_DOCUMENT_TEMPLATE
        .replace("__TITLE__", escape_html(title))
        .replace("__VERSION__", escape_html(version))
        .replace("__GENERATED_ON__", escape_html(generated_on))
        .replace("__COUNTRIES_JSON__", json.dumps(list(countries), ensure_ascii=False))
        .replace("__POINT_LAYERS_JSON__", json.dumps(point_layers, ensure_ascii=False))
        .replace("__POLYGON_LAYERS_JSON__", json.dumps(polygon_layers, ensure_ascii=False))
        .replace("__BOUNDS_JSON__", json.dumps(state.bounds))
        .replace("__ASSET_BASE_PATH__", asset_base_path)
        .replace("__INITIAL_DIAMETER__", str(state.initial_diameter_km))
        .replace("__INITIAL_RADIUS__", f"{state.initial_diameter_km / 2:.1f}")
        .replace("__TIME_MIN_BP__", str(state.time_min_bp))
        .replace("__TIME_MAX_BP__", str(state.time_max_bp))
        .replace("__TIME_HAS_DATA__", str(state.has_time_data).lower())
        .replace("__INITIAL_TIME_START_BP__", str(state.initial_time_start_bp))
        .replace("__INITIAL_TIME_END_BP__", str(state.initial_time_end_bp))
        .replace("__INITIAL_TIME_INTERVAL__", str(state.initial_time_interval_years))
        .replace("__TIME_INTERVAL_MAX__", str(state.max_time_span))
    )
