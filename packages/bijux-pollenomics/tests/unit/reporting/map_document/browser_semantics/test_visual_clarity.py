from __future__ import annotations

import re

import pytest

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
    match = re.search(
        r"^\s*\.map-stage\s*\{([^}]*)\}", MAP_DOCUMENT_TEMPLATE, re.MULTILINE
    )
    assert match is not None
    declarations = re.findall(r"([a-z-]+)\s*:\s*([^;]+);", match.group(1))
    declaration_map = dict(declarations)
    assert declaration_map["display"] == "grid"
    assert declaration_map["height"] == "100dvh"
    assert declaration_map["overflow"] == "hidden"
    assert "minmax(min(260px, 30dvh), 1fr)" in declaration_map["grid-template-rows"]
    assert declaration_map["grid-template-areas"] == (
        '"toolbar" "map" "reader" "status" "footer"'
    )
    reader_rule = template_block(".focus-card {", ".focus-card[hidden]")
    assert "overflow: auto;" in reader_rule
    assert "min-height: 0;" in reader_rule
    assert "body.has-search-open .map-topbar-main" not in MAP_DOCUMENT_TEMPLATE
    assert "body.has-legend-open .map-status" in MAP_DOCUMENT_TEMPLATE


def test_narrow_search_results_keep_a_local_scroll_region() -> None:
    narrow_css = template_block(
        "@media (max-width: 640px)", "@media (max-height: 640px)"
    )
    search_rule = narrow_css.split(".topbar-search {", 1)[1].split("}", 1)[0]
    results_rule = narrow_css.split(".search-results--floating {", 1)[1].split("}", 1)[
        0
    ]
    results_base = template_block(
        ".search-results--floating {", ".search-results--floating[hidden]"
    )
    assert "position: relative;" in search_rule
    assert "width: 100%;" in search_rule
    assert "position: relative;" in results_rule
    assert "max-height: min(14vh, 88px);" in results_rule
    assert "overflow: auto;" in results_base
    short_css = template_block(
        "@media (max-height: 640px)",
        "@media (min-width: 480px) and (max-height: 640px)",
    )
    short_search = short_css.split(".topbar-search {", 1)[1].split("}", 1)[0]
    assert "position: absolute;" in short_search
    assert "top: calc(100% + 8px);" in short_search


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
    assert "visiblePolygonFeatureEntries.find" in block
    assert "visibleRaaDensityLayer?.density_count_label" in block


@pytest.mark.parametrize("visible_relation", [False, True])
def test_visible_relation_legend_explains_endpoint_geometry(
    visible_relation: bool,
) -> None:
    observed = run_node_json(
        "const visibleRelation="
        + str(visible_relation).lower()
        + ";\n"
        + """
const edges=visibleRelation ? [{signal_id:'taxon:fixture',edge_id:'relation:fixture'}] : [];
const before=JSON.stringify(edges);
const visiblePointEntries=[{
  layer:{key:'points'},neighborContext:true,
  feature:{scientific_signal_ids:['taxon:fixture']},
}];
const visiblePolygonFeatureEntries=[],ALL_LAYERS=[],LAYER_GROUP_DEFINITIONS=[];
const SCIENTIFIC_SIGNALS=[{
  signal_id:'taxon:fixture',label:'Synthetic taxon',resolution:'taxon',
  feature_key:'taxon:fixture',color:'#14532d',non_color_cue:'triangle',
}];
const activeScientificSignalIds=new Set(['taxon:fixture']);
const activeSourceChronologyLevel=null;
const legendItems={innerHTML:''},densityRamp={hidden:false};
const document={getElementById(){return null}};
function visibleGovernedEdges(){return edges}
function sourceChronologyLayerForLevel(){return null}
function escapeHtml(value){return String(value)}
function scientificCueGlyph(value){return value}
"""
        + template_block("function renderLegend", "function sourceChronologyPopupHtml")
        + """
renderLegend();
console.log(JSON.stringify({html:legendItems.innerHTML,unchanged:JSON.stringify(edges)===before}));
"""
    )
    text = (
        "Lines connect evidence endpoints; they are relations, "
        "not reconstructed movement paths."
    )
    assert (text in observed["html"]) is visible_relation
    assert ("Evidence relations" in observed["html"]) is visible_relation
    assert "Accepted scientific comparison" in observed["html"]
    assert 'data-cue="triangle"' in observed["html"]
    assert 'style="color:#14532d"' in observed["html"]
    assert "Synthetic taxon · taxon · taxon:fixture" in observed["html"]
    assert "Cross-border context" in observed["html"]
    assert "Dimmed, labeled neighboring endpoints" in observed["html"]
    assert observed["unchanged"] is True


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
    status_rule = template_block(".map-status {", ".north-orientation {")
    status_markup = template_block(
        '<div class="map-status">', '<footer class="map-reader-footer"'
    )
    assert status_markup.count('class="status-pill"') == 5
    assert "grid-template-columns: repeat(5, minmax(0, 1fr));" in status_rule
    narrow_css = template_block(
        "@media (max-width: 900px)", "@media (max-width: 640px)"
    )
    assert "grid-template-columns: repeat(3, minmax(0, 1fr));" in narrow_css
    assert ".map-status .status-pill:nth-child(1)," in narrow_css
    assert ".map-status .status-pill:nth-child(3) {" in narrow_css
    for role in ("center-readout", "selection-readout", "basemap-readout"):
        assert f'id="{role}"' in status_markup
