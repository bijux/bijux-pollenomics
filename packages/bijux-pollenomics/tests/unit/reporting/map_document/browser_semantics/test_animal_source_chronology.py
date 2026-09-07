"""Browser contracts for source-native animal chronology context."""

from __future__ import annotations

from .support import MAP_DOCUMENT_TEMPLATE, run_node_json, template_block


def test_animal_source_chronology_is_discoverable_but_default_off() -> None:
    assert "{ key: 'animal-chronology-context', label: 'Animal source chronology' }" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "const ANIMAL_CHRONOLOGY_LAYER_GROUP = 'animal-chronology-context';" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert (
        "new Set([...ANIMAL_EVIDENCE_LAYER_GROUPS, "
        "ANIMAL_CHRONOLOGY_LAYER_GROUP])"
    ) in MAP_DOCUMENT_TEMPLATE
    assert "layer.default_enabled === false" in MAP_DOCUMENT_TEMPLATE


def test_animal_source_chronology_layer_posture_fails_closed() -> None:
    block = template_block(
        "function animalSourceChronologyPostureIsValid",
        "function featureMatchesAnimalFilters",
    )

    for expected in (
        "value.semantic_role === 'animal_source_chronology_context'",
        "value.contribution_role === 'display_only'",
        "value.candidate_ranking_eligible === false",
        "value.scientific_classification_eligible === false",
        "value.scientific_selection_enabled === false",
        "value.propagation_status === 'refused'",
        "value.propagation_reason_code === 'display_only_source_chronology'",
        "value.edge_count === 0",
        "layer.group === ANIMAL_CHRONOLOGY_LAYER_GROUP",
        "layer.default_enabled === false",
        "layer.applies_country_filter === true",
        "layer.applies_time_filter === true",
        "layer.circle_enabled === false",
        "layer.species_attribution_basis === 'governed_project_registry'",
        "feature.species_attribution_basis === 'governed_project_registry'",
        "hasOwnProperty.call(layer, 'species_latin_name')",
        "hasOwnProperty.call(layer, 'species_common_name')",
        "hasOwnProperty.call(layer, 'animal_scope')",
        "hasOwnProperty.call(layer, 'classification_id')",
        "hasOwnProperty.call(layer, 'classification_status')",
        "hasOwnProperty.call(layer, 'taxon_alignment_status')",
        "hasOwnProperty.call(layer, 'taxon_alignment_statuses')",
        "hasOwnProperty.call(layer, 'scientific_signal_ids')",
        "hasOwnProperty.call(feature, 'species_latin_name')",
        "hasOwnProperty.call(feature, 'species_common_name')",
        "hasOwnProperty.call(feature, 'animal_scope')",
        "hasOwnProperty.call(feature, 'classification_id')",
        "hasOwnProperty.call(feature, 'classification_status')",
        "hasOwnProperty.call(feature, 'taxon_alignment_status')",
        "hasOwnProperty.call(feature, 'taxon_alignment_statuses')",
        "hasOwnProperty.call(feature, 'scientific_signal_ids')",
    ):
        assert expected in block

    visibility = template_block(
        "function pointFeatureVisible", "function polygonFeatureVisible"
    )
    assert "animalSourceChronologyLayerIsValid(layer)" in visibility
    assert "animalSourceChronologyFeatureIsValid(feature)" in visibility
    candidates = template_block("function animalCandidateEntries", "function animalEntryMatchesFilters")
    assert "!animalSourceChronologyLayerIsValid(layer)" in candidates
    assert "!animalSourceChronologyFeatureIsValid(feature)" in candidates


def test_invalid_animal_source_chronology_layer_cannot_be_enabled() -> None:
    controls = template_block(
        "function renderLayerControls", "function renderAnimalEvidencePanel"
    )

    assert "animalChronologyInvalid" in controls
    assert "sourceChronologyInvalid || animalChronologyInvalid ? 'disabled'" in controls


def test_project_species_attribution_is_filterable_without_taxonomic_alias() -> None:
    assert "layer.species_latin_name || layer.project_species_latin_name" in (
        MAP_DOCUMENT_TEMPLATE
    )
    filters = template_block(
        "function animalEntryMatchesFilters", "function animalVisibleEntries"
    )
    assert (
        "feature.species_latin_name || feature.project_species_latin_name"
    ) in filters
    popup = template_block(
        "function animalSourceChronologyPopupHtml", "function popupHtml"
    )
    assert "Project-registry species attribution" in popup
    assert "not an accepted source-native taxonomic classification" in popup
    assert "excluded from candidate ranking" in popup
    assert "layer?.traceability_artifact" in popup
    assert "Open chronology accountability and refusals" in popup


def test_project_species_attribution_selects_unloaded_static_chunks() -> None:
    helper = template_block(
        "function staticAtlasSignalNeeded", "function staticAtlasViewportNeeded"
    )
    observed = run_node_json(
        """
const activeAnimalScope='all';
const activeScientificSignalIds=new Set();
const SCIENTIFIC_SIGNALS=[];
function isAnimalLayer(layer){return layer.group==='animal-chronology-context'}
"""
        + helper
        + """
const row={scientific_signal_ids:[]};
const layer={
  group:'animal-chronology-context',
  project_species_latin_name:'Equus caballus',
  scientific_selection_enabled:false,
};
let activeAnimalSpecies='Equus caballus';
const selected=staticAtlasSignalNeeded(row,layer);
activeAnimalSpecies='Felis catus';
const rejected=staticAtlasSignalNeeded(row,layer);
console.log(JSON.stringify({selected,rejected}));
"""
    )

    assert observed == {"selected": True, "rejected": False}


def test_animal_metrics_do_not_merge_atlas_evidence_and_source_chronology() -> None:
    metrics = template_block("function summarizeAnimalMetrics", "function countryStyle")
    panel = template_block(
        "function renderAnimalEvidencePanel", "function renderAnimalControls"
    )
    controls = template_block("function renderAnimalControls", "function applyLayerPreset")

    assert "visibleSourceChronologyEntries" in metrics
    assert "visibleAtlasEvidenceEntries" in metrics
    assert "Visible atlas evidence points" in panel
    assert "Visible source chronology points" in panel
    assert "atlas evidence" in controls
    assert "source chronology" in controls


def test_animal_source_chronology_does_not_enter_neotoma_playback() -> None:
    layers = template_block(
        "function sourceChronologyLayers", "function sourceChronologyLayerForLevel"
    )
    assert ".filter(sourceChronologyLayerIsValid)" in layers
    assert "animal_source_chronology_context" not in layers


def test_context_preset_explicitly_enables_animal_source_chronology() -> None:
    presets = template_block("function applyLayerPreset", "function renderLegend")

    assert "'animal-chronology-context', 'environmental-context'" in presets
    evidence_preset = presets.split("if (preset === 'context')", maxsplit=1)[0]
    assert "animal-chronology-context" not in evidence_preset


def test_animal_source_chronology_uses_inclusive_numeric_bp_filtering() -> None:
    posture = template_block(
        "function isAnimalSourceChronologyLayer",
        "function featureMatchesAnimalFilters",
    )
    time_helpers = template_block(
        "function finiteTimeValue", "function pointFeatureInTimeWindow"
    )
    observed = run_node_json(
        """
const ANIMAL_CHRONOLOGY_LAYER_GROUP='animal-chronology-context';
const TIME_HAS_DATA=true;
let timeStartBp=900,timeIntervalYears=200;
function timeWindowEndBp(){return timeStartBp+timeIntervalYears}
function timeFilterUsesFullExtent(){return false}
"""
        + posture
        + time_helpers
        + """
const layer={
  group:ANIMAL_CHRONOLOGY_LAYER_GROUP,
  semantic_role:'animal_source_chronology_context',
  contribution_role:'display_only',
  candidate_ranking_eligible:false,
  scientific_classification_eligible:false,
  scientific_selection_enabled:false,
  propagation_status:'refused',
  propagation_reason_code:'display_only_source_chronology',
  edge_count:0,
  default_enabled:false,
  applies_country_filter:true,
  applies_time_filter:true,
  circle_enabled:false,
  project_species_latin_name:'Bos taurus',
  species_attribution_basis:'governed_project_registry',
};
function feature(start,end,posture='numeric_interval'){
  return {
    semantic_role:'animal_source_chronology_context',
    contribution_role:'display_only',
    candidate_ranking_eligible:false,
    scientific_classification_eligible:false,
    scientific_selection_enabled:false,
    propagation_status:'refused',
    propagation_reason_code:'display_only_source_chronology',
    edge_count:0,
    project_species_latin_name:'Bos taurus',
    species_attribution_basis:'governed_project_registry',
    time_start_bp:start,
    time_end_bp:end,
    temporal_semantics:{comparability_posture:posture},
  };
}
console.log(JSON.stringify({
  layerValid:animalSourceChronologyLayerIsValid(layer),
  youngerBoundary:featureInTimeWindow(layer,feature(800,900)),
  olderBoundary:featureInTimeWindow(layer,feature(1100,1200)),
  youngerOutside:featureInTimeWindow(layer,feature(800,899)),
  olderOutside:featureInTimeWindow(layer,feature(1101,1200)),
  nullIsNotZero:featureInTimeWindow(layer,feature(null,null)),
  negativeRefused:featureInTimeWindow(layer,feature(-1,100)),
  reversedRefused:featureInTimeWindow(layer,feature(1100,900)),
  unsupportedPosture:featureInTimeWindow(layer,feature(900,1000,'source_sample_interval')),
}));
"""
    )

    assert observed == {
        "layerValid": True,
        "youngerBoundary": True,
        "olderBoundary": True,
        "youngerOutside": False,
        "olderOutside": False,
        "nullIsNotZero": False,
        "negativeRefused": False,
        "reversedRefused": False,
        "unsupportedPosture": False,
    }
