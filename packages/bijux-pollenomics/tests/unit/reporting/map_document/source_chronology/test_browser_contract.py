from __future__ import annotations

import re
from pathlib import Path
import json
from typing import cast

from bijux_pollenomics.reporting.map_document import render_multi_country_map_html
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    ASSET_TABLE_STORED_FIELDS,
)
from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE
from bijux_pollenomics.reporting.map_publication import MapScopePolicy

from ..browser_semantics.support import (
    check_javascript_syntax,
    run_node_json,
    template_block,
)
from .support import (
    ASSET_TABLE_FIELDS,
    compact_bootstrap,
    compressed_node_asset,
    compressed_provenance_asset,
    sharded_index_payload,
)


def test_controls_are_accessible_source_native_and_separate_from_modeled_context() -> (
    None
):
    assert 'id="source-chronology-controls"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="source-chronology-level"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="source-chronology-code"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="source-chronology-taxon-query"' in MAP_DOCUMENT_TEMPLATE
    assert 'type="search"' in MAP_DOCUMENT_TEMPLATE
    assert 'aria-controls="source-chronology-taxon"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="source-chronology-taxon"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="source-chronology-taxon-shortcuts"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="source-chronology-state"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="source-time-density"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="source-time-density-bars"' in MAP_DOCUMENT_TEMPLATE
    assert (
        'id="time-stepper-status" class="time-stepper-status" type="button"'
        in MAP_DOCUMENT_TEMPLATE
    )
    assert "bins are not additive" in MAP_DOCUMENT_TEMPLATE
    assert "refreshTimeStepperStatus();" in MAP_DOCUMENT_TEMPLATE
    assert "mobilePanelReturnFocus = timeStepperStatus" in MAP_DOCUMENT_TEMPLATE
    assert (
        "sourceChronologyLevel.focus({ preventScroll: true })" in MAP_DOCUMENT_TEMPLATE
    )
    assert (
        "mobilePanelCloseButton.addEventListener('click', closeMobilePanel)"
        in MAP_DOCUMENT_TEMPLATE
    )
    assert (
        "mobilePanelReturnFocus.focus({ preventScroll: true })" in MAP_DOCUMENT_TEMPLATE
    )
    assert (
        "classList.contains('atlas-capture-mode') ? 'auto' : 'smooth'"
        in MAP_DOCUMENT_TEMPLATE
    )
    assert "source-reported taxon and pollen-type labels" in MAP_DOCUMENT_TEMPLATE
    assert "not a species assertion" in MAP_DOCUMENT_TEMPLATE
    assert "chronology context only" in MAP_DOCUMENT_TEMPLATE

    source_controls = template_block(
        '<details id="source-chronology-controls"',
        '<details id="modeled-context-controls"',
    )
    assert "modeled-context" not in source_controls
    assert "propagation evidence" in source_controls
    assert "migration" not in source_controls.lower()
    assert "caus" not in source_controls.lower()


def test_metadata_contract_fails_closed_and_dense_layers_are_opt_in() -> None:
    helpers = template_block(
        "const SOURCE_CHRONOLOGY_LEVEL_ORDER",
        "let activeCountries",
    )
    observed = run_node_json(
        """
function facets(level, rows={}) {
  const withExtent=(row)=>{
    const extended={...row,time_min_bp:row.node_count ? 100 : null,time_max_bp:row.node_count ? 900 : null};
    if (!row.node_count) return extended;
    return {...extended,time_density:{
      schema_version:'source-chronology-time-density.v1',temporal_direction:'oldest_to_present',
      interval_semantics:'[younger_bp, older_bp]',bin_admission:'closed_interval_overlap',bins_are_additive:false,
      node_count:row.node_count,observation_denominator:row.observation_denominator,time_min_bp:100,time_max_bp:900,
      bins:Array.from({length:12},(_,ordinal)=>({ordinal,younger_bp:100+((11-ordinal)*800/12),older_bp:100+((12-ordinal)*800/12),node_count:row.node_count,observation_denominator:row.observation_denominator})),
    }};
  };
  const overall=withExtent({node_count:2,observation_denominator:7});
  return {
    schema_version:'neotoma-source-chronology-facets.v3',
    node_level:level,
    ...overall,
    country_counts:[
      {value:'Sweden',node_count:2,observation_denominator:7},
      {value:'Denmark',node_count:0,observation_denominator:0},
      {value:'Norway',node_count:0,observation_denominator:0},
      {value:'Finland',node_count:0,observation_denominator:0},
    ].map(withExtent),
    source_unit_counts:[{value:'percent',node_count:2,observation_denominator:7}].map(withExtent),
    source_ecological_codes:(rows.codes || []).map(withExtent),
    source_taxa:(rows.taxa || []).map(withExtent),
  };
}
function layer(level, key, defaultEnabled, rows={}) {
  return {
    key, node_level:level, default_enabled:defaultEnabled, count:2,
    semantic_role:'source_chronology_context', propagation_status:'refused',
    edge_count:0, temporal_direction:'oldest_to_present',
    interval_semantics:'[younger_bp, older_bp]',
    facet_metadata:facets(level, rows),
  };
}
const sample=layer('source_sample_presence','sample',true);
const code=layer('source_ecological_code','code',false,{codes:[
  {value:'AQVP',label:'AQVP',feature_key:'source:code:AQVP',node_count:1,observation_denominator:2},
  {value:'TRSH',label:'TRSH',feature_key:'source:code:TRSH',node_count:1,observation_denominator:3},
  {value:'UPHE',label:'UPHE',feature_key:'source:code:UPHE',node_count:1,observation_denominator:2},
]});
const taxon=layer('source_taxon','taxon',false,{taxa:[
  {value:'source:taxon:41',source_taxon_id:'41',label:'Cerealia-type',node_count:2,observation_denominator:7},
]});
const invalidDense={...code,default_enabled:true};
const invalidDirection={...sample,temporal_direction:'present_to_oldest'};
const invalidDensity={...sample,facet_metadata:{...sample.facet_metadata,time_density:{...sample.facet_metadata.time_density,node_count:3}}};
const POINT_LAYERS=[sample,code,taxon];
let activeSourceChronologyCode='all';
let activeSourceChronologyTaxon='all';
"""
        + helpers
        + """
const sourcePosture={semantic_role:'source_chronology_context',propagation_eligible:false,candidate_generation_status:'refused',candidate_refusal_reason:'source_chronology_context_only'};
const codeFeature={...sourcePosture,node_level:'source_ecological_code',feature_key:'source:code:TRSH',source_unit:'percent',source_ecological_code:'TRSH',source_reported_name:null,source_taxon_id:null};
const taxonFeature={...sourcePosture,node_level:'source_taxon',feature_key:'source:taxon:41',source_unit:'percent',source_ecological_code:null,source_reported_name:'Cerealia-type',source_taxon_id:'41'};
console.log(JSON.stringify({
  levels:sourceChronologyLayers().map((entry)=>entry.node_level),
  literals:code.facet_metadata.source_ecological_codes.map((row)=>row.value),
  denseDefaultRejected:sourceChronologyLayerIsValid(invalidDense),
  directionRejected:sourceChronologyLayerIsValid(invalidDirection),
  densityDriftRejected:sourceChronologyLayerIsValid(invalidDensity),
  countryOrderRejected:sourceChronologyLayerIsValid({...sample,facet_metadata:{...sample.facet_metadata,country_counts:[...sample.facet_metadata.country_counts].reverse()}}),
  malformedRejected:sourceChronologyLayerIsValid({...code,facet_metadata:null}),
  stringExtentRejected:sourceChronologyLayerIsValid({...code,facet_metadata:{...code.facet_metadata,time_min_bp:'100'}}),
  codeSelected:sourceChronologyFeatureMatches(code,codeFeature,'TRSH','all'),
  codeExcluded:sourceChronologyFeatureMatches(code,codeFeature,'AQVP','all'),
  codeNullRejected:sourceChronologyFeatureMatches(code,{...codeFeature,source_ecological_code:null},'all','all'),
  taxonSelected:sourceChronologyFeatureMatches(taxon,taxonFeature,'all','source:taxon:41'),
  taxonExcluded:sourceChronologyFeatureMatches(taxon,taxonFeature,'all','source:taxon:99'),
  taxonNullRejected:sourceChronologyFeatureMatches(taxon,{...taxonFeature,source_taxon_id:null},'all','all'),
  crossLevelRejected:sourceChronologyFeatureMatches(code,{...codeFeature,node_level:'source_taxon'},'all','all'),
  postureRejected:sourceChronologyFeatureMatches(code,{...codeFeature,propagation_eligible:true},'all','all'),
  unrelatedUnaffected:sourceChronologyFeatureMatches({semantic_role:'other'},{},'all','all'),
}));
"""
    )

    assert observed == {
        "levels": [
            "source_sample_presence",
            "source_ecological_code",
            "source_taxon",
        ],
        "literals": ["AQVP", "TRSH", "UPHE"],
        "denseDefaultRejected": False,
        "directionRejected": False,
        "densityDriftRejected": False,
        "countryOrderRejected": False,
        "malformedRejected": False,
        "stringExtentRejected": False,
        "codeSelected": True,
        "codeExcluded": False,
        "codeNullRejected": False,
        "taxonSelected": True,
        "taxonExcluded": False,
        "taxonNullRejected": False,
        "crossLevelRejected": False,
        "postureRejected": False,
        "unrelatedUnaffected": True,
    }


def test_denominators_and_exact_source_identity_drive_selector_state() -> None:
    renderer = template_block(
        "function selectSourceChronologyLevel",
        "function renderLayerControls",
    )
    assert "selectedFacet.node_count" in renderer
    assert "selectedFacet.observation_denominator" in renderer
    assert "if (!selectedFacet)" in renderer
    assert "source taxon ${escapeHtml(row.source_taxon_id)}" in renderer
    assert "row.value === activeSourceChronologyTaxon" in renderer
    assert "`${row.label} ${row.source_taxon_id}`" in renderer
    assert "denominator before country and BP-window filters" in renderer


def test_hash_filters_are_distinct_and_source_selection_drives_playback() -> None:
    assert "sourceChronologyLevel: params.get('source_chronology_level')" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "sourceChronologyCode: params.get('source_ecological_code')" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "sourceChronologyTaxon: params.get('source_taxon')" in (
        MAP_DOCUMENT_TEMPLATE
    )
    hash_block = template_block(
        "function syncHashState()", "function clearHighlightedPoint"
    )
    assert (
        "params.set('source_chronology_level', activeSourceChronologyLevel)"
        in hash_block
    )
    assert (
        "params.set('source_ecological_code', activeSourceChronologyCode)" in hash_block
    )
    assert "params.set('source_taxon', activeSourceChronologyTaxon)" in hash_block
    assert (
        "initialState.sourceChronologyLevel && initialSourceChronologyLayer && "
        "initialState.layers === null" in MAP_DOCUMENT_TEMPLATE
    )

    handlers = template_block(
        "sourceChronologyLevel.addEventListener",
        "densityOpacitySlider.addEventListener",
    )
    assert "timeStartBp" not in handlers
    assert "timeIntervalYears" not in handlers
    assert "modeledContext" not in handlers
    assert "Play oldest → present" in MAP_DOCUMENT_TEMPLATE
    assert "direction: rtl" in MAP_DOCUMENT_TEMPLATE
    assert "sourceChronologyPlaybackSelection()" in MAP_DOCUMENT_TEMPLATE
    assert "source playback extent ${extentLabel}" in MAP_DOCUMENT_TEMPLATE
    assert "slider, arrows, and playback use that exact sample" in MAP_DOCUMENT_TEMPLATE
    assert "Disable the source layer to navigate the complete atlas span" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "timeStartSlider.min = String(navigationExtent.time_min_bp)" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "timeStartSlider.max = String(Math.max(navigationExtent.time_min_bp" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "timeIntervalSlider.max = String(navigationSpan)" in MAP_DOCUMENT_TEMPLATE
    assert "!initialTimeWindowIsExplicit) focusSourceChronologyNavigation()" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "untimed source nodes excluded before viewport filtering" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "stopTimePlayback();\n        activeSourceChronologyCode" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "stopTimePlayback();\n        activeSourceChronologyTaxon" in (
        MAP_DOCUMENT_TEMPLATE
    )


def test_source_shortcuts_preserve_literal_semantics_and_reset_exact_taxa() -> None:
    assert "Source sample presence" in MAP_DOCUMENT_TEMPLATE
    assert "Find cereal-like labels" in MAP_DOCUMENT_TEMPLATE
    assert "Whole pollen sites" not in MAP_DOCUMENT_TEMPLATE
    handlers = template_block(
        "document.querySelectorAll('[data-source-shortcut]')",
        "countryPairFilter.addEventListener",
    )
    assert (
        "sourceChronologyTaxonSearch = shortcut === 'cereals' ? 'cereal|secale'"
        in handlers
    )
    assert "sourceChronologyTaxonQuery.value = sourceChronologyTaxonSearch" in handlers
    assert "shortcut === 'taxa'" in handlers
    assert "activeSourceChronologyTaxon = 'all'" in handlers
    assert "row.label.trim().toLowerCase() === 'secale'" in handlers
    assert "row.source_taxon_id === '967'" in handlers
    assert "preferredCerealFacet?.value" in handlers


def test_taxon_search_exposes_distinct_exact_source_identity_shortcuts() -> None:
    renderer = template_block(
        "function renderSourceChronologyControls",
        "function renderLayerControls",
    )
    assert "data-source-taxon-facet" in renderer
    assert "${escapeHtml(row.label)} · ${escapeHtml(row.source_taxon_id)}" in renderer
    assert "button.dataset.sourceTaxonFacet" in renderer
    assert "activeSourceChronologyTaxon = normalizedSingleValue" in renderer
    assert "queryAlternatives.length" in renderer


def test_restore_defaults_returns_to_the_source_chronology_landing_window() -> None:
    restore = template_block(
        "async function restoreDefaults", "searchInput.addEventListener"
    )
    assert "activeSourceChronologyLevel = defaultSourceChronologyLevel" in restore
    assert "timeStartBp = DEFAULT_TIME_START_BP" in restore
    assert "timeIntervalYears = DEFAULT_TIME_INTERVAL_YEARS" in restore
    assert "focusSourceChronologyNavigation()" in restore


def test_source_facet_extent_bounds_automatic_playback_without_global_empty_frames() -> (
    None
):
    controls = template_block("function finiteControlNumber", "const initialState")
    observed = run_node_json(
        """
const TIME_MIN_BP=0, TIME_MAX_BP=2700000, TIME_HAS_DATA=true;
const DEFAULT_TIME_START_BP=2699900, DEFAULT_TIME_INTERVAL_YEARS=100;
const TIME_INTERVAL_MAX=2700000;
const reducedMotionQuery={matches:false};
const timePlaybackToggle={setAttribute(){},textContent:'',disabled:false,title:''};
const timeStartSlider={},timeIntervalSlider={},dockTimeSummary={};
const timeStartValue={},timeIntervalValue={};
const window={clearTimeout(){},setTimeout(){return 1},location:{hash:''}};
const mobileLayoutQuery={matches:false};
let timeStartBp=200,timeIntervalYears=100;
let selection={time_min_bp:100,time_max_bp:900,selection_key:'taxon|41|100|900'};
function sourceChronologyPlaybackSelection(){return selection}
async function renderMapState(){}
function deactivateModeledContext(){}
"""
        + controls
        + """
const extent=selectedTimePlaybackExtent();
const starts=[];
let cursor=oldestPlaybackStart(100,extent);
while(true){starts.push(cursor);const next=nextPlaybackTimeStart(cursor,100,extent);if(next===cursor)break;cursor=next;}
console.log(JSON.stringify({extent,frames:automaticPlaybackFrameCount(100),starts}));
"""
    )

    assert observed == {
        "extent": {
            "time_min_bp": 100,
            "time_max_bp": 900,
            "selection_key": "taxon|41|100|900",
        },
        "frames": 8,
        "starts": [800, 700, 600, 500, 400, 300, 200, 100],
    }


def test_source_shortcuts_open_real_chronology_levels_and_cereal_labels() -> None:
    assert 'data-source-shortcut="sample"' in MAP_DOCUMENT_TEMPLATE
    for source_code in ("TRSH", "UPHE", "AQVP"):
        assert f'data-source-shortcut="{source_code}"' in MAP_DOCUMENT_TEMPLATE
    assert 'data-source-shortcut="cereals"' in MAP_DOCUMENT_TEMPLATE
    assert "sourceChronologyTaxonSearch = shortcut === 'cereals' ? 'cereal|secale'" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "/cereal|secale/i.test(row.label)" in MAP_DOCUMENT_TEMPLATE
    assert "focusSourceChronologyNavigation();" in MAP_DOCUMENT_TEMPLATE


def test_topbar_chronology_status_reports_off_and_visible_source_counts() -> None:
    status_helper = template_block(
        "function refreshTimeStepperStatus",
        "function renderLayerControls",
    )
    observed = run_node_json(
        """
const TIME_HAS_DATA=true;
const timeStepperStatus={disabled:false,textContent:'',title:''};
const selectedLayer={key:'source-code',node_level:'source_ecological_code'};
const activeLayerKeys=new Set();
const activeSourceChronologyLevel='source_ecological_code';
const activeSourceChronologyCode='TRSH';
const activeSourceChronologyTaxon='all';
const selectedFacet={node_count:10,observation_denominator:40};
const visiblePointEntries=[
  {layer:selectedLayer,feature:{observation_denominator:3}},
  {layer:selectedLayer,feature:{observation_denominator:5}},
];
const sourceRecordConcentrationActive=false;
const sourceRecordConcentrationSnapshot=null;
let timeStartBp=100;
function timeWindowEndBp(){return 200}
function sourceChronologyLayers(){return [selectedLayer]}
function sourceChronologyLayerForLevel(){return selectedLayer}
function sourceChronologyFacetForSelection(){return selectedFacet}
function sourceRecordConcentrationFacetLabel(){return 'literal source code TRSH'}
function sourceChronologyCount(value){return Number.isSafeInteger(value) && value >= 0 ? value : null}
"""
        + status_helper
        + """
refreshTimeStepperStatus();
const off=timeStepperStatus.textContent;
activeLayerKeys.add('source-code');
refreshTimeStepperStatus();
console.log(JSON.stringify({off,active:timeStepperStatus.textContent,disabled:timeStepperStatus.disabled}));
"""
    )

    assert observed == {
        "off": "Source chronology off · [100, 200] BP · complete atlas extent",
        "active": (
            "literal source code TRSH · 2/10 nodes · 8/40 observations · [100, 200] BP"
        ),
        "disabled": False,
    }


def test_manual_chronology_arrows_move_exactly_one_window() -> None:
    controls = template_block("function finiteControlNumber", "const initialState")
    observed = run_node_json(
        """
const TIME_MIN_BP=0, TIME_MAX_BP=1000, TIME_HAS_DATA=true;
const DEFAULT_TIME_START_BP=0, DEFAULT_TIME_INTERVAL_YEARS=1000;
const TIME_INTERVAL_MAX=1000;
const reducedMotionQuery={matches:false};
const timePlaybackToggle={setAttribute(){},textContent:'',disabled:false,title:''};
const timeStartSlider={},timeIntervalSlider={},dockTimeSummary={};
const timeStartValue={},timeIntervalValue={};
const timeStepOlder={},timeStepNewer={},timeStepperStatus={};
const window={clearTimeout(){},setTimeout(){return 1},location:{hash:''}};
const mobileLayoutQuery={matches:false};
let timeStartBp=400,timeIntervalYears=100;
function sourceChronologyPlaybackSelection(){return {time_min_bp:100,time_max_bp:900,selection_key:'TRSH'}}
async function renderMapState(){}
"""
        + controls
        + """
console.log(JSON.stringify({
  older:previousPlaybackTimeStart(timeStartBp,timeIntervalYears),
  newer:nextPlaybackTimeStart(timeStartBp,timeIntervalYears),
  oldest:previousPlaybackTimeStart(800,timeIntervalYears),
  present:nextPlaybackTimeStart(100,timeIntervalYears),
}));
"""
    )

    assert observed == {"older": 500, "newer": 300, "oldest": 800, "present": 100}


def test_playback_rechecks_restored_interval_after_leaving_modeled_context() -> None:
    controls = template_block("function finiteControlNumber", "const initialState")
    observed = run_node_json(
        """
const TIME_MIN_BP=0, TIME_MAX_BP=2700000, TIME_HAS_DATA=true;
const DEFAULT_TIME_START_BP=2699900, DEFAULT_TIME_INTERVAL_YEARS=100;
const TIME_INTERVAL_MAX=2700000;
const reducedMotionQuery={matches:false};
const timePlaybackToggle={setAttribute(){},textContent:'',disabled:false,title:''};
const timeStartSlider={},timeIntervalSlider={},dockTimeSummary={};
const timeStartValue={},timeIntervalValue={};
const window={clearTimeout(){},setTimeout(){throw new Error('timer must not run')},location:{hash:''}};
const mobileLayoutQuery={matches:false};
let timeStartBp=200,timeIntervalYears=100;
function sourceChronologyPlaybackSelection(){return {time_min_bp:100,time_max_bp:900,selection_key:'taxon'}}
function deactivateModeledContext(){timeIntervalYears=1000}
async function renderMapState(){throw new Error('blocked playback must not render')}
"""
        + controls
        + """
startTimePlayback().then(() => console.log(JSON.stringify({timer:timePlaybackTimer,interval:timeIntervalYears,disabled:timePlaybackToggle.disabled})));
"""
    )

    assert observed == {"timer": None, "interval": 1000, "disabled": True}


def test_untimed_exclusion_uses_previewport_asset_counts_and_refuses_ambiguity() -> (
    None
):
    helpers = template_block(
        "const SOURCE_CHRONOLOGY_LEVEL_ORDER",
        "let activeCountries",
    )
    observed = run_node_json(
        """
const sourceLayer={
  key:'source-code',node_level:'source_ecological_code',default_enabled:false,count:2,
  semantic_role:'source_chronology_context',propagation_status:'refused',edge_count:0,
  temporal_direction:'oldest_to_present',interval_semantics:'[younger_bp, older_bp]',
  applies_country_filter:true,
  facet_metadata:{
    schema_version:'neotoma-source-chronology-facets.v3',node_level:'source_ecological_code',
    node_count:2,observation_denominator:2,time_min_bp:100,time_max_bp:900,
    time_density:{
      schema_version:'source-chronology-time-density.v1',temporal_direction:'oldest_to_present',
      interval_semantics:'[younger_bp, older_bp]',bin_admission:'closed_interval_overlap',bins_are_additive:false,
      node_count:2,observation_denominator:2,time_min_bp:100,time_max_bp:900,
      bins:Array.from({length:12},(_,ordinal)=>({ordinal,younger_bp:100+((11-ordinal)*800/12),older_bp:100+((12-ordinal)*800/12),node_count:2,observation_denominator:2})),
    },
    country_counts:[
      {value:'Sweden',node_count:2,observation_denominator:2,time_min_bp:100,time_max_bp:900},
      {value:'Denmark',node_count:0,observation_denominator:0,time_min_bp:null,time_max_bp:null},
      {value:'Norway',node_count:0,observation_denominator:0,time_min_bp:null,time_max_bp:null},
      {value:'Finland',node_count:0,observation_denominator:0,time_min_bp:null,time_max_bp:null},
    ],
    source_unit_counts:[{value:'percent',node_count:2,observation_denominator:2,time_min_bp:100,time_max_bp:900}],
    source_ecological_codes:[{value:'TRSH',label:'TRSH',feature_key:'source:code:TRSH',node_count:2,observation_denominator:2,time_min_bp:100,time_max_bp:900,time_density:{
      schema_version:'source-chronology-time-density.v1',temporal_direction:'oldest_to_present',
      interval_semantics:'[younger_bp, older_bp]',bin_admission:'closed_interval_overlap',bins_are_additive:false,
      node_count:2,observation_denominator:2,time_min_bp:100,time_max_bp:900,
      bins:Array.from({length:12},(_,ordinal)=>({ordinal,younger_bp:100+((11-ordinal)*800/12),older_bp:100+((12-ordinal)*800/12),node_count:2,observation_denominator:2})),
    }}],
    source_taxa:[],
  },
};
const POINT_LAYERS=[sourceLayer];
const STATIC_ATLAS_INLINE=false;
let STATIC_ATLAS_BOOTSTRAP={assets:[
  {asset_key:'sweden',domain:'nodes',layer_key:'source-code',country_keys:['Sweden'],record_count:2,untimed_record_count:1},
  {asset_key:'norway',domain:'nodes',layer_key:'source-code',country_keys:['Norway'],record_count:2,untimed_record_count:2},
]};
const activeLayerKeys=new Set(['source-code']);
let activeCountries=new Set(['Sweden']);
let activeSourceChronologyLevel='source_ecological_code';
let activeSourceChronologyCode='all';
let activeSourceChronologyTaxon='all';
function staticAtlasNonnegativeInteger(value){return Number(value)}
function featureTimeWindow(){return null}
"""
        + helpers
        + """
const exact=sourceChronologyUntimedExclusion(sourceLayer);
STATIC_ATLAS_BOOTSTRAP={assets:[
  {asset_key:'mixed',domain:'nodes',layer_key:'source-code',country_keys:['Sweden','Norway'],record_count:4,untimed_record_count:1},
]};
const mixed=sourceChronologyUntimedExclusion(sourceLayer);
STATIC_ATLAS_BOOTSTRAP={assets:[
  {asset_key:'sweden',domain:'nodes',layer_key:'source-code',country_keys:['Sweden'],record_count:2,untimed_record_count:1},
]};
activeSourceChronologyCode='TRSH';
const facet=sourceChronologyUntimedExclusion(sourceLayer);
console.log(JSON.stringify({exact,mixed,facet}));
"""
    )

    assert observed == {
        "exact": {"status": "available", "count": 1},
        "mixed": {"status": "unavailable", "count": None},
        "facet": {"status": "unavailable", "count": None},
    }


def test_point_visibility_applies_source_filter_without_touching_other_layers() -> None:
    visibility = template_block(
        "function pointFeatureVisible", "function polygonFeatureVisible"
    )
    assert "sourceChronologyFeatureMatches(layer, feature)" in visibility
    assert visibility.index("pointFeatureInTimeWindow") < visibility.index(
        "sourceChronologyFeatureMatches"
    )


def test_popup_keeps_source_identity_and_interpretation_posture_visible() -> None:
    popup = template_block("function sourceChronologyPopupHtml", "function popupHtml")
    assert "Source-native chronology context" in popup
    assert "Literal ecological code" in popup
    assert "Source-reported label" in popup
    assert "Source taxon identifier" in popup
    assert "Literal source unit" in popup
    assert "Contributing observations" in popup
    assert "Chronology context only; propagation use refused." in popup
    assert "species" not in popup.lower()


def test_restore_defaults_returns_to_sample_presence_and_all_source_facets() -> None:
    restore = template_block(
        "async function restoreDefaults", "document.getElementById('countries-all')"
    )
    assert "activeSourceChronologyLevel = defaultSourceChronologyLevel" in restore
    assert "activeSourceChronologyCode = 'all'" in restore
    assert "activeSourceChronologyTaxon = 'all'" in restore
    assert "sourceChronologyTaxonSearch = ''" in restore


def test_generic_layer_toggle_preserves_one_source_level_and_allows_off() -> None:
    helpers = template_block(
        "function selectSourceChronologyLevel",
        "function renderSourceChronologyControls",
    )
    observed = run_node_json(
        """
const sourceLayers=[
  {key:'sample',node_level:'source_sample_presence',semantic_role:'source_chronology_context'},
  {key:'code',node_level:'source_ecological_code',semantic_role:'source_chronology_context'},
  {key:'taxon',node_level:'source_taxon',semantic_role:'source_chronology_context'},
];
const other={key:'other',node_level:null,semantic_role:'other'};
const ALL_LAYERS=[...sourceLayers,other];
const activeLayerKeys=new Set(['sample','code','taxon']);
let activeSourceChronologyLevel='source_sample_presence';
function sourceChronologyLayers(){return sourceLayers}
function sourceChronologyLayerForLevel(level){return sourceLayers.find((layer)=>layer.node_level===level)||null}
function stopTimePlayback(){}
let sourceRecordConcentrationActive=false;
"""
        + helpers
        + """
toggleLayerSelection('code',true);
const codeOnly={active:[...activeLayerKeys].sort(),level:activeSourceChronologyLevel};
toggleLayerSelection('code',false);
const sourceOff={active:[...activeLayerKeys].sort(),level:activeSourceChronologyLevel};
toggleLayerSelection('taxon',true);
toggleLayerSelection('other',true);
console.log(JSON.stringify({
  codeOnly,
  sourceOff,
  taxonAndOther:{active:[...activeLayerKeys].sort(),level:activeSourceChronologyLevel},
}));
"""
    )

    assert observed == {
        "codeOnly": {"active": ["code"], "level": "source_ecological_code"},
        "sourceOff": {"active": [], "level": "source_ecological_code"},
        "taxonAndOther": {
            "active": ["other", "taxon"],
            "level": "source_taxon",
        },
    }
    layer_controls = template_block(
        "function renderLayerControls", "function renderAnimalEvidencePanel"
    )
    assert "toggleLayerSelection(checkbox.value, checkbox.checked)" in layer_controls
    presets = template_block("function applyLayerPreset", "function renderLegend")
    assert "if (activeSourceLayerCount > 1)" in presets


def test_rendered_browser_javascript_is_syntactically_valid(tmp_path: Path) -> None:
    policy = MapScopePolicy(
        key="source-chronology-test",
        label="Source chronology test",
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
    rendered = render_multi_country_map_html(
        "Source chronology test",
        "source-chronology-test-build",
        "2026-09-05",
        ("Sweden",),
        policy,
        [],
        [],
        "assets",
    )
    executable_scripts = [
        body
        for attributes, body in re.findall(
            r"<script([^>]*)>(.*?)</script>", rendered, flags=re.DOTALL
        )
        if 'type="application/json"' not in attributes
    ]
    check_javascript_syntax("\n".join(executable_scripts), tmp_path / "atlas.js")


def test_sharded_indexes_merge_without_dropped_references() -> None:
    helpers = template_block(
        "const STATIC_ATLAS_INDEX_KINDS", "function validateStaticAtlasPayload"
    )
    payload = json.dumps(sharded_index_payload(), separators=(",", ":"))
    observed = run_node_json(
        f"""
const STATIC_ATLAS_BOOTSTRAP={{budgets:{{chunk_max_bytes:4194304}}}};
function staticAtlasFailure(message){{throw new Error(`Static atlas data cannot be loaded: ${{message}}`)}}
function staticAtlasNonnegativeInteger(value,label){{
  const numeric=Number(value);
  if(!Number.isSafeInteger(numeric)||numeric<0) staticAtlasFailure(`${{label}} is invalid`);
  return numeric;
}}
async function staticAtlasSha256(text){{
  const digest=await globalThis.crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));
  return Array.from(new Uint8Array(digest)).map((value)=>value.toString(16).padStart(2,'0')).join('');
}}
{helpers}
const row={{asset_key:'indexes:1',record_count:4}};
const payload={payload};
(async()=>{{
  const merged=await staticAtlasMergeIndexShards(row,payload);
  console.log(JSON.stringify({{
    schema:merged.schema_version,
    referenceCount:merged.reference_count,
    countries:merged.country_feature_indexes,
    spatial:merged.spatial_degree_feature_indexes,
    time:merged.time_interval_feature_indexes,
    signals:merged.signal_layer_indexes,
    details:merged.detail_record_asset_keys,
  }}));
}})();
"""
    )

    assert observed == {
        "schema": "atlas-static-indexes.v2",
        "referenceCount": 4,
        "countries": {
            "Norway": {"source-samples": [1]},
            "Sweden": {"source-samples": [0, 2]},
        },
        "spatial": {"59:18": {"source-samples": [0, 1]}},
        "time": [[100, 200, "source-samples", 0]],
        "signals": {"source-samples": ["source-samples"]},
        "details": {"neotoma:site:1": "details:1"},
    }


def test_sharded_indexes_reject_duplicate_missing_and_count_drift() -> None:
    helpers = template_block(
        "const STATIC_ATLAS_INDEX_KINDS", "function validateStaticAtlasPayload"
    )
    duplicate = json.dumps(
        sharded_index_payload(duplicate_country=True), separators=(",", ":")
    )
    missing_payload = sharded_index_payload()
    missing_shards = list(cast(list[dict[str, object]], missing_payload["shards"]))
    missing_payload["shards"] = missing_shards[:-1]
    missing_payload["shard_count"] = len(missing_shards) - 1
    missing = json.dumps(missing_payload, separators=(",", ":"))
    drift_payload = sharded_index_payload()
    drift_payload["reference_count"] = 5
    drift = json.dumps(drift_payload, separators=(",", ":"))
    shard_count_payload = sharded_index_payload()
    shard_count_rows = cast(list[dict[str, object]], shard_count_payload["shards"])
    shard_count_rows[0]["record_count"] = 2
    shard_count = json.dumps(shard_count_payload, separators=(",", ":"))
    observed = run_node_json(
        f"""
const STATIC_ATLAS_BOOTSTRAP={{budgets:{{chunk_max_bytes:4194304}}}};
function staticAtlasFailure(message){{throw new Error(`Static atlas data cannot be loaded: ${{message}}`)}}
function staticAtlasNonnegativeInteger(value,label){{
  const numeric=Number(value);
  if(!Number.isSafeInteger(numeric)||numeric<0) staticAtlasFailure(`${{label}} is invalid`);
  return numeric;
}}
async function staticAtlasSha256(text){{
  const digest=await globalThis.crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));
  return Array.from(new Uint8Array(digest)).map((value)=>value.toString(16).padStart(2,'0')).join('');
}}
{helpers}
async function refusal(payload,row){{
  try {{ await staticAtlasMergeIndexShards(row,payload); return null; }}
  catch(error) {{ return error.message; }}
}}
(async()=>{{
  console.log(JSON.stringify({{
    duplicate:await refusal({duplicate},{{asset_key:'indexes:1',record_count:4}}),
    missing:await refusal({missing},{{asset_key:'indexes:1',record_count:4}}),
    drift:await refusal({drift},{{asset_key:'indexes:1',record_count:5}}),
    shardCount:await refusal({shard_count},{{asset_key:'indexes:1',record_count:4}}),
  }}));
}})();
"""
    )

    assert "duplicated or out of order" in observed["duplicate"]
    assert "index shard kind is missing" in observed["missing"]
    assert "merged reference count mismatch" in observed["drift"]
    assert "record count mismatch" in observed["shardCount"]


def test_index_runtime_retains_single_payload_compatibility() -> None:
    assert (
        "indexes: ['atlas-static-indexes.v1', 'atlas-static-indexes.v2', "
        "'atlas-static-indexes.v3']" in MAP_DOCUMENT_TEMPLATE
    )
    consume = template_block(
        "async function consumeStaticAtlasAsset", "function loadStaticAtlasAsset"
    )
    assert (
        "row.domain === 'indexes' && payload.schema_version === "
        "'atlas-static-indexes.v3'" in consume
    )
    assert ": payload;" in consume
    assert "STATIC_ATLAS_CHUNKS[row.domain] = acceptedPayload" in consume


def test_large_static_indexes_are_lazy_without_losing_detail_or_country_support() -> (
    None
):
    startup = template_block(
        "if (!STATIC_ATLAS_INLINE)", "function hydrateStaticAtlasLayers"
    )
    assert "candidate.initial_load === true" in startup
    assert "STATIC_ATLAS_CHUNKS.provenance" in startup
    assert "STATIC_ATLAS_CHUNKS.edges" in startup
    assert "STATIC_ATLAS_CHUNKS.sequences" in startup
    assert "STATIC_ATLAS_CHUNKS.indexes" not in startup

    detail_lookup = template_block(
        "async function detailTabsForRecordId", "async function detailTabsForFeature"
    )
    assert "await ensureStaticAtlasIndexesLoaded()" in detail_lookup
    assert "detail_index_load_failed" in detail_lookup

    country_controls = template_block(
        "function renderCountryControls", "function renderScientificControls"
    )
    assert "visiblePointEntries.filter" in country_controls
    assert "feature.country === country" in country_controls
    assert "STATIC_ATLAS_BOOTSTRAP.assets" not in country_controls
    assert "STATIC_ATLAS_CHUNKS.indexes" not in country_controls


def test_lazy_index_loader_is_one_time_and_refuses_invalid_inventory() -> None:
    loader = template_block(
        "async function ensureStaticAtlasIndexesLoaded",
        "async function detailTabsForRecordId",
    )
    observed = run_node_json(
        f"""
function staticAtlasNonnegativeInteger(value,label){{
  const numeric=Number(value);
  if(!Number.isSafeInteger(numeric)||numeric<0) throw new Error(`${{label}} is invalid`);
  return numeric;
}}
async function probe(assets, existingIndexes, interactionBytes, loadOutcome){{
  const STATIC_ATLAS_INLINE=false;
  const STATIC_ATLAS_BOOTSTRAP={{assets,budgets:{{interaction_max_bytes:interactionBytes}}}};
  const STATIC_ATLAS_CHUNKS={{indexes:existingIndexes}};
  let loadCount=0;
  async function loadStaticAtlasAsset(row){{
    loadCount+=1;
    if(loadOutcome==='failure') throw new Error('request failed');
    STATIC_ATLAS_CHUNKS.indexes={{detail_record_asset_keys:{{'site:1':'details:2'}}}};
  }}
  {loader}
  const first=await ensureStaticAtlasIndexesLoaded();
  const second=loadOutcome==='valid' ? await ensureStaticAtlasIndexesLoaded() : null;
  return {{first,second,loadCount}};
}}
const indexRow={{asset_key:'indexes:1',domain:'indexes',byte_count:512}};
(async()=>{{
  console.log(JSON.stringify({{
    already:await probe([indexRow],{{detail_record_asset_keys:{{}}}},1024,'valid'),
    valid:await probe([indexRow],null,1024,'valid'),
    missing:await probe([],null,1024,'valid'),
    duplicate:await probe([indexRow,{{...indexRow,asset_key:'indexes:2'}}],null,1024,'valid'),
    oversized:await probe([indexRow],null,511,'valid'),
    loadFailure:await probe([indexRow],null,1024,'failure'),
  }}));
}})();
"""
    )

    assert observed == {
        "already": {"first": True, "second": True, "loadCount": 0},
        "valid": {"first": True, "second": True, "loadCount": 1},
        "missing": {"first": False, "second": False, "loadCount": 0},
        "duplicate": {"first": False, "second": False, "loadCount": 0},
        "oversized": {"first": False, "second": False, "loadCount": 0},
        "loadFailure": {"first": False, "second": None, "loadCount": 1},
    }


def test_compressed_node_transport_is_bounded_authenticated_and_counted() -> None:
    valid_row, valid_envelope = compressed_node_asset("nodes:valid")
    drift_row, drift_envelope = compressed_node_asset("nodes:drift")
    drift_row["decoded_byte_count"] = cast(int, drift_row["decoded_byte_count"]) + 1
    over_row, over_envelope = compressed_node_asset(
        "nodes:over", padding="x" * 4096, decoded_byte_count=900
    )
    digest_row, digest_envelope = compressed_node_asset(
        "nodes:digest", payload_sha256="0" * 64
    )
    runtime = template_block(
        "async function staticAtlasSha256", "function loadStaticAtlasAsset"
    )
    observed = run_node_json(
        f"""
const STATIC_ATLAS_BOOTSTRAP={{
  build_id:'atlas-{"a" * 64}',scope_slug:'nordic',version:'test',
  budgets:{{chunk_max_bytes:1024}},
}};
const STATIC_ATLAS_SCHEMAS={{nodes:['atlas-node-chunk.v1'],details:['atlas-details-chunk.v1'],provenance:[],edges:[],sequences:[],indexes:['atlas-static-indexes.v1','atlas-static-indexes.v2','atlas-static-indexes.v3']}};
const STATIC_ATLAS_RAW_CHUNKS={json.dumps([valid_envelope, drift_envelope, over_envelope, digest_envelope], separators=(",", ":"))};
const STATIC_ATLAS_CHUNKS={{nodes:[],details:[]}};
const staticAtlasLoadedAssets=new Set();
function staticAtlasFailure(message){{throw new Error(`Static atlas data cannot be loaded: ${{message}}`)}}
function staticAtlasNonnegativeInteger(value,label){{
  const numeric=Number(value);
  if(!Number.isSafeInteger(numeric)||numeric<0) staticAtlasFailure(`${{label}} is invalid`);
  return numeric;
}}
{runtime}
async function refusal(row){{
  try {{ await consumeStaticAtlasAsset(row); return null; }}
  catch(error) {{ return error.message; }}
}}
(async()=>{{
  await consumeStaticAtlasAsset({json.dumps(valid_row, separators=(",", ":"))});
  console.log(JSON.stringify({{
    valid:{{loaded:[...staticAtlasLoadedAssets],nodeCount:STATIC_ATLAS_CHUNKS.nodes.length}},
    sizeDrift:await refusal({json.dumps(drift_row, separators=(",", ":"))}),
    overBudget:await refusal({json.dumps(over_row, separators=(",", ":"))}),
    digestDrift:await refusal({json.dumps(digest_row, separators=(",", ":"))}),
  }}));
}})();
"""
    )

    assert observed["valid"] == {"loaded": ["nodes:valid"], "nodeCount": 1}
    assert "decoded byte count mismatch" in observed["sizeDrift"]
    assert "decoded payload exceeds its byte budget" in observed["overBudget"]
    assert "payload integrity mismatch" in observed["digestDrift"]


def test_bootstrap_allows_governed_compressed_domains_without_weakening_legacy_json() -> (
    None
):
    bootstrap = template_block(
        "function validateStaticAtlasBootstrap", "async function staticAtlasSha256"
    )
    assert "!['provenance', 'nodes', 'details'].includes(row.domain)" in bootstrap
    assert (
        "['provenance', 'nodes', 'details'].includes(row.domain) && "
        "payloadEncoding === 'gzip_base64'" in bootstrap
    )
    assert "row.decoded_byte_count" in bootstrap
    consume = template_block(
        "async function consumeStaticAtlasAsset", "function loadStaticAtlasAsset"
    )
    assert "staticAtlasBoundedGunzip" in consume
    assert "new Response(stream).text()" not in consume
    assert "const payloadEncoding = row.payload_encoding || 'json'" in consume


def test_compressed_provenance_uses_bounded_authenticated_transport() -> None:
    row, envelope = compressed_provenance_asset()
    refused_row, refused_envelope = compressed_provenance_asset(
        "provenance:drift", decoded_byte_count=1
    )
    runtime = template_block(
        "async function staticAtlasSha256", "function loadStaticAtlasAsset"
    )
    observed = run_node_json(
        f"""
const STATIC_ATLAS_BOOTSTRAP={{
  build_id:'atlas-{"a" * 64}',scope_slug:'nordic',version:'test',
  budgets:{{chunk_max_bytes:4096}},
}};
const STATIC_ATLAS_SCHEMAS={{nodes:[],details:[],provenance:['atlas-provenance-chunk.v3'],edges:[],sequences:[],indexes:[]}};
const STATIC_ATLAS_RAW_CHUNKS={json.dumps([envelope, refused_envelope], separators=(",", ":"))};
const STATIC_ATLAS_CHUNKS={{nodes:[],details:[],provenance:null}};
const staticAtlasLoadedAssets=new Set();
function staticAtlasFailure(message){{throw new Error(`Static atlas data cannot be loaded: ${{message}}`)}}
function staticAtlasNonnegativeInteger(value,label){{
  const numeric=Number(value);
  if(!Number.isSafeInteger(numeric)||numeric<0) staticAtlasFailure(`${{label}} is invalid`);
  return numeric;
}}
{runtime}
(async()=>{{
  await consumeStaticAtlasAsset({json.dumps(row, separators=(",", ":"))});
  let refusal=null;
  try {{ await consumeStaticAtlasAsset({json.dumps(refused_row, separators=(",", ":"))}); }}
  catch(error) {{ refusal=error.message; }}
  console.log(JSON.stringify({{
    loaded:[...staticAtlasLoadedAssets],
    schema:STATIC_ATLAS_CHUNKS.provenance.schema_version,
    layerCount:STATIC_ATLAS_CHUNKS.provenance.layers.length,
    refusal,
  }}));
}})();
"""
    )

    assert observed["loaded"] == ["provenance:0"]
    assert observed["schema"] == "atlas-provenance-chunk.v3"
    assert observed["layerCount"] == 0
    assert "decoded payload exceeds its declared byte count" in observed["refusal"]


def test_compact_bootstrap_reconstructs_exact_rows_and_preserves_v1() -> None:
    normalizer = template_block(
        "function normalizeStaticAtlasBootstrap",
        "function validateStaticAtlasBootstrap",
    )
    observed = run_node_json(
        f"""
const STATIC_ATLAS_ASSET_TABLE_FIELDS=Object.freeze({json.dumps(ASSET_TABLE_FIELDS)});
const STATIC_ATLAS_ASSET_CORE_FIELD_COUNT=12;
function staticAtlasFailure(message){{throw new Error(message)}}
{normalizer}
const compact={json.dumps(compact_bootstrap(), separators=(",", ":"))};
const normalized=normalizeStaticAtlasBootstrap(compact);
const legacy={{schema_version:'atlas-static-bootstrap.v1',assets:[{{asset_key:'legacy'}}]}};
console.log(JSON.stringify({{
  schema:normalized.schema_version,
  node:normalized.assets[0],
  indexes:normalized.assets[1],
  legacyIdentity:normalizeStaticAtlasBootstrap(legacy)===legacy,
}}));
"""
    )

    assert observed["schema"] == "atlas-static-bootstrap.v2"
    assert observed["node"]["layer_key"] == "source-samples"
    assert observed["node"]["bounds"] == [55.0, 10.0, 70.0, 25.0]
    assert observed["indexes"]["asset_key"] == "indexes:1"
    assert "layer_key" not in observed["indexes"]
    assert observed["legacyIdentity"] is True


def test_derived_bootstrap_reconstructs_transport_metadata() -> None:
    integrity_helper = template_block(
        "function staticAtlasIntegrityFromHex",
        "function normalizeStaticAtlasBootstrap",
    )
    normalizer = template_block(
        "function normalizeStaticAtlasBootstrap",
        "function validateStaticAtlasBootstrap",
    )
    legacy_table = cast(dict[str, object], compact_bootstrap()["assets"])
    legacy_records = cast(list[list[object]], legacy_table["records"])
    field_indexes = {field: index for index, field in enumerate(ASSET_TABLE_FIELDS)}
    compact = {
        "schema_version": "atlas-static-bootstrap.v2",
        "assets": {
            "schema_version": "atlas-static-asset-table.v2",
            "scope_slug": "nordic",
            "fields": list(ASSET_TABLE_STORED_FIELDS),
            "record_count": len(legacy_records),
            "records": [
                [record[field_indexes[field]] for field in ASSET_TABLE_STORED_FIELDS]
                for record in legacy_records
            ],
        },
    }
    observed = run_node_json(
        f"""
const STATIC_ATLAS_ASSET_TABLE_FIELDS=Object.freeze({json.dumps(ASSET_TABLE_FIELDS)});
const STATIC_ATLAS_ASSET_TABLE_STORED_FIELDS=Object.freeze({json.dumps(ASSET_TABLE_STORED_FIELDS)});
const STATIC_ATLAS_ASSET_CORE_FIELD_COUNT=12;
function staticAtlasFailure(message){{throw new Error(message)}}
{integrity_helper}
{normalizer}
const normalized=normalizeStaticAtlasBootstrap({json.dumps(compact, separators=(",", ":"))});
console.log(JSON.stringify({{node:normalized.assets[0],indexes:normalized.assets[1]}}));
"""
    )

    assert observed["node"]["asset_key"] == "nodes:0"
    assert observed["node"]["path"] == "nordic.atlas-nodes.0000.aaaaaaaaaaaaaaaa.js"
    assert observed["node"]["payload_encoding"] == "gzip_base64"
    assert observed["node"]["initial_load"] is False
    assert observed["indexes"]["asset_key"] == "indexes:1"
    assert observed["indexes"]["path"] == (
        "nordic.atlas-indexes.0001.cccccccccccccccc.js"
    )
    assert observed["indexes"]["payload_encoding"] == "json"
    assert observed["indexes"]["initial_load"] is False


def test_compact_bootstrap_rejects_schema_width_count_identity_and_type_tamper() -> (
    None
):
    normalizer = template_block(
        "function normalizeStaticAtlasBootstrap",
        "function validateStaticAtlasBootstrap",
    )
    observed = run_node_json(
        f"""
const STATIC_ATLAS_ASSET_TABLE_FIELDS=Object.freeze({json.dumps(ASSET_TABLE_FIELDS)});
const STATIC_ATLAS_ASSET_CORE_FIELD_COUNT=12;
function staticAtlasFailure(message){{throw new Error(message)}}
{normalizer}
const base={json.dumps(compact_bootstrap(), separators=(",", ":"))};
function changed(change){{const value=structuredClone(base);change(value);return value}}
function refusal(value){{try{{normalizeStaticAtlasBootstrap(value);return null}}catch(error){{return error.message}}}}
const cases={{
  unknownTableKey:changed((value)=>{{value.assets.extra=true}}),
  duplicateField:changed((value)=>{{value.assets.fields[20]='asset_key'}}),
  width:changed((value)=>{{value.assets.records[0].pop()}}),
  count:changed((value)=>{{value.assets.record_count=3}}),
  duplicatePath:changed((value)=>{{value.assets.records[1][3]=value.assets.records[0][3]}}),
  sequence:changed((value)=>{{value.assets.records[1][2]=4}}),
  accountingType:changed((value)=>{{value.assets.records[0][8]='300'}}),
  nonNodeSelection:changed((value)=>{{value.assets.records[1][12]=0}}),
}};
console.log(JSON.stringify(Object.fromEntries(Object.entries(cases).map(([key,value])=>[key,refusal(value)]))));
"""
    )

    assert "asset table shape is invalid" in observed["unknownTableKey"]
    assert "asset table fields are invalid" in observed["duplicateField"]
    assert "width is invalid" in observed["width"]
    assert "record count is invalid" in observed["count"]
    assert "identity is duplicated" in observed["duplicatePath"]
    assert "sequence is invalid" in observed["sequence"]
    assert "accounting field is invalid" in observed["accountingType"]
    assert "non-node selection field is not null" in observed["nonNodeSelection"]
