from __future__ import annotations

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE

from .support import run_node_json, template_block


def test_time_window_overlap_and_playback_run_from_oldest_to_present() -> None:
    controls = template_block("function finiteControlNumber", "const initialState")
    intervals = template_block(
        "function finiteTimeValue", "function pointFeatureInTimeWindow"
    )
    observed = run_node_json(
        """
const TIME_MIN_BP=0, TIME_MAX_BP=1000, TIME_HAS_DATA=true;
const DEFAULT_TIME_START_BP=700, DEFAULT_TIME_INTERVAL_YEARS=100;
const TIME_INTERVAL_MAX=1000;
let timeStartBp=200, timeIntervalYears=100;
const timePlaybackToggle={setAttribute(){},textContent:'',disabled:false};
const timeStartSlider={}, timeIntervalSlider={}, dockTimeSummary={};
const timeStartValue={}, timeIntervalValue={};
const window={clearTimeout(){},setTimeout(){return 1},location:{hash:''}};
const mobileLayoutQuery={matches:false};
const reducedMotionQuery={matches:false};
function sourceChronologyPlaybackSelection(){return null}
async function renderMapState(){}
"""
        + controls
        + intervals
        + """
const playback=[];
let cursor=oldestPlaybackStart(100);
while (true) {
  playback.push(cursor);
  const next=nextPlaybackTimeStart(cursor,100);
  if (next===cursor) break;
  cursor=next;
}
timeStartBp=200; timeIntervalYears=100;
const layer={applies_time_filter:true};
const sourceLayer={applies_time_filter:true,semantic_role:'source_chronology_context'};
const narrowUntimed=featureInTimeWindow(layer,{time_mean_bp:null});
const touching=featureInTimeWindow(layer,{time_start_bp:100,time_end_bp:200});
const outside=featureInTimeWindow(layer,{time_start_bp:0,time_end_bp:99});
const reversed=featureInTimeWindow(layer,{time_start_bp:300,time_end_bp:200});
timeStartBp=0; timeIntervalYears=1000;
console.log(JSON.stringify({
  zeroStart:clampTimeStart(0,100),
  playback,
  touching,
  outside,
  reversed,
  untimedNarrow:narrowUntimed,
  genericUntimedFullExtent:featureInTimeWindow(layer,{time_mean_bp:null}),
  sourceUntimedFullExtent:featureInTimeWindow(sourceLayer,{time_mean_bp:null}),
  negativeDeclaredFullExtent:featureInTimeWindow(layer,{time_start_bp:-1,time_end_bp:100}),
  reversedDeclaredFullExtent:featureInTimeWindow(layer,{time_start_bp:300,time_end_bp:200}),
  blankDeclaredFullExtent:featureInTimeWindow(layer,{time_start_bp:'',time_end_bp:''}),
  arrayDeclaredFullExtent:featureInTimeWindow(layer,{time_start_bp:[],time_end_bp:[100]}),
  objectDeclaredFullExtent:featureInTimeWindow(layer,{time_start_bp:{},time_end_bp:100}),
  partialDeclaredFullExtent:featureInTimeWindow(layer,{time_start_bp:100,time_end_bp:null}),
  genuinelyUntimedFullExtent:featureInTimeWindow(layer,{}),
  nullIntervalMeanFallback:featureInTimeWindow(layer,{time_start_bp:null,time_end_bp:null,time_mean_bp:123}),
  refusedSemantics:featureInTimeWindow(layer,{time_start_bp:null,time_end_bp:null,temporal_semantics:{comparability_posture:'refused',refusal_reason_code:'negative_bp'}}),
  refusedNumericSemantics:featureInTimeWindow(layer,{time_start_bp:100,time_end_bp:200,temporal_semantics:{comparability_posture:'refused',refusal_reason_code:'source_age_system_not_comparable'}}),
  absentStatus:featureTimeAdmission({}).status,
  refusedStatus:featureTimeAdmission({time_start_bp:null,time_end_bp:null,temporal_semantics:{comparability_posture:'refused',refusal_reason_code:'negative_bp'}}).status,
  invalidWithoutLayerFilter:featureInTimeWindow({applies_time_filter:false},{time_start_bp:'bad',time_end_bp:'bad'}),
}));
"""
    )

    assert observed == {
        "zeroStart": 0,
        "playback": [900, 800, 700, 600, 500, 400, 300, 200, 100, 0],
        "touching": True,
        "outside": False,
        "reversed": False,
        "untimedNarrow": False,
        "genericUntimedFullExtent": True,
        "sourceUntimedFullExtent": False,
        "negativeDeclaredFullExtent": False,
        "reversedDeclaredFullExtent": False,
        "blankDeclaredFullExtent": False,
        "arrayDeclaredFullExtent": False,
        "objectDeclaredFullExtent": False,
        "partialDeclaredFullExtent": False,
        "genuinelyUntimedFullExtent": True,
        "nullIntervalMeanFallback": True,
        "refusedSemantics": False,
        "refusedNumericSemantics": False,
        "absentStatus": "absent",
        "refusedStatus": "refused",
        "invalidWithoutLayerFilter": False,
    }

    no_global_time = run_node_json(
        """
const TIME_HAS_DATA=false;
let timeStartBp=0,timeIntervalYears=1000;
function timeWindowEndBp(){return 1000}
function timeFilterUsesFullExtent(){return true}
const layer={applies_time_filter:true};
const sourceLayer={applies_time_filter:false,semantic_role:'source_chronology_context'};
"""
        + intervals
        + """
console.log(JSON.stringify({
  invalid:featureInTimeWindow(layer,{time_start_bp:'bad',time_end_bp:'bad'}),
  untimedSource:featureInTimeWindow(sourceLayer,{time_start_bp:null,time_end_bp:null}),
}));
"""
    )
    assert no_global_time == {"invalid": False, "untimedSource": False}


def test_contextual_source_label_is_displayed_but_not_time_admitted() -> None:
    helpers = template_block(
        "function finiteTimeValue", "function pointFeatureInTimeWindow"
    )
    observed = run_node_json(
        """
const TIME_HAS_DATA=true;
let timeStartBp=0,timeIntervalYears=1000;
function timeWindowEndBp(){return 1000}
function timeFilterUsesFullExtent(){return true}
const feature={time_start_bp:null,time_end_bp:null,time_label:'4700 BP'};
const layer={applies_time_filter:true,semantic_role:'source_chronology_context'};
"""
        + helpers
        + """
console.log(JSON.stringify({label:featureTimeLabel(feature),descriptor:featureTimeDescriptor(feature),admitted:featureInTimeWindow(layer,feature)}));
"""
    )

    assert observed == {
        "label": "4700 BP",
        "descriptor": {"label": "Chronology context", "value": "4700 BP"},
        "admitted": False,
    }
    assert "].concat(featureTimeDescriptor(properties)" in MAP_DOCUMENT_TEMPLATE
    assert (
        "${escapeHtml(timeDescriptor.label)}: ${escapeHtml(timeDescriptor.value)}"
        in (MAP_DOCUMENT_TEMPLATE)
    )


def test_time_controls_expose_canonical_interval_and_playback_direction() -> None:
    assert 'id="time-playback-toggle"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="time-step-older"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="time-step-newer"' in MAP_DOCUMENT_TEMPLATE
    assert "Play oldest → present" in MAP_DOCUMENT_TEMPLATE
    assert "direction: rtl" in MAP_DOCUMENT_TEMPLATE
    assert "dockTimeSummary.textContent = `[${timeStartBp}, ${endBp}] BP`" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert (
        "timeIntervalYears = Math.min(clampTimeInterval(timeIntervalYears), navigationSpan)"
        in MAP_DOCUMENT_TEMPLATE
    )
    assert "timeIntervalSlider.min = captureInterval ? '0' : '1'" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "timeStartSlider.step = captureInterval ? 'any' : '1'" in (
        MAP_DOCUMENT_TEMPLATE
    )


def test_desktop_header_is_compact_and_control_toggle_shows_direction() -> None:
    assert "@media (min-width: 901px)" in MAP_DOCUMENT_TEMPLATE
    assert "width: min(720px, calc(100vw - 352px))" in MAP_DOCUMENT_TEMPLATE
    assert "width: min(460px, 100%)" in MAP_DOCUMENT_TEMPLATE
    assert "← Show controls" in MAP_DOCUMENT_TEMPLATE
    assert "Hide controls →" in MAP_DOCUMENT_TEMPLATE
    assert 'class="time-stepper topbar-time-stepper"' in MAP_DOCUMENT_TEMPLATE
    assert "min-height: 44px" in MAP_DOCUMENT_TEMPLATE
    topbar = template_block('<div class="map-topbar">', '<div id="map"')
    assert 'id="time-step-older"' in topbar
    assert 'id="time-step-newer"' in topbar
    assert 'id="time-playback-toggle"' in topbar
    assert 'data-basemap="street"' not in topbar
    control_panel = template_block('<aside id="sidebar"', '<section id="focus-card"')
    assert 'aria-label="Basemap selection"' in control_panel
    assert 'data-basemap="none"' in control_panel


def test_map_opens_with_dismissible_surfaces_collapsed() -> None:
    assert 'id="sidebar" class="control-panel is-collapsed"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="legend-body" class="legend-body is-collapsed"' in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert 'aria-controls="sidebar" aria-expanded="false">← Show controls' in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert 'aria-controls="legend-body" aria-expanded="false">Expand' in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert 'id="topbar-search" class="topbar-search" hidden' in MAP_DOCUMENT_TEMPLATE
    assert 'aria-controls="topbar-search" aria-expanded="false">Search' in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "return true;" in template_block(
        "function defaultPanelCollapsed()",
        "function panelPreferenceFromHash()",
    )
    assert "let legendCollapsed = initialState.legend !== 'expanded';" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "if (!legendCollapsed) params.set('legend', 'expanded');" in (
        MAP_DOCUMENT_TEMPLATE
    )


def test_overlays_yield_to_the_surface_the_user_opened() -> None:
    panel_collapse = template_block(
        "function setPanelCollapsed",
        "function closeMobilePanel",
    )
    legend_collapse = template_block(
        "function setLegendCollapsed",
        "function openHelpDialog",
    )
    focus_state = template_block(
        "function setFocusState", "function unavailableDetailTabs"
    )
    search_state = template_block("function setSearchOpen", "function openHelpDialog")
    assert "setLegendCollapsed(true, false)" in panel_collapse
    assert "setPanelCollapsed(true, false)" in legend_collapse
    assert "setSearchOpen(false)" in legend_collapse
    assert "if (focusState) setFocusState(null);" in legend_collapse
    assert "if (nextState) {" in focus_state
    assert "setPanelCollapsed(true, false);" in focus_state
    assert "mobilePanelReturnFocus = null;" in focus_state
    assert "setLegendCollapsed(true, false);" in focus_state
    assert "setSearchOpen(false);" in focus_state
    assert "classList.toggle('has-legend-open', !collapsed)" in legend_collapse
    assert "classList.toggle('has-search-open', open)" in search_state


def test_focused_point_identity_survives_rendered_entry_replacement() -> None:
    focus_identity = template_block(
        "function stableFeatureRecordId", "function unavailableDetailTabs"
    )
    focus_render = template_block(
        "function renderFocusCard", "function countActiveOverrides"
    )
    focus_navigation = template_block(
        "focusPreviousButton.addEventListener", "focusZoomButton.addEventListener"
    )

    observed = run_node_json(
        focus_identity
        + """
const layer={key:'source-taxon'};
const entries=[
  {layer,feature:{record_id:'site:42',node_id:'node:early'}},
  {layer,feature:{record_id:'site:42',node_id:'node:late'}},
  {layer,feature:{record_id:'site:99',evidence_row_id:'row:early'}},
  {layer,feature:{record_id:'site:99',evidence_row_id:'row:late'}},
  {layer,feature:{record_id:'site:100'}},
  {layer,feature:{evidence_row_id:'row:only'}},
];
const early=pointFocusIdentity(layer,entries[0].feature);
const late=pointFocusIdentity(layer,entries[1].feature);
const evidenceEarly=pointFocusIdentity(layer,entries[2].feature);
const evidenceLate=pointFocusIdentity(layer,entries[3].feature);
const record=pointFocusIdentity(layer,entries[4].feature);
const evidenceOnly=pointFocusIdentity(layer,entries[5].feature);
let duplicateRefused=false;
try { uniquePointEntryForFocus([entries[0],entries[0]],{kind:'point',...early}); }
catch (error) { duplicateRefused=error.message === 'point focus identity is not unique'; }
console.log(JSON.stringify({
  early,
  late,
  evidenceEarly,
  evidenceLate,
  record,
  evidenceOnly,
  resolvedEarly:uniquePointEntryForFocus(entries,{kind:'point',...early})?.feature.node_id,
  resolvedLate:uniquePointEntryForFocus(entries,{kind:'point',...late})?.feature.node_id,
  resolvedEvidenceEarly:uniquePointEntryForFocus(entries,{kind:'point',...evidenceEarly})?.feature.evidence_row_id,
  resolvedEvidenceLate:uniquePointEntryForFocus(entries,{kind:'point',...evidenceLate})?.feature.evidence_row_id,
  resolvedEvidenceOnly:uniquePointEntryForFocus(entries,{kind:'point',...evidenceOnly})?.feature.evidence_row_id,
  missingRecord:pointFocusIdentity(layer,{node_id:'orphan'}),
  duplicateRefused,
}));
"""
    )

    assert observed == {
        "early": {
            "layerKey": "source-taxon",
            "featureKey": "node:node:early",
            "recordId": "site:42",
        },
        "late": {
            "layerKey": "source-taxon",
            "featureKey": "node:node:late",
            "recordId": "site:42",
        },
        "evidenceEarly": {
            "layerKey": "source-taxon",
            "featureKey": "evidence:row:early",
            "recordId": "site:99",
        },
        "evidenceLate": {
            "layerKey": "source-taxon",
            "featureKey": "evidence:row:late",
            "recordId": "site:99",
        },
        "record": {
            "layerKey": "source-taxon",
            "featureKey": "record:site:100",
            "recordId": "site:100",
        },
        "evidenceOnly": {
            "layerKey": "source-taxon",
            "featureKey": "evidence:row:only",
            "recordId": "row:only",
        },
        "resolvedEarly": "node:early",
        "resolvedLate": "node:late",
        "resolvedEvidenceEarly": "row:early",
        "resolvedEvidenceLate": "row:late",
        "resolvedEvidenceOnly": "row:only",
        "missingRecord": None,
        "duplicateRefused": True,
    }
    assert (
        "const identity = pointFocusIdentity(entry.layer, entry.feature);"
        in focus_render
    )
    assert "if (!identity) return;" in focus_render
    assert "...identity," in focus_render
    assert (
        "highlightPointEntry(visiblePointEntryForFocus(focusState))" in focus_identity
    )
    assert "const pointEntry = visiblePointEntryForFocus();" in focus_render
    assert "focusState.layerKey === nextFocus.layerKey" in focus_render
    assert "focusState.featureKey === nextFocus.featureKey" in focus_render
    assert "focusState.recordId === nextFocus.recordId" in focus_render
    assert "visiblePointEntryForFocus(focusState)" in focus_navigation
    assert "visiblePointIndex" not in MAP_DOCUMENT_TEMPLATE


def test_search_results_are_explicit_and_close_on_escape() -> None:
    search_handlers = template_block(
        "searchInput.addEventListener('keydown'",
        "document.addEventListener('click'",
    )
    assert "if (event.key === 'Escape')" in search_handlers
    assert "setSearchOpen(false, true);" in search_handlers
    search_state = template_block("function setSearchOpen", "function openHelpDialog")
    assert "setPanelCollapsed(true, false)" in search_state
    assert "setLegendCollapsed(true, false)" in search_state
    assert (
        "searchToggleButton.setAttribute('aria-expanded', String(open))" in search_state
    )
    assert "searchToggleButton.focus({ preventScroll: true })" in search_state


def test_populated_search_and_mobile_focus_preserve_map_space() -> None:
    assert "width: min(360px, 100%);" in MAP_DOCUMENT_TEMPLATE
    assert "max-height: min(18vh, 140px);" in MAP_DOCUMENT_TEMPLATE
    assert "width: min(240px, 46vw);" in MAP_DOCUMENT_TEMPLATE
    assert "width: min(220px, calc(100vw - 16px));" in MAP_DOCUMENT_TEMPLATE
    assert "max-height: min(14vh, 96px);" in MAP_DOCUMENT_TEMPLATE
    assert "width: min(340px, 46vw);" in MAP_DOCUMENT_TEMPLATE
    assert "max-height: min(32vh, 320px);" in MAP_DOCUMENT_TEMPLATE
    assert "max-height: min(22vh, 220px);" in MAP_DOCUMENT_TEMPLATE
    assert "width: min(188px, 46vw);" in MAP_DOCUMENT_TEMPLATE
    assert "max-height: min(18vh, 152px);" in MAP_DOCUMENT_TEMPLATE
    assert MAP_DOCUMENT_TEMPLATE.index('class="time-stepper topbar-time-stepper"') < (
        MAP_DOCUMENT_TEMPLATE.index('id="topbar-search" class="topbar-search"')
    )


def test_time_window_feedback_uses_visible_records_after_static_loading() -> None:
    country_controls = template_block(
        "function renderCountryControls",
        "function renderScientificControls",
    )
    assert "visiblePointEntries.filter" in country_controls
    assert "STATIC_ATLAS_BOOTSTRAP.assets" not in country_controls

    source_controls = template_block(
        "function renderSourceChronologyControls",
        "function renderLayerControls",
    )
    assert "visibleSourceEntries.length" in source_controls
    assert "visibleObservationDenominator" in source_controls
    assert "visible in ${activeWindowLabel}" in source_controls
    assert "global selected-facet denominator" in source_controls

    render_state = template_block(
        "async function renderMapState",
        "function renderLoadedMapState",
    )
    assert "Loading selected evidence…" in render_state
    assert "admitted records loaded" not in render_state
    assert "selectionReadout.dataset.staticLoad" in render_state
    assert "selectionReadout.dataset.filterRenderMs" in render_state


def test_diameter_hash_value_is_finite_bounded_and_step_normalized() -> None:
    helper = template_block(
        "function finiteControlNumber", "function clampTimeInterval"
    )
    helper = helper.replace("__INITIAL_DIAMETER__", "40")
    observed = run_node_json(
        helper
        + """
console.log(JSON.stringify({
  invalid:clampDiameter('abc'),
  blank:clampDiameter(''),
  low:clampDiameter(-20),
  high:clampDiameter(140),
  stepped:clampDiameter(42),
  zero:clampDiameter(0),
  array:clampDiameter([]),
  singletonArray:clampDiameter([0]),
  object:clampDiameter({}),
}));
"""
    )

    assert observed == {
        "invalid": 40,
        "blank": 40,
        "low": 0,
        "high": 100,
        "stepped": 40,
        "zero": 0,
        "array": 40,
        "singletonArray": 40,
        "object": 40,
    }
