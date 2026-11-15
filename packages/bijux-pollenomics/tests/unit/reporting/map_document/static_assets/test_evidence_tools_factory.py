"""The distributed optional factory binds its explicit presentation dependencies."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from bijux_pollenomics.reporting.map_document import render as subject

from ..browser_semantics.support import run_node_json
from .test_runtime_packaging import request_args as request_args


def test_optional_factory_binds_escape_and_supplied_glyph_callback(
    tmp_path: Path, request_args: dict[str, Any]
) -> None:
    html, _ = subject.write_static_map_document(tmp_path / "atlas.html", **request_args)
    evidence = subject.static_map_optional_controller_paths(html)[0]
    evidence_raw = evidence.read_bytes()
    observed = run_node_json(
        evidence_raw.decode()
        + """
const tools=BijuxPollenomicsEvidenceTools(value=>String(value),cue=>'supplied-glyph-'+cue);
const catalog=tools.pickerCatalog([{signal_id:'exact',label:'Exact',feature_key:'taxon:exact',resolution:'taxon',status:'accepted',color:'#112233',non_color_cue:'circle'}]);
const source=tools.sourceDetails({detailTableShape:()=>false,decodeDetailTableRow:()=>null,
detailTableText:value=>String(value),renderDetailTable:()=>'',escapeHtml:value=>String(value)});
console.log(JSON.stringify({frozen:Object.isFrozen(tools),methods:Object.keys(tools),
country:tools.countryData([]),time:tools.timeData([]),picker:tools.pickerCatalog([]),
sourceFrozen:Object.isFrozen(source),sourceMethods:Object.keys(source),sourceHtml:source.overview({},{}),
chronologyHtml:source.chronology({chronology:{}}),
depth:source.depthProfile({},'collection','dataset'),
charcoal:source.charcoalSignal?.({}, {}) ?? null,
ageGroup:source.ageDepthGroup({identity:['collection','dataset','model','basis','year'],names:['native'],
 rows:[{point:10,endpoints:null,depth:2,sample:'sample',claim:{chronology_claim_id:'claim'}}]},0),
html:tools.pickerHtml(catalog,{pinnedIds:[],visibleIds:[]})}));
"""
    )
    assert observed["frozen"] is True
    assert observed["methods"] == [
        "countryData",
        "countryHtml",
        "timeData",
        "timeHtml",
        "pickerCatalog",
        "pickerSearch",
        "pickerInitial",
        "pickerAction",
        "pickerHtml",
        "pickerMount",
        "sourceDetails",
        "sourceExport",
        "sourceResources",
        "selectionExport",
    ]
    assert all(
        observed[key]["status"] == "available" for key in ("country", "time", "picker")
    )
    assert "supplied-glyph-circle" in observed["html"]
    assert observed["sourceFrozen"] is True
    assert observed["sourceMethods"] == [
        "overview",
        "samples",
        "chronology",
        "classification",
        "provenance",
        "depthProfile",
        "ageDepthGroup",
        "charcoalSignal",
    ]
    assert "Selected sample metadata is supported for Neotoma" in observed["sourceHtml"]
    assert 'data-source-chronology-review="unavailable"' in observed["chronologyHtml"]
    assert (
        "does not establish that no source issues exist" in observed["chronologyHtml"]
    )
    assert observed["depth"]["unit"] is None
    assert observed["depth"]["label"] == "Source depth (unit not supplied)"
    assert "matching source depth profile unavailable" in observed["depth"]["html"]
    assert "Source depth (unit not supplied)" in observed["ageGroup"]
    assert "claim; sample sample; depth 2 (unit not supplied)" in observed["ageGroup"]
    assert observed["charcoal"]["status"] == "unavailable"


def test_optional_classification_renders_reviewed_counts_with_explicit_supplements(
    tmp_path: Path, request_args: dict[str, Any]
) -> None:
    import json

    from ....analysis.classification.test_reviewed_context import (
        _crop_indicator_payload,
    )

    html, _ = subject.write_static_map_document(tmp_path / "atlas.html", **request_args)
    source = subject.static_map_optional_controller_paths(html)[0].read_text()
    observed = run_node_json(
        source
        + "\nconst payload="
        + json.dumps(_crop_indicator_payload())
        + """;
const tools=BijuxPollenomicsEvidenceTools(String,String);
const bindings={detailTableShape:()=>false,decodeDetailTableRow:()=>null,
 detailTableText:String,renderDetailTable:()=>'',escapeHtml:String};
let supplements=[];
const reader=tools.sourceDetails({...bindings,renderDetailObjectEntries:(value,path,excluded)=>{
 supplements.push({same:value===payload,path,excluded:[...excluded]});return '<p>Supplied supplement</p>';
}});
const html=reader.classification(payload,'classification');
const legacy=tools.sourceDetails(bindings);
console.log(JSON.stringify({html,supplements,legacyNative:legacy.classification({}),
 missingBinding:legacy.classification(payload,'classification'),methods:Object.keys(reader),frozen:Object.isFrozen(reader)}));
"""
    )
    assert "Reviewed crop and indicator context" in observed["html"]
    assert "Unique observations across these categories: 3." in observed["html"]
    assert "Supplied supplement" in observed["html"]
    assert observed["supplements"] == [
        {
            "same": True,
            "path": "classification",
            "excluded": [
                "crop_indicator_totals",
                "crop_indicator_union_observation_count",
                "whole_pollen_category_observation_count",
            ],
        }
    ]
    assert "Native classification context is unavailable" in observed["legacyNative"]
    assert (
        "reviewed_classification_context_renderer_unavailable"
        in observed["missingBinding"]
    )
    assert len(observed["methods"]) == 8 and observed["frozen"] is True
