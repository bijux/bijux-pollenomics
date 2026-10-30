"""Display limits preserve scientific candidates and use the map projection."""

from __future__ import annotations

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE

from ..support import run_node_json, template_block

CLIPPING_CASES = r"""
const assert = require('node:assert/strict');
const map = {getSize:()=>({x:100,y:100}),latLngToContainerPoint:([y,x])=>({x,y})};
const hit = (a,b)=>atlasEdgeIntersectsViewport(map,[a,b]);
assert.equal(hit([50,-10],[50,110]),true); // Both endpoints outside.
assert.equal(hit([-10,-10],[110,110]),true);
assert.equal(hit([-10,1],[1,-10]),false); // Bounding boxes alone would overlap.
assert.equal(hit([101,-10],[101,110]),false);
assert.equal(hit([0,-10],[0,110]),true); // Inclusive viewport boundary.
assert.equal(hit([100,100],[100,100]),true);
assert.equal(hit([101,101],[101,101]),false);
// Use the viewer's projected world offset, without inventing longitude wrapping.
const shifted = {getSize:map.getSize,latLngToContainerPoint:([y,x])=>({x:x+360,y})};
assert.equal(atlasEdgeIntersectsViewport(shifted,[[50,-370],[50,-250]]),true);
assert.equal(atlasEdgeIntersectsViewport(shifted,[[50,-250],[50,-240]]),false);
assert.throws(()=>atlasEdgeIntersectsViewport(map,[[0,NaN],[0,1]]));
console.log(JSON.stringify({passed:true}));
"""

SELECTION_CASES = r"""
const assert = require('node:assert/strict');
const edges = Array.from({length:600},(_,i)=>Object.freeze({
  edge_id:'native:'+String(i).padStart(4,'0'),source_record_id:'a',target_record_id:'b'
}));
Object.freeze(edges);
const entries = new Map([['a',{feature:{latitude:50,longitude:-10}}],['b',{feature:{latitude:50,longitude:110}}]]);
const original = JSON.stringify(edges), coords = row=>row;
const select = (rows,z)=>atlasEdgeRenderSelection(rows,entries,z,coords,null);
for(const [zoom,count] of [[0,128],[4.9,128],[5,256],[7.9,256],[8,512],[18,512]]){
  const selected=select(edges,zoom), reversed=select([...edges].reverse(),zoom);
  assert.equal(selected.rows.length,count);
  assert.equal(selected.viewport_count,600);
  assert.deepEqual(selected.rows.map(r=>r.edge.edge_id),reversed.rows.map(r=>r.edge.edge_id));
}
assert.deepEqual(select([edges[2],edges[1]],0).rows.map(r=>r.edge),[edges[2],edges[1]]);
assert.equal(atlasEdgeRenderSelection(edges,new Map(),0,coords,null).rows.length,0);
assert.equal(atlasEdgeRenderSelection(edges,entries,0,()=>null,null).rows.length,0);
assert.equal(atlasEdgeRenderSelection(edges,entries,0,coords,()=>false).viewport_count,0);
assert.throws(()=>select(edges,NaN));
assert.equal(JSON.stringify(edges),original);
assert.equal(edges.length,600);
console.log(JSON.stringify({passed:true}));
"""

RENDER_SETUP = r"""
const assert = require('node:assert/strict');
const edges=Object.freeze(Array.from({length:600},(_,i)=>Object.freeze({
  edge_id:'native:'+String(i).padStart(4,'0'),source_record_id:'a'+i,target_record_id:'b'+i,
  signal_id:'taxon:fixture',status:'possible_candidate',source_country:'Norway',target_country:'Sweden'
})));
const visiblePointEntries=edges.flatMap((edge,i)=>[
  {feature:{record_id:edge.source_record_id,latitude:i<200?50:101,longitude:-10}},
  {feature:{record_id:edge.target_record_id,latitude:i<200?50:101,longitude:110}}
]).filter(entry=>entry.feature.record_id!=='b0'); // One selected endpoint is not loaded.
const original=JSON.stringify({edges,visiblePointEntries});
const STATIC_ATLAS_INLINE=false, STATIC_ATLAS_CHUNKS={edges:{status:'available'},sequences:{status:'available'}};
const GOVERNED_SEQUENCE_RECORDS=[],GOVERNED_EDGE_ELIGIBILITY_COUNT=600,SCIENTIFIC_SIGNALS=[],COUNTRY_PAIR_KEYS=[];
const countryPairFilter={},crossBorderOnlyCheckbox={},relationSummary={dataset:{}};
const relationEventDefinitionControl={},relationEventDefinitionStatus={};
const GOVERNED_EDGE_RECORDS=edges,relationFilterStatus={},relationFilterControls=Object.fromEntries(relationFilterFields().map(([key])=>[key,{}]));
let activeEvidenceDisplay=resetEvidenceDisplay();
let crossBorderOnly=false,activeCountryPair='all',offset=0,zoom=0;
const map={_loaded:true,getZoom:()=>zoom,getSize:()=>({x:100,y:100}),latLngToContainerPoint:([y,x])=>({x:x+offset,y})};
const renderedEdgeLayers=[],captured=[];
const L={polyline(coords,opts){captured.push({coords,opts});return{bindPopup(){},on(){},addTo(){}}}};
function featureCoordinatePair(row){return row}
function visibleGovernedEdges(){return edges.slice(0,450)}
function escapeHtml(value){return String(value)}
"""

RENDER_CASES = r"""
function render(){renderedEdgeLayers.length=0;captured.length=0;renderEdgeLayers();renderRelationControls()}
render();
assert.equal(captured.length,128);
assert.equal(relationSummary.dataset.filterMatchedCandidateCount,'450');
assert.equal(relationSummary.dataset.admittedCandidateCount,'600');
assert.equal(relationSummary.dataset.viewportCandidateCount,'199');
assert.equal(relationSummary.dataset.renderedCandidateCount,'128');
assert.match(relationSummary.textContent,/450 of 600 retained rows matched by country\/signal\/relation filters/);
assert.match(relationSummary.textContent,/Showing 128 of 199 loaded display-eligible viewport candidates/);
assert.match(relationSummary.textContent,/Zoom in or narrow country and signal filters/);
zoom=8;render();assert.equal(captured.length,199);
offset=1000;render();assert.equal(captured.length,0);
assert.equal(relationSummary.dataset.filterMatchedCandidateCount,'450');
offset=0;render();assert.equal(captured.length,199);
assert.equal(JSON.stringify({edges,visiblePointEntries}),original);
console.log(JSON.stringify({passed:true}));
"""


def display_source() -> str:
    return template_block(
        "function atlasEdgeIntersectsViewport", "function renderEdgeLayers"
    )


def test_projected_segments_preserve_crossings_and_world_offsets() -> None:
    assert run_node_json(display_source() + CLIPPING_CASES) == {"passed": True}


def test_zoom_limits_are_permutation_stable_without_changing_candidates() -> None:
    assert run_node_json(display_source() + SELECTION_CASES) == {"passed": True}


def test_leaflet_primitives_and_readout_follow_viewport_and_zoom() -> None:
    source = (
        RENDER_SETUP
        + template_block(
            "function scientificSignalById", "function renderPolygonLayers"
        )
        + template_block(
            "function renderRelationControls", "function selectSourceChronologyLevel"
        )
        + RENDER_CASES
    )
    assert run_node_json(source) == {"passed": True}
    assert (
        'id="relation-summary" role="status" aria-live="polite" aria-atomic="true"'
        in MAP_DOCUMENT_TEMPLATE
    )
    summary_tag = MAP_DOCUMENT_TEMPLATE.split('id="relation-summary"', 1)[1].split(
        ">", 1
    )[0]
    assert summary_tag.count("aria-live=") == 1
    move_handler = template_block("map.on('moveend'", "map.on('mousemove'")
    assert "renderMapState();" in move_handler
