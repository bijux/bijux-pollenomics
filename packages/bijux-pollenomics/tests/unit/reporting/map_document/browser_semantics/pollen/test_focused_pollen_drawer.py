"""Real source map clicks retain exact sample facets and independent display choices."""

from __future__ import annotations

import json
from pathlib import Path
import re
from subprocess import CalledProcessError
from typing import Any, cast

import pytest

from ..chronology import test_age_depth_diagram as age
from ..controls.loading.test_evidence_tools_loading import DESCRIPTOR, OPTIONAL_BODY
from ..support import run_node_json, template_block
from .test_focused_source_signal import feature
from .test_pollen_diagram import add_row, decoded
from .test_pollen_small_multiples import add_variable


def node_result(source: str) -> Any:
    try:
        return run_node_json(source)
    except CalledProcessError as error:
        raise AssertionError(error.stderr) from error


@pytest.fixture
def tabs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    result = decoded(cast(dict[str, Any], age.projected_tabs(tmp_path, monkeypatch)))
    add_variable(result)
    return result


def observe(
    tabs: dict[str, Any],
    signals: list[dict[str, Any]],
    actions: str,
    *,
    transport: bool = False,
) -> dict[str, Any]:
    source = (
        age.diagram_script()
        + template_block(
            "function unavailableDetailTabs",
            "async function ensureStaticAtlasIndexesLoaded",
        )
        + template_block("function stableFeatureRecordId", "function setFocusState")
        + template_block(
            "async function focusPointAtVisibleIndex", "function countActiveOverrides"
        )
    )
    loader = ""
    if transport:
        loader = (
            "const STATIC_ATLAS_BOOTSTRAP={runtime:{optional_controllers:{evidence_tools:"
            + json.dumps(DESCRIPTOR)
            + "}}};const window={location:{protocol:'https:'}},scripts=[];"
            + "document.head={appendChild(script){scripts.push(script)}};"
            + "document.createElement=()=>({events:{},addEventListener(name,fn){this.events[name]=fn}});"
            + "function scientificCueGlyph(){return ''};const optionalBody="
            + json.dumps(OPTIONAL_BODY.decode())
            + ";\n"
            + template_block(
                "let evidenceTools = null", "const standaloneMetadata"
            ).replace(
                "let evidenceTools = null, evidenceToolsRequest = null, evidenceToolsError = null;",
                "let evidenceTools = null;",
            )
        )
    return cast(
        dict[str, Any],
        node_result(
            source
            + "const tabs="
            + json.dumps(tabs)
            + ",signals="
            + json.dumps(signals)
            + r""";
const before=JSON.stringify([tabs,signals]),callbacks={},selectors={};
const COUNTRIES=['Denmark','Finland','Norway','Sweden'],activeCountries=new Set(['Sweden']);
const detailTablePages=new Map(),DETAIL_TABLE_PAGE_SIZE=25;
const focusTabs={innerHTML:'',contains(){return false;},querySelectorAll(){return ['overview','pollen_composition'].map(key=>({dataset:{focusTab:key},addEventListener(event,cb){callbacks[key]=cb;}}));}};
const focusDetail={_html:'',get innerHTML(){return this._html;},set innerHTML(value){this._html=value;for(const key of Object.keys(selectors))delete selectors[key];},dataset:{},contains(element){return Object.values(selectors).includes(element);},focus(){document.activeElement=this;},setAttribute(){},querySelectorAll(selector){
  if(selector==='[data-source-diagram-retry]'&&this._html.includes('data-source-diagram-retry'))return [{addEventListener(event,cb){callbacks.retry=cb;}}];
  if(selector==='[data-detail-table-page]')return [{dataset:{detailTablePage:'pollen_composition',pageDirection:'next'},disabled:false,addEventListener(event,cb){callbacks.next=cb;}}];
  if((selector==='[data-pollen-depth-group]'||selector==='[data-pollen-age-group]')&&activeFocusTab==='pollen_composition'){
    if(!selectors[selector])selectors[selector]={value:'',dataset:{[selector.includes('depth')?'pollenDepthGroup':'pollenAgeGroup']:'true'},focus(){document.activeElement=this;},addEventListener(event,cb){callbacks[selector]=cb;}};
    return [selectors[selector]];
  }return [];
}};
const focusExportButton={},focusCopyLinkButton={},focusExportStatus={},document={activeElement:null};
function sourcePollenExportAvailable(){return false;}
function syncHashState(){}
function normalizedMediaLinks(){return [];}
function coordinateLabel(){return '59, 18';}
function featureTimeDescriptor(){return null;}
function featureCoordinatePair(feature){return {latitude:feature.latitude,longitude:feature.longitude};}
async function detailTabsForFeature(){return tabs;}
let focusState=null,activeFocusTab='pollen_composition',evidenceToolsRequest=null;
const edgeFocusLoadState={request:0};
let edgeVisible=true;
function visibleGovernedEdges(){return edgeVisible?[{edge_id:'edge:1'}]:[]}
function availableEdgeFocus(){return edgeVisible?{}:null}
function loadEvidenceTools(){return Promise.resolve(currentEvidenceTools())}
function setFocusState(state){focusState=state;edgeFocusLoadState.request++;renderFocusDetail();}
const visiblePointEntries=signals.map(signal=>({layer:{key:'source-neotoma',label:'Source context'},feature:signal}));
const snapshots={},keys=pollenDepthDiagramData(tabs).groups.map(group=>group.key);
function snapshot(name){snapshots[name]=focusDetail.innerHTML;}
function chooseNative(key){selectors['[data-pollen-depth-group]'].value=key;callbacks['[data-pollen-depth-group]']();}
"""
            + loader
            + "\n(async()=>{\n"
            + actions
            + r"""
console.log(JSON.stringify({snapshots,keys,focused:document.activeElement?.dataset||null,focusIsCurrent:focusDetail.contains(document.activeElement),sourceRetained:focusState.sourceSignal===signals.at(-1),cached:focusState.detailTabs===tabs,unchanged:before===JSON.stringify([tabs,signals])}));
})();
"""
        ),
    )


def anchor(html: str) -> str | None:
    match = re.search(r"Selected anchor: ([^<]+)", html)
    return match.group(1) if match else None


def test_delayed_diagram_tools_render_only_current_focused_record(
    tabs: dict[str, Any],
) -> None:
    first, second = feature(tabs), feature(tabs, taxon=50)
    output = observe(
        tabs,
        [first, second],
        """
let ready=false,release;
const pending=new Promise(resolve=>{release=resolve});
currentEvidenceTools=()=>ready?{sourceDetails:createSourceRecordDetails,sourceDiagrams:createSourceDiagrams}:null;
loadEvidenceTools=()=>pending;
const firstLoad=focusPointAtVisibleIndex(0);
await new Promise(resolve=>setImmediate(resolve));snapshot('pending');
const secondLoad=focusPointAtVisibleIndex(1);
await new Promise(resolve=>setImmediate(resolve));snapshot('secondPending');
ready=true;release();await Promise.all([firstLoad,secondLoad]);snapshot('ready');
""",
    )
    assert 'role="status"' in output["snapshots"]["pending"]
    assert "Loading source diagrams" in output["snapshots"]["secondPending"]
    assert (
        anchor(output["snapshots"]["ready"])
        == "Triticum (canonical variable representative; observation name unavailable)"
    )
    assert output["sourceRetained"] and output["unchanged"]


def test_diagram_transport_failure_offers_explicit_retry(tabs: dict[str, Any]) -> None:
    output = observe(
        tabs,
        [feature(tabs)],
        """
let ready=false;
currentEvidenceTools=()=>ready?{sourceDetails:createSourceRecordDetails,sourceDiagrams:createSourceDiagrams}:null;
evidenceToolsError='Diagram transport failed';
loadEvidenceTools=async()=>{ready=true};
setFocusState({kind:'point',...pointFocusIdentity(visiblePointEntries[0].layer,signals[0]),sourceSignal:signals[0],detailTabs:tabs});
snapshot('failed');await callbacks.retry();snapshot('ready');
""",
    )
    assert "Diagram transport failed" in output["snapshots"]["failed"]
    assert "Retry source diagrams" in output["snapshots"]["failed"]
    assert "data-pollen-focused-signal" in output["snapshots"]["ready"]


def test_late_retry_does_not_render_filtered_record(tabs: dict[str, Any]) -> None:
    output = observe(
        tabs,
        [feature(tabs)],
        """
let ready=false,release;
currentEvidenceTools=()=>ready?{sourceDetails:createSourceRecordDetails,sourceDiagrams:createSourceDiagrams}:null;
evidenceToolsError='Diagram transport failed';
loadEvidenceTools=()=>new Promise(resolve=>{release=()=>{ready=true;resolve()}});
setFocusState({kind:'point',...pointFocusIdentity(visiblePointEntries[0].layer,signals[0]),sourceSignal:signals[0],detailTabs:tabs});
const retry=callbacks.retry();snapshot('pending');visiblePointEntries.splice(0,1);
release();await retry;snapshot('after');
""",
    )
    assert output["snapshots"]["pending"] == output["snapshots"]["after"]
    assert "Loading source diagrams" in output["snapshots"]["after"]


def test_late_retry_does_not_render_filtered_edge(tabs: dict[str, Any]) -> None:
    output = observe(
        tabs,
        [feature(tabs)],
        """
let ready=false,release;
currentEvidenceTools=()=>ready?{sourceDetails:createSourceRecordDetails,sourceDiagrams:createSourceDiagrams}:null;
evidenceToolsError='Diagram transport failed';
loadEvidenceTools=()=>new Promise(resolve=>{release=()=>{ready=true;resolve()}});
setFocusState({kind:'edge',edgeId:'edge:1',sourceSignal:signals[0],detailTabs:tabs});
const retry=callbacks.retry();snapshot('pending');edgeVisible=false;
release();await retry;snapshot('after');
""",
    )
    assert output["snapshots"]["pending"] == output["snapshots"]["after"]
    assert "Loading source diagrams" in output["snapshots"]["after"]


def test_retry_completion_rerenders_same_record_after_detail_replacement(
    tabs: dict[str, Any],
) -> None:
    output = observe(
        tabs,
        [feature(tabs)],
        """
let ready=false,release;
currentEvidenceTools=()=>ready?{sourceDetails:createSourceRecordDetails,sourceDiagrams:createSourceDiagrams}:null;
evidenceToolsError='Diagram transport failed';
loadEvidenceTools=()=>new Promise(resolve=>{release=()=>{ready=true;resolve()}});
setFocusState({kind:'point',...pointFocusIdentity(visiblePointEntries[0].layer,signals[0]),sourceSignal:signals[0],detailTabs:tabs});
const retry=callbacks.retry();focusState={...focusState,detailTabs:tabs};renderFocusDetail();snapshot('pending');
release();await retry;snapshot('ready');
""",
    )
    assert "Loading source diagrams" in output["snapshots"]["pending"]
    assert "data-pollen-focused-signal" in output["snapshots"]["ready"]


def test_real_loader_retry_uses_verified_factory_for_current_focus(
    tabs: dict[str, Any],
) -> None:
    output = observe(
        tabs,
        [feature(tabs), feature(tabs, taxon=50)],
        """
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const first=focusPointAtVisibleIndex(0);await tick();snapshot('pending');
snapshots.descriptor={src:scripts[0].src,integrity:scripts[0].integrity,crossOrigin:scripts[0].crossOrigin};
scripts[0].events.error();await first;snapshot('failed');
const retry=callbacks.retry();await tick();
const second=focusPointAtVisibleIndex(1);await tick();snapshot('secondPending');
eval(optionalBody);scripts[1].events.load();await Promise.all([retry,second]);snapshot('ready');
""",
        transport=True,
    )
    assert output["snapshots"]["descriptor"] == {
        "src": f"./{DESCRIPTOR['path']}",
        "integrity": DESCRIPTOR["integrity"],
        "crossOrigin": "anonymous",
    }
    assert "Loading source diagrams" in output["snapshots"]["pending"]
    assert "Retry source diagrams" in output["snapshots"]["failed"]
    assert "Loading source diagrams" in output["snapshots"]["secondPending"]
    assert (
        anchor(output["snapshots"]["ready"])
        == "Triticum (canonical variable representative; observation name unavailable)"
    )
    assert output["sourceRetained"] and output["unchanged"]


def test_rerender_retains_keyboard_focus_on_native_selector(
    tabs: dict[str, Any],
) -> None:
    output = observe(
        tabs,
        [feature(tabs)],
        "await focusPointAtVisibleIndex(0);chooseNative(keys[0]);renderFocusDetail();",
    )
    assert output["focused"] == {"pollenDepthGroup": "true"}
    assert output["focusIsCurrent"] is True


def test_map_click_selects_exact_taxon_and_cached_site_resets_feature_choices(
    tabs: dict[str, Any],
) -> None:
    first, second = feature(tabs), feature(tabs, taxon=50)
    output = observe(
        tabs,
        [first, second],
        """
await focusPointAtVisibleIndex(0);snapshot('first');
chooseNative(keys.find(key=>JSON.parse(key)[2]==='neotoma:variable:50'));snapshot('manual');
renderFocusDetail();snapshot('rerender');callbacks.next();snapshot('page');
callbacks.overview();callbacks.pollen_composition();snapshot('tab');
chooseNative(keys.find(key=>JSON.parse(key)[2]==='neotoma:variable:51'));
await focusPointAtVisibleIndex(1);snapshot('second');
""",
    )
    snapshots = output["snapshots"]
    first_label = "Native taxon 51 (canonical variable representative; observation name unavailable)"
    assert anchor(snapshots["first"]) == first_label
    for key in ("manual", "rerender", "page", "tab", "second"):
        assert anchor(snapshots[key]) != first_label, key
    assert 'data-pollen-focused-signal="matched"' in snapshots["manual"]
    assert "native taxon 51" in snapshots["manual"]
    assert "native taxon 50" in snapshots["second"]
    for key in ("first", "manual", "rerender", "page", "tab"):
        selected = re.findall(
            r'<g[^>]*data-selected-observation="true"[^>]*aria-label="([^"]+)"',
            snapshots[key],
        )
        assert len(selected) == 1 and "observation-51;" in selected[0], key
    assert (
        "Selected map-signal observation; neotoma:observation:40:50:1;"
        in snapshots["second"]
    )
    assert output["sourceRetained"] and output["cached"] and output["unchanged"]


def test_age_axis_choice_does_not_leak_between_features_on_cached_site(
    tabs: dict[str, Any],
) -> None:
    output = observe(
        tabs,
        [feature(tabs), feature(tabs, taxon=50)],
        """
await focusPointAtVisibleIndex(0);
const key=pollenDisplaySelection(tabs).key,ageKey=pollenAgeAxisData(tabs,key).options[0].key;
selectors['[data-pollen-age-group]'].value=ageKey;callbacks['[data-pollen-age-group]']();snapshot('age');
callbacks.overview();callbacks.pollen_composition();snapshot('return');
await focusPointAtVisibleIndex(1);snapshot('second');
""",
    )
    for key in ("age", "return"):
        assert ">Source age (year)</text>" in output["snapshots"][key]
    assert ">Source age (year)</text>" not in output["snapshots"]["second"]
    assert ">Source depth (unit not supplied)</text>" in output["snapshots"]["second"]
    assert output["unchanged"]


@pytest.mark.parametrize("state", ["unmatched", "incompatible"])
def test_unresolved_source_match_requires_manual_anchor(
    tabs: dict[str, Any], state: str
) -> None:
    signal = feature(tabs)
    if state == "unmatched":
        signal["source_record_id"] = "foreign-sample"
    else:
        add_row(
            tabs["pollen_composition"],
            observation_id="other-context-observation",
            variable_id="neotoma:variable:51",
            source_taxon_id=51,
            source_context="different preparation",
        )
    output = observe(
        tabs,
        [signal],
        """
await focusPointAtVisibleIndex(0);snapshot('initial');
chooseNative(keys[0]);snapshot('manual');
""",
    )
    assert anchor(output["snapshots"]["initial"]) is None
    assert "<svg" not in output["snapshots"]["initial"]
    assert "<svg" in output["snapshots"]["manual"]
    assert output["sourceRetained"] and output["unchanged"]
