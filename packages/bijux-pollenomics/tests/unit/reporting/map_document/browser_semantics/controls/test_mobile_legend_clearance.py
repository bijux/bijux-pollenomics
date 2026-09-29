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
