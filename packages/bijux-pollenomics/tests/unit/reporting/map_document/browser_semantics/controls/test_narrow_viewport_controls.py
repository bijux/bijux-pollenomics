from __future__ import annotations

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE

from ..support import template_block


def test_short_viewport_reader_shares_the_map_track_and_retains_controls() -> None:
    short_css = template_block("@media (max-height: 640px)", "</style>")
    reader_rule = short_css.split(".focus-card {", 1)[1].split("}", 1)[0]
    assert "grid-area: map;" in reader_rule
    assert "max-height: calc(100% - 16px);" in reader_rule
    assert "display: none" not in short_css
    assert "minmax(min(260px, 30dvh), 1fr)" in short_css
    assert "min-height: max-content;" in short_css
    assert (
        "grid-column: 1 / -1;"
        in short_css.split("#time-stepper-status {", 1)[1].split("}", 1)[0]
    )
    assert 'aria-label="Chronology navigation"' in MAP_DOCUMENT_TEMPLATE
