"""Real source map clicks retain exact sample facets and independent display choices."""

from __future__ import annotations

import json
from pathlib import Path
import re
from subprocess import CalledProcessError
from typing import Any, cast

import pytest

from .chronology import test_age_depth_diagram as age
from .support import run_node_json, template_block
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
    tabs: dict[str, Any], signals: list[dict[str, Any]], actions: str
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
const detailTablePages=new Map(),DETAIL_TABLE_PAGE_SIZE=25;
const focusTabs={innerHTML:'',contains(){return false;},querySelectorAll(){return ['overview','pollen_composition'].map(key=>({dataset:{focusTab:key},addEventListener(event,cb){callbacks[key]=cb;}}));}};
const focusDetail={_html:'',get innerHTML(){return this._html;},set innerHTML(value){this._html=value;for(const key of Object.keys(selectors))delete selectors[key];},dataset:{},contains(){return false;},setAttribute(){},querySelectorAll(selector){
  if(selector==='[data-detail-table-page]')return [{dataset:{detailTablePage:'pollen_composition',pageDirection:'next'},disabled:false,addEventListener(event,cb){callbacks.next=cb;}}];
  if((selector==='[data-pollen-depth-group]'||selector==='[data-pollen-age-group]')&&activeFocusTab==='pollen_composition'){
    if(!selectors[selector])selectors[selector]={value:'',focus(){},addEventListener(event,cb){callbacks[selector]=cb;}};
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
let focusState=null,activeFocusTab='pollen_composition';
const edgeFocusLoadState={request:0};
function loadEvidenceTools(){return Promise.resolve(currentEvidenceTools())}
function setFocusState(state){focusState=state;edgeFocusLoadState.request++;renderFocusDetail();}
const visiblePointEntries=signals.map(signal=>({layer:{key:'source-neotoma',label:'Source context'},feature:signal}));
const snapshots={},keys=pollenDepthDiagramData(tabs).groups.map(group=>group.key);
function snapshot(name){snapshots[name]=focusDetail.innerHTML;}
function chooseNative(key){selectors['[data-pollen-depth-group]'].value=key;callbacks['[data-pollen-depth-group]']();}
(async()=>{
"""
            + actions
            + r"""
console.log(JSON.stringify({snapshots,keys,sourceRetained:focusState.sourceSignal===signals.at(-1),cached:focusState.detailTabs===tabs,unchanged:before===JSON.stringify([tabs,signals])}));
})();
"""
        ),
    )


def anchor(html: str) -> str | None:
    match = re.search(r"Selected anchor: ([^<]+)", html)
    return match.group(1) if match else None


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
    assert anchor(snapshots["first"]) == "Native taxon 51"
    for key in ("manual", "rerender", "page", "tab", "second"):
        assert anchor(snapshots[key]) != "Native taxon 51", key
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
