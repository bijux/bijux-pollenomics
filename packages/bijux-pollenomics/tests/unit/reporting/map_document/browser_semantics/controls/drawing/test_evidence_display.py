"""Drawing choices preserve evidence and refuse unavailable shared modes."""

from __future__ import annotations

from importlib.resources import files
import json
from typing import Any
from xml.etree import ElementTree as ET

import pytest

from ...support import run_node_json, template_block


def display_script() -> str:
    return (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/evidence-display.js")
        .read_text(encoding="utf-8")
    )


def evaluate(action: str) -> Any:
    return run_node_json(
        template_block("function escapeHtml", "function normalizedMediaLinks")
        + display_script()
        + action
    )


@pytest.mark.parametrize(
    ("query", "mode", "nodes", "edges"),
    [
        ("", "both", True, True),
        ("display_mode=both", "both", True, True),
        ("display_mode=nodes", "nodes", True, False),
        ("display_mode=edges", "edges", False, True),
    ],
)
def test_modes_change_only_drawing_decisions(
    query: str, mode: str, nodes: bool, edges: bool
) -> None:
    observed = evaluate(
        f"const state=evidenceDisplayFromHash(new URLSearchParams({json.dumps(query)}));"
        "console.log(JSON.stringify(evidenceDisplayMetadata(state)));"
    )
    assert observed == {
        "mode": mode,
        "status": "available",
        "reason": None,
        "drawNodes": nodes,
        "drawEdges": edges,
        "requestedValues": [] if not query else [mode],
        "scope": "drawing_only_retained_evidence_unchanged",
    }


@pytest.mark.parametrize(
    "query",
    [
        "display_mode=",
        "display_mode=unknown",
        "display_mode=Nodes",
        "display_mode=nodes+",
        "display_mode=nodes&display_mode=nodes",
        "display_mode=nodes&display_mode=edges",
        "display_mode=density",
        "display_mode=concentration",
        "display_mode=LandClim",
    ],
)
def test_unavailable_modes_never_fall_back_to_other_primitives(query: str) -> None:
    observed = evaluate(
        f"const state=evidenceDisplayFromHash(new URLSearchParams({json.dumps(query)}));"
        "const decision=evidenceDisplayDecision(state);"
        "console.log(JSON.stringify({decision,html:renderEvidenceDisplayControls(state)}));"
    )
    assert observed["decision"]["status"] == "unavailable"
    assert observed["decision"]["drawNodes"] is False
    assert observed["decision"]["drawEdges"] is False
    assert "unavailable" in observed["html"].lower()
    assert 'role="status"' in observed["html"]
    if query == "display_mode=density":
        assert "no governed density product is supplied" in observed["html"]
        assert "different products" in observed["html"]


@pytest.mark.parametrize(
    "query",
    [
        "country=SE&display_mode=edges&focus_edge=edge-one",
        "display_mode=both",
        "display_mode=density",
        "display_mode=",
        "display_mode=edges&display_mode=nodes",
        "display_mode=%3Cscript%3Ealert%281%29%3C%2Fscript%3E",
    ],
)
def test_hash_roundtrip_retains_invalid_requests_and_other_selection(
    query: str,
) -> None:
    observed = evaluate(
        f"const input=new URLSearchParams({json.dumps(query)});"
        "const before=input.toString(), state=evidenceDisplayFromHash(input);"
        "const output=new URLSearchParams(before);"
        "writeEvidenceDisplayHash(output,state);"
        "console.log(JSON.stringify({before,unchanged:input.toString(),"
        "state,restored:evidenceDisplayFromHash(output),"
        "entries:[...output.entries()],html:renderEvidenceDisplayControls(state)}));"
    )
    assert observed["before"] == observed["unchanged"]
    assert observed["state"] == observed["restored"]
    if "country=" in query:
        assert ["country", "SE"] in observed["entries"]
        assert ["focus_edge", "edge-one"] in observed["entries"]
    assert "<script>" not in observed["html"]
    assert "alert(1)" not in observed["html"]


def test_reset_removes_only_display_choice_and_restores_default_both() -> None:
    observed = evaluate(
        "const params=new URLSearchParams('display_mode=edges&country=NO&focus_layer=source');"
        "const reset=resetEvidenceDisplay();writeEvidenceDisplayHash(params,reset);"
        "console.log(JSON.stringify({query:params.toString(),reset,"
        "decision:evidenceDisplayDecision(evidenceDisplayFromHash(params))}));"
    )
    assert observed["query"] == "country=NO&focus_layer=source"
    assert observed["reset"]["values"] == []
    assert observed["decision"]["drawNodes"] is True
    assert observed["decision"]["drawEdges"] is True


@pytest.mark.parametrize("mode", ["nodes", "edges", "both", "density"])
def test_controls_are_accessible_and_preserve_explicit_selection(mode: str) -> None:
    html = evaluate(
        f"console.log(JSON.stringify(renderEvidenceDisplayControls(evidenceDisplayState([{json.dumps(mode)}]))));"
    )
    xml = html.replace(" selected", ' selected="selected"')
    root = ET.fromstring(f"<div>{xml}</div>")
    label = root.find("label")
    select = root.find("select")
    assert label is not None and select is not None
    assert label.attrib["for"] == select.attrib["id"] == "evidence-display-mode"
    assert select.attrib["aria-describedby"] == "evidence-display-status"
    assert [row.attrib["value"] for row in select if "selected" in row.attrib] == [mode]
    assert (
        "retained records, endpoint matching, counts, detail views and data exports are unchanged"
        in html
    )
    assert "Other context layers remain separate" in html


def test_state_and_metadata_do_not_share_mutable_requested_values() -> None:
    observed = evaluate(
        "const values=['edges'], state=evidenceDisplayState(values);values[0]='nodes';"
        "const metadata=evidenceDisplayMetadata(state);metadata.requestedValues[0]='both';"
        "console.log(JSON.stringify({state,frozen:Object.isFrozen(state)&&Object.isFrozen(state.values),"
        "decision:evidenceDisplayDecision(state)}));"
    )
    assert observed["frozen"] is True
    assert observed["state"]["values"] == ["edges"]
    assert observed["decision"]["drawNodes"] is False
    assert observed["decision"]["drawEdges"] is True


def test_malformed_internal_state_cannot_invent_an_available_mode() -> None:
    observed = evaluate(
        "const states=[null,{}, {mode:'both',status:'available'}, {values:[true]}, {values:'edges'}];"
        "console.log(JSON.stringify(states.map(state=>evidenceDisplayDecision(state))));"
    )
    assert all(row["status"] == "unavailable" for row in observed)
    assert all(not row["drawNodes"] and not row["drawEdges"] for row in observed)
