from __future__ import annotations

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
