from __future__ import annotations

from html.parser import HTMLParser

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE


def test_mobile_controls_keep_touch_targets_and_readable_status() -> None:
    mobile_css = MAP_DOCUMENT_TEMPLATE.split("@media (max-width: 640px) {", 1)[1].split(
        "</style>", 1
    )[0]
    toggle_rule = mobile_css.split(".legend-toggle {", 1)[1].split("}", 1)[0]
    status_rule = mobile_css.split("\n        .map-status {", 1)[1].split("}", 1)[0]

    assert "min-height: 44px;" in toggle_rule
    assert "grid-template-columns: repeat(3, minmax(0, 1fr));" in status_rule
    assert "padding: 6px 10px;" in status_rule


def test_workspace_keeps_full_reader_and_chrome_outside_map_viewport() -> None:
    class Workspace(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.stack: list[tuple[str, str]] = []
            self.parents: dict[str, str] = {}

        def handle_starttag(
            self, tag: str, attrs: list[tuple[str, str | None]]
        ) -> None:
            attributes = dict(attrs)
            name = attributes.get("id") or attributes.get("class") or tag
            self.parents[name] = self.stack[-1][1] if self.stack else ""
            if tag not in {"input", "meta", "link", "br", "hr", "img", "path"}:
                self.stack.append((tag, name))

        def handle_endtag(self, tag: str) -> None:
            for index in range(len(self.stack) - 1, -1, -1):
                if self.stack[index][0] == tag:
                    self.stack = self.stack[:index]
                    break

    workspace = Workspace()
    workspace.feed(MAP_DOCUMENT_TEMPLATE)
    assert workspace.parents["map"] == "map-viewport"
    assert workspace.parents["floating-legend"] == "map-viewport"
    for name in ("map-topbar", "map-status", "focus-card", "sidebar", "mobile-scrim"):
        assert workspace.parents[name] == "map-stage"
    for name in ("focus-tabs", "focus-detail", "focus-source-link", "focus-export"):
        assert name in workspace.parents


def test_narrow_search_results_preserve_a_map_grid_row() -> None:
    narrow_css = MAP_DOCUMENT_TEMPLATE.split("@media (max-width: 640px) {", 1)[1].split(
        "</style>", 1
    )[0]
    results_rule = narrow_css.split(".search-results--floating {", 1)[1].split("}", 1)[
        0
    ]

    assert "max-height: min(14vh, 88px);" in results_rule
