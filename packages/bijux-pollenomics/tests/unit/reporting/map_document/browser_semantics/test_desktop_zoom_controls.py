from __future__ import annotations

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE


def test_desktop_zoom_lane_clears_status_and_mobile_override_remains() -> None:
    desktop_css = MAP_DOCUMENT_TEMPLATE.split("@media (max-width: 1080px) {", 1)[0]
    desktop_lane = desktop_css.split(".leaflet-bottom.leaflet-right {", 1)[1].split(
        "}", 1
    )[0]
    mobile_css = MAP_DOCUMENT_TEMPLATE.split("@media (max-width: 640px) {", 1)[1]
    mobile_lane = mobile_css.split(".leaflet-bottom.leaflet-right {", 1)[1].split(
        "}", 1
    )[0]

    assert "top: 72px;" in desktop_lane
    assert "bottom: auto;" in desktop_lane
    assert "right: 16px;" in desktop_lane
    assert "top: 228px;" in mobile_lane
    assert "bottom: auto;" in mobile_lane
    assert "right: 8px;" in mobile_lane
