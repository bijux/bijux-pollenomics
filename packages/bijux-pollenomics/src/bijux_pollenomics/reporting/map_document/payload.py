from __future__ import annotations

import json
from collections.abc import Callable
from typing import TYPE_CHECKING

from ...core.geojson import JsonObject
from ..map_publication import MapScopePolicy
from .state import build_map_document_state

if TYPE_CHECKING:
    from .static_assets import StaticAtlasAssets


def build_map_document_payload(
    *,
    title: str,
    version: str,
    generated_on: str,
    countries: tuple[str, ...],
    policy: MapScopePolicy,
    point_layers: list[JsonObject],
    polygon_layers: list[JsonObject],
    asset_base_path: str,
    escape_html_fn: Callable[[str], str],
    static_assets: StaticAtlasAssets | None = None,
) -> dict[str, str]:
    """Build placeholder replacements for the standalone map document template."""
    state = build_map_document_state(
        policy=policy,
        point_layers=point_layers,
        polygon_layers=polygon_layers,
    )
    if static_assets is None:
        bootstrap_json = json.dumps(
            {
                "schema_version": "atlas-inline-bootstrap.v1",
                "status": "inline_test_fixture",
            },
            separators=(",", ":"),
        )
        chunk_script_tags = ""
        point_layers_json = json.dumps(point_layers, ensure_ascii=False)
        polygon_layers_json = json.dumps(polygon_layers, ensure_ascii=False)
    else:
        bootstrap_json = static_assets.bootstrap_json
        chunk_script_tags = static_assets.script_tags
        point_layers_json = "hydrateStaticAtlasLayers('point')"
        polygon_layers_json = "hydrateStaticAtlasLayers('polygon')"
    return {
        "__TITLE__": escape_html_fn(title),
        "__SCOPE_BADGE__": escape_html_fn(policy.eyebrow_label),
        "__SCOPE_NOTE__": escape_html_fn(policy.summary),
        "__VERSION__": escape_html_fn(version),
        "__GENERATED_ON__": escape_html_fn(generated_on),
        "__COUNTRIES_JSON__": json.dumps(list(countries), ensure_ascii=False),
        "__POINT_LAYERS_JSON__": point_layers_json,
        "__POLYGON_LAYERS_JSON__": polygon_layers_json,
        "__STATIC_BOOTSTRAP_JSON__": bootstrap_json,
        "__STATIC_CHUNK_SCRIPT_TAGS__": chunk_script_tags,
        "__BOUNDS_JSON__": json.dumps(state.bounds),
        "__ASSET_BASE_PATH__": asset_base_path,
        "__INITIAL_BASEMAP__": escape_html_fn(policy.default_basemap),
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
