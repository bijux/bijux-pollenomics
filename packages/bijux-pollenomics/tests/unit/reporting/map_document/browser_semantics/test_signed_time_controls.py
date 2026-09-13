from __future__ import annotations

from bijux_pollenomics.reporting.map_document.template import NATIVE_LRA_CONTROLLER

from .support import run_node_json


def test_signed_endpoint_state_preserves_fractions_points_and_url_identity() -> None:
    observed = run_node_json(
        NATIVE_LRA_CONTROLLER
        + """
const sha='a'.repeat(64), extent=[-1, Number.MAX_SAFE_INTEGER-1];
const selected=[-.5,Number.MAX_SAFE_INTEGER-1];
const state=createSignedNativeTimeState(extent,sha);
state.set(selected);
const params=new URLSearchParams();state.write(params);
const restored=createSignedNativeTimeState(extent,sha);restored.restore(new URLSearchParams(params.toString()));
const exact=restored.window();state.set([0,0]);const point=state.window();
const refused=[];
for (const window of [[null,0],[false,0],['-.5',0],[1,0],[-Infinity,0],[-(2**53),0]]) {
  try {state.set(window);refused.push(false)}catch(error){refused.push(true)}
}
const forgeries=[];
for (const kind of ['duplicate','partial','axis','view','noncanonical','legacy']) {
  const bad=new URLSearchParams(params.toString());
  if(kind==='duplicate')bad.append('calendar_younger','-.5');
  if(kind==='partial')bad.delete('calendar_older');
  if(kind==='axis')bad.set('calendar_profile','radiocarbon');
  if(kind==='view')bad.set('calendar_view','b'.repeat(64));
  if(kind==='noncanonical')bad.set('calendar_younger','-0.50');
  if(kind==='legacy')bad.set('time_start','0');
  try {restored.restore(bad);forgeries.push(false)}catch(error){forgeries.push(true)}
}
console.log(JSON.stringify({exact,point,refused,forgeries,unchanged:state.window()}));
"""
    )
    assert observed == {
        "exact": [-0.5, 2**53 - 2],
        "point": [0, 0],
        "refused": [True] * 6,
        "forgeries": [True] * 6,
        "unchanged": [0, 0],
    }


def test_rejected_calendar_edit_restores_visible_applied_bounds_and_export() -> None:
    import json

    from ..lra_products.signed_support import signed_fixture

    view, _ = signed_fixture()
    observed = run_node_json(
        NATIVE_LRA_CONTROLLER
        + """
class Element {
 constructor(){this.children=[];this.listeners={};this.value='';this.textContent='';this.customValidity='';this.disabled=false;}
 append(...items){this.children.push(...items);for(const item of items)if(item.id)nodes.set(item.id,item);}
 prepend(...items){this.append(...items);}
 setAttribute(key,value){this[key]=value;}
 addEventListener(key,callback){this.listeners[key]=callback;}
 setCustomValidity(value){this.customValidity=value;}
 get valueAsNumber(){return this.value===''?NaN:Number(this.value);}
 querySelector(key){this.queries??=new Map();if(!this.queries.has(key))this.queries.set(key,new Element());return this.queries.get(key);}
 querySelectorAll(){return [];}
}
const nodes=new Map(['time-controls','time-step-older','time-step-newer','time-playback-toggle','dock-time-summary','time-stepper-status','lra-download'].map(id=>[id,new Element()]));
const document={getElementById:id=>nodes.get(id)||null,createElement:()=>new Element()};
(async()=>{
const view=VIEW;
const state=createSignedNativeTimeState([-50.75,-49.25],'e'.repeat(64));let changes=0;
const controller=createNativeLraController(view,'e'.repeat(64),{
 globalContext:()=>({time_window_bp:state.window(),active_layer_keys:['layer-r','layer-l'],temporal_profile:view.temporal_profile,temporal_axis:view.temporal_axis}),
 changed:()=>{},sha256:async bytes=>require('crypto').createHash('sha256').update(bytes).digest('hex')});
mountSignedNativeTimeControls(state,()=>{changes++;});
const younger=nodes.get('calendar-younger-input'),older=nodes.get('calendar-older-input');
const before=await controller.exportSelection();const refused=[];
for(const values of [['-48.25','-48.25'],['','-50'],['-49.5','-50.5'],['NaN','0']]){
 younger.value=values[0];older.value=values[1];older.listeners.change();
 const exported=await controller.exportSelection();
 refused.push({visible:[younger.valueAsNumber,older.valueAsNumber],window:exported.payload.global_context.time_window_bp,
 hash_unchanged:exported.sha256===before.sha256,validity:[younger.customValidity,older.customValidity],
 message:nodes.get('calendar-window-error').textContent,callbacks:changes});
}
younger.value='-50.5';older.value='-50';older.listeners.change();
const valid=await controller.exportSelection();
console.log(JSON.stringify({refused,valid:{visible:[younger.valueAsNumber,older.valueAsNumber],window:valid.payload.global_context.time_window_bp,
 hash_changed:valid.sha256!==before.sha256,message:nodes.get('calendar-window-error').textContent,callbacks:changes}}));
})().catch(error=>{console.error(error);process.exitCode=1});
""".replace("VIEW", json.dumps(view))
    )
    for refusal in observed["refused"]:
        assert refusal["visible"] == refusal["window"] == [-50.75, -49.25]
        assert refusal["hash_unchanged"] is True
        assert refusal["validity"] == ["", ""]
        assert refusal["message"].startswith("Edit not applied.")
        assert refusal["callbacks"] == 0
    assert observed["valid"] == {
        "visible": [-50.5, -50],
        "window": [-50.5, -50],
        "hash_changed": True,
        "message": "",
        "callbacks": 1,
    }
