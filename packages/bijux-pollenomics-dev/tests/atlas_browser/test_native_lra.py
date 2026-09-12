"""The native browser verdict independently reconciles values and selection."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from bijux_pollenomics_dev.ci import atlas_browser
from bijux_pollenomics_dev.ci.atlas_browser.verdict import (
    NATIVE_LRA_REQUIRED_ASSERTIONS,
)


def _module() -> str:
    return Path(atlas_browser.__file__).with_name("native-lra.mjs").as_uri()


def test_native_python_and_javascript_required_assertions_agree() -> None:
    result = subprocess.run(
        [
            "node",
            "--input-type=module",
            "--eval",
            f"import {{NATIVE_LRA_REQUIRED_ASSERTIONS as names}} from {json.dumps(_module())}; console.log(JSON.stringify(names));",
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    names = json.loads(result.stdout)
    assert len(names) == len(set(names))
    assert frozenset(names) == NATIVE_LRA_REQUIRED_ASSERTIONS


@pytest.mark.parametrize(
    "mutation",
    [
        "none",
        "digest",
        "wrong_unit",
        "zero_imputed",
        "visible_value",
        "hidden_row",
        "false_denominator",
        "false_anchor",
        "ignored_global_time",
        "forged_source_row",
        "missing_contract",
        "wrong_schema",
        "forged_provenance",
        "approved",
        "stale_selection",
        "stale_context",
        "invented_sites",
        "missing_snapshot_rows",
        "unknown_selection",
        "duplicate_selection",
        "reversed_time",
        "string_time",
        "missing_cues",
        "swapped_cue_role",
        "dom_selection",
        "wrong_view",
        "visible_taxon",
        "noncanonical_export",
    ],
)
def test_selection_challenge_detects_consistent_but_wrong_presentation(
    mutation: str,
) -> None:
    script = """
import {createHash} from 'node:crypto';
import {selectionAgreement} from MODULE;
const view={product_manifest_sha256:'a'.repeat(64),geometry_sha256:'b'.repeat(64),
request_sha256:'c'.repeat(64),scientific_content_sha256:'d'.repeat(64),data_kind:'synthetic',operation:'lra',
method:{profile:'disqover-0.9.14'},uncertainty_omissions:['chronology'],exclusions:[],rows:[
  {row_id:'a',role:'regional',site_id:'one',taxon:'pine',bin_id:'old',native_unit:'percent',native_value:'0',declared_bin:{younger_bp:5,older_bp:10}},
  {row_id:'b',role:'local',site_id:'two',taxon:'pine',bin_id:'old',native_unit:'fraction',native_value:null,declared_bin:{younger_bp:5,older_bp:10}},
],sites:[
  {role:'regional',site_id:'one',map_status:'synthetic_anchor',anchor_id:'anchor',layer_key:'regional',model_row_ids:['a']},
  {role:'local',site_id:'two',map_status:'refused',model_row_ids:['b']},
]};
const observation={snapshot:{
  view_sha256:'e'.repeat(64),product_manifest_sha256:view.product_manifest_sha256,geometry_sha256:view.geometry_sha256,
  selection:{roles:['local','regional'],site_ids:['one','two'],taxa:['pine'],bin_ids:['old']},
  global_context:{active_layer_keys:['regional'],time_window_bp:[5,10]},
  selected_row_ids:['a','b'],mapped_anchor_ids:['anchor'],
  counts:{selected_rows:2,mapped_anchors:1,refused_sites:1,missing_values:1},
  rows:structuredClone(view.rows),sites:structuredClone(view.sites),refusal:null,
  temporal_refusal_policy:'geometry-refused rows retained; global map time/layers apply only to admitted anchors',
},exported:{payload:{rows:structuredClone(view.rows)}},dom:{rows:[
  {row_id:'a',value:'0',missing:'false',visible_value:'0',unit:'percent',visible_unit:'percent'},
  {row_id:'b',value:'',missing:'true',visible_value:'N/A (source statistic unavailable)',unit:'fraction',visible_unit:'fraction'},
]}};
observation.dom.selection=structuredClone(observation.snapshot.selection);
for(const row of view.rows)row.statistic='mean';
observation.snapshot.rows=structuredClone(view.rows);
for(const rendered of observation.dom.rows){
 const source=view.rows.find(row=>row.row_id===rendered.row_id);
 for(const key of ['role','site_id','taxon','statistic'])rendered[key]=source[key];
}
observation.dom.model_cues=[{anchor_id:'anchor',role:'regional',text:'R'}];
observation.exported.payload={schema_version:'lra-selected-estimates.v1',serialization:'ECMAScript JSON.stringify + LF; UTF-8',
 ...structuredClone(observation.snapshot),request_sha256:view.request_sha256,scientific_content_sha256:view.scientific_content_sha256,
 data_kind:view.data_kind,operation:view.operation,method:view.method,scientific_acceptance:'not_evaluated',publication_authorized:false,
 uncertainty_omissions:view.uncertainty_omissions,exclusions:view.exclusions};
const mutation=MUTATION;
if(mutation==='wrong_unit')observation.exported.payload.rows[0].native_unit='fraction';
if(mutation==='zero_imputed')observation.exported.payload.rows[1].native_value='0';
if(mutation==='visible_value')observation.dom.rows[0].visible_value='100';
if(mutation==='hidden_row')observation.dom.rows.pop();
if(mutation==='false_denominator')observation.snapshot.counts.refused_sites=0;
if(mutation==='false_anchor')observation.snapshot.mapped_anchor_ids=['invented'];
if(mutation==='ignored_global_time')observation.snapshot.global_context.time_window_bp=[11,20];
if(mutation==='forged_source_row')observation.exported.payload.rows[0].source_locator='forged';
if(mutation==='missing_contract')observation.exported.payload={rows:structuredClone(view.rows)};
if(mutation==='wrong_schema')observation.exported.payload.schema_version='wrong';
if(mutation==='forged_provenance')observation.exported.payload.request_sha256='f'.repeat(64);
if(mutation==='approved')observation.exported.payload.publication_authorized=true;
if(mutation==='stale_selection')observation.exported.payload.selection.taxa=[];
if(mutation==='stale_context')observation.exported.payload.global_context.time_window_bp=[0,1];
if(mutation==='invented_sites')observation.exported.payload.sites=[];
if(mutation==='missing_snapshot_rows')delete observation.snapshot.rows;
if(mutation==='unknown_selection')observation.snapshot.selection.taxa.push('unknown');
if(mutation==='duplicate_selection')observation.snapshot.selection.taxa.push('pine');
if(mutation==='reversed_time')observation.snapshot.global_context.time_window_bp=[10,5];
if(mutation==='string_time')observation.snapshot.global_context.time_window_bp=['5',10];
if(mutation==='missing_cues')observation.dom.model_cues=[];
if(mutation==='swapped_cue_role')observation.dom.model_cues[0]={anchor_id:'anchor',role:'local',text:'L'};
if(mutation==='dom_selection')observation.dom.selection.taxa=[];
if(mutation==='wrong_view')observation.snapshot.view_sha256='f'.repeat(64);
if(mutation==='visible_taxon')observation.dom.rows[0].taxon='birch';
if(['unknown_selection','duplicate_selection','reversed_time','string_time','wrong_view','false_denominator','false_anchor','ignored_global_time'].includes(mutation)){
 Object.assign(observation.exported.payload,structuredClone(observation.snapshot));
 observation.dom.selection=structuredClone(observation.snapshot.selection);
}
observation.exported.bytes=JSON.stringify(observation.exported.payload)+'\\n';
if(mutation==='noncanonical_export')observation.exported.bytes=JSON.stringify(observation.exported.payload,null,2)+'\\n';
observation.exported.sha256=createHash('sha256').update(observation.exported.bytes).digest('hex');
if(mutation==='digest')observation.exported.sha256='0'.repeat(64);
console.log(JSON.stringify(selectionAgreement(view,observation,'e'.repeat(64))));
""".replace("MODULE", json.dumps(_module())).replace("MUTATION", json.dumps(mutation))
    result = subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout) is (mutation == "none")


@pytest.mark.parametrize(
    "mutation",
    [
        "none",
        "document_scroll",
        "horizontal_scroll",
        "scroller",
        "map",
        "cropped",
        "occluded",
    ],
)
def test_layout_refuses_displaced_or_obscured_native_controls(mutation: str) -> None:
    script = """
import {layoutPasses} from MODULE;
const layout={no_horizontal_overflow:true,document_scroll_x:0,document_scroll_y:0,inside_scroller:true,map_bounded:true,
 values:[{present:true,visible:true,bounded:true,uncovered:true,labeled:true}]};
const mutation=MUTATION;
if(mutation==='document_scroll')layout.document_scroll_y=1;
if(mutation==='horizontal_scroll')layout.document_scroll_x=1;
if(mutation==='scroller')layout.inside_scroller=false;
if(mutation==='map')layout.map_bounded=false;
if(mutation==='cropped')layout.values[0].bounded=false;
if(mutation==='occluded')layout.values[0].uncovered=false;
console.log(JSON.stringify(layoutPasses(layout)));
""".replace("MODULE", json.dumps(_module())).replace("MUTATION", json.dumps(mutation))
    result = subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout) is (mutation == "none")
