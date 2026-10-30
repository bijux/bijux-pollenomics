from __future__ import annotations

import json
import re

import pytest

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE

from ..support import run_node_json, template_block


def _hidden_declarations() -> str:
    styles = MAP_DOCUMENT_TEMPLATE.split("<style>", 1)[1].split("</style>", 1)[0]
    rule = re.search(r"(?m)^\s*\[hidden\]\s*\{([^}]+)\}", styles)
    assert rule is not None, "Native hidden state must override author display styles"
    return rule[1]


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


def test_unavailable_control_groups_do_not_override_native_hidden_state() -> None:
    modeled_group = MAP_DOCUMENT_TEMPLATE.split(
        '<details id="modeled-context-controls"', 1
    )[1].split(">", 1)[0]
    styles = MAP_DOCUMENT_TEMPLATE.split("<style>", 1)[1].split("</style>", 1)[0]
    visible_rule = re.search(r"\.control-group\s*\{([^}]+)\}", styles)

    assert 'class="control-group" hidden' in modeled_group
    assert "modeledContextControls.hidden = !available;" in MAP_DOCUMENT_TEMPLATE
    assert visible_rule is not None and "display: grid;" in visible_rule[1]
    assert "display: none !important;" in _hidden_declarations()


@pytest.mark.parametrize("source_url", [None, "https://example.org/source"])
def test_source_link_native_hidden_state_preserves_available_links(
    source_url: str | None,
) -> None:
    styles = MAP_DOCUMENT_TEMPLATE.split("<style>", 1)[1].split("</style>", 1)[0]
    link_rule = re.search(r"\.focus-link\s*\{([^}]+)\}", styles)
    assert link_rule is not None and "display: inline-flex;" in link_rule[1]
    assert "!important" not in link_rule[1]
    assert "display: none !important;" in _hidden_declarations()
    renderer = template_block(
        "function renderFocusCard()", "async function focusPointAtVisibleIndex"
    )
    observed = run_node_json(
        "const sourceUrl="
        + json.dumps(source_url)
        + ";"
        + """
const entry={feature:{record_id:'fixture-record'}};
const visiblePointEntries=[entry],activeLayerKeys=new Set(['points']);
const focusState={kind:'point',layerKey:'points',title:'Fixture',subtitle:'Source context',meta:[],sourceUrl};
const focusCard={},focusTitle={},focusSubtitle={},focusMeta={},focusSourceLink={};
const focusPreviousButton={},focusNextButton={};
function visiblePointEntryForFocus(){return entry}
function highlightPointEntry(){}
function renderFocusDetail(){}
"""
        + renderer
        + """
renderFocusCard();
console.log(JSON.stringify({cardHidden:focusCard.hidden,linkHidden:focusSourceLink.hidden,href:focusSourceLink.href,label:focusSourceLink.textContent}));
"""
    )
    assert observed == {
        "cardHidden": False,
        "linkHidden": source_url is None,
        "href": source_url or "#",
        "label": "Open source",
    }
