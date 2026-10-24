"""The mounted supplied picker owns display pins separately from visibility."""

from __future__ import annotations

from importlib.resources import files
import json
from typing import Any, cast

import pytest

from ...edges.inspection.focus_support import published as published
from ...support import run_node_json, template_block
from .test_scientific_picker import SCRIPT, signals

MOUNT = (
    files("bijux_pollenomics.reporting.map_document")
    .joinpath("assets/scientific-picker-mount.js")
    .read_text()
)


def observe(
    action: str, request: object = (), *, accepted: bool = True
) -> dict[str, Any]:
    rows = signals()
    rows.append(
        {
            **rows[-1],
            "signal_id": "supplied:extra",
            "label": "Supplied extra",
            "feature_key": "taxon:extra",
        }
    )
    source = (
        template_block("function escapeHtml", "function normalizedMediaLinks")
        + template_block("function scientificCueGlyph", "function finiteControlNumber")
        + SCRIPT
        + MOUNT
        + "const SCIENTIFIC_SIGNALS="
        + json.dumps(rows)
        + ";const request="
        + json.dumps(request)
        + ";const accepted="
        + json.dumps(accepted)
        + r""";
const ids=SCIENTIFIC_SIGNALS.map(row=>row.signal_id),sourceBefore=JSON.stringify(SCIENTIFIC_SIGNALS);
const DEFAULT_SCIENTIFIC_SIGNAL_IDS=[...ids];
let activeScientificSignalIds=new Set(ids),loaded=false,loadFailure=false,loads=0,renders=0;
const initialState={scientificPins:request},ATLAS_EVIDENCE={classifications_status:accepted?'available':'unavailable'};
let evidenceToolsError=null;
const listeners={},filters={innerHTML:'',textContent:'',
 addEventListener(key,fn){listeners[key]=fn;listeners.bindings=(listeners.bindings||0)+1},contains(button){return button.inside!==false},
 querySelector(){return {focus(){listeners.focused=true},setSelectionRange(a,b){listeners.caret=[a,b]}}}};
const panel={open:false,addEventListener(key,fn){listeners[key]=fn}};
const buttons={};
const scientificFilters=filters,scientificActions={},scientificStatus={},scientificSummary={};
const sourceChronologyShortcuts={querySelectorAll(){return []}};
const document={getElementById(id){return id==='scientific-controls'?panel:(buttons[id]||=( {addEventListener(key,fn){this[key]=fn}}))}};
function sourceChronologyLayers(){return []}
function currentEvidenceTools(){return loaded?{pickerCatalog:scientificPickerCatalog,pickerInitial:scientificPickerInitialState,pickerAction:scientificPickerAction,pickerHtml:renderScientificPicker,pickerMount:mountScientificPicker}:null}
function loadEvidenceTools(){loads++;if(loadFailure){evidenceToolsError='Owned tools unavailable';return Promise.reject(Error(evidenceToolsError))}loaded=true;return Promise.resolve(currentEvidenceTools())}
function renderMapState(){renders++;renderScientificControls()}
const click=(type,id,disabled=false,inside=true)=>listeners.click({target:{closest(selector){return selector==='[data-scientific-action]'?{disabled,inside,dataset:{scientificAction:type,scientificId:id}}:null}}});
const tick=()=>new Promise(resolve=>setImmediate(resolve));
"""
        + template_block("let scientificPinValues", "let activeEvidenceDisplay")
        + template_block(
            "function renderScientificControls", "function visibleGovernedEdges"
        )
        + template_block(
            "document.getElementById('scientific-whole')",
            "document.querySelectorAll('[data-source-shortcut]')",
        )
        + "\n(async()=>{\n"
        + action
        + "\nif(sourceBefore!==JSON.stringify(SCIENTIFIC_SIGNALS))throw Error('Source mutated');"
        + "\n})().catch(error=>{console.error(error);process.exitCode=1});"
    )
    return cast(dict[str, Any], run_node_json(source))


def test_explicit_open_loads_once_and_preserves_visible_unpinned_signals() -> None:
    actual = observe(
        "renderScientificControls();const closed=loads;panel.open=true;"
        "listeners.toggle({currentTarget:panel});await tick();"
        "console.log(JSON.stringify({closed,loads,meta:scientificPickerMetadata(),"
        "visible:[...activeScientificSignalIds],html:filters.innerHTML}));"
    )
    assert actual["closed"] == 0 and actual["loads"] == 1
    assert actual["meta"]["status"] == "available"
    assert len(actual["meta"]["pinned_ids"]) == 6
    assert len(actual["visible"]) == 7
    assert "Visible but unpinned: 1" in actual["html"]
    assert actual["meta"]["requested_pin_values"] == []


def test_no_accepted_catalog_never_requests_or_invents_signals() -> None:
    actual = observe(
        "panel.open=true;listeners.toggle({currentTarget:panel});await tick();"
        "renderScientificControls();console.log(JSON.stringify({loads,html:filters.innerHTML,"
        "meta:scientificPickerMetadata(),hidden:scientificActions.hidden}));",
        accepted=False,
    )
    assert actual == {
        "loads": 0,
        "html": "",
        "meta": {
            "pinned_ids": None,
            "requested_pin_values": [],
            "status": "not_loaded",
        },
        "hidden": True,
    }


def test_hidden_pins_order_actions_and_search_use_actual_mounted_handlers() -> None:
    actual = observe(
        "panel.open=true;listeners.toggle({currentTarget:panel});await tick();"
        "click('hide',ids[0]);click('later',ids[0]);const hidden=scientificPickerMetadata();"
        "listeners.input({target:{matches(){return true},value:'Explicit source synonym',selectionStart:4,selectionEnd:4}});"
        "const searched=filters.innerHTML,searchRenders=renders;"
        "click('solo',ids[1]);const solo=[...activeScientificSignalIds];"
        "click('show',ids[0]);click('remove',ids[1]);"
        "console.log(JSON.stringify({hidden,searched,searchRenders,caret:listeners.caret,"
        "solo,visible:[...activeScientificSignalIds],meta:scientificPickerMetadata(),ids}));"
    )
    ids = actual["ids"]
    assert actual["hidden"]["pinned_ids"][:2] == [ids[1], ids[0]]
    assert actual["searchRenders"] == 2 and actual["caret"] == [4, 4]
    assert "Showing first 1 of 1 matches" in actual["searched"]
    assert actual["solo"] == [ids[1]] and actual["visible"] == [ids[0]]
    assert ids[1] not in actual["meta"]["pinned_ids"]
    assert (
        json.loads(actual["meta"]["requested_pin_values"][0])
        == actual["meta"]["pinned_ids"]
    )


@pytest.mark.parametrize("pin_request", [["not-json"], ['["unknown"]'], ["[]", "[]"]])
def test_invalid_request_is_visible_and_preserved_until_explicit_reset(
    pin_request: object,
) -> None:
    actual = observe(
        "panel.open=true;listeners.toggle({currentTarget:panel});await tick();"
        "const refused={meta:scientificPickerMetadata(),html:filters.innerHTML,visible:[...activeScientificSignalIds]};"
        "listeners.click({target:{closest(){return {hasAttribute(){return true}}}}});"
        "console.log(JSON.stringify({refused,meta:scientificPickerMetadata(),visible:[...activeScientificSignalIds]}));",
        pin_request,
    )
    assert actual["refused"]["meta"] == {
        "pinned_ids": None,
        "requested_pin_values": pin_request,
        "status": "unavailable",
    }
    assert "Reset comparison pins" in actual["refused"]["html"]
    assert actual["visible"] == actual["refused"]["visible"]
    assert actual["meta"]["status"] == "available"
    assert actual["meta"]["requested_pin_values"] == []


def test_explicit_empty_pins_and_buttons_preserve_existing_visibility_ownership() -> (
    None
):
    actual = observe(
        "panel.open=true;listeners.toggle({currentTarget:panel});await tick();"
        "const empty=scientificPickerMetadata(),visible=[...activeScientificSignalIds];"
        "buttons['scientific-clear'].click();const cleared=scientificPickerMetadata();"
        "buttons['scientific-whole'].click();"
        "console.log(JSON.stringify({empty,visible,cleared,restored:scientificPickerMetadata(),"
        "restoredVisible:[...activeScientificSignalIds]}));",
        ["[]"],
    )
    assert actual["empty"]["pinned_ids"] == [] and len(actual["visible"]) == 7
    assert actual["cleared"]["pinned_ids"] == []
    assert len(actual["restored"]["pinned_ids"]) == 6
    assert actual["restoredVisible"] == actual["visible"]


def test_loading_failure_keeps_unvalidated_raw_request_and_visibility() -> None:
    actual = observe(
        "loadFailure=true;panel.open=true;listeners.toggle({currentTarget:panel});await tick();"
        "console.log(JSON.stringify({meta:scientificPickerMetadata(),text:filters.textContent,"
        "visible:[...activeScientificSignalIds],loads}));",
        ['["not-yet-validated"]'],
    )
    assert actual["meta"]["status"] == "unavailable"
    assert actual["meta"]["pinned_ids"] is None
    assert actual["meta"]["requested_pin_values"] == ['["not-yet-validated"]']
    assert len(actual["visible"]) == 7 and actual["loads"] == 1
    assert "Owned tools unavailable" in actual["text"]


def test_refused_seventh_pin_keeps_valid_state_and_reports_action_failure() -> None:
    actual = observe(
        "panel.open=true;listeners.toggle({currentTarget:panel});await tick();"
        "const before=scientificPickerMetadata();click('pin',ids[6]);"
        "console.log(JSON.stringify({before,after:scientificPickerMetadata(),html:filters.innerHTML}));"
    )
    assert actual["before"] == actual["after"]
    assert "At most six exact signal IDs" in actual["html"]


def test_pin_request_roundtrips_real_hash_without_altering_scientific_visibility(
    published: dict[str, Any],
) -> None:
    from ...edges.inspection.focus_support import browser

    actual = browser(
        published,
        "scientificPinValues=['[\"unknown\"]','[]'];"
        "const before=[...activeScientificSignalIds];"
        "window.location.hash='#'+atlasSelectionHashParams().toString();"
        "const parsed=parseHashState();"
        "console.log(JSON.stringify({request:parsed.scientificPins,before,"
        "after:[...activeScientificSignalIds]}));",
    )
    assert actual["request"] == ['["unknown"]', "[]"]
    assert actual["before"] == actual["after"]


def test_capture_and_download_publish_same_validated_pin_metadata() -> None:
    for start, end in (
        ("function atlasCaptureSnapshot", "function atlasCaptureOrientationKeys"),
        ("focusExportButton.addEventListener", "focusTabs.addEventListener"),
    ):
        assert "scientific_picker: scientificPickerMetadata()" in template_block(
            start, end
        )
    assert "resetScientificPins();" in template_block(
        "async function restoreDefaults", "document.getElementById('countries-all')"
    )


def test_delegated_actions_ignore_disabled_and_foreign_buttons_without_rebinding() -> (
    None
):
    actual = observe(
        "panel.open=true;listeners.toggle({currentTarget:panel});await tick();"
        "const before=scientificPickerMetadata();"
        "renderScientificControls();renderScientificControls();"
        "click('remove',ids[0],true);click('remove',ids[0],false,false);"
        "console.log(JSON.stringify({before,after:scientificPickerMetadata(),"
        "renders,bindings:listeners.bindings}));"
    )
    assert actual["before"] == actual["after"]
    assert actual["renders"] == 0 and actual["bindings"] == 2
