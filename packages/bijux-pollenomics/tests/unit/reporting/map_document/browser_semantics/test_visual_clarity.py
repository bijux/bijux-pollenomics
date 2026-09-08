from __future__ import annotations

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE

from .support import run_node_json, template_block


def test_interactive_framing_preserves_records_with_quiet_visual_density() -> None:
    cluster_block = template_block(
        "function createClusterGroup", "function sourceRecordConcentrationPopupHtml"
    )
    boundary_block = template_block(
        "function renderPolygonLayers", "function updateStats"
    )

    assert "maxClusterRadius: 56" in cluster_block
    assert "disableClusteringAtZoom: 10" in cluster_block
    assert "count > 100 ? 44 : count > 25 ? 38 : 32" in cluster_block
    assert "${count}</div>" in cluster_block
    assert "border: 2px solid rgba(255, 255, 255, 0.88)" in MAP_DOCUMENT_TEMPLATE
    assert "box-shadow: 0 6px 14px rgba(20, 33, 61, 0.14)" in MAP_DOCUMENT_TEMPLATE
    assert "weight: 1.4" in boundary_block
    assert "fillOpacity: 0.04" in boundary_block
    assert "opacity: 0.72" in boundary_block
    assert "activeCountries.has(country) ? 2.2" not in boundary_block
    assert "const boundaryRenderer = L.svg({ pane: 'boundaryPane' });" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "renderer: boundaryRenderer" in boundary_block
    assert "preferCanvas: true" in MAP_DOCUMENT_TEMPLATE


def test_fit_active_keeps_evidence_polygons_outside_orientation_bounds() -> None:
    render_block = template_block(
        "function renderPolygonLayers", "function activeBounds"
    )
    bounds_block = template_block("function activeBounds", "function updateStats")
    remove_block = template_block(
        "function removeRenderedLayers", "function createClusterGroup"
    )

    assert "if (layer.kind !== 'country-boundaries')" in render_block
    assert "renderedFittablePolygonLayers.push(geoJsonLayer)" in render_block
    assert "renderedFittablePolygonLayers.forEach" in bounds_block
    assert "renderedPolygonLayers.forEach" not in bounds_block
    assert "renderedFittablePolygonLayers = [];" in remove_block

    observed = run_node_json(
        """
const visiblePointEntries=[{feature:{latitude:60,longitude:18}}];
function featureCoordinatePair(feature){
  return {latitude:feature.latitude,longitude:feature.longitude};
}
function bounds(south,west,north,east){
  return {
    isValid(){return true},
    getSouth(){return south},getWest(){return west},
    getNorth(){return north},getEast(){return east},
  };
}
const evidencePolygon={getBounds(){return bounds(55,10,65,25)}};
const orientationBoundary={getBounds(){return bounds(-54,-9,81,34)}};
const renderedFittablePolygonLayers=[evidencePolygon];
const renderedPolygonLayers=[evidencePolygon,orientationBoundary];
const L={latLngBounds(values){return values}};
"""
        + bounds_block
        + """
console.log(JSON.stringify(activeBounds()));
"""
    )

    assert observed == [[60, 18], [55, 10], [65, 25]]


def test_viewport_chrome_is_compact_clipped_and_non_overlapping() -> None:
    assert ".map-stage {\n        position: relative;" in MAP_DOCUMENT_TEMPLATE
    assert "min-height: 100vh;\n        overflow: hidden;" in MAP_DOCUMENT_TEMPLATE
    assert (
        ".map-topbar .eyebrow,\n      .map-topbar .topbar-note {\n"
        "        display: none;"
    ) in MAP_DOCUMENT_TEMPLATE
    assert (
        ".map-topbar .topbar-state-pill {\n          display: none;"
        in MAP_DOCUMENT_TEMPLATE
    )
    assert "max-height: min(60vh, calc(100dvh - 188px));" in (MAP_DOCUMENT_TEMPLATE)
    assert "body.has-legend-open .map-status" in MAP_DOCUMENT_TEMPLATE
    assert "body.has-search-open .map-topbar-main" not in MAP_DOCUMENT_TEMPLATE
    assert "width: min(188px, calc(100vw - 16px));" in MAP_DOCUMENT_TEMPLATE
    assert "--legend-max-height: min(24vh, 184px);" in MAP_DOCUMENT_TEMPLATE


def test_narrow_search_is_a_locally_bounded_popover_outside_topbar_flow() -> None:
    narrow_css = MAP_DOCUMENT_TEMPLATE.split("@media (max-width: 640px) {", maxsplit=1)[
        1
    ].split("</style>", maxsplit=1)[0]
    search_rule = narrow_css.split(".topbar-search {", maxsplit=1)[1].split(
        "}", maxsplit=1
    )[0]
    results_rule = narrow_css.split(".search-results--floating {", maxsplit=1)[1].split(
        "}", maxsplit=1
    )[0]

    assert "position: absolute;" in search_rule
    assert "top: calc(100% + 8px);" in search_rule
    assert "right: 0;" in search_rule
    assert "width: min(220px, calc(100vw - 16px));" in search_rule
    assert "position: relative;" in results_rule
    assert "top: auto;" in results_rule
    assert "right: auto;" in results_rule
    assert "width: 100%;" in results_rule
    assert "max-height: min(14vh, 96px);" in results_rule


def test_expanded_legend_scrolls_inside_its_bounded_surface() -> None:
    assert "--legend-max-height: min(42vh, 360px);" in MAP_DOCUMENT_TEMPLATE
    assert "max-height: var(--legend-max-height);" in MAP_DOCUMENT_TEMPLATE
    assert "display: flex;" in MAP_DOCUMENT_TEMPLATE
    assert "flex-direction: column;" in MAP_DOCUMENT_TEMPLATE
    assert ".legend-body {" in MAP_DOCUMENT_TEMPLATE
    assert "flex: 1 1 auto;" in MAP_DOCUMENT_TEMPLATE
    assert "min-height: 0;" in MAP_DOCUMENT_TEMPLATE
    assert "overflow-y: auto;" in MAP_DOCUMENT_TEMPLATE


def test_legend_uses_rendered_layer_and_country_colors() -> None:
    block = template_block(
        "function renderLegend", "function sourceChronologyPopupHtml"
    )

    assert "visiblePointEntries.map(({ layer }) => layer.key)" in block
    assert "visiblePolygonFeatureEntries.map(({ layer }) => layer.key)" in block
    assert "renderedLayerKeys.has(layer.key)" in block
    assert "data-legend-country" in block
    assert "countryStyle(country)" in block
    assert "data-legend-layer" in block
    assert "data-legend-acceptance-layer" in block
    assert "layer.style.circleFill || fill" in block
    assert "layer.style.circleStroke || stroke" in block
    assert "data-legend-concentration-size" in block
    assert "concentrationLayer.style.stroke" in block
    assert "current zoom" in block
    assert "not abundance" in block
    assert "Animal scope" not in block
    assert "Coordinate trust" not in block
    assert "Tracked species" not in block
    assert "visibleScientificSignalIds.has(signal.signal_id)" in block
    assert "visiblePolygonFeatureEntries.some" in block


def test_collapsed_chrome_preserves_map_space_and_open_surfaces_are_exclusive() -> None:
    assert ".floating-legend:has(.legend-body.is-collapsed)" in MAP_DOCUMENT_TEMPLATE
    assert "width: auto;\n        max-height: none;\n        padding: 8px 10px;" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "let legendCollapsed = initialState.legend !== 'expanded';" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "function defaultPanelCollapsed() {\n        return true;" in (
        MAP_DOCUMENT_TEMPLATE
    )

    panel = template_block("function setPanelCollapsed", "function closeMobilePanel")
    legend = template_block("function setLegendCollapsed", "function setSearchOpen")
    search = template_block("function setSearchOpen", "function openHelpDialog")
    assert "setLegendCollapsed(true, false)" in panel
    assert "setSearchOpen(false)" in panel
    assert "setPanelCollapsed(true, false)" in legend
    assert "setSearchOpen(false)" in legend
    assert "setPanelCollapsed(true, false)" in search
    assert "setLegendCollapsed(true, false)" in search

    capture_hidden = template_block(
        "html.atlas-capture-mode .map-topbar", ".atlas-capture-overlay"
    )
    assert "html.atlas-capture-mode .floating-legend" in capture_hidden
    assert "html.atlas-capture-mode .control-panel" in capture_hidden
    assert "html.atlas-capture-mode .map-status" in capture_hidden


def test_status_strip_uses_one_column_per_desktop_status() -> None:
    assert (
        MAP_DOCUMENT_TEMPLATE.count(
            "grid-template-columns: repeat(5, minmax(0, auto));"
        )
        == 1
    )
    assert (
        MAP_DOCUMENT_TEMPLATE.count("grid-template-columns: repeat(5, minmax(0, 1fr));")
        == 1
    )
