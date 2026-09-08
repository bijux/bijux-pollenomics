from __future__ import annotations

import json

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE

from ...source_chronology.support import projection
from ..browser_semantics.support import (
    run_node_json,
    template_block,
)


def test_source_shortcuts_preserve_literal_semantics_and_reset_exact_taxa() -> None:
    assert "Source sample presence" in MAP_DOCUMENT_TEMPLATE
    assert "Find cereal-like labels" not in MAP_DOCUMENT_TEMPLATE
    assert "Whole pollen sites" not in MAP_DOCUMENT_TEMPLATE
    handlers = template_block(
        "document.querySelectorAll('[data-source-shortcut]')",
        "countryPairFilter.addEventListener",
    )
    assert "cereal|secale" not in handlers
    assert "/cereal|secale/i" not in handlers
    assert "sourceChronologyTaxonQuery.value = sourceChronologyTaxonSearch" in handlers
    assert "shortcut === 'taxa'" in handlers
    assert "activeSourceChronologyTaxon = 'all'" in handlers
    assert "document.querySelectorAll('[data-source-preset]')" in handlers
    assert "source_label_preset_accountability.presets" in handlers
    assert "button.dataset.sourcePreset" in handlers
    assert "activeSourceChronologyPreset" in handlers


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


def test_source_shortcuts_open_real_chronology_levels_and_governed_presets() -> None:
    assert 'data-source-shortcut="sample"' in MAP_DOCUMENT_TEMPLATE
    for source_code in ("TRSH", "UPHE", "AQVP"):
        assert f'data-source-shortcut="{source_code}"' in MAP_DOCUMENT_TEMPLATE
    for preset in ("avena", "hordeum", "triticum", "secale", "cerealia"):
        assert f'data-source-preset="{preset}"' in MAP_DOCUMENT_TEMPLATE
    assert 'data-source-shortcut="cereals"' not in MAP_DOCUMENT_TEMPLATE
    assert "literal_source_label_membership" in MAP_DOCUMENT_TEMPLATE
    assert "preset.member_taxon_ids.includes" in MAP_DOCUMENT_TEMPLATE
    assert "focusSourceChronologyNavigation();" in MAP_DOCUMENT_TEMPLATE


def test_topbar_chronology_status_reports_off_and_visible_source_counts() -> None:
    status_helper = template_block(
        "function refreshTimeStepperStatus",
        "function renderLayerControls",
    )
    observed = run_node_json(
        """
const TIME_HAS_DATA=true;
const timeStepperStatus={disabled:false,textContent:'',title:'',ariaControls:'',setAttribute(name,value){if(name==='aria-controls')this.ariaControls=value}};
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
let sourceLayers=[selectedLayer];
function sourceChronologyLayers(){return sourceLayers}
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
const active=timeStepperStatus.textContent;
sourceLayers=[];
refreshTimeStepperStatus();
console.log(JSON.stringify({off,active,generic:timeStepperStatus.textContent,ariaControls:timeStepperStatus.ariaControls,disabled:timeStepperStatus.disabled}));
"""
    )

    assert observed == {
        "off": "Source chronology off · [100, 200] BP · complete atlas extent",
        "active": (
            "literal source code TRSH · 2/10 nodes · 8/40 observations · [100, 200] BP"
        ),
        "generic": (
            "Complete atlas chronology · [100, 200] BP · choose a shorter span to explore change"
        ),
        "ariaControls": "time-controls",
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
    source_layer = next(
        layer
        for layer in projection()[1].point_layers
        if layer["node_level"] == "source_ecological_code"
    )
    observed = run_node_json(
        """
const sourceLayer="""
        + json.dumps(source_layer)
        + """;
const POINT_LAYERS=[sourceLayer];
const STATIC_ATLAS_INLINE=false;
let STATIC_ATLAS_BOOTSTRAP={assets:[
  {asset_key:'sweden',domain:'nodes',layer_key:sourceLayer.key,country_keys:['Sweden'],record_count:2,untimed_record_count:1},
  {asset_key:'norway',domain:'nodes',layer_key:sourceLayer.key,country_keys:['Norway'],record_count:2,untimed_record_count:2},
]};
const activeLayerKeys=new Set([sourceLayer.key]);
let activeCountries=new Set(['Sweden']);
let activeSourceChronologyLevel='source_ecological_code';
let activeSourceChronologyCode='all';
let activeSourceChronologyTaxon='all';
let activeSourceChronologyPreset='none';
function staticAtlasNonnegativeInteger(value){return Number(value)}
"""
        + helpers
        + """
const exact=sourceChronologyUntimedExclusion(sourceLayer);
STATIC_ATLAS_BOOTSTRAP={assets:[
  {asset_key:'mixed',domain:'nodes',layer_key:sourceLayer.key,country_keys:['Sweden','Norway'],record_count:4,untimed_record_count:1},
]};
const mixed=sourceChronologyUntimedExclusion(sourceLayer);
STATIC_ATLAS_BOOTSTRAP={assets:[
  {asset_key:'sweden',domain:'nodes',layer_key:sourceLayer.key,country_keys:['Sweden'],record_count:2,untimed_record_count:1},
]};
activeSourceChronologyCode='TRSH';
const facet=sourceChronologyUntimedExclusion(sourceLayer);
console.log(JSON.stringify({exact,mixed,facet}));
"""
    )

    assert observed == {
        "exact": {
            "status": "available",
            "count": 1,
            "split_status": "unavailable",
            "absent_count": None,
            "refused_count": None,
            "contextual_count": None,
        },
        "mixed": {
            "status": "unavailable",
            "count": None,
            "split_status": "unavailable",
        },
        "facet": {
            "status": "unavailable",
            "count": None,
            "split_status": "unavailable",
        },
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
    popup = template_block(
        "function sourceChronologyPopupHtml",
        "function animalSourceChronologyPopupHtml",
    )
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
    assert "activeSourceChronologyPreset = 'none'" in restore
    assert "sourceChronologyTaxonSearch = ''" in restore


def test_capture_contract_validates_and_restores_exact_preset_state() -> None:
    normalization = template_block(
        "function normalizeAtlasCaptureFrame", "async function awaitAtlasCaptureReady"
    )
    application = template_block(
        "async function applyAtlasCaptureFrame",
        "globalThis.BijuxPollenomicsAtlasCapture",
    )
    snapshot = template_block(
        "function atlasCaptureSnapshot", "function atlasCaptureOrientationKeys"
    )

    assert "frameSpec.source_preset || 'none'" in normalization
    assert "source_label_preset_accountability.presets" in normalization
    assert "capture source_preset is unavailable" in normalization
    assert (
        "capture cannot combine an exact source taxon and a source-label preset"
        in normalization
    )
    assert (
        "sourceChronologyFacetForSelection(sourceLayer, sourceCode, sourceTaxon, sourcePreset)"
        in normalization
    )
    assert "activeSourceChronologyPreset = captureFrame.sourcePreset" in application
    assert "source_preset:" in snapshot
    assert "source_preset_member_taxon_ids:" in snapshot
    assert "source_preset_catalog_sha256:" in snapshot
    assert (
        "const sourceCaveat = snapshot.source_chronology.source_preset"
        in MAP_DOCUMENT_TEMPLATE
    )
    assert "Literal exact-ID source-label union only" in MAP_DOCUMENT_TEMPLATE
    assert "not an accepted classification or abundance" in MAP_DOCUMENT_TEMPLATE
    assert "sourceChronologyCapturePresetAuthority" in normalization
    assert "facet_site_count:" in snapshot
    assert "visible_site_count:" in snapshot
    assert "sourceChronologyPreset: params.get('source_label_preset')" in (
        MAP_DOCUMENT_TEMPLATE
    )


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
let activeSourceChronologyPreset='none';
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
