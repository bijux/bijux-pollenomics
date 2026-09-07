from __future__ import annotations

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE

from ..browser_semantics.support import run_node_json, template_block


def test_control_is_opt_in_and_names_the_non_interpolated_evidence_posture() -> None:
    assert 'id="source-record-concentration-toggle"' in MAP_DOCUMENT_TEMPLATE
    assert 'aria-pressed="false" disabled' in MAP_DOCUMENT_TEMPLATE
    assert 'id="source-chronology-global-denominator"' in MAP_DOCUMENT_TEMPLATE
    assert "Captured source-record concentration" in MAP_DOCUMENT_TEMPLATE
    assert "raw visible node count" in MAP_DOCUMENT_TEMPLATE
    assert "never combines source levels or weights reported values" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "not abundance, absence, propagation, flow, or heat" in (
        MAP_DOCUMENT_TEMPLATE
    )


def test_source_taxon_identity_accepts_governed_numeric_feature_ids() -> None:
    helper = template_block(
        "function sourceChronologyTaxonIdentifierIsValid",
        "function sourceRecordConcentrationFailure",
    )
    observed = run_node_json(
        """
let activeSourceChronologyCode='all',activeSourceChronologyTaxon='source:neotoma:taxon:338';
let activeSourceChronologyPreset='none';
function sourceChronologyLayerIsValid(){return true}
const taxonLayer={semantic_role:'source_chronology_context',node_level:'source_taxon',source_snapshot_id:'sha256:snapshot',build_id:'sha256:build'};
const posture={
  semantic_role:'source_chronology_context',node_level:'source_taxon',
  source_snapshot_id:'sha256:snapshot',build_id:'sha256:build',node_id:'node:338',record_id:'site:338',
  propagation_eligible:false,candidate_generation_status:'refused',
  candidate_refusal_reason:'source_taxon_equivalence_not_reviewed',
  feature_key:'source:neotoma:taxon:338',source_unit:'percent',
  source_reported_name:'Acer',source_taxon_id:338,source_ecological_code:null,
};
"""
        + helper
        + """
console.log(JSON.stringify({
  numeric:sourceChronologyTaxonIdentifierIsValid(338),
  string:sourceChronologyTaxonIdentifierIsValid('338'),
  zero:sourceChronologyTaxonIdentifierIsValid(0),
  nullValue:sourceChronologyTaxonIdentifierIsValid(null),
  fractional:sourceChronologyTaxonIdentifierIsValid(3.5),
  blank:sourceChronologyTaxonIdentifierIsValid('  '),
  featureSelected:sourceChronologyFeatureMatches(taxonLayer,posture),
}));
"""
    )

    assert observed == {
        "numeric": True,
        "string": True,
        "zero": True,
        "nullValue": False,
        "fractional": False,
        "blank": False,
        "featureSelected": True,
    }


def test_site_grouping_is_deterministic_and_preserves_both_denominators() -> None:
    helpers = template_block(
        "function sourceRecordConcentrationFailure", "let activeCountries"
    )
    observed = run_node_json(
        """
function sourceChronologyCount(value){return Number.isSafeInteger(value)&&value>=0?value:null}
const layer={key:'source-samples',node_level:'source_sample_presence',facet_metadata:{node_count:4,observation_denominator:9}};
const activeLayerKeys=new Set([layer.key]);
let activeSourceChronologyCode='all', activeSourceChronologyTaxon='all';
function sourceChronologyLayerIsValid(candidate){return candidate===layer}
function sourceChronologyLayers(){return [layer]}
function sourceChronologyFacetForSelection(){return layer.facet_metadata}
function sourceChronologyFeatureMatches(candidate,feature){return candidate===layer&&feature.valid!==false}
function featureCoordinatePair(feature){
  return Number.isFinite(feature.latitude)&&Number.isFinite(feature.longitude)
    ? {latitude:feature.latitude,longitude:feature.longitude}:null;
}
function featureTimeWindow(feature){
  return Number.isFinite(feature.time_start_bp)&&Number.isFinite(feature.time_end_bp)&&feature.time_start_bp<=feature.time_end_bp
    ? {start:feature.time_start_bp,end:feature.time_end_bp}:null;
}
function pointFeatureVisible(candidate,feature){return candidate===layer&&feature.visible!==false}
const posture={valid:true,country:'Sweden',time_start_bp:0,time_end_bp:100};
const features=[
  {...posture,node_id:'node-b',record_id:'site-a',latitude:59,longitude:18,observation_denominator:3},
  {...posture,node_id:'node-d',record_id:'site-b',latitude:60,longitude:-2,observation_denominator:1},
  {...posture,node_id:'node-a',record_id:'site-a',latitude:59,longitude:18,observation_denominator:2},
  {...posture,node_id:'node-c',record_id:'site-c',latitude:61,longitude:19,observation_denominator:3,visible:false},
];
"""
        + helpers
        + """
const viewport={contains(pair){return pair[1]>=0}};
const result=buildSourceRecordConcentration(layer,features,viewport);
console.log(JSON.stringify({
  siteCount:result.site_count,
  visibleNodes:result.visible_node_count,
  visibleObservations:result.visible_observation_denominator,
  globalNodes:result.global_node_count,
  globalObservations:result.global_observation_denominator,
  sites:result.entries.map((entry)=>({
    site:entry.site_id,nodes:entry.node_count,observations:entry.observation_denominator,nodeIds:entry.node_ids,
  })),
  radii:[1,2,5,10,25].map(sourceRecordConcentrationRadius),
}));
"""
    )

    assert observed == {
        "siteCount": 1,
        "visibleNodes": 2,
        "visibleObservations": 5,
        "globalNodes": 4,
        "globalObservations": 9,
        "sites": [
            {
                "site": "site-a",
                "nodes": 2,
                "observations": 5,
                "nodeIds": ["node-a", "node-b"],
            }
        ],
        "radii": [7, 10, 13, 16, 19],
    }


def test_corrupt_identity_coordinates_and_counts_fail_closed() -> None:
    helpers = template_block(
        "function sourceRecordConcentrationFailure", "let activeCountries"
    )
    observed = run_node_json(
        """
function sourceChronologyCount(value){return Number.isSafeInteger(value)&&value>=0?value:null}
const layer={key:'source-samples',node_level:'source_sample_presence',facet_metadata:{node_count:8,observation_denominator:16}};
const activeLayerKeys=new Set([layer.key]);
let activeSourceChronologyCode='all', activeSourceChronologyTaxon='all';
function sourceChronologyLayerIsValid(candidate){return candidate===layer}
function sourceChronologyLayers(){return [layer]}
function sourceChronologyFacetForSelection(){return layer.facet_metadata}
function sourceChronologyFeatureMatches(candidate,feature){return candidate===layer&&feature.valid!==false}
function featureCoordinatePair(feature){return {latitude:feature.latitude,longitude:feature.longitude}}
function featureTimeWindow(){return {start:0,end:0}}
function pointFeatureVisible(){return true}
const base={valid:true,country:'Sweden',time_start_bp:0,time_end_bp:0,latitude:59,longitude:18,observation_denominator:1};
"""
        + helpers
        + """
function refusal(features){
  try { buildSourceRecordConcentration(layer,features,{contains(){return true}}); return null; }
  catch(error){ return error.message; }
}
console.log(JSON.stringify({
  duplicate:refusal([{...base,node_id:'same',record_id:'site-a'},{...base,node_id:'same',record_id:'site-b'}]),
  coordinates:refusal([{...base,node_id:'a',record_id:'site-a'},{...base,node_id:'b',record_id:'site-a',longitude:19}]),
  negative:refusal([{...base,node_id:'a',record_id:'site-a',observation_denominator:-1}]),
  fractional:refusal([{...base,node_id:'a',record_id:'site-a',observation_denominator:1.5}]),
}));
"""
    )

    assert "duplicate node identity same" in observed["duplicate"]
    assert "site site-a has conflicting coordinates" in observed["coordinates"]
    assert "invalid contributing-observation count" in observed["negative"]
    assert "invalid contributing-observation count" in observed["fractional"]


def test_dense_levels_require_one_exact_facet_and_hash_state_is_explicit() -> None:
    selection = template_block(
        "function sourceRecordConcentrationFailure",
        "function sourceRecordConcentrationRadius",
    )
    assert "activeSourceChronologyCode === 'all'" in selection
    assert "activeSourceChronologyTaxon === 'all'" in selection
    assert "activeSourceLayers.length !== 1" in selection
    assert "source_record_concentration" in MAP_DOCUMENT_TEMPLATE
    assert "sourceRecordConcentrationActive = false" in template_block(
        "sourceChronologyCode.addEventListener", "densityOpacitySlider.addEventListener"
    )
