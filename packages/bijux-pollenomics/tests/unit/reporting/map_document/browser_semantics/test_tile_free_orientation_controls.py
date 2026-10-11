from __future__ import annotations

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE


def test_north_orientation_is_visible_and_named_without_tile_dependency() -> None:
    assert (
        '<div id="north-orientation" class="north-orientation" role="img" '
        'aria-label="North is up">'
    ) in MAP_DOCUMENT_TEMPLATE
    assert 'class="north-orientation-arrow" aria-hidden="true">↑</span>' in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert (
        "pointer-events: none;"
        in MAP_DOCUMENT_TEMPLATE.split(".north-orientation {", 1)[1].split("}", 1)[0]
    )
    assert "html.atlas-capture-mode .north-orientation" not in MAP_DOCUMENT_TEMPLATE


def test_narrow_status_retains_center_and_basemap_with_clear_map_controls() -> None:
    narrow_css = MAP_DOCUMENT_TEMPLATE.split("@media (max-width: 900px) {", 1)[1].split(
        "@media (max-width: 640px) {", 1
    )[0]
    mobile_css = MAP_DOCUMENT_TEMPLATE.split("@media (max-width: 640px) {", 1)[1].split(
        "</style>", 1
    )[0]

    assert ".map-status .status-pill:nth-child(1)," in narrow_css
    assert ".map-status .status-pill:nth-child(3) {" in narrow_css
    assert ".map-status .status-pill:nth-child(-n + 3)" not in narrow_css
    assert (
        "grid-column: 1 / -1;"
        in narrow_css.split(".map-status .status-pill:nth-child(5) {", 1)[1].split(
            "}", 1
        )[0]
    )
    assert (
        "top: 176px;" in mobile_css.split(".north-orientation {", 1)[1].split("}", 1)[0]
    )
    assert 'id="center-readout"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="basemap-readout"' in MAP_DOCUMENT_TEMPLATE
    assert (
        "min-height: 44px;"
        in mobile_css.split(".map-status .status-pill-action {", 1)[1].split("}", 1)[0]
    )
