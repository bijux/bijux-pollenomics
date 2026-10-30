"""The actual selection renderer publishes only current-generation empty states."""

from __future__ import annotations

from importlib.resources import files
import json
from typing import Any, cast

import pytest

from ..support import run_node_json, template_block


def mounted(action: str, **changes: Any) -> dict[str, Any]:
    payload = {
        "pointCount": 0,
        "polygonCount": 0,
        "retainedCount": 0,
        "viewportCount": 0,
        "drawnCount": 0,
        "query": "",
        "countries": ["Sweden"],
        "layers": [{"key": "points", "scientific_selection_enabled": False}],
        "signalCount": 1,
        "selectedSignalCount": 1,
        "narrowedTime": False,
        **changes,
    }
    display = (
        files("bijux_pollenomics.reporting.map_document")
        .joinpath("assets/evidence-display.js")
        .read_text()
    )
    source = (
        template_block("function escapeHtml", "function normalizedMediaLinks")
        + display
        + template_block(
            "function selectionEmptyState", "function renderEvidenceDisplayPanel"
        )
        + template_block(
            "function renderSelectionEmptyStatePanel", "const ATLAS_CAPTURE_API_VERSION"
        )
        + "const supplied="
        + json.dumps(payload)
        + r""";
const original=JSON.stringify(supplied),emptyState={hidden:true,dataset:{},innerHTML:''};
const activeCountries=new Set(supplied.countries),ALL_LAYERS=supplied.layers;
const activeLayerKeys=new Set(ALL_LAYERS.map(layer=>layer.key));
const SCIENTIFIC_SIGNALS=Array.from({length:supplied.signalCount},(_,i)=>({signal_id:String(i)}));
const activeScientificSignalIds=new Set(SCIENTIFIC_SIGNALS.slice(0,supplied.selectedSignalCount).map(row=>row.signal_id));
const activeEvidenceDisplay=evidenceDisplayFromHash(new URLSearchParams(supplied.query));
let visiblePointEntries=[],renderedPolygonLayers=[],edgeRenderSummary={viewport_count:0,shown:0};
let retainedRows=Array.from({length:supplied.retainedCount},(_,i)=>({edge_id:String(i)}));
const beforeRetained=JSON.stringify(retainedRows);
function visibleGovernedEdges(){return retainedRows}
const TIME_HAS_DATA=true;
function timeFilterUsesFullExtent(){return !supplied.narrowedTime}
let untimedReads=0;
function genericUntimedExclusion(){untimedReads++;return {status:'available',count:3,split_status:'available',absent_count:1,refused_count:2,contextual_count:0}}
const topbarStatePill={textContent:'',setAttribute(key,value){this[key]=value}};
const mapElement={setAttribute(key,value){this[key]=value}};
const document={getElementById(){return mapElement},documentElement:{classList:{contains(){return false}}}};
let staticAtlasLoadGeneration=0,retainedNeighborRecordCountries=null;
const edgeFocusLoadState={generation:0},STATIC_ATLAS_INLINE=true;
const POINT_LAYERS=[],POLYGON_LAYERS=[],STATIC_ATLAS_BOOTSTRAP={budgets:{filter_main_thread_max_ms:50}};
const selectionReadout={dataset:{}},nativeLraController=null,pendingEdgeFocus=null;
const diameterValue={},radiusValue={},densityOpacityValue={},slider={value:10},densityOpacity=.5;
const atlasCapturePresentation=null;
let delayed=false,pending=[],renders=0,errors=[];
const console={error(error){errors.push(String(error))}};
function atlasRetainedNeighborRecordCountries(){return new Map()}
function ensureStaticAtlasSelectionLoaded(){return delayed?new Promise((resolve,reject)=>pending.push({resolve,reject})):Promise.resolve([])}
function removeRenderedLayers(){renders++;visiblePointEntries=[];renderedPolygonLayers=[]}
function renderPointLayers(){visiblePointEntries=Array.from({length:supplied.pointCount},(_,i)=>({feature:{record_id:String(i)}}))}
function renderEdgeLayers(){edgeRenderSummary={viewport_count:supplied.viewportCount,shown:supplied.drawnCount}}
function renderPolygonLayers(){renderedPolygonLayers=Array(supplied.polygonCount).fill({})}
for(const name of ['refreshTimeControls','renderCountryControls','renderScientificControls','renderRelationControls',
 'renderAnimalControls','renderSourceChronologyControls','refreshTimeStepperStatus','renderModeledContextControls',
 'renderLegend','renderControlPanelSummary','updateStats','renderEvidenceDisplayPanel','preparePublishedSearch',
 'buildSearchResults','renderFocusCard','syncPresetButtons','syncTimePresetButtons','syncHashState','renderEvidenceToolPanels'])globalThis[name]=()=>{};
function snapshot(){return {hidden:emptyState.hidden,reason:emptyState.dataset.reason,html:emptyState.innerHTML,
 points:visiblePointEntries.length,polygons:renderedPolygonLayers.length,edges:{...edgeRenderSummary},
 busy:mapElement['aria-busy'],renders,untimedReads,errors:[...errors],sourceUnchanged:JSON.stringify(supplied)===original,
 retainedUnchanged:JSON.stringify(retainedRows)===beforeRetained}}
const tick=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
"""
        + action
        + "\n})().catch(error=>{process.stderr.write(String(error.stack));process.exitCode=1});"
    )
    return cast(dict[str, Any], run_node_json(source))


@pytest.mark.parametrize(
    ("changes", "reason", "hidden"),
    [
        ({"countries": []}, "empty_countries", False),
        ({"layers": []}, "empty_layers", False),
        (
            {
                "layers": [{"key": "points", "scientific_selection_enabled": True}],
                "selectedSignalCount": 0,
            },
            "empty_scientific_selection",
            False,
        ),
        ({}, "unknown", False),
        ({"pointCount": 2}, "not_empty", True),
        (
            {"pointCount": 2, "query": "display_mode=edges"},
            "points_not_drawn",
            False,
        ),
        ({"pointCount": 2, "query": "display_mode=density"}, "drawing_disabled", False),
        ({"polygonCount": 1}, "polygons_only", False),
        (
            {"retainedCount": 4, "viewportCount": 0},
            "retained_relations_not_display_eligible",
            False,
        ),
        (
            {"retainedCount": 4, "viewportCount": 2, "query": "display_mode=nodes"},
            "relations_not_drawn",
            False,
        ),
        (
            {"retainedCount": 4, "viewportCount": 2, "drawnCount": 1},
            "not_empty",
            True,
        ),
    ],
)
def test_actual_ready_renderer_binds_selection_population_and_drawing(
    changes: dict[str, Any], reason: str, hidden: bool
) -> None:
    observed = mounted(
        "await renderMapState();process.stdout.write(JSON.stringify(snapshot()));",
        **changes,
    )
    assert observed["reason"] == reason
    assert observed["hidden"] is hidden
    assert observed["renders"] == 1 and observed["busy"] == "false"
    assert observed["points"] == changes.get("pointCount", 0)
    assert observed["polygons"] == changes.get("polygonCount", 0)
    assert observed["edges"]["viewport_count"] == changes.get("viewportCount", 0)
    assert observed["sourceUnchanged"] and observed["retainedUnchanged"]
    assert observed["errors"] == []


def test_ready_renderer_keeps_untimed_exclusions_separate_from_unknown_cause() -> None:
    observed = mounted(
        "await renderMapState();process.stdout.write(JSON.stringify(snapshot()));",
        narrowedTime=True,
    )
    assert observed["reason"] == "unknown"
    assert observed["untimedReads"] == 1
    assert "3 records" in observed["html"]
    assert "1 absent, 2 refused, 0 contextual" in observed["html"]
    assert "separate count does not explain" in observed["html"]


def test_loading_and_failure_do_not_read_stale_ready_populations() -> None:
    observed = mounted(
        "delayed=true;visiblePointEntries=Array(7).fill({});"
        "edgeRenderSummary={viewport_count:20,shown:10};"
        "const request=renderMapState(),loading=snapshot();"
        "pending[0].reject(Error('current transport failed'));await request;"
        "process.stdout.write(JSON.stringify({loading,failed:snapshot()}));",
        narrowedTime=True,
    )
    assert observed["loading"]["reason"] == "loading"
    assert observed["failed"]["reason"] == "loading_unavailable"
    for state in observed.values():
        assert state["points"] == 7 and state["renders"] == 0
        assert state["untimedReads"] == 0
        assert "20 display" not in state["html"]
        assert "7 eligible" not in state["html"]
    assert observed["failed"]["errors"] == ["Error: current transport failed"]
    assert observed["failed"]["busy"] == "false"


@pytest.mark.parametrize("obsolete_fails", [False, True])
def test_obsolete_selection_completion_cannot_replace_current_summary(
    obsolete_fails: bool,
) -> None:
    finish = (
        "pending[0].reject(Error('obsolete failed'))"
        if obsolete_fails
        else "pending[0].resolve([])"
    )
    observed = mounted(
        "delayed=true;const first=renderMapState(),second=renderMapState();"
        "pending[1].resolve([]);await second;const before=snapshot();"
        + finish
        + ";await first;process.stdout.write(JSON.stringify({before,after:snapshot()}));"
    )
    assert observed["before"] == observed["after"]
    assert observed["after"]["reason"] == "unknown"
    assert observed["after"]["renders"] == 1
    assert observed["after"]["errors"] == []


def test_helper_is_in_main_runtime_and_empty_panel_announces_status() -> None:
    main = template_block(
        "<!-- atlas-runtime:begin -->", "/* atlas-evidence-tools:begin */"
    )
    assert "function selectionEmptyState" in main
    panel = template_block('<div id="empty-state"', '<div id="floating-legend"')
    assert 'role="status"' in panel and 'aria-live="polite"' in panel
