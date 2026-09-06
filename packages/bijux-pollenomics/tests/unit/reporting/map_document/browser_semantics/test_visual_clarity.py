from __future__ import annotations

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE

from .support import template_block


def test_interactive_framing_preserves_records_with_quiet_visual_density() -> None:
    cluster_block = template_block("function createClusterGroup", "function sourceRecordConcentrationPopupHtml")
    boundary_block = template_block("function renderPolygonLayers", "function updateStats")

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
    assert "max-height: min(60vh, calc(100dvh - 188px));" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "body.has-legend-open .map-status" in MAP_DOCUMENT_TEMPLATE
    assert "body.has-search-open .map-topbar-main" in MAP_DOCUMENT_TEMPLATE


def test_expanded_legend_scrolls_inside_its_bounded_surface() -> None:
    assert "--legend-max-height: min(42vh, 360px);" in MAP_DOCUMENT_TEMPLATE
    assert "max-height: var(--legend-max-height);" in MAP_DOCUMENT_TEMPLATE
    assert ".legend-body {" in MAP_DOCUMENT_TEMPLATE
    assert "max-height: calc(var(--legend-max-height) - 54px);" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "overflow-y: auto;" in MAP_DOCUMENT_TEMPLATE


def test_legend_uses_rendered_layer_and_country_colors() -> None:
    block = template_block("function renderLegend", "function sourceChronologyPopupHtml")

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


def test_status_strip_uses_one_column_per_desktop_status() -> None:
    assert MAP_DOCUMENT_TEMPLATE.count(
        "grid-template-columns: repeat(5, minmax(0, auto));"
    ) == 1
    assert MAP_DOCUMENT_TEMPLATE.count(
        "grid-template-columns: repeat(5, minmax(0, 1fr));"
    ) == 1
