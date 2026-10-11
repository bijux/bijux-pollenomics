from __future__ import annotations

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE


def test_narrow_control_lane_clears_wrapped_top_bar() -> None:
    narrow_css = MAP_DOCUMENT_TEMPLATE.split("@media (max-width: 360px) {", 1)[1].split(
        "</style>", 1
    )[0]
    north_rule = narrow_css.split(".north-orientation {", 1)[1].split("}", 1)[0]
    leaflet_rule = narrow_css.split(".leaflet-bottom.leaflet-right {", 1)[1].split(
        "}", 1
    )[0]

    assert "top: 230px;" in north_rule
    assert "top: 282px;" in leaflet_rule
