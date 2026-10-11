from __future__ import annotations

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE


def test_collapsed_controls_leave_the_keyboard_order() -> None:
    scrim = MAP_DOCUMENT_TEMPLATE.split('<button id="mobile-scrim"', 1)[1].split(
        "</button>", 1
    )[0]
    sidebar = MAP_DOCUMENT_TEMPLATE.split('<aside id="sidebar"', 1)[1].split(">", 1)[0]
    collapse_handler = MAP_DOCUMENT_TEMPLATE.split(
        "function setPanelCollapsed(collapsed, persist = true) {", 1
    )[1].split("function closeMobilePanel()", 1)[0]

    assert 'tabindex="-1"' in scrim
    assert 'aria-hidden="true"' in scrim
    assert "inert" in sidebar
    assert "sidebar.inert = collapsed;" in collapse_handler
    assert "mobileScrim.setAttribute('aria-hidden'," not in MAP_DOCUMENT_TEMPLATE
