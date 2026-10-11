from __future__ import annotations

from collections.abc import Callable
import json
from typing import TYPE_CHECKING, Any

from ...core.geospatial.geojson import JsonObject
from ..map_publication import MapScopePolicy
from ..modeled_context import build_modeled_context_manifest
from ..modeled_context.publication_projection import project_modeled_context_layers
from .native_lra import bind_native_view, validate_native_layers
from .state import build_map_document_state
from .static_assets.budgets import ATLAS_FILTER_MAIN_THREAD_MAX_MS
from .template import (
    NATIVE_LRA_CONTROLLER,
    SOURCE_RECORD_EXPORT_CONTROLLER,
    URL_STATE_CONTROLLER,
)
from .temporal_admission import read_calendar_profile

if TYPE_CHECKING:
    from .static_assets import StaticAtlasAssets

from .static_assets import validate_atlas_release_id, validate_static_atlas_assets


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
    native_lra: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Build placeholder replacements for the standalone map document template."""
    validate_atlas_release_id(version)
    temporal_profile = (
        read_calendar_profile(native_lra) if native_lra is not None else None
    )
    if native_lra is not None:
        validate_native_layers(native_lra, point_layers)
    if temporal_profile is not None:
        if native_lra is None or static_assets is None or polygon_layers:
            raise ValueError(
                "Signed native presentation requires complete static point transport"
            )
        if (
            read_calendar_profile(static_assets.manifest) != temporal_profile
            or static_assets.manifest.get("native_view_sha256")
            != bind_native_view(native_lra)["sha256"]
        ):
            raise ValueError("Signed static transport belongs to another native view")
        validate_static_atlas_assets(static_assets)
    state = build_map_document_state(
        policy=policy,
        point_layers=point_layers,
        polygon_layers=polygon_layers,
        temporal_profile=temporal_profile,
    )
    publication_polygon_layers = project_modeled_context_layers(polygon_layers)
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
        polygon_layers_json = serialize_json_for_script(publication_polygon_layers)
    else:
        bootstrap_json = serialize_json_for_script(static_assets.manifest)
        chunk_script_tags = static_assets.script_tags
        point_layers_json = "hydrateStaticAtlasLayers('point')"
        polygon_layers_json = "hydrateStaticAtlasLayers('polygon')"
    return {
        "__SOURCE_RECORD_EXPORT_CONTROLLER__": SOURCE_RECORD_EXPORT_CONTROLLER,
        "__URL_STATE_CONTROLLER__": URL_STATE_CONTROLLER,
        "__NATIVE_LRA_BINDING__": serialize_json_for_script(
            bind_native_view(native_lra) if native_lra is not None else None
        ),
        "__NATIVE_LRA_CONTROLLER__": NATIVE_LRA_CONTROLLER
        if native_lra is not None
        else "",
        "__NATIVE_LRA_CONTROLS__": (
            '<details id="lra-controls" class="control-group" hidden open '
            'aria-label="Native exploratory LRA estimates">'
            '<summary class="control-group-head"><div>'
            '<span class="control-group-label">Model estimates</span>'
            "<h3>Exploratory LRA</h3></div></summary>"
            '<div class="control-group-body">'
            '<p class="search-meta">R: regional REVEALS percent; L: local LOVE fraction. '
            "Display anchors are synthetic, not estimate footprints. N/A remains missing. "
            "q10/q90 are method quantiles, not total uncertainty or prediction intervals.</p>"
            '<p class="search-meta">Multiple selections are supported. '
            "An empty selection contains zero values.</p>"
            '<label class="field-label" for="lra-role">Model role</label>'
            '<select id="lra-role" class="search-input" multiple size="2"></select>'
            '<label class="field-label" for="lra-site">Site</label>'
            '<select id="lra-site" class="search-input" multiple size="2"></select>'
            '<label class="field-label" for="lra-taxon">Taxon</label>'
            '<select id="lra-taxon" class="search-input" multiple size="3"></select>'
            '<label class="field-label" for="lra-bin">Declared time bin</label>'
            '<select id="lra-bin" class="search-input" multiple size="2"></select>'
            '<p id="lra-selection-status" class="search-meta" '
            'role="status" aria-live="polite"></p>'
            '<div class="focus-detail-table-wrap lra-estimates-scroll" tabindex="0" '
            'role="region" aria-label="Selected native model values">'
            '<table id="lra-estimates" class="focus-detail-table"><thead><tr>'
            "<th>Role</th><th>Site</th><th>Taxon</th><th>Statistic</th><th>Value</th><th>Native unit</th>"
            "</tr></thead><tbody></tbody></table></div>"
            '<div class="inline-actions"><button id="lra-download" '
            'class="inline-button is-primary" type="button">'
            "Download selected estimates</button></div>"
            '<p class="search-meta"><a href="native-view.json">Complete bound model view</a> · '
            '<a href="index.html">Complete report and original product downloads</a>'
            "</p></div></details>"
            if native_lra is not None
            else ""
        ),
        "__TITLE__": escape_html_fn(title),
        "__SCOPE_BADGE__": escape_html_fn(policy.eyebrow_label),
        "__SCOPE_KEY_JSON__": serialize_json_for_script(policy.key),
        "__SCOPE_NOTE__": escape_html_fn(policy.summary),
        "__CHRONOLOGY_PLAYBACK_ACTION__": (
            '<div class="inline-actions">'
            f'<a class="inline-button is-primary" href="{escape_html_fn(policy.chronology_playback_href)}">'
            "Open prepared chronology playback</a></div>"
            if policy.chronology_playback_href is not None
            else ""
        ),
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
