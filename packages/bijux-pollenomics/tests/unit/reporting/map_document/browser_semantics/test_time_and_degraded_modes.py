from __future__ import annotations

import json

from bijux_pollenomics.reporting.map_document import render_multi_country_map_html
from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE
from bijux_pollenomics.reporting.map_publication import MapScopePolicy

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
  partialDeclaredFullExtent:featureInTimeWindow(layer,{time_start_bp:100,time_end_bp:null}),
  genuinelyUntimedFullExtent:featureInTimeWindow(layer,{}),
  nullIntervalMeanFallback:featureInTimeWindow(layer,{time_start_bp:null,time_end_bp:null,time_mean_bp:123}),
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
        "partialDeclaredFullExtent": False,
        "genuinelyUntimedFullExtent": True,
        "nullIntervalMeanFallback": True,
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
    assert "setLegendCollapsed(true, false)" in panel_collapse
    assert "setPanelCollapsed(true, false)" in legend_collapse
    assert "setSearchOpen(false)" in legend_collapse
    assert "if (focusState) setFocusState(null);" in legend_collapse
    assert "if (nextState) {" in focus_state
    assert "setPanelCollapsed(true, false);" in focus_state
    assert "mobilePanelReturnFocus = null;" in focus_state
    assert "setLegendCollapsed(true, false);" in focus_state
    assert "setSearchOpen(false);" in focus_state


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
    assert "max-height: min(26vh, 260px);" in MAP_DOCUMENT_TEMPLATE
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
    }


def test_static_assets_keep_generic_untimed_context_at_full_extent() -> None:
    helper = template_block(
        "function staticAtlasTimeNeeded", "function staticAtlasSignalNeeded"
    )
    observed = run_node_json(
        """
const TIME_HAS_DATA=true;
let timeStartBp=0,timeIntervalYears=1000;
function timeWindowEndBp(){return timeStartBp+timeIntervalYears}
function timeFilterUsesFullExtent(){return timeStartBp===0&&timeWindowEndBp()>=1000}
function staticAtlasNonnegativeInteger(value){return Number(value)}
const row={asset_key:'untimed',record_count:359,untimed_record_count:359,time_min_bp:null,time_max_bp:null};
const generic={applies_time_filter:true,semantic_role:'archaeological_context'};
const source={applies_time_filter:true,semantic_role:'source_chronology_context'};
"""
        + helper
        + """
const genericFull=staticAtlasTimeNeeded(row,generic);
const sourceFull=staticAtlasTimeNeeded(row,source);
timeStartBp=100;timeIntervalYears=100;
console.log(JSON.stringify({genericFull,sourceFull,genericNarrow:staticAtlasTimeNeeded(row,generic)}));
"""
    )

    assert observed == {
        "genericFull": True,
        "sourceFull": False,
        "genericNarrow": False,
    }


def test_country_filtered_assets_require_a_governed_active_country() -> None:
    helper = template_block(
        "function staticAtlasCountryNeeded", "function staticAtlasTimeNeeded"
    )
    observed = run_node_json(
        """
const activeCountries=new Set(['Sweden']);
const layer={applies_country_filter:true};
"""
        + helper
        + """
console.log(JSON.stringify({
  sweden:staticAtlasCountryNeeded({country_keys:['Sweden']},layer),
  norway:staticAtlasCountryNeeded({country_keys:['Norway']},layer),
  unassigned:staticAtlasCountryNeeded({country_keys:['UNASSIGNED']},layer),
  blank:staticAtlasCountryNeeded({country_keys:[]},layer),
}));
"""
    )

    assert observed == {
        "sweden": True,
        "norway": False,
        "unassigned": False,
        "blank": False,
    }


def test_country_filtered_features_refuse_blank_country_values() -> None:
    visibility = template_block(
        "function pointFeatureVisible", "function geoJsonPositionIsAdmitted"
    )
    observed = run_node_json(
        """
const activeLayerKeys=new Set(['points','polygons']);
const activeCountries=new Set(['Sweden']);
function featureCoordinatePair(){return {latitude:59,longitude:18}}
function pointFeatureInTimeWindow(){return true}
function sourceChronologyFeatureMatches(){return true}
function featureMatchesAnimalFilters(){return true}
function featureMatchesScientificSelection(){return true}
function modeledContextFeatureVisible(){return true}
function featureInTimeWindow(){return true}
const points={key:'points',applies_country_filter:true};
const polygons={key:'polygons',applies_country_filter:true};
"""
        + visibility
        + """
console.log(JSON.stringify({
  pointSweden:pointFeatureVisible(points,{country:'Sweden'}),
  pointBlank:pointFeatureVisible(points,{country:''}),
  polygonSweden:polygonFeatureVisible(polygons,{country:'Sweden'}),
  polygonBlank:polygonFeatureVisible(polygons,{country:''}),
}));
"""
    )

    assert observed == {
        "pointSweden": True,
        "pointBlank": False,
        "polygonSweden": True,
        "polygonBlank": False,
    }


def test_animal_candidates_refuse_blank_country_values() -> None:
    helper = template_block(
        "function animalCandidateEntries", "function animalEntryMatchesFilters"
    )
    observed = run_node_json(
        """
const layer={key:'animals',applies_country_filter:true,features:[
  {record_id:'sweden',country:'Sweden'},
  {record_id:'blank',country:''},
]};
const POINT_LAYERS=[layer];
const activeLayerKeys=new Set(['animals']);
const activeCountries=new Set(['Sweden']);
function isAnimalLayer(){return true}
function pointFeatureInTimeWindow(){return true}
"""
        + helper
        + """
console.log(JSON.stringify(animalCandidateEntries().map(({feature})=>feature.record_id)));
"""
    )

    assert observed == ["sweden"]


def test_generic_untimed_exclusion_reports_exact_or_ambiguous_denominator() -> None:
    helper = template_block(
        "function genericUntimedExclusion", "function sourceChronologyUntimedExclusion"
    )
    observed = run_node_json(
        """
let STATIC_ATLAS_INLINE=false;
const COUNTRIES=['Denmark','Finland','Norway','Sweden'];
const activeLayerKeys=new Set(['context']);
const ALL_LAYERS=[{key:'context',applies_time_filter:true,applies_country_filter:true,semantic_role:'context'}];
const STATIC_ATLAS_BOOTSTRAP={assets:[
  {asset_key:'sweden',domain:'nodes',layer_key:'context',country_keys:['Sweden'],untimed_record_count:4},
  {asset_key:'mixed',domain:'nodes',layer_key:'context',country_keys:['Sweden','Norway'],untimed_record_count:3},
]};
function staticAtlasNonnegativeInteger(value){return Number(value)}
function featureTimeAdmission(feature){return {status:feature.status}}
let activeCountries=new Set(COUNTRIES);
"""
        + helper
        + """
const all=genericUntimedExclusion();
activeCountries=new Set(['Sweden']);
const sweden=genericUntimedExclusion();
STATIC_ATLAS_INLINE=true;
ALL_LAYERS[0].features=[
  {country:'Sweden',status:'untimed'},
  {country:'Sweden',status:'valid'},
  {country:'Sweden',status:'invalid'},
  {country:'Norway',status:'untimed'},
];
const inline=genericUntimedExclusion();
console.log(JSON.stringify({all,sweden,inline}));
"""
    )

    assert observed == {
        "all": {"status": "available", "count": 7},
        "sweden": {"status": "unavailable", "count": None},
        "inline": {"status": "available", "count": 1},
    }


def test_provider_failure_reaches_no_basemap_without_mutating_evidence() -> None:
    basemap_helpers = template_block(
        "function nextBasemapAfter", "Object.entries(basemaps)"
    )
    observed = run_node_json(
        """
const BASEMAP_FALLBACK_ORDER=['street','terrain','none'];
const BASEMAP_NAMES=[...BASEMAP_FALLBACK_ORDER];
const failedBasemaps=new Set(['street','terrain']);
const basemapErrorCounts=new Map();
const evidence=[{record_id:'site:1',latitude:0,longitude:0}];
let currentBasemap='terrain', activeBasemap='terrain', readout='';
const map={removed:0,removeLayer(){this.removed += 1}};
const basemaps={terrain:{added:0,addTo(){this.added += 1}}};
const document={querySelectorAll(){return []}};
function updateBasemapReadout(message){readout=message}
function syncHashState(){}
"""
        + basemap_helpers
        + """
const fallback=nextBasemapAfter('terrain');
setBasemap(fallback,{reason:'provider unavailable; evidence unaffected'});
console.log(JSON.stringify({fallback,currentBasemap,activeBasemap,readout,evidence,mapRemoved:map.removed}));
"""
    )

    assert observed == {
        "fallback": "none",
        "currentBasemap": "none",
        "activeBasemap": None,
        "readout": "provider unavailable; evidence unaffected",
        "evidence": [{"record_id": "site:1", "latitude": 0, "longitude": 0}],
        "mapRemoved": 1,
    }


def test_empty_and_provider_failure_modes_are_explicit() -> None:
    assert "const MAX_PROVIDER_TILE_ERRORS = 3" in MAP_DOCUMENT_TEMPLATE
    assert "failedBasemaps.add(name)" in MAP_DOCUMENT_TEMPLATE
    assert "return 'none'" in MAP_DOCUMENT_TEMPLATE
    assert 'data-basemap="none"' in MAP_DOCUMENT_TEMPLATE
    assert "Evidence data unaffected." in MAP_DOCUMENT_TEMPLATE
    assert (
        "emptyState.hidden = visiblePointEntries.length > 0 || renderedPolygonLayers.length > 0"
        in MAP_DOCUMENT_TEMPLATE
    )
    assert "failure.setAttribute('role', 'alert')" in MAP_DOCUMENT_TEMPLATE


def test_scientific_controls_cover_all_resolution_levels() -> None:
    resolution_order = template_block(
        "const SCIENTIFIC_RESOLUTION_ORDER", "const DETAIL_RECORDS"
    )
    selection_helpers = template_block(
        "function featureMatchesScientificSelection", "function pointFeatureVisible"
    )
    control_renderer = template_block(
        "function renderScientificControls", "function visibleGovernedEdges"
    )
    observed = run_node_json(
        """
const SCIENTIFIC_SIGNALS=[
  {signal_id:'group:crops',resolution:'group'},
  {signal_id:'subgroup:cereals',resolution:'subgroup'},
  {signal_id:'role:direct',resolution:'role'},
  {signal_id:'taxon:wheat',resolution:'taxon'},
];
const activeScientificSignalIds=new Set(['subgroup:cereals']);
const ATLAS_EVIDENCE={classifications_status:'available'};
const scientificStatus={textContent:''}, scientificFilters={innerHTML:''};
const scientificActions={hidden:false};
const scientificSummary={textContent:''};
const document={querySelectorAll(){return []}};
function escapeHtml(value){return String(value)}
function scientificCueGlyph(){return 'x'}
"""
        + resolution_order
        + selection_helpers
        + control_renderer
        + """
const layer={scientific_selection_enabled:true};
const feature={scientific_signal_ids:['subgroup:cereals']};
renderScientificControls();
console.log(JSON.stringify({
  order:SCIENTIFIC_RESOLUTION_ORDER,
  selected:featureMatchesScientificSelection(layer,feature),
  signals:scientificSignalsForFeature(feature).map((row)=>row.signal_id),
  subgroupControl:scientificFilters.innerHTML.includes('value="subgroup:cereals"'),
}));
"""
    )

    assert observed == {
        "order": ["whole", "group", "subgroup", "role", "taxon"],
        "selected": True,
        "signals": ["subgroup:cereals"],
        "subgroupControl": True,
    }


def test_inline_payload_supplies_the_runtime_filter_budget() -> None:
    policy = MapScopePolicy(
        key="test",
        label="Test",
        eyebrow_label="Test",
        summary="Test",
        bounds_summary="Test",
        default_basemap="none",
        initial_diameter_km=0,
        minimum_bounds=((0.0, 0.0), (1.0, 1.0)),
        filter_surfaces=(),
        legend_sections=(),
        visible_caveats=(),
        engine_summary="Test",
    )
    document = render_multi_country_map_html(
        "Test",
        "test-build",
        "2026-09-05",
        ("Sweden",),
        policy,
        [],
        [],
        "assets",
    )
    bootstrap_json = document.split(
        '<script id="atlas-static-bootstrap" type="application/json">', 1
    )[1].split("</script>", 1)[0]
    bootstrap = json.loads(bootstrap_json)
    runtime = run_node_json(
        f"const bootstrap={bootstrap_json}; console.log(JSON.stringify({{"
        "budget:bootstrap.budgets.filter_main_thread_max_ms,"
        "slow:51 > Number(bootstrap.budgets.filter_main_thread_max_ms)"
        "}));"
    )

    assert bootstrap["schema_version"] == "atlas-inline-bootstrap.v1"
    assert bootstrap["budgets"]["filter_main_thread_max_ms"] == 50
    assert isinstance(bootstrap["budgets"]["filter_main_thread_max_ms"], int)
    assert runtime == {"budget": 50, "slow": True}
