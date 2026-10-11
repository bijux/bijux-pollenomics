from __future__ import annotations

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE


def test_narrow_attribution_occupies_a_visible_lane_below_north() -> None:
    mobile_css = MAP_DOCUMENT_TEMPLATE.split("@media (max-width: 640px) {", 1)[1].split(
        "</style>", 1
    )[0]
    north_rule = mobile_css.split(".north-orientation {", 1)[1].split("}", 1)[0]
    attribution_rule = mobile_css.split(".leaflet-bottom.leaflet-right {", 1)[1].split(
        "}", 1
    )[0]

    assert "top: 176px;" in north_rule
    assert "top: 228px;" in attribution_rule
    assert "bottom: auto;" in attribution_rule
    assert "right: 8px;" in attribution_rule
    assert "max-width: calc(100vw - 16px);" in attribution_rule
