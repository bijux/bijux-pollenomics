from __future__ import annotations

import json
from pathlib import Path
import re
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
from ...source_chronology.support import projection


def test_mobile_scrim_stays_below_interactive_controls() -> None:
    def z_index(selector: str) -> int:
        match = re.search(
            rf"{re.escape(selector)} \{{[^}}]*z-index: (?P<value>\d+);",
            MAP_DOCUMENT_TEMPLATE,
            re.DOTALL,
        )
        assert match is not None
        return int(match.group("value"))

    assert (
        z_index(".mobile-scrim") < z_index(".control-panel") < z_index(".help-dialog")
    )


def test_help_dialog_traps_focus_and_restores_its_opener() -> None:
    assert (
        'id="help-toggle" class="toolbar-button" type="button" '
        'aria-controls="help-dialog" aria-expanded="false"' in MAP_DOCUMENT_TEMPLATE
    )
    assert "helpDialogReturnFocus = document.activeElement" in MAP_DOCUMENT_TEMPLATE
    assert "appShell.inert = true" in MAP_DOCUMENT_TEMPLATE
    assert "helpCloseButton.focus({ preventScroll: true })" in MAP_DOCUMENT_TEMPLATE
    assert "event.key === 'Tab' && !helpDialog.hidden" in MAP_DOCUMENT_TEMPLATE
    assert "helpDialog.contains(document.activeElement)" in MAP_DOCUMENT_TEMPLATE
    assert "appShell.inert = false" in MAP_DOCUMENT_TEMPLATE
    assert (
        "helpDialogReturnFocus.focus({ preventScroll: true })" in MAP_DOCUMENT_TEMPLATE
    )
    assert "helpToggleButton.setAttribute('aria-expanded', 'false')" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert 'id="help-return"' in MAP_DOCUMENT_TEMPLATE
    assert "helpReturnButton.addEventListener('click', closeHelpDialog)" in (
        MAP_DOCUMENT_TEMPLATE
    )


def test_help_dialog_describes_the_available_basemap_choices() -> None:
    help_markup = template_block(
        '<div id="help-dialog"', '<script id="atlas-static-bootstrap"'
    )

    assert "Street" in help_markup
    assert "OpenStreetMap" in help_markup
    assert "Terrain" in help_markup
    assert "OpenTopoMap" in help_markup
    assert "No basemap" in help_markup
    assert "Offline mode" in help_markup
    assert "Voyager" not in help_markup
    assert "Light" not in help_markup


def test_controls_are_accessible_source_native_and_separate_from_modeled_context() -> (
    None
):
    assert 'id="source-chronology-controls"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="time-controls"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="source-chronology-level"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="source-chronology-code"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="source-chronology-taxon-query"' in MAP_DOCUMENT_TEMPLATE
    assert 'type="search"' in MAP_DOCUMENT_TEMPLATE
    assert 'aria-controls="source-chronology-taxon"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="source-chronology-taxon"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="source-chronology-taxon-shortcuts"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="source-label-preset-controls"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="source-label-preset-state"' in MAP_DOCUMENT_TEMPLATE
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
    assert "mobilePanelReturnFocus = panelToggleButton" in MAP_DOCUMENT_TEMPLATE
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
    assert "closeMobilePanel();" in MAP_DOCUMENT_TEMPLATE
    assert "intervalPreset.focus({ preventScroll: true })" in MAP_DOCUMENT_TEMPLATE
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
    layers = list(projection()[1].point_layers)
    observed = run_node_json(
        """
const POINT_LAYERS="""
        + json.dumps(layers)
        + """;
const sample=POINT_LAYERS.find((layer)=>layer.node_level==='source_sample_presence');
const code=POINT_LAYERS.find((layer)=>layer.node_level==='source_ecological_code');
const taxon=POINT_LAYERS.find((layer)=>layer.node_level==='source_taxon');
const invalidDense={...code,default_enabled:true};
const invalidDirection={...sample,temporal_direction:'present_to_oldest'};
const invalidDensity={...sample,facet_metadata:{...sample.facet_metadata,time_density:{...sample.facet_metadata.time_density,node_count:3}}};
let activeSourceChronologyCode='all';
let activeSourceChronologyTaxon='all';
let activeSourceChronologyPreset='none';
"""
        + helpers
        + """
const codeFeature=code.features[0];
const taxonFeature=taxon.features[0];
console.log(JSON.stringify({
  levels:sourceChronologyLayers().map((entry)=>entry.node_level),
  literals:code.facet_metadata.source_ecological_codes.map((row)=>row.value),
  denseDefaultRejected:sourceChronologyLayerIsValid(invalidDense),
  directionRejected:sourceChronologyLayerIsValid(invalidDirection),
  densityDriftRejected:sourceChronologyLayerIsValid(invalidDensity),
  countryOrderRejected:sourceChronologyLayerIsValid({...sample,facet_metadata:{...sample.facet_metadata,country_counts:[...sample.facet_metadata.country_counts].reverse()}}),
  countryOmissionRejected:sourceChronologyLayerIsValid({...sample,facet_metadata:{...sample.facet_metadata,country_counts:sample.facet_metadata.country_counts.slice(0,3)}}),
  countryNameDriftRejected:sourceChronologyLayerIsValid({...sample,facet_metadata:{...sample.facet_metadata,country_counts:sample.facet_metadata.country_counts.map((row,index)=>index===0?{...row,value:'Sverige'}:row)}}),
  countrySiteDriftRejected:sourceChronologyLayerIsValid({...sample,facet_metadata:{...sample.facet_metadata,country_counts:sample.facet_metadata.country_counts.map((row,index)=>index===0?{...row,site_count:2}:row)}}),
  emptyCountryBoundsRejected:sourceChronologyLayerIsValid({...sample,facet_metadata:{...sample.facet_metadata,country_counts:sample.facet_metadata.country_counts.map((row,index)=>index===1?{...row,time_min_bp:0}:row)}}),
  booleanCountRejected:sourceChronologyLayerIsValid({...sample,facet_metadata:{...sample.facet_metadata,site_count:true}}),
  malformedRejected:sourceChronologyLayerIsValid({...code,facet_metadata:null}),
  stringExtentRejected:sourceChronologyLayerIsValid({...code,facet_metadata:{...code.facet_metadata,time_min_bp:'100'}}),
  presetIdentityDriftRejected:sourceChronologyLayerIsValid({...taxon,facet_metadata:{...taxon.facet_metadata,source_label_preset_catalog:{...taxon.facet_metadata.source_label_preset_catalog,build_id:'sha256:'+'c'.repeat(64)}}}),
  presetSnapshotDriftRejected:sourceChronologyLayerIsValid({...taxon,facet_metadata:{...taxon.facet_metadata,source_label_preset_catalog:{...taxon.facet_metadata.source_label_preset_catalog,source_snapshot_id:'sha256:'+'c'.repeat(64)}}}),
  catalogPropagationRejected:sourceChronologyLayerIsValid({...taxon,facet_metadata:{...taxon.facet_metadata,source_label_preset_catalog:{...taxon.facet_metadata.source_label_preset_catalog,propagation_allowed:true}}}),
  accountabilityPropagationRejected:sourceChronologyLayerIsValid({...taxon,facet_metadata:{...taxon.facet_metadata,source_label_preset_accountability:{...taxon.facet_metadata.source_label_preset_accountability,propagation_allowed:true}}}),
  presetPropagationRejected:sourceChronologyLayerIsValid({...taxon,facet_metadata:{...taxon.facet_metadata,source_label_preset_accountability:{...taxon.facet_metadata.source_label_preset_accountability,presets:taxon.facet_metadata.source_label_preset_accountability.presets.map((row,index)=>index===0?{...row,propagation_allowed:true}:row)}}}),
  unionPropagationRejected:sourceChronologyLayerIsValid({...taxon,facet_metadata:{...taxon.facet_metadata,source_label_preset_accountability:{...taxon.facet_metadata.source_label_preset_accountability,union:{...taxon.facet_metadata.source_label_preset_accountability.union,propagation_allowed:true}}}}),
  codeSelected:sourceChronologyFeatureMatches(code,codeFeature,'TRSH','all'),
  codeExcluded:sourceChronologyFeatureMatches(code,codeFeature,'AQVP','all'),
  codeNullRejected:sourceChronologyFeatureMatches(code,{...codeFeature,source_ecological_code:null},'all','all'),
  taxonSelected:sourceChronologyFeatureMatches(taxon,taxonFeature,'all',taxonFeature.feature_key),
  taxonExcluded:sourceChronologyFeatureMatches(taxon,taxonFeature,'all','source:taxon:99'),
  taxonNullRejected:sourceChronologyFeatureMatches(taxon,{...taxonFeature,source_taxon_id:null},'all','all'),
  featureSnapshotRejected:sourceChronologyFeatureMatches(taxon,{...taxonFeature,source_snapshot_id:'sha256:'+'c'.repeat(64)},'all',taxonFeature.feature_key),
  featureBuildRejected:sourceChronologyFeatureMatches(taxon,{...taxonFeature,build_id:'sha256:'+'c'.repeat(64)},'all',taxonFeature.feature_key),
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
        "literals": ["TRSH"],
        "denseDefaultRejected": False,
        "directionRejected": False,
        "densityDriftRejected": False,
        "countryOrderRejected": False,
        "countryOmissionRejected": False,
        "countryNameDriftRejected": False,
        "countrySiteDriftRejected": False,
        "emptyCountryBoundsRejected": False,
        "booleanCountRejected": False,
        "malformedRejected": False,
        "stringExtentRejected": False,
        "presetIdentityDriftRejected": False,
        "presetSnapshotDriftRejected": False,
        "catalogPropagationRejected": False,
        "accountabilityPropagationRejected": False,
        "presetPropagationRejected": False,
        "unionPropagationRejected": False,
        "codeSelected": True,
        "codeExcluded": False,
        "codeNullRejected": False,
        "taxonSelected": True,
        "taxonExcluded": False,
        "taxonNullRejected": False,
        "featureSnapshotRejected": False,
        "featureBuildRejected": False,
        "crossLevelRejected": False,
        "postureRejected": False,
        "unrelatedUnaffected": True,
    }


def test_source_label_presets_filter_exact_multi_id_unions_without_regex() -> None:
    helpers = template_block(
        "const SOURCE_CHRONOLOGY_LEVEL_ORDER",
        "function sourceRecordConcentrationFailure",
    )
    taxon_layer = next(
        layer
        for layer in projection()[1].point_layers
        if layer["node_level"] == "source_taxon"
    )
    observed = run_node_json(
        "const POINT_LAYERS="
        + json.dumps([taxon_layer])
        + ";let activeSourceChronologyCode='all';let activeSourceChronologyTaxon='all';let activeSourceChronologyPreset='none';"
        + helpers
        + """
const layer=POINT_LAYERS[0];
const base=layer.features[0];
const feature=(source_taxon_id,source_reported_name)=>({...base,source_taxon_id,source_reported_name,feature_key:`source:neotoma:taxon:${source_taxon_id}`});
console.log(JSON.stringify({
  avenaDirect:sourceChronologyFeatureMatches(layer,feature(414,'Avena-type'),'all','all','avena'),
  avenaOverlap:sourceChronologyFeatureMatches(layer,feature(415,'Avena/Triticum'),'all','all','avena'),
  triticumOverlap:sourceChronologyFeatureMatches(layer,feature(415,'Avena/Triticum'),'all','all','triticum'),
  hordeumOverlap:sourceChronologyFeatureMatches(layer,feature(3924,'Hordeum/Secale'),'all','all','hordeum'),
  secaleOverlap:sourceChronologyFeatureMatches(layer,feature(3924,'Hordeum/Secale'),'all','all','secale'),
  wrongFamily:sourceChronologyFeatureMatches(layer,feature(3924,'Hordeum/Secale'),'all','all','avena'),
  labelLookalike:sourceChronologyFeatureMatches(layer,feature(4150,'Avena/Triticum lookalike'),'all','all','avena'),
  malformedId:sourceChronologyFeatureMatches(layer,feature('415x','Avena/Triticum'),'all','all','avena'),
}));
"""
    )

    assert observed == {
        "avenaDirect": True,
        "avenaOverlap": True,
        "triticumOverlap": True,
        "hordeumOverlap": True,
        "secaleOverlap": True,
        "wrongFamily": False,
        "labelLookalike": False,
        "malformedId": False,
    }


def test_capture_preset_authority_is_observed_from_governed_browser_data() -> None:
    helpers = template_block(
        "const SOURCE_CHRONOLOGY_LEVEL_ORDER",
        "function sourceRecordConcentrationFailure",
    )
    taxon_layer = next(
        layer
        for layer in projection()[1].point_layers
        if layer["node_level"] == "source_taxon"
    )
    facets = taxon_layer["facet_metadata"]
    assert isinstance(facets, dict)
    catalog = facets["source_label_preset_catalog"]
    assert isinstance(catalog, dict)
    catalog_identity = catalog["content_sha256"]
    assert isinstance(catalog_identity, str)
    observed = run_node_json(
        "const POINT_LAYERS="
        + json.dumps([taxon_layer])
        + ";"
        + helpers
        + """
const layer=POINT_LAYERS[0];
const membershipDrift=JSON.parse(JSON.stringify(layer));
membershipDrift.facet_metadata.source_label_preset_accountability.presets[0].member_taxon_ids=[999];
const digestDrift=JSON.parse(JSON.stringify(layer));
digestDrift.facet_metadata.source_label_preset_catalog.content_sha256='sha256:'+'f'.repeat(64);
const missingCatalog=JSON.parse(JSON.stringify(layer));
delete missingCatalog.facet_metadata.source_label_preset_catalog;
function outcome(candidate) {
  try { return {status:'accepted',value:sourceChronologyCapturePresetAuthority(candidate,'avena')}; }
  catch (error) { return {status:'refused',message:error.message}; }
}
console.log(JSON.stringify({
  governed:outcome(layer),
  membershipDrift:outcome(membershipDrift),
  digestDrift:outcome(digestDrift),
  missingCatalog:outcome(missingCatalog),
  noPreset:sourceChronologyCapturePresetAuthority(layer,'none'),
}));
"""
    )

    assert observed == {
        "governed": {
            "status": "accepted",
            "value": {
                "memberTaxonIds": [414, 415, 3915, 3917, 3918, 31581, 48827],
                "catalogSha256": catalog_identity.removeprefix("sha256:"),
            },
        },
        "membershipDrift": {
            "status": "refused",
            "message": "capture source preset authority is unavailable",
        },
        "digestDrift": {
            "status": "refused",
            "message": "capture source preset authority is unavailable",
        },
        "missingCatalog": {
            "status": "refused",
            "message": "capture source preset authority is unavailable",
        },
        "noPreset": None,
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
    assert "sourceChronologyPreset: params.get('source_label_preset')" in (
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
        "params.set('source_label_preset', activeSourceChronologyPreset)"
        in hash_block
    )
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
    assert "source nodes without admitted numeric chronology excluded" in (
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
        "exact": {"status": "available", "count": 1, "split_status": "unavailable", "absent_count": None, "refused_count": None, "contextual_count": None},
        "mixed": {"status": "unavailable", "count": None, "split_status": "unavailable"},
        "facet": {"status": "unavailable", "count": None, "split_status": "unavailable"},
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
    assert "activeSourceChronologyPreset = 'none'" in restore
    assert "sourceChronologyTaxonSearch = ''" in restore


def test_capture_contract_validates_and_restores_exact_preset_state() -> None:
    normalization = template_block(
        "function normalizeAtlasCaptureFrame", "async function awaitAtlasCaptureReady"
    )
    application = template_block(
        "async function applyAtlasCaptureFrame", "globalThis.BijuxPollenomicsAtlasCapture"
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
    assert "sourceChronologyFacetForSelection(sourceLayer, sourceCode, sourceTaxon, sourcePreset)" in normalization
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
    assert "BP interval contradicts its untimed record count" in bootstrap
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
    v2_stored_fields = [
        field
        for field in ASSET_TABLE_STORED_FIELDS
        if field
        not in {
            "chronology_absent_record_count",
            "refused_chronology_record_count",
            "contextual_chronology_record_count",
        }
    ]
    compact = {
        "schema_version": "atlas-static-bootstrap.v2",
        "assets": {
            "schema_version": "atlas-static-asset-table.v2",
            "scope_slug": "nordic",
            "fields": v2_stored_fields,
            "record_count": len(legacy_records),
            "records": [
                [record[field_indexes[field]] for field in v2_stored_fields]
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


def test_v3_bootstrap_requires_reconciled_chronology_split() -> None:
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
    old_indexes = {field: index for index, field in enumerate(ASSET_TABLE_FIELDS)}
    split_fields = {
        "chronology_absent_record_count",
        "refused_chronology_record_count",
        "contextual_chronology_record_count",
    }
    current_fields = [
        *ASSET_TABLE_FIELDS[:-1],
        "chronology_absent_record_count",
        "refused_chronology_record_count",
        "contextual_chronology_record_count",
        ASSET_TABLE_FIELDS[-1],
    ]
    records = [
        [
            (
                0
                if field in split_fields and record[old_indexes["domain"]] == "nodes"
                else None
                if field in split_fields
                else record[old_indexes[field]]
            )
            for field in ASSET_TABLE_STORED_FIELDS
        ]
        for record in legacy_records
    ]
    bootstrap = {
        "schema_version": "atlas-static-bootstrap.v2",
        "assets": {
            "schema_version": "atlas-static-asset-table.v3",
            "scope_slug": "nordic",
            "fields": list(ASSET_TABLE_STORED_FIELDS),
            "record_count": len(records),
            "records": records,
        },
    }
    observed = run_node_json(
        f"""
const STATIC_ATLAS_ASSET_TABLE_FIELDS=Object.freeze({json.dumps(current_fields)});
const STATIC_ATLAS_ASSET_TABLE_STORED_FIELDS=Object.freeze({json.dumps(ASSET_TABLE_STORED_FIELDS)});
const STATIC_ATLAS_ASSET_CORE_FIELD_COUNT=12;
function staticAtlasFailure(message){{throw new Error(message)}}
{integrity_helper}
{normalizer}
const base={json.dumps(bootstrap, separators=(",", ":"))};
const valid=normalizeStaticAtlasBootstrap(base);
const missing=structuredClone(base);
const indexes=Object.fromEntries(missing.assets.fields.map((field,index)=>[field,index]));
for (const field of ['chronology_absent_record_count','refused_chronology_record_count','contextual_chronology_record_count']) missing.assets.records[0][indexes[field]]=null;
let refusal=null;
try{{normalizeStaticAtlasBootstrap(missing)}}catch(error){{refusal=error.message}}
console.log(JSON.stringify({{split:valid.assets[0].chronology_absent_record_count,refusal}}));
"""
    )

    assert observed["split"] == 0
    assert "chronology split is required" in observed["refusal"]


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


def test_static_asset_numbers_reject_non_scalar_zero_coercion() -> None:
    helpers = template_block(
        "function staticAtlasNonnegativeInteger",
        "function staticAtlasIntegrityFromHex",
    )
    observed = run_node_json(
        """
function staticAtlasFailure(message){throw new Error(message)}
function outcome(callback){
  try{return {status:'accepted',value:callback()}}
  catch(error){return {status:'refused',message:error.message}}
}
"""
        + helpers
        + """
const invalid=[[],[0],{},true,null,'1'];
console.log(JSON.stringify({
  integerZero:outcome(()=>staticAtlasNonnegativeInteger(0,'count')),
  integerStringZero:outcome(()=>staticAtlasNonnegativeInteger('0','count')),
  integerInvalid:invalid.map((value)=>outcome(()=>staticAtlasNonnegativeInteger(value,'count')).status),
  nullableMissing:outcome(()=>staticAtlasNullableFiniteNumber(null,'bound',-180,180)),
  nullableZero:outcome(()=>staticAtlasNullableFiniteNumber(0,'bound',-180,180)),
  nullableStringZero:outcome(()=>staticAtlasNullableFiniteNumber('0','bound',-180,180)),
  nullableInvalid:invalid.map((value)=>outcome(()=>staticAtlasNullableFiniteNumber(value,'bound',-180,180)).status),
}));
"""
    )

    assert observed == {
        "integerZero": {"status": "accepted", "value": 0},
        "integerStringZero": {"status": "refused", "message": "count is invalid"},
        "integerInvalid": ["refused"] * 6,
        "nullableMissing": {"status": "accepted", "value": None},
        "nullableZero": {"status": "accepted", "value": 0},
        "nullableStringZero": {"status": "accepted", "value": 0},
        "nullableInvalid": ["refused"] * 4 + ["accepted"] * 2,
    }
