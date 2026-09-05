from __future__ import annotations

from collections.abc import Callable
import json
from typing import TYPE_CHECKING

from ...core.geospatial.geojson import JsonObject
from ..modeled_context import build_modeled_context_manifest
from ..map_publication import MapScopePolicy
from .state import build_map_document_state
from .static_assets.budgets import ATLAS_FILTER_MAIN_THREAD_MAX_MS

if TYPE_CHECKING:
    from .static_assets import StaticAtlasAssets

from .static_assets import validate_atlas_release_id


def serialize_json_for_script(value: object) -> str:
    """Serialize JSON without raw characters that can escape an HTML script node."""
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


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
    validate_atlas_release_id(version)
    state = build_map_document_state(
        policy=policy,
        point_layers=point_layers,
        polygon_layers=polygon_layers,
    )
    if static_assets is None:
        bootstrap_json = serialize_json_for_script(
            {
                "schema_version": "atlas-inline-bootstrap.v1",
                "status": "inline_test_fixture",
                "budgets": {
                    "filter_main_thread_max_ms": ATLAS_FILTER_MAIN_THREAD_MAX_MS,
                },
            },
        )
        chunk_script_tags = ""
        point_layers_json = serialize_json_for_script(point_layers)
        polygon_layers_json = serialize_json_for_script(polygon_layers)
    else:
        bootstrap_json = serialize_json_for_script(static_assets.manifest)
        chunk_script_tags = static_assets.script_tags
        point_layers_json = "hydrateStaticAtlasLayers('point')"
        polygon_layers_json = "hydrateStaticAtlasLayers('polygon')"
    return {
        "__TITLE__": escape_html_fn(title),
        "__SCOPE_BADGE__": escape_html_fn(policy.eyebrow_label),
        "__SCOPE_NOTE__": escape_html_fn(policy.summary),
        "__VERSION_JSON__": serialize_json_for_script(version),
        "__GENERATED_ON__": escape_html_fn(generated_on),
        "__COUNTRIES_JSON__": serialize_json_for_script(list(countries)),
        "__POINT_LAYERS_JSON__": point_layers_json,
        "__POLYGON_LAYERS_JSON__": polygon_layers_json,
        "__MODELED_CONTEXT_JSON__": serialize_json_for_script(
            build_modeled_context_manifest(polygon_layers)
        ),
        "__STATIC_BOOTSTRAP_JSON__": bootstrap_json,
        "__STATIC_CHUNK_SCRIPT_TAGS__": chunk_script_tags,
        "__BOUNDS_JSON__": serialize_json_for_script(state.bounds),
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


__all__ = ["build_map_document_payload", "serialize_json_for_script"]
