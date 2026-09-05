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
console.log(JSON.stringify({
  zeroStart:clampTimeStart(0,100),
  playback,
  touching:featureInTimeWindow(layer,{time_start_bp:100,time_end_bp:200}),
  outside:featureInTimeWindow(layer,{time_start_bp:0,time_end_bp:99}),
  reversed:featureInTimeWindow(layer,{time_start_bp:300,time_end_bp:200}),
  untimedNarrow:featureInTimeWindow(layer,{time_mean_bp:null}),
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
    }


def test_time_controls_expose_canonical_interval_and_playback_direction() -> None:
    assert 'id="time-playback-toggle"' in MAP_DOCUMENT_TEMPLATE
    assert "Play oldest → present" in MAP_DOCUMENT_TEMPLATE
    assert "direction: rtl" in MAP_DOCUMENT_TEMPLATE
    assert "dockTimeSummary.textContent = `[${timeStartBp}, ${endBp}] BP`" in (
        MAP_DOCUMENT_TEMPLATE
    )


def test_provider_failure_reaches_no_basemap_without_mutating_evidence() -> None:
    basemap_helpers = template_block(
        "function nextBasemapAfter", "Object.entries(basemaps)"
    )
    observed = run_node_json(
        """
const BASEMAP_FALLBACK_ORDER=['voyager','light','terrain','none'];
const BASEMAP_NAMES=[...BASEMAP_FALLBACK_ORDER];
const failedBasemaps=new Set(['voyager','light','terrain']);
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
