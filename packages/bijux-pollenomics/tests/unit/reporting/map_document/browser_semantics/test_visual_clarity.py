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
