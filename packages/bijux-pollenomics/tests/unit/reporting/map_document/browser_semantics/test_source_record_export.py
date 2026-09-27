from __future__ import annotations

from bijux_pollenomics.reporting.map_document.template import (
    SOURCE_RECORD_EXPORT_CONTROLLER,
)

from .support import run_node_json


def test_source_export_preserves_zero_null_units_and_all_chronology_statuses() -> None:
    observed = run_node_json(
        SOURCE_RECORD_EXPORT_CONTROLLER
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
        },
        "scope": "complete_source_record_not_filtered_to_map_time_window",
        "filename": "neotoma-site-12.pollen-series.json",
        "unchanged": True,
    }


def test_source_export_refuses_unavailable_or_inconsistent_tables() -> None:
    observed = run_node_json(
        SOURCE_RECORD_EXPORT_CONTROLLER
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
        SOURCE_RECORD_EXPORT_CONTROLLER
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
        SOURCE_RECORD_EXPORT_CONTROLLER
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
