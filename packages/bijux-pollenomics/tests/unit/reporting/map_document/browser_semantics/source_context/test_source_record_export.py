from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.reporting.map_document.template import (
    SOURCE_RECORD_EXPORT_CONTROLLER,
    URL_STATE_CONTROLLER,
)

from ...evidence_projection.neotoma_metadata.test_chronology_models import (
    materialized,
    native_source,
)
from ..chronology.test_age_depth_diagram import diagram_script
from ..support import run_node_json, template_block


def source_export_script() -> str:
    """Exercise the real export factory with its maintained drawer bindings."""
    return (
        SOURCE_RECORD_EXPORT_CONTROLLER
        + """
function buildSourcePollenRecordExport(focus,selection,decodeRow) {
 return createSourceRecordExport({tableAvailable:sourcePollenTableAvailable,
   exportAvailable:sourcePollenExportAvailable,decodeRow})(focus,selection);
}
"""
    )


@pytest.mark.parametrize("load_result", ["available", "refused", "selection_hidden"])
def test_download_waits_for_actual_lazy_factory_or_reports_load_failure(
    tmp_path: Path,
    load_result: str,
) -> None:
    tabs, _ = materialized(tmp_path, native_source())
    handler = template_block(
        "focusExportButton.addEventListener", "focusTabs.addEventListener"
    )
    observed = run_node_json(
        diagram_script()
        + source_export_script()
        + "const tabs="
        + json.dumps(tabs)
        + ";const loadResult="
        + json.dumps(load_result)
        + """;
const focusState={kind:'point',recordId:'neotoma:site:20',detailTabs:tabs};
const focusCard={hidden:false},focusExportStatus={textContent:''};
let callback,resolveLoad,rejectLoad,loadCalls=0,clicks=0;
const blobs=[],focusExportButton={addEventListener(name,handler){callback=handler}};
const window={location:{href:'https://atlas.example/#focus_record=neotoma%3Asite%3A20'},setTimeout(){}};
const document={createElement(){return {click(){clicks++}}}};
URL.createObjectURL=blob=>{blobs.push(blob);return 'blob:source'};
function syncHashState(){}
const STATIC_ATLAS_BOOTSTRAP={build_id:'retained'},activeCountries=new Set(['Sweden']),activeLayerKeys=new Set(['neotoma-pollen']),activeScientificSignalIds=new Set();
const GOVERNED_EDGE_RECORDS=[],activeRelationFilters={},activeRelationEventDefinition={},activeEvidenceDisplay={},TIME_HAS_DATA=false,activeFocusTab='chronology',currentBasemap='none';
function relationFilterMetadata(){return {}} function relationEventDefinitionMetadata(){return {}}
function scientificPickerMetadata(){return {}} function evidenceDisplayMetadata(){return {}}
function loadEvidenceTools(){loadCalls++;return new Promise((resolve,reject)=>{resolveLoad=resolve;rejectLoad=reject})}
"""
        + handler
        + """
(async()=>{
 const completion=callback();await Promise.resolve();
 const before={loadCalls,downloads:blobs.length};
 if(!loadCalls){console.log(JSON.stringify({before}));return}
 if(loadResult==='refused')rejectLoad(Error('Retained evidence tools could not load'));
 else {
   if(loadResult==='selection_hidden')focusCard.hidden=true;
   resolveLoad({sourceExport:createSourceRecordExport});
 }
 await completion;
 const payload=blobs.length?JSON.parse(await blobs[0].text()):null;
 console.log(JSON.stringify({before,clicks,status:focusExportStatus.textContent,
   models:payload?.source_chronology_models.record_count??null,
   controls:payload?.source_chronology_controls.record_count??null}));
})();
"""
    )
    assert observed["before"] == {"loadCalls": 1, "downloads": 0}
    if load_result in {"refused", "selection_hidden"}:
        assert observed == {
            "before": {"loadCalls": 1, "downloads": 0},
            "clicks": 0,
            "status": (
                "Retained evidence tools could not load"
                if load_result == "refused"
                else "The selected record changed while export tools were loading. Select it again to download."
            ),
            "models": None,
            "controls": None,
        }
    else:
        assert observed["clicks"] == 1
        assert observed["models"] == 2
        assert observed["controls"] == 2
        assert "Download requested" in observed["status"]
        assert "downloaded" not in observed["status"]


def test_download_preserves_native_chronology_models_controls_and_locators(
    tmp_path: Path,
) -> None:
    tabs, _ = materialized(tmp_path, native_source())
    observed = run_node_json(
        diagram_script()
        + source_export_script()
        + "const tabs="
        + json.dumps(tabs)
        + """;
const original=JSON.stringify(tabs);
const payload=buildSourcePollenRecordExport({kind:'point',recordId:'neotoma:site:20',detailTabs:tabs},{},decodeDetailTableRow);
console.log(JSON.stringify({models:payload.source_chronology_models,controls:payload.source_chronology_controls,posture:payload.temporal_support.model_metadata_posture,unchanged:original===JSON.stringify(tabs)}));
"""
    )
    assert observed["unchanged"] is True
    assert observed["models"]["record_count"] == 2
    first, second = observed["models"]["records"]
    assert first["chronology_id"] == "neotoma:chronology:301:7001"
    assert first["selected_by_collection_unit_reference"] is True
    assert first["source_is_default_assertion"] is False
    assert second["selected_by_collection_unit_reference"] is False
    assert second["source_is_default_assertion"] is True
    assert observed["controls"]["record_count"] == 2
    control = observed["controls"]["records"][0]
    assert control["chronology_id"] == first["chronology_id"]
    assert control["source_payload"]["chroncontrolage"] == 0
    assert control["source_payload"]["ageunits"] is None
    assert control["source_payload"]["depthunits"] == "mm"
    assert observed["models"]["source_locator_contract"] == (
        "surfaces/chronologies/part-{source_part_number:05d}.json#chronology_id={chronology_id}"
    )
    assert observed["controls"]["source_locator_contract"] == (
        "surfaces/chronology_controls/part-{source_part_number:05d}.json#chronology_control_id={chronology_control_id}"
    )
    assert "neither selects an analysis chronology" in observed["posture"]


@pytest.mark.parametrize("state", ["missing", "unavailable", "empty"])
def test_download_distinguishes_missing_model_surface_from_retained_empty(
    state: str,
) -> None:
    observed = run_node_json(
        source_export_script()
        + "const state="
        + json.dumps(state)
        + """;
const table=(fields,records)=>({fields,records,record_count:records.length});
const family=state==='missing'?'sead':'neotoma';
const tabs={overview:{source_family:family},samples:{samples:table(['sample_id'],[])},chronology:table(['comparability_status'],[]),pollen_composition:table(['sample_id','source_value','source_unit'],[]),provenance:{build_id:'retained'}};
for(const [key,surface] of [['models','chronologies'],['controls','chronology_controls']]) {
 if(state==='empty')tabs.chronology[key]=table(['source_payload'],[]);
 if(state==='unavailable')tabs.chronology[key]={status:'unavailable',reason_code:`neotoma_${surface}_surface_not_available`};
}
const payload=buildSourcePollenRecordExport({kind:'point',recordId:`${family}:site:20`,detailTabs:tabs},{},(table,row)=>row);
console.log(JSON.stringify({record:payload.record_id,models:payload.source_chronology_models,controls:payload.source_chronology_controls}));
"""
    )
    if state == "empty":
        assert observed == {
            "record": "neotoma:site:20",
            "models": {"record_count": 0, "records": []},
            "controls": {"record_count": 0, "records": []},
        }
    else:
        prefix = "source" if state == "missing" else "neotoma"
        assert observed == {
            "record": "sead:site:20" if state == "missing" else "neotoma:site:20",
            "models": {
                "status": "unavailable",
                "reason_code": f"{prefix}_chronologies_surface_not_available",
            },
            "controls": {
                "status": "unavailable",
                "reason_code": f"{prefix}_chronology_controls_surface_not_available",
            },
        }


def test_source_export_preserves_zero_null_units_and_all_chronology_statuses() -> None:
    observed = run_node_json(
        source_export_script()
        + """
const table=(fields,records)=>({fields,records,record_count:records.length});
const focus={kind:'point',recordId:'neotoma:site:12',layerKey:'neotoma-pollen',featureKey:'evidence:12',title:'Ageröds Mosse',detailTabs:{
  samples:{samples:table(['sample_id','depth'],[['sample:1',0],['sample:2',null]])},
  chronology:table(['sample_id','comparability_status','younger_bp','refusal_reason'],[['sample:1','comparable',0,null],['sample:2','context_only',null,null],['sample:2','refused',null,'negative_bp']]),
  pollen_composition:table(['sample_id','source_value','source_unit','source_denominator'],[['sample:1',0,'NISP',null],['sample:2',null,'NISP digitized',null]]),
  provenance:{source_snapshot_id:'snapshot',record_locator:'surfaces/sites#site_id=neotoma:site:12'},
}};
const original=JSON.stringify(focus);
const selection={shared_url:'http://localhost/#focus_record=neotoma%3Asite%3A12',map_window_bp:[0,100]};
const decoded=(table,row)=>Object.fromEntries(table.fields.map((field,index)=>[field,row[index]]));
const payload=buildSourcePollenRecordExport(focus,selection,decoded);
console.log(JSON.stringify({
 observations:payload.pollen_observations.records,
 statuses:payload.chronology_claims.records.map(row=>row.comparability_status),
 support:payload.temporal_support,
 scope:payload.record_scope,
 filename:sourcePollenRecordFilename('neotoma:site:12'),
 unchanged:JSON.stringify(focus)===original,
}));
"""
    )
    assert observed == {
        "observations": [
            {
                "sample_id": "sample:1",
                "source_value": 0,
                "source_unit": "NISP",
                "source_denominator": None,
            },
            {
                "sample_id": "sample:2",
                "source_value": None,
                "source_unit": "NISP digitized",
                "source_denominator": None,
            },
        ],
        "statuses": ["comparable", "context_only", "refused"],
        "support": {
            "chronology_scope": "all_source_claims_including_contextual_and_refused",
            "interval_semantics": None,
            "interpolation_allowed": False,
            "site_range_is_continuous_support": False,
            "model_metadata_posture": None,
        },
        "scope": "complete_source_record_not_filtered_to_map_time_window",
        "filename": "neotoma-site-12.pollen-series.json",
        "unchanged": True,
    }


def test_source_export_refuses_unavailable_or_inconsistent_tables() -> None:
    observed = run_node_json(
        source_export_script()
        + """
const focus={kind:'point',recordId:'site:1',detailTabs:{
 pollen_composition:{fields:['source_value'],records:[[1]],record_count:2},
 chronology:{fields:[],records:[],record_count:0},
 samples:{samples:{fields:[],records:[],record_count:0}},provenance:{status:'unavailable'},
}};
let error;
try{buildSourcePollenRecordExport(focus,{},()=>{throw Error('decoder must not run')});}catch(observed){error=observed.message;}
console.log(JSON.stringify({ready:sourcePollenExportAvailable(focus),error}));
"""
    )
    assert observed == {
        "ready": False,
        "error": "source_pollen_record_export_unavailable",
    }


def test_record_url_preserves_exact_identity_and_refuses_partial_identity() -> None:
    observed = run_node_json(
        source_export_script()
        + """
const identity={kind:'point',layerKey:'neotoma-source-sample-pollen-context',featureKey:'node:source-chronology-node:exact',recordId:'neotoma:site:12'};
const params=new URLSearchParams();
writeSourceRecordFocusHash(params,identity,'chronology');
console.log(JSON.stringify({
 restored:sourceRecordFocusFromHash(new URLSearchParams(params.toString()),['overview','chronology']),
 partial:sourceRecordFocusFromHash(new URLSearchParams('focus_record=neotoma%3Asite%3A12'),['overview']),
 unknownTab:sourceRecordFocusFromHash(new URLSearchParams(params.toString()),['overview']).tab,
}));
"""
    )
    assert observed == {
        "restored": {
            "kind": "point",
            "layerKey": "neotoma-source-sample-pollen-context",
            "featureKey": "node:source-chronology-node:exact",
            "recordId": "neotoma:site:12",
            "tab": "chronology",
        },
        "partial": None,
        "unknownTab": "overview",
    }


def test_source_export_refuses_generic_composition_without_literal_source_fields() -> (
    None
):
    observed = run_node_json(
        source_export_script()
        + """
const table=(fields,records)=>({fields,records,record_count:records.length});
const focus={kind:'point',recordId:'model:1',detailTabs:{
 samples:{samples:table(['sample_id'],[['sample:1']])},
 chronology:table(['comparability_status'],[['comparable']]),
 pollen_composition:table(['value','unit'],[[1,'model fraction']]),
 provenance:{build_id:'model-build'},
}};
console.log(JSON.stringify({ready:sourcePollenExportAvailable(focus)}));
"""
    )
    assert observed == {"ready": False}


def test_url_replay_keeps_internal_publication_in_document() -> None:
    observed = run_node_json(
        URL_STATE_CONTROLLER
        + """
let url='https://atlas.example/index.html?scope=nordic#basemap=none',replays=0;
const published=[];
const controller=createAtlasURLStateController({readURL:()=>url,publishURL:next=>{url=next;published.push(next);},replayURL:()=>replays++});
controller.publish('countries=Denmark&focus_record=site%3A1');
controller.observe();
controller.publish('countries=Finland');
console.log(JSON.stringify({url,published:published.length,replays,canPublish:controller.canPublish()}));
"""
    )
    assert observed == {
        "url": "https://atlas.example/index.html?scope=nordic#countries=Finland",
        "published": 2,
        "replays": 0,
        "canPublish": True,
    }


def test_url_replay_preserves_complete_external_url_against_stale_writers() -> None:
    observed = run_node_json(
        URL_STATE_CONTROLLER
        + """
let url='https://atlas.example/index.html#countries=Sweden',replays=0;
const published=[];
const controller=createAtlasURLStateController({readURL:()=>url,publishURL:next=>{url=next;published.push(next);},replayURL:()=>replays++});
url='https://atlas.example/index.html?scope=nordic#countries=Norway&focus_record=site%3A2&time_start=0&native_view_sha256=exact';
const incoming=url;
const stalePublish=controller.publish('countries=Sweden');
controller.observe();controller.observe();controller.publish('');
console.log(JSON.stringify({incomingPreserved:url===incoming,replays,published:published.length,stalePublish,canPublish:controller.canPublish()}));
"""
    )
    assert observed == {
        "incomingPreserved": True,
        "replays": 1,
        "published": 0,
        "stalePublish": False,
        "canPublish": False,
    }


def test_url_replay_duplicate_history_events_and_latest_navigation_reload_once() -> (
    None
):
    observed = run_node_json(
        URL_STATE_CONTROLLER
        + """
let url='https://atlas.example/#countries=Sweden',replays=0;
const controller=createAtlasURLStateController({readURL:()=>url,publishURL:next=>url=next,replayURL:()=>replays++});
url='https://atlas.example/#countries=Denmark';controller.observe();
url='https://atlas.example/#countries=Finland';controller.observe();controller.publish('countries=Sweden');
const replay=createAtlasURLStateController({readURL:()=>url,publishURL:next=>url=next,replayURL:()=>replays++});
replay.observe();replay.publish('countries=Finland');
console.log(JSON.stringify({url,replays,canPublish:replay.canPublish()}));
"""
    )
    assert observed == {
        "url": "https://atlas.example/#countries=Finland",
        "replays": 1,
        "canPublish": True,
    }
