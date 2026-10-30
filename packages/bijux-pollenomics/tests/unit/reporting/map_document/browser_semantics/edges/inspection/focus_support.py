"""Published relation fixtures and actual asynchronous drawer harness."""

from __future__ import annotations

import json
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.template import (
    SOURCE_RECORD_EXPORT_CONTROLLER,
)

from .....atlas.static_assets.fixtures.scientific_evidence import (
    build_scientific_point_layers,
)
from ...support import run_node_json, template_block
from ..test_scientific_edges import normalize_edges
from .test_edge_popup import projected_edge
from .test_relation_details import relation


@pytest.fixture(scope="module")
def published(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    edge = normalize_edges([projected_edge()])[0]
    manual = normalize_edges([relation()])[0]
    layers = [dict(row) for row in build_scientific_point_layers()[:1]]
    features = cast(list[dict[str, Any]], layers[0]["features"])[:2]
    for row, key in zip(
        features, ("source_record_id", "target_record_id"), strict=True
    ):
        row["record_id"] = edge[key]
        row["scientific_signal_ids"] = [edge["signal_id"]]
    layers[0]["features"] = features
    assets = write_static_atlas_assets(
        tmp_path_factory.mktemp("published-edge"),
        slug="relation",
        version="relation-link",
        point_layers=layers,
        polygon_layers=[],
        edge_records=[edge, manual],
        scientific_signals=[
            {
                "signal_id": edge["signal_id"],
                "feature_key": edge["feature_key"],
                "resolution": "taxon",
                "label": "Native fixture",
                "status": "accepted",
            }
        ],
    )
    return {
        "edge": edge,
        "manual": manual,
        "manifest": assets.manifest,
        "features": features,
    }


def browser(published: dict[str, Any], action: str) -> dict[str, Any]:
    script = (
        SOURCE_RECORD_EXPORT_CONTROLLER
        + template_block("function escapeHtml", "function normalizedMediaLinks")
        + template_block("function detailTableShape", "function renderFocusCard")
        + template_block(
            "function atlasCountryPairKey", "function atlasFilterStateSnapshot"
        )
        + template_block(
            "function scientificSignalById", "function renderPolygonLayers"
        )
        + template_block("function setFocusState", "function restoreFocusFromCard")
        + template_block(
            "function renderFocusCard", "async function focusPointAtVisibleIndex"
        ).replace("function renderFocusCard", "function renderActualFocusCard", 1)
        + template_block("function parseHashState", "function normalizedSetFromList")
        + template_block("function syncHashState()", "function clearHighlightedPoint")
        + template_block(
            "function renderSelectionEmptyStatePanel", "function renderLoadedMapState"
        )
        + template_block(
            "function visibleGovernedEdges", "function isRetainedNeighborContext"
        )
        + template_block(
            "async function restoreDefaults()", "        stopTimePlayback();"
        )
        + "}\n"
        + "const supplied="
        + json.dumps(published)
        + ";"
        + r"""
const original=JSON.stringify(supplied), STATIC_ATLAS_BOOTSTRAP=supplied.manifest;
let GOVERNED_EDGE_RECORDS=[supplied.edge];
const STATIC_ATLAS_INLINE=false,STATIC_ATLAS_CHUNKS={edges:{status:'available'}};
const SCIENTIFIC_SIGNALS=[{signal_id:supplied.edge.signal_id,label:'Native fixture',non_color_cue:'circle'}];
let visiblePointEntries=supplied.features.map(feature=>({layer:{key:'points'},feature}));
let scientificPinValues=[];
function resetScientificPins(){scientificPinValues=[]}
const COUNTRIES=['Norway','Sweden'],DEFAULT_LAYER_KEYS=['points'],DEFAULT_SCIENTIFIC_SIGNAL_IDS=[supplied.edge.signal_id];
const activeCountries=new Set(['Norway']),activeScientificSignalIds=new Set(DEFAULT_SCIENTIFIC_SIGNAL_IDS);
let activeLayerKeys=new Set(DEFAULT_LAYER_KEYS),activeCountryPair='all',crossBorderOnly=true;
let activeEvidenceDisplay=resetEvidenceDisplay();
const activeAnimalSpecies='all',activeAnimalScope='all',activeAnimalConfidence='all',activeAnimalTemporalWindow='all',animalNordicOnly=false;
const activeSourceChronologyLevel='none',sourceRecordConcentrationActive=false;
function sourceChronologyLayerForLevel(){return null}
const slider={value:0},densityOpacity=.6,currentBasemap='none',DEFAULT_BASEMAP='none';
const sidebar={classList:{contains(){return false}}},legendCollapsed=true,nativeLraController=null;
const TIME_HAS_DATA=false,signedNativeTime=null,modeledContextActive=false;
function currentModeledContextWindow(){return null}function defaultPanelCollapsed(){return false}
const DETAIL_TAB_DEFINITIONS=[['overview','Overview'],['relation','Relation'],['provenance','Provenance']];
let savedHash='',pendingEdgeFocus=null,focusState=null,activeFocusTab='overview',focusCardReturnFocus=null,mobilePanelReturnFocus=null;
const atlasURLState={canPublish(){return true},publish(hash){savedHash=hash}};
const focusCard={hidden:true,contains(){return false}},focusTabs={contains(){return false},querySelectorAll(){return []},querySelector(){return {focus(){}}}},detailTablePages=new Map();
const DETAIL_TABLE_PAGE_SIZE=25;
const focusDetail={dataset:{},contains(){return false},setAttribute(key,value){this[key]=value},querySelectorAll(){return []}},focusSourceLink={},focusPreviousButton={},focusNextButton={},focusExportButton={},focusExportStatus={};
let copyAction,copies=0;const focusCopyLinkButton={disabled:false,addEventListener(type,callback){copyAction=callback}};
const navigator={clipboard:{async writeText(){copies++}}};
const topbarSearch={contains(){return false}},searchToggleButton={};
function setPanelCollapsed(){}function setLegendCollapsed(){}function setSearchOpen(){}
function highlightPointEntry(){}function visiblePointEntryForFocus(){return null}function clearHighlightedPoint(){}
function renderFocusCard(){focusCard.hidden=!focusState}
let staticAtlasLoadGeneration=0;const ALL_LAYERS=[],selectionReadout={dataset:{}};
const topbarStatePill={textContent:'',setAttribute(key,value){this[key]=value}};
const mapElement={setAttribute(key,value){this[key]=value},getAttribute(key){return this[key]}};
const emptyState={hidden:true,dataset:{},innerHTML:''};
const document={activeElement:null,getElementById(id){return id==='map'?mapElement:{focus(){}}}};
const renderedEdgeLayers=[],callbacks=[],map={};
const L={polyline(){const events={};callbacks.push(events);return {bindPopup(){},on(key,callback){events[key]=callback},addTo(){}}}};
const window={location:{hash:''}};
function featureCoordinatePair(row){return row}function scientificCueGlyph(cue){return cue}
function unavailableDetailTabs(reason){return {overview:{reason_code:reason}}}
let loads=0,release=null,delayed=false;const releases=[];
async function detailTabsForRecordId(id){loads++;if(delayed)await new Promise(resolve=>{release=resolve;releases.push(resolve)});return {overview:{record_id:id},relation:{retained:'original'},provenance:{status:'available'}}}
let delaySelection=false;const selections=[];
async function ensureStaticAtlasSelectionLoaded(){if(delaySelection)await new Promise(resolve=>selections.push(resolve));return []}function renderLoadedMapState(){syncHashState()}
function hash(){const p=new URLSearchParams();writeEdgeFocusHash(p,focusState,activeFocusTab,publishedEdgeFocusBuild());return p}
function request(){return edgeFocusFromHash(new URLSearchParams({focus_edge:supplied.edge.edge_id,focus_scenario:supplied.edge.scenario_id,focus_build:STATIC_ATLAS_BOOTSTRAP.build_id,focus_tab:'relation'}),DETAIL_TAB_DEFINITIONS.map(row=>row[0]))}
(async()=>{
"""
        + action
        + "\n})().catch(error=>{console.error(error);process.exit(1)});"
    ).replace("__INITIAL_DIAMETER__", "0")
    return cast(dict[str, Any], run_node_json(script))
