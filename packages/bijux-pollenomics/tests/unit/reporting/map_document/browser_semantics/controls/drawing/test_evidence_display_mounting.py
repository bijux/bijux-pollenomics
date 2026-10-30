"""Actual map renderers change drawing while retaining endpoint evidence."""

from __future__ import annotations

import json
from typing import Any, cast

import pytest

from ...edges.inspection.test_edge_popup import projected_edge
from ...edges.test_scientific_edges import normalize_edges
from ...support import run_node_json, template_block


def mounted(
    query: str = "",
    *,
    concentration: bool = False,
    missing: bool = False,
    action: str = "",
) -> dict[str, Any]:
    edge: dict[str, Any] = dict(normalize_edges([projected_edge()])[0])
    features = [
        {
            "record_id": edge[f"{side}_record_id"],
            "node_id": side + "-source-node",
            "country": edge[f"{side}_country"],
            "latitude": edge[f"{side}_event"]["latitude"],
            "longitude": edge[f"{side}_event"]["longitude"],
            "time_start_bp": 0,
            "time_end_bp": 100,
            "observation_denominator": count,
        }
        for side, count in (("source", 2), ("target", 3))
    ]
    payload = {
        "edges": [edge],
        "features": features,
        "concentration": concentration,
        "missing": missing,
        "query": query,
    }
    source = (
        "const payload="
        + json.dumps(payload)
        + ";const original=JSON.stringify(payload);"
        + template_block("function escapeHtml", "function normalizedMediaLinks")
        + template_block(
            "function atlasCountryPairKey", "function atlasFilterStateSnapshot"
        )
        + template_block(
            "function isRetainedNeighborContext", "function renderRelationControls"
        )
        + template_block(
            "function sourceRecordConcentrationFailure", "let activeCountries"
        )
        + template_block(
            "function scientificSignalsForFeature", "function pointFeatureVisible"
        )
        + template_block(
            "function pointFeatureVisible", "function polygonFeatureVisible"
        )
        + template_block("function createClusterGroup", "function renderPolygonLayers")
        + r"""
let activeEvidenceDisplay=evidenceDisplayFromHash(new URLSearchParams(payload.query));
const records=payload.edges,activeCountries=new Set(['Sweden']);
const retainedNeighborRecordCountries=atlasRetainedNeighborRecordCountries(records,activeCountries);
const sourceLayer={key:'source',semantic_role:payload.concentration?'source_chronology_context':'pollen',
  group:'pollen',node_level:'source_sample_presence',applies_country_filter:true,
  circle_enabled:true,style:{stroke:'#112233',fill:'#445566',circleStroke:'#000000',circleFill:'#aaaaaa'},
  facet_metadata:{node_count:2,observation_denominator:5},features:payload.features};
const POINT_LAYERS=[sourceLayer],activeLayerKeys=new Set(['source']);
const SCIENTIFIC_SIGNALS=[],activeScientificSignalIds=new Set();
const STATIC_ATLAS_INLINE=false,STATIC_ATLAS_CHUNKS={edges:{status:'available'}};
const activeSourceChronologyLevel='source_sample_presence',activeSourceChronologyCode='all',activeSourceChronologyTaxon='all',activeSourceChronologyPreset='none';
const timeStartBp=0;function timeWindowEndBp(){return 100}
const sourceRecordConcentrationActive=payload.concentration,SOURCE_CHRONOLOGY_LEVEL_LABELS={source_sample_presence:'Source sample presence'};
let sourceRecordConcentrationSnapshot=null;
function sourceChronologyLayers(){return [sourceLayer]}
function sourceChronologyLayerForLevel(){return sourceLayer}
function sourceChronologyLayerIsValid(layer){return layer===sourceLayer}
function sourceChronologyFacetForSelection(){return sourceLayer.facet_metadata}
function sourceChronologyFeatureMatches(){return true}
function sourceChronologyCount(value){return Number.isSafeInteger(value)&&value>=0?value:null}
function featureCoordinatePair(row){return {latitude:row.latitude,longitude:row.longitude}}
function featureTimeWindow(row){return {start:row.time_start_bp,end:row.time_end_bp}}
function pointFeatureInTimeWindow(layer,row){return !payload.missing||row.record_id!==records[0].target_record_id}
function animalSourceChronologyCountryFilterBypassed(){return false}
function featureMatchesAnimalFilters(){return true}
function featureMatchesScientificSelection(){return true}
function visibleGovernedEdges(){return records}
function popupHtml(){return ''}
function focusPointAtVisibleIndex(){}
const nativeLraController=null,slider={value:10};
let visiblePointEntries=[],renderedPointGroups=[],renderedEdgeLayers=[],groupsMounted=[],edgesMounted=[],circleLayers=[],styles=[],tooltips=[];
const map={_loaded:true,getZoom(){return 8},getSize(){return {x:100,y:100}},latLngToContainerPoint([y,x]){return {x,y}},getBounds(){return {contains(){return true}}}};
function group(){const layers=[];return {addLayer(value){layers.push(value)},getLayers(){return layers},addTo(){groupsMounted.push(this)}}}
function marker(){return {bindPopup(){},on(){},setStyle(style){styles.push(style)},setOpacity(){},bindTooltip(text){tooltips.push(text)}}}
const L={markerClusterGroup:group,layerGroup:group,circleMarker:marker,marker,
 divIcon(value){return value},circle(position,options){return {position,options}},
 polyline(){return {bindPopup(){},on(){},addTo(){edgesMounted.push(this)}}}};
const circleLayerGroup={addLayer(value){circleLayers.push(value)}};
const mapElement={dataset:{}},displayControl={innerHTML:'',querySelector(){return {addEventListener(type,handler){changeHandler=handler}}}};
let changeHandler=null,changes=0;
const document={getElementById(id){if(id==='map')return mapElement;if(id==='evidence-display-controls')return displayControl;throw Error(id)}};
const topbarStatePill={textContent:'',setAttribute(key,value){this[key]=value}};
function renderMapState(){changes++}
function render(){
 visiblePointEntries=[];renderedPointGroups=[];renderedEdgeLayers=[];groupsMounted=[];edgesMounted=[];circleLayers=[];styles=[];tooltips=[];
 renderPointLayers();renderEdgeLayers();renderEvidenceDisplayPanel();
 return {entries:visiblePointEntries.map(({feature,neighborContext})=>({record:feature.record_id,neighbor:neighborContext===true})),
  groups:groupsMounted.length,edges:edgesMounted.length,circles:circleLayers.map(row=>row.options.radius),
  retained:visibleGovernedEdges().map(row=>row.edge_id),eligibility:{...edgeRenderSummary},metadata:evidenceDisplayMetadata(activeEvidenceDisplay),
  snapshot:sourceRecordConcentrationSnapshot,labels:[...tooltips],styles:[...styles],map:{...mapElement.dataset},message:topbarStatePill.textContent,role:topbarStatePill.role};
}
const result=render();
"""
        + action
        + "console.log(JSON.stringify({result,unchanged:original===JSON.stringify(payload)}));"
    )
    observed = cast(dict[str, Any], run_node_json(source))
    assert observed["unchanged"] is True
    return cast(dict[str, Any], observed["result"])


@pytest.mark.parametrize(
    ("mode", "nodes", "edges"),
    [
        ("both", True, True),
        ("nodes", True, False),
        ("edges", False, True),
        ("density", False, False),
        ("unknown", False, False),
        ("", False, False),
    ],
)
def test_actual_renderers_mount_only_requested_primitives_and_keep_evidence(
    mode: str, nodes: bool, edges: bool
) -> None:
    observed = mounted("display_mode=" + mode)
    assert observed["entries"] == [
        {"record": "source:record", "neighbor": True},
        {"record": "target:record", "neighbor": False},
    ]
    assert observed["groups"] == (2 if nodes else 0)
    assert observed["edges"] == int(edges)
    assert observed["circles"] == ([5000] if nodes else [])
    assert len(observed["retained"]) == 1
    assert observed["eligibility"] == {
        "shown": int(edges),
        "viewport_count": 1,
        "limit": 512,
    }
    assert observed["map"]["drawingEnabledPointCount"] == ("2" if nodes else "0")
    assert observed["map"]["evidenceDisplayStatus"] == (
        "available" if mode in {"both", "nodes", "edges"} else "unavailable"
    )
    assert observed["labels"] == ["Neighbor context · Norway"]
    assert observed["styles"] == [{"opacity": 0.45, "fillOpacity": 0.25}]
    if mode not in {"both", "nodes", "edges"}:
        assert observed["role"] == "alert"
        assert "unavailable" in observed["message"].lower()


@pytest.mark.parametrize("mode", ["both", "nodes", "edges", "density"])
def test_source_concentration_denominators_survive_hidden_node_groups(
    mode: str,
) -> None:
    observed = mounted("display_mode=" + mode, concentration=True)
    nodes = mode in {"both", "nodes"}
    assert observed["groups"] == int(nodes)
    assert observed["circles"] == []
    assert len(observed["entries"]) == 2 and len(observed["retained"]) == 1
    assert observed["snapshot"]["status"] == "available"
    assert observed["snapshot"]["visible_node_count"] == 2
    assert observed["snapshot"]["visible_observation_denominator"] == 5
    assert observed["snapshot"]["global_node_count"] == 2
    assert observed["snapshot"]["global_observation_denominator"] == 5


@pytest.mark.parametrize("mode", ["both", "nodes", "edges"])
def test_display_choice_cannot_restore_a_time_filtered_endpoint(mode: str) -> None:
    observed = mounted("display_mode=" + mode, missing=True)
    assert len(observed["entries"]) == 1
    assert len(observed["retained"]) == 1
    assert observed["edges"] == 0
    assert observed["eligibility"]["viewport_count"] == 0


def test_actual_control_handler_changes_drawing_without_changing_retained_membership() -> (
    None
):
    observed = mounted(
        action="""
const before=result;changeHandler({target:{value:'edges'}});const after=render();
result.before=before.entries;result.after=after;result.changes=changes;
"""
    )
    assert observed["changes"] == 1
    assert observed["after"]["groups"] == 0 and observed["after"]["edges"] == 1
    assert observed["after"]["entries"] == observed["before"]
    assert observed["after"]["retained"] == observed["retained"]


def test_display_state_is_explicit_in_real_hash_reset_capture_and_export_hooks() -> (
    None
):
    assert "evidenceDisplay: evidenceDisplayFromHash(params)" in template_block(
        "function parseHashState", "function normalizedSetFromList"
    )
    assert "writeEvidenceDisplayHash(params, activeEvidenceDisplay)" in template_block(
        "function syncHashState()", "function clearHighlightedPoint"
    )
    assert "activeEvidenceDisplay = resetEvidenceDisplay()" in template_block(
        "async function restoreDefaults", "document.getElementById('countries-all')"
    )
    for start, end in (
        ("function atlasCaptureSnapshot", "function atlasCaptureOrientationKeys"),
        ("focusExportButton.addEventListener", "focusTabs.addEventListener"),
    ):
        assert (
            "evidence_display: evidenceDisplayMetadata(activeEvidenceDisplay)"
            in template_block(start, end)
        )
    rendered = template_block(
        "function renderLoadedMapState", "const ATLAS_CAPTURE_API_VERSION"
    )
    assert rendered.index("updateStats();") < rendered.index(
        "renderEvidenceDisplayPanel();"
    )
