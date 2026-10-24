from __future__ import annotations

import json

import pytest

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE

from .support import run_node_json, template_block


def test_general_playback_is_bounded_without_coarsening_the_interval() -> None:
    controls = template_block("function finiteControlNumber", "const initialState")
    observed = run_node_json(
        """
const TIME_MIN_BP=0,TIME_MAX_BP=2000000,TIME_HAS_DATA=true;
const TIME_INTERVAL_MAX=2000000,DEFAULT_TIME_INTERVAL_YEARS=100;
const DEFAULT_TIME_START_BP=0;
let timeStartBp=0,timeIntervalYears=100;
const reducedMotionQuery={matches:false};
const timePlaybackToggle={disabled:false,title:'',textContent:'',setAttribute(){}};
const timeStartSlider={},timeIntervalSlider={},dockTimeSummary={},timeStartValue={},timeIntervalValue={};
const mobileLayoutQuery={matches:false};
const window={clearTimeout(){},setTimeout(){return 1},location:{hash:''}};
async function renderMapState(){}
function deactivateModeledContext(){}
function sourceChronologyPlaybackSelection(){return null}
"""
        + controls
        + """
console.log(JSON.stringify({
  exactInterval:clampTimeInterval(100),
  frames:automaticPlaybackFrameCount(100),
  reason:automaticTimePlaybackBlockReason(),
  next:nextPlaybackTimeStart(500,100),
  zero:nextPlaybackTimeStart(0,100),
}));
"""
    )

    assert observed == {
        "exactInterval": 100,
        "frames": 20000,
        "reason": (
            "20000 exact frames exceed the 1000-frame automatic limit; "
            "use manual BP navigation."
        ),
        "next": 400,
        "zero": 0,
    }


def test_reduced_motion_stops_both_timers_and_keeps_manual_surfaces() -> None:
    assert "window.matchMedia('(prefers-reduced-motion: reduce)')" in (
        MAP_DOCUMENT_TEMPLATE
    )
    runtime = template_block(
        "reducedMotionQuery.addEventListener",
        "document.querySelectorAll('[data-layer-preset]')",
    )
    assert "stopTimePlayback()" in runtime
    assert "stopModeledContextPlayback()" in runtime
    assert "refreshTimePlaybackControl()" in runtime
    assert "renderModeledContextControls()" in runtime

    general_start = template_block(
        "async function startTimePlayback", "function refreshTimeControls"
    )
    modeled_start = template_block(
        "async function startModeledContextPlayback",
        "function modeledContextFrameFeatures",
    )
    modeled_controls = template_block(
        "function renderModeledContextControls", "const SOURCE_CHRONOLOGY_LEVEL_ORDER"
    )
    assert "automaticTimePlaybackBlockReason()" in general_start
    assert "reducedMotionQuery.matches" in modeled_start
    assert "modeledContextPlayback.disabled" in modeled_controls
    assert "modeledContextDownload.disabled = !modeledContextActive" in modeled_controls
    assert "timeStartSlider.disabled = true" in MAP_DOCUMENT_TEMPLATE
    assert "timeIntervalSlider.disabled = true" in MAP_DOCUMENT_TEMPLATE
    assert "reducedMotionQuery.matches" not in template_block(
        "timeStartSlider.addEventListener", "modeledContextFamily.addEventListener"
    )


def test_reduced_motion_reason_does_not_change_manual_bp_or_export_semantics() -> None:
    controls = template_block("function finiteControlNumber", "const initialState")
    observed = run_node_json(
        """
const TIME_MIN_BP=0,TIME_MAX_BP=1000,TIME_HAS_DATA=true;
const TIME_INTERVAL_MAX=1000,DEFAULT_TIME_INTERVAL_YEARS=100;
const DEFAULT_TIME_START_BP=0;
let timeStartBp=0,timeIntervalYears=100;
const reducedMotionQuery={matches:true};
const timePlaybackToggle={disabled:false,title:'',textContent:'',setAttribute(){}};
const timeStartSlider={},timeIntervalSlider={},dockTimeSummary={},timeStartValue={},timeIntervalValue={};
const mobileLayoutQuery={matches:false};
const window={clearTimeout(){},setTimeout(){throw new Error('timer must not be scheduled')},location:{hash:''}};
async function renderMapState(){}
function deactivateModeledContext(){}
function sourceChronologyPlaybackSelection(){return null}
"""
        + controls
        + """
refreshTimePlaybackControl();
console.log(JSON.stringify({
  reason:automaticTimePlaybackBlockReason(),
  playbackDisabled:timePlaybackToggle.disabled,
  manualStart:clampTimeStart(0,100),
  manualEnd:timeWindowEndBp(),
}));
"""
    )

    assert observed == {
        "reason": "Reduced motion is active; use the BP controls for manual navigation.",
        "playbackDisabled": True,
        "manualStart": 0,
        "manualEnd": 100,
    }


@pytest.mark.parametrize("reduced", [False, True])
@pytest.mark.parametrize(
    "kind", ["point", "zoomed_point", "polygon", "absent", "invalid"]
)
def test_focus_navigation_preserves_destination_and_honors_motion_preference(
    reduced: bool, kind: str
) -> None:
    handler = template_block(
        "focusZoomButton.addEventListener('click'", "map.on('zoomend'"
    )
    states: dict[str, object] = {
        "point": {"kind": "point", "latitude": 59.25, "longitude": 18.75},
        "zoomed_point": {"kind": "point", "latitude": 59.25, "longitude": 18.75},
        "polygon": {"kind": "polygon", "bounds": [[58, 17], [60, 19]]},
        "absent": None,
        "invalid": {"kind": "point", "latitude": None, "longitude": 18.75},
    }
    zoom = 12 if kind == "zoomed_point" else 3
    observed = run_node_json(
        "const calls=[];let listener;"
        f"const reducedMotionQuery={{matches:{json.dumps(reduced)}}};"
        f"const focusState={json.dumps(states[kind])};"
        f"const map={{getZoom:()=>{zoom},"
        "fitBounds:(...args)=>calls.push(['bounds',...args]),"
        "flyTo:(...args)=>calls.push(['point',...args])};"
        "const focusZoomButton={addEventListener(type,fn){listener=fn}};"
        + handler
        + "listener();console.log(JSON.stringify({calls,focusState}));"
    )
    options: dict[str, object] = {"animate": False} if reduced else {}
    bounds_options: dict[str, object] = {"padding": [32, 32], **options}
    expected = (
        [["bounds", [[58, 17], [60, 19]], bounds_options]]
        if kind == "polygon"
        else []
        if kind in {"absent", "invalid"}
        else [["point", [59.25, 18.75], max(zoom, 8), {"duration": 0.7, **options}]]
    )
    assert observed == {"calls": expected, "focusState": states[kind]}


@pytest.mark.parametrize("reduced", [False, True])
def test_search_result_focus_preserves_identity_with_motion_preference(
    reduced: bool,
) -> None:
    handler = template_block(
        "function buildSearchResults()", "function renderSelectionEmptyStatePanel("
    )
    observed = run_node_json(
        f"const reducedMotionQuery={{matches:{json.dumps(reduced)}}};"
        """
const calls=[],focused=[],timers=[];let click,popup=0,searchOpen=true;
const match={layer:{label:'Source'},feature:{title:'Exact source',country:'Sweden'},
 marker:{openPopup(){popup++}}};
const visiblePointEntries=[{feature:{title:'Other'}},match];
const searchInput={value:'Exact source'},searchClearButton={},searchCount={};
const searchResults={querySelectorAll:()=>[{addEventListener(type,fn){click=fn}}]};
const publishedSearchCounts=()=>({focalCount:2,neighborCount:0});
const publishedSearchResults=()=>[match];
const featureTimeDescriptor=()=>null,escapeHtml=String;
const featureCoordinatePair=()=>({latitude:59.25,longitude:18.75});
const focusPointAtVisibleIndex=index=>focused.push(index);
const setSearchOpen=value=>{searchOpen=value};
const window={setTimeout(fn,delay){timers.push(delay);fn()}};
const map={getZoom:()=>11,flyTo:(...args)=>calls.push(args)};
"""
        + handler
        + "buildSearchResults();click();console.log(JSON.stringify({calls,focused,timers,popup,searchOpen}));"
    )
    options: dict[str, object] = {"duration": 0.7}
    if reduced:
        options["animate"] = False
    assert observed == {
        "calls": [[[59.25, 18.75], 11, options]],
        "focused": [1],
        "timers": [250],
        "popup": 1,
        "searchOpen": False,
    }


@pytest.mark.parametrize("reduced", [False, True])
@pytest.mark.parametrize("bounds_kind", ["valid", "invalid", "missing"])
def test_fit_and_reset_navigation_preserve_bounds_and_motion_preference(
    reduced: bool, bounds_kind: str
) -> None:
    handlers = template_block(
        "function fitToActive()", "async function restoreDefaults"
    )
    observed = run_node_json(
        f"const reducedMotionQuery={{matches:{json.dumps(reduced)}}};"
        f"const boundsKind={json.dumps(bounds_kind)};"
        """
const INITIAL_BOUNDS=[[54,10],[70,32]],calls=[];
const selected=boundsKind==='missing'?null:{isValid:()=>boundsKind==='valid'};
let reads=0;
function activeBounds(){reads++;return selected}
const map={fitBounds(bounds,options){calls.push({target:bounds===INITIAL_BOUNDS?'initial':bounds===selected?'active':'unknown',options})}};
"""
        + handlers
        + """
resetView();fitToActive();resetView();
console.log(JSON.stringify({calls,reads,initial:INITIAL_BOUNDS}));
"""
    )
    options: dict[str, object] = {"padding": [36, 36]}
    if reduced:
        options["animate"] = False
    initial = {"target": "initial", "options": options}
    assert observed == {
        "calls": [initial]
        + ([{"target": "active", "options": options}] if bounds_kind == "valid" else [])
        + [initial],
        "reads": 1,
        "initial": [[54, 10], [70, 32]],
    }
