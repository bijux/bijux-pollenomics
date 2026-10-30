"""The actual drawer keeps source-age display choices explicit and record-local."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from ..support import run_node_json
from .test_age_depth_diagram import diagram_script, projected_tabs


def mounted_choices(tabs: dict[str, object]) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        run_node_json(
            diagram_script()
            + "const tabs="
            + json.dumps(tabs)
            + r""";
const before=JSON.stringify(tabs), callbacks={}, selectors={};
const detailTablePages=new Map(), DETAIL_TABLE_PAGE_SIZE=25;
let focusCount=0;
const focusTabs={innerHTML:'',contains(){return false;},querySelectorAll(){
  return ['overview','pollen_composition'].map(key=>({dataset:{focusTab:key},addEventListener(event,cb){callbacks[key]=cb;}}));
}};
const focusDetail={_html:'',get innerHTML(){return this._html;},set innerHTML(value){this._html=value;for(const key of Object.keys(selectors))delete selectors[key];},dataset:{},contains(){return false;},setAttribute(k,v){this[k]=v;},querySelectorAll(selector){
  if(selector==='[data-detail-table-page]')return [{dataset:{detailTablePage:'pollen_composition',pageDirection:'next'},disabled:false,addEventListener(event,cb){callbacks.next=cb;}}];
  if(selector==='[data-pollen-depth-group]'||selector==='[data-pollen-age-group]'){
    if(activeFocusTab!=='pollen_composition')return [];
    if(selectors[selector])return [selectors[selector]];
    const item={value:'',focus(){focusCount++;},addEventListener(event,cb){callbacks[selector]=cb;}};
    selectors[selector]=item;return [item];
  }
  return [];
}};
const focusExportButton={},focusCopyLinkButton={},focusExportStatus={},document={activeElement:null};
function sourcePollenExportAvailable(){return false;}
function syncHashState(){}
let activeFocusTab='pollen_composition',focusState={kind:'point',detailTabs:tabs};
const nativeKeys=pollenDepthDiagramData(tabs).groups.map(group=>group.key);
const options=pollenAgeAxisData(tabs,nativeKeys[0]).options;
const captured={};
function choose(key){selectors['[data-pollen-age-group]'].value=key;callbacks['[data-pollen-age-group]']();}
renderFocusDetail();captured.initial=focusDetail.innerHTML;
for(const option of options){choose(option.key);captured[option.key]=focusDetail.innerHTML;}
choose(options[0].key);captured.chosen=focusDetail.innerHTML;
renderFocusDetail();captured.rerender=focusDetail.innerHTML;
callbacks.next();captured.paginated=focusDetail.innerHTML;
callbacks.overview();captured.overview=focusDetail.innerHTML;
callbacks.pollen_composition();captured.returned=focusDetail.innerHTML;
selectors['[data-pollen-depth-group]'].value=nativeKeys[1];callbacks['[data-pollen-depth-group]']();captured.nativeChanged=focusDetail.innerHTML;
choose(options[0].key);choose('foreign');captured.invalid=focusDetail.innerHTML;
choose(options[0].key);choose('');captured.depth=focusDetail.innerHTML;
choose(options[0].key);focusState={kind:'point',detailTabs:JSON.parse(JSON.stringify(tabs))};
renderFocusDetail();captured.newRecord=focusDetail.innerHTML;
console.log(JSON.stringify({captured,options,focusCount,unchanged:before===JSON.stringify(tabs)}));
"""
        ),
    )


def test_explicit_age_choice_survives_pages_tabs_and_resets_for_source_or_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tabs = projected_tabs(tmp_path, monkeypatch)
    table = cast(dict[str, Any], tabs["pollen_composition"])
    # Decode through the actual transport before creating controlled source groups.
    table["records"] = run_node_json(
        diagram_script()
        + "const table="
        + json.dumps(table)
        + ";console.log(JSON.stringify(table.records.map(row=>{const item=decodeDetailTableRow(table,row);return table.fields.map(field=>item[field]);})));"
    )
    table.pop("identifier_prefixes", None)
    table.pop("column_dictionaries", None)
    original = table["records"][0]
    for index in range(1, 27):
        row = original.copy()
        row[table["fields"].index("observation_id")] = f"source-observation:{index}"
        if index == 1:
            row[table["fields"].index("source_context")] = "alternative context"
        table["records"].append(row)
    table["record_count"] = len(table["records"])
    output = mounted_choices(tabs)
    captured = output["captured"]
    assert output["unchanged"] is True and len(output["options"]) == 3
    for key in ("initial", "nativeChanged", "invalid", "depth", "newRecord"):
        assert 'id="native-value-depth-title-0"' in captured[key]
        assert ">Source depth (unit not supplied)</text>" in captured[key]
        assert 'data-pollen-age-group="true"' in captured[key]
        assert ">Source age (year)</text>" not in captured[key]
    for key in ("chosen", "rerender", "paginated", "returned"):
        assert ">Source age (year)</text>" in captured[key], key
        assert ">Source depth (unit not supplied)</text>" not in captured[key]
    assert "Showing 26–27 of 27" in captured["paginated"]
    assert 'data-pollen-age-group="true"' not in captured["overview"]
    for option in output["options"]:
        html = captured[option["key"]]
        assert 'id="native-value-source-age-title-0"' in html
        assert ">Source age (year)</text>" in html
        assert "Showing 1–25 of 27" in html
        assert "neotoma:observation:40:50:1" in html
    assert output["focusCount"] == 10
