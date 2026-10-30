"""Explicit point intent loads bound source context without withholding raw tables."""

from __future__ import annotations

from importlib.resources import files
from typing import Any, cast

import pytest

from ..support import run_node_json, template_block

ORIGINAL = (
    files("bijux_pollenomics.reporting.map_document")
    .joinpath("assets/source-record-details.js")
    .read_text()
)
FACTORY = template_block(
    "function createSourceRecordDetails", "/* atlas-evidence-tools:end */"
)


def observe(action: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        run_node_json(
            template_block("function escapeHtml", "function normalizedMediaLinks")
            + FACTORY
            + template_block("function stableFeatureRecordId", "function setFocusState")
            + template_block("let sourceDetailRenderers", "function renderFocusDetail")
            + template_block(
                "async function focusPointAtVisibleIndex",
                "function countActiveOverrides",
            )
            + r"""
let loads=0,tools=null,evidenceToolsError=null,focusState=null;
const edgeFocusLoadState={request:0},events=[],pending=[];
const visiblePointEntries=['a','b'].map(id=>({layer:{key:'source',label:'Source'},feature:{record_id:id,latitude:0,longitude:0}}));
function featureCoordinatePair(feature){return {latitude:feature.latitude,longitude:feature.longitude}}
function normalizedMediaLinks(){return []}
function coordinateLabel(){return '0, 0'}
function featureTimeDescriptor(){return null}
function unavailableDetailTabs(reason){return {overview:{status:'unavailable',reason_code:reason}}}
function setFocusState(value){focusState=value;edgeFocusLoadState.request++}
function renderFocusDetail(){events.push({id:focusState?.recordId,raw:focusState?.detailTabs?.raw===true,tools:Boolean(tools)})}
function detailTabsForFeature(feature){return Promise.resolve({overview:{source_family:'neotoma'},raw:true,id:feature.record_id})}
function currentEvidenceTools(){return tools}
function loadEvidenceTools(){loads++;return new Promise(resolve=>pending.push(()=>{tools={sourceDetails:createSourceRecordDetails};resolve(tools)}))}
function detailTableShape(){return false}
function decodeDetailTableRow(){throw Error('Unexpected decode')}
function detailTableText(value){return String(value)}
function renderDetailTable(){return '<p>Original table</p>'}
const tick=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
"""
            + action
            + "\n})().catch(error=>{console.error(error);process.exitCode=1});"
        ),
    )


def test_factory_contains_unchanged_original_body_and_requires_explicit_bindings() -> (
    None
):
    assert ORIGINAL in FACTORY
    actual = observe(
        "const bindings={detailTableShape,decodeDetailTableRow,detailTableText,renderDetailTable,escapeHtml};"
        "const missing=[];for(const key of Object.keys(bindings)){"
        "try{createSourceRecordDetails({...bindings,[key]:null})}catch(error){missing.push(key)}}"
        "const result=createSourceRecordDetails(bindings);"
        "console.log(JSON.stringify({keys:Object.keys(result),frozen:Object.isFrozen(result),missing,loads}));"
    )
    assert actual["keys"] == ["overview", "samples", "classification", "provenance"]
    assert actual["frozen"] and len(actual["missing"]) == 5
    assert actual["loads"] == 0


def test_point_intent_exposes_raw_details_before_optional_context_finishes() -> None:
    actual = observe(
        "const untouched=loads,request=focusPointAtVisibleIndex(0);await tick();"
        "const before={loads,events:[...events],context:renderSourceDetailContext('samples',focusState.detailTabs)};"
        "pending[0]();await request;"
        "console.log(JSON.stringify({untouched,before,events,context:renderSourceDetailContext('samples',focusState.detailTabs)}));"
    )
    assert actual["untouched"] == 0 and actual["before"]["loads"] == 1
    assert actual["before"]["events"] == [{"id": "a", "raw": True, "tools": False}]
    assert "Loading source detail context" in actual["before"]["context"]
    assert actual["events"][-1] == {"id": "a", "raw": True, "tools": True}
    assert "Neotoma sample observation values" in actual["context"]


def test_optional_failure_retains_raw_details_and_visible_failure() -> None:
    actual = observe(
        "loadEvidenceTools=()=>{loads++;evidenceToolsError='Context transport failed';return Promise.reject(Error(evidenceToolsError))};"
        "await focusPointAtVisibleIndex(0);"
        "console.log(JSON.stringify({loads,raw:focusState.detailTabs.raw,context:renderSourceDetailContext('samples',focusState.detailTabs)}));"
    )
    assert actual["loads"] == 1 and actual["raw"] is True
    assert "Context transport failed" in actual["context"]
    assert "Original source tables remain available below" in actual["context"]


@pytest.mark.parametrize("action", ["close", "new_point", "same_point", "filter"])
def test_late_optional_completion_cannot_rerender_superseded_point(action: str) -> None:
    actual = observe(
        "const first=focusPointAtVisibleIndex(0);await tick();"
        + {
            "close": "setFocusState(null);",
            "new_point": "const second=focusPointAtVisibleIndex(1);await tick();pending[1]();await second;",
            "same_point": "const second=focusPointAtVisibleIndex(0);await tick();pending[1]();await second;",
            "filter": "visiblePointEntries.splice(0,1);",
        }[action]
        + "const before=events.length;pending[0]();await first;"
        + "console.log(JSON.stringify({before,after:events.length,id:focusState?.recordId||null}));"
    )
    assert actual["before"] == actual["after"]
    assert (
        actual["id"]
        == {"close": None, "new_point": "b", "same_point": "a", "filter": "a"}[action]
    )


def test_late_raw_detail_completion_cannot_replace_newer_same_identity_focus() -> None:
    actual = observe(
        "let release;detailTabsForFeature=()=>new Promise(resolve=>{release=resolve});"
        "const first=focusPointAtVisibleIndex(0);await tick();"
        "setFocusState({...focusState,detailTabs:{newer:true}});"
        "release({raw:true});pending[0]();await first;"
        "console.log(JSON.stringify({newer:focusState.detailTabs.newer,events}));"
    )
    assert actual == {"newer": True, "events": []}


def test_current_focus_survives_rebuilt_display_entry_with_same_exact_identity() -> (
    None
):
    actual = observe(
        "let release;detailTabsForFeature=()=>new Promise(resolve=>{release=resolve});"
        "const first=focusPointAtVisibleIndex(0);await tick();"
        "visiblePointEntries[0]={...visiblePointEntries[0]};"
        "release({raw:true});await tick();pending[0]();await first;"
        "console.log(JSON.stringify({raw:focusState.detailTabs.raw,events}));"
    )
    assert actual["raw"] is True
    assert actual["events"] == [
        {"id": "a", "raw": True, "tools": False},
        {"id": "a", "raw": True, "tools": True},
    ]
