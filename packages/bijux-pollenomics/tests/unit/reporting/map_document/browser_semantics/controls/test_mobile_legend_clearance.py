from __future__ import annotations

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE


def test_mobile_legend_clears_status_and_keeps_a_touch_sized_toggle() -> None:
    mobile_css = MAP_DOCUMENT_TEMPLATE.split("@media (max-width: 640px) {", 1)[1].split(
        "</style>", 1
    )[0]
    legend_rule = mobile_css.split(".floating-legend {", 1)[1].split("}", 1)[0]
    toggle_rule = mobile_css.split(".legend-toggle {", 1)[1].split("}", 1)[0]
    scale_rule = mobile_css.split(".leaflet-bottom .leaflet-control-scale {", 1)[
        1
    ].split("}", 1)[0]
    status_rule = mobile_css.split("\n        .map-status {", 1)[1].split("}", 1)[0]

    assert "bottom: calc(176px + env(safe-area-inset-bottom));" in legend_rule
    assert "min-height: 44px;" in toggle_rule
    assert "margin-bottom: calc(176px + env(safe-area-inset-bottom));" in scale_rule
    assert "bottom: 8px;" in status_rule
    assert "grid-template-columns: repeat(3, minmax(0, 1fr));" in status_rule
    assert "padding: 6px 10px;" in status_rule


def test_narrow_focus_stacks_above_status() -> None:
    focus_layer = MAP_DOCUMENT_TEMPLATE.split(
        ".focus-card {\n        position: absolute;", 1
    )[1].split("}", 1)[0]
    status_layer = MAP_DOCUMENT_TEMPLATE.split(
        ".map-status {\n        position: absolute;", 1
    )[1].split("}", 1)[0]

    assert "z-index: 1120;" in focus_layer
    assert "z-index: 1100;" in status_layer


def test_narrow_search_results_preserve_a_map_grid_row() -> None:
    narrow_css = MAP_DOCUMENT_TEMPLATE.split("@media (max-width: 640px) {", 1)[1].split(
        "</style>", 1
    )[0]
    results_rule = narrow_css.split(".search-results--floating {", 1)[1].split("}", 1)[
        0
    ]

    assert "max-height: min(14vh, 88px);" in results_rule
