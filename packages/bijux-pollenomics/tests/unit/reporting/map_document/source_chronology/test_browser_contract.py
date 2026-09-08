from __future__ import annotations

import json
import re

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE

from ...source_chronology.support import projection
from ..browser_semantics.support import (
    run_node_json,
    template_block,
)


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
        "params.set('source_label_preset', activeSourceChronologyPreset)" in hash_block
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
