"""Shared point URLs restore only against the settled, authoritative selection."""

from __future__ import annotations

from typing import Any, cast

from bijux_pollenomics.reporting.map_document.template import (
    MAP_DOCUMENT_TEMPLATE,
    SOURCE_RECORD_EXPORT_CONTROLLER,
    URL_STATE_CONTROLLER,
)

from .edges.inspection.focus_support import browser
from .edges.inspection.focus_support import published as published
from .support import run_node_json, template_block


def point_replay(action: str) -> dict[str, Any]:
    """Run real render, point focus and URL functions with controlled I/O promises."""
    start = MAP_DOCUMENT_TEMPLATE.rindex("      await renderMapState();")
    end = MAP_DOCUMENT_TEMPLATE.index("      zoomReadout.textContent", start)
    startup = MAP_DOCUMENT_TEMPLATE[start:end]
    source = (
        SOURCE_RECORD_EXPORT_CONTROLLER
        + URL_STATE_CONTROLLER
        + template_block(
            "function stableFeatureRecordId", "function unavailableDetailTabs"
        )
        + template_block(
            "async function focusPointAtVisibleIndex", "function countActiveOverrides"
        )
        + template_block(
            "function syncHashState()", "function atlasSelectionHashParams"
        )
        + template_block(
            "async function renderMapState()", "function renderLoadedMapState()"
        )
        + template_block(
            "async function restoreDefaults()", "        stopTimePlayback();"
        )
        + "}\n"
        + r"""
const request=sourceRecordFocusFromHash(new URLSearchParams({focus_layer:'neotoma-pollen',
 focus_feature:'evidence:12',focus_record:'neotoma:site:12',focus_tab:'provenance'}),['overview','samples','provenance']);
const initialState={focus:request,edgeFocus:null};
let url='https://atlas.example/#'+new URLSearchParams({basemap:'none',focus_layer:request.layerKey,
 focus_feature:request.featureKey,focus_record:request.recordId,focus_tab:request.tab});
const initialURL=url,hashWrites=[],errors=[];let replays=0;
const atlasURLState=createAtlasURLStateController({readURL:()=>url,
 publishURL:value=>{url=value;hashWrites.push(value)},replayURL:()=>{replays++}});
let pendingPointFocus=request,pendingEdgeFocus=null,focusState=null,activeFocusTab='overview';
let unresolvedPointFocus=request;
let focusCardReturnFocus=null,mobilePanelReturnFocus=null,staticAtlasLoadGeneration=0;
let retainedNeighborRecordCountries=null,visiblePointEntries=[];
const edgeFocusLoadState={request:0,generation:0},detailTablePages=new Map();
const focusCard={hidden:true},focusTabs={querySelector(){return {focus(){}}}};
const topbarSearch={contains(){return false}},document={activeElement:null,getElementById(){return mapElement}};
const mapElement={setAttribute(key,value){this[key]=value}};
const topbarStatePill={textContent:'',setAttribute(key,value){this[key]=value}};
const selectionReadout={dataset:{}},STATIC_ATLAS_INLINE=true,POINT_LAYERS=[],POLYGON_LAYERS=[],ALL_LAYERS=[];
const activeCountries=new Set(['Sweden']);
const STATIC_ATLAS_BOOTSTRAP={budgets:{filter_main_thread_max_ms:50}};
const console={error:error=>errors.push(String(error))};
const entries=[12,3009].map(id=>({layer:{key:'neotoma-pollen',label:'Neotoma pollen sites'},
 feature:{record_id:`neotoma:site:${id}`,evidence_row_id:String(id),title:`Native site ${id}`,
 country:'Sweden',latitude:55,longitude:13}}));
const original=JSON.stringify(entries),nodeLoads=[],detailLoads=[],detailReleases=[];
let selectedEntries=entries,delayNodes=true,delayDetails=false;
function ensureStaticAtlasSelectionLoaded(){return delayNodes?new Promise(resolve=>nodeLoads.push(resolve)):Promise.resolve([])}
async function detailTabsForFeature(feature){
 detailLoads.push(feature.record_id);
 if(delayDetails)await new Promise(resolve=>detailReleases.push(resolve));
 return {overview:{site_id:feature.record_id},samples:{site_id:feature.record_id},provenance:{site_id:feature.record_id}};
}
function renderLoadedMapState(){visiblePointEntries=selectedEntries.map(row=>({...row,feature:{...row.feature}}));renderFocusCard();syncHashState()}
function renderFocusCard(){focusCard.hidden=!focusState||!visiblePointEntryForFocus()}
function renderFocusDetail(){syncHashState()}
function atlasSelectionHashParams(){const params=new URLSearchParams({basemap:'none'});const selected=pointFocusHashState();writeSourceRecordFocusHash(params,selected.focus,selected.tab);return params}
function featureCoordinatePair(feature){return feature}
function coordinateLabel(){return '55, 13'}
function normalizedMediaLinks(){return []}
function featureTimeDescriptor(){return null}
function setPanelCollapsed(){} function setLegendCollapsed(){} function setSearchOpen(){}
function highlightPointEntry(){} function clearHighlightedPoint(){}
function unavailableDetailTabs(reason){return {overview:{reason_code:reason},samples:{reason_code:reason},provenance:{reason_code:reason}}}
function loadEvidenceTools(){return Promise.resolve({})}
function atlasRetainedNeighborRecordCountries(){return new Map()}
function visibleGovernedEdges(){return []}
function renderSelectionEmptyStatePanel(){} function buildSearchResults(){}
async function restoreEdgeFocus(){throw Error('Point replay must not restore an edge')}
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function snapshot(){return {record:focusState?.recordId??null,tab:activeFocusTab,
 detail:focusState?.detailTabs?.provenance?.site_id??null,pending:pendingPointFocus!==null,
 hash:new URL(url).hash,urlUnchanged:url===initialURL,detailLoads:[...detailLoads],
 status:topbarStatePill.textContent,statusRole:topbarStatePill.role??null,replays,
 sourceUnchanged:JSON.stringify(entries)===original,errors:[...errors]}}
function output(value){process.stdout.write(JSON.stringify(value))}
async function startup(){
"""
        + startup
        + "}\n(async()=>{\n"
        + action
        + "\n})().catch(error=>{process.stderr.write(String(error.stack));process.exitCode=1});"
    )
    return cast(dict[str, Any], run_node_json(source))


def test_superseded_startup_retains_request_until_current_nodes_settle() -> None:
    observed = point_replay(
        """
const first=startup(),second=renderMapState();nodeLoads[0]([]);await first;
const premature=snapshot();nodeLoads[1]([]);await second;
output({premature,settled:snapshot()});
"""
    )
    assert observed["premature"]["record"] is None
    assert observed["premature"]["pending"] is True
    assert observed["premature"]["urlUnchanged"] is True
    assert observed["premature"]["detailLoads"] == []
    assert observed["settled"]["record"] == "neotoma:site:12"
    assert observed["settled"]["detail"] == "neotoma:site:12"
    assert observed["settled"]["tab"] == "provenance"
    assert observed["settled"]["pending"] is False
    assert observed["settled"]["sourceUnchanged"] is True
    assert observed["settled"]["errors"] == []


def test_latest_absent_identity_preserves_shared_url_without_alternative_focus() -> (
    None
):
    observed = point_replay(
        """
selectedEntries=[entries[1]];const running=startup();nodeLoads[0]([]);await running;output(snapshot());
"""
    )
    assert observed["record"] is None
    assert observed["pending"] is False
    assert observed["urlUnchanged"] is True
    assert observed["detailLoads"] == []
    assert "unavailable" in observed["status"].lower()
    assert observed["statusRole"] == "status"
    assert observed["errors"] == []


def test_manual_clear_supersedes_pending_source_restore() -> None:
    observed = point_replay(
        """
const running=startup();setFocusState(null);nodeLoads[0]([]);await running;output(snapshot());
"""
    )
    assert observed["record"] is None
    assert observed["pending"] is False
    assert observed["detailLoads"] == []
    assert observed["hash"] == "#basemap=none"
    assert observed["errors"] == []


def test_unavailable_identity_survives_render_until_explicit_reset() -> None:
    observed = point_replay(
        """
selectedEntries=[entries[1]];delayNodes=false;await startup();await renderMapState();
const unavailable=snapshot();await restoreDefaults();output({unavailable,reset:snapshot()});
"""
    )
    assert observed["unavailable"]["record"] is None
    assert observed["unavailable"]["urlUnchanged"] is True
    assert "unavailable" in observed["unavailable"]["status"].lower()
    assert observed["reset"]["record"] is None
    assert observed["reset"]["hash"] == "#basemap=none"
    assert observed["reset"]["errors"] == []


def test_unavailable_request_restores_when_latest_filters_admit_exact_record() -> None:
    observed = point_replay(
        """
selectedEntries=[entries[1]];delayNodes=false;await startup();
selectedEntries=entries;await renderMapState();output(snapshot());
"""
    )
    assert observed["record"] == "neotoma:site:12"
    assert observed["detail"] == "neotoma:site:12"
    assert observed["tab"] == "provenance"
    assert observed["errors"] == []


def test_external_navigation_supersedes_pending_source_restore() -> None:
    observed = point_replay(
        """
const running=startup();url='https://atlas.example/#basemap=none&focus_record=another-request';
nodeLoads[0]([]);await running;output(snapshot());
"""
    )
    assert observed["record"] is None
    assert observed["detailLoads"] == []
    assert observed["hash"] == "#basemap=none&focus_record=another-request"
    assert observed["replays"] == 1
    assert observed["errors"] == []


def test_restore_defaults_supersedes_pending_source_restore() -> None:
    observed = point_replay(
        """
const running=startup();await restoreDefaults();nodeLoads[0]([]);await running;output(snapshot());
"""
    )
    assert observed["record"] is None
    assert observed["pending"] is False
    assert observed["detailLoads"] == []
    assert observed["errors"] == []


def test_manual_relation_supersedes_pending_point_before_detail_load(
    published: dict[str, Any],
) -> None:
    observed = browser(
        published,
        """
pendingPointFocus={kind:'point',recordId:'source:pending'};delayed=true;
const loading=openEdgeDetail(supplied.edge,visiblePointEntries[0]);
const consumed=pendingPointFocus===null;release();await loading;
console.log(JSON.stringify({consumed,kind:focusState?.kind,pending:pendingPointFocus}));
""",
    )
    assert observed == {"consumed": True, "kind": "edge", "pending": None}


def test_requested_tab_precedes_detail_load_without_overwriting_manual_tab() -> None:
    observed = point_replay(
        """
delayDetails=true;const running=startup();nodeLoads[0]([]);await tick();
const loading=snapshot();activeFocusTab='samples';renderFocusDetail();detailReleases[0]();
await running;output({loading,settled:snapshot()});
"""
    )
    assert observed["loading"]["record"] == "neotoma:site:12"
    assert observed["loading"]["tab"] == "provenance"
    assert observed["settled"]["tab"] == "samples"
    assert observed["settled"]["detail"] == "neotoma:site:12"
    assert observed["settled"]["errors"] == []


def test_new_manual_record_supersedes_shared_detail_load() -> None:
    observed = point_replay(
        """
delayDetails=true;const running=startup();nodeLoads[0]([]);await tick();
const manual=focusPointAtVisibleIndex(1);detailReleases[0]();await running;
detailReleases[1]();await manual;output(snapshot());
"""
    )
    assert observed["record"] == "neotoma:site:3009"
    assert observed["detail"] == "neotoma:site:3009"
    assert observed["tab"] == "overview"
    assert observed["pending"] is False
    assert observed["errors"] == []
