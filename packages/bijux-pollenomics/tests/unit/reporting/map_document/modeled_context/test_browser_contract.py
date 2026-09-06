from __future__ import annotations

import json

from bijux_pollenomics.reporting.context.polygons import build_external_polygon_layer
from bijux_pollenomics.reporting.map_document.payload import build_map_document_payload
from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE
from bijux_pollenomics.reporting.map_publication import resolve_map_scope_policy
from tests.support.repository import REPOSITORY_ROOT

from ..browser_semantics.support import run_node_json, template_block


def test_mode_has_dedicated_truthful_controls_and_download() -> None:
    assert 'id="modeled-context-controls"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="modeled-context-family"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="modeled-context-metric"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="modeled-context-window"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="modeled-context-toggle"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="modeled-context-playback"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="modeled-context-download"' in MAP_DOCUMENT_TEMPLATE
    assert 'id="modeled-context-legend"' in MAP_DOCUMENT_TEMPLATE
    assert "context_only" in MAP_DOCUMENT_TEMPLATE
    assert "propagation_use_allowed: false" in MAP_DOCUMENT_TEMPLATE
    assert "interpolation_allowed: false" in MAP_DOCUMENT_TEMPLATE
    assert "pangaea-937075-${metricSlug}-${windowSlug}.geojson" in MAP_DOCUMENT_TEMPLATE
    assert (
        ".sort((left, right) => String(left.properties.record_id"
        in MAP_DOCUMENT_TEMPLATE
    )
    assert "escapeHtml(metric.source_label)" in MAP_DOCUMENT_TEMPLATE
    assert "escapeHtml(metric.key)" in MAP_DOCUMENT_TEMPLATE
    assert "escapeHtml(entry.label)" in MAP_DOCUMENT_TEMPLATE
    assert "modeledContextFamily.addEventListener('change'" in MAP_DOCUMENT_TEMPLATE
    assert "modeledContextMetric.addEventListener('change'" in MAP_DOCUMENT_TEMPLATE


def test_payload_injects_available_contract_from_repository_layer() -> None:
    source_path = (
        REPOSITORY_ROOT
        / "data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson"
    )
    geojson = json.loads(source_path.read_text(encoding="utf-8"))
    polygon_layer = build_external_polygon_layer(geojson, source_path=source_path)

    payload = build_map_document_payload(
        title="Nordic",
        version="modeled-context-test",
        generated_on="2026-09-05",
        countries=("Denmark", "Finland", "Norway", "Sweden"),
        policy=resolve_map_scope_policy(None),
        point_layers=[],
        polygon_layers=[polygon_layer],
        asset_base_path="assets",
        escape_html_fn=lambda value: value,
    )
    manifest = json.loads(payload["__MODELED_CONTEXT_JSON__"])

    assert manifest["status"] == "available"
    assert manifest["feature_count"] == 1875
    assert manifest["metric_count"] == 47
    assert [family["metric_count"] for family in manifest["metric_families"]] == [
        31,
        13,
        3,
    ]
    assert manifest["windows_oldest_to_present"][0]["label"] == "11200-11700 BP"


def test_activation_selects_exact_source_window_and_hide_restores_generic_time() -> (
    None
):
    block = template_block(
        "const MODELED_CONTEXT_WINDOWS",
        "let activeCountries",
    )
    result = run_node_json(
        """
const MODELED_CONTEXT = {
  status: 'available',
  schema_version: 'modeled-context-manifest.v3',
  feature_count: 1875,
  quality_classes: ['high', 'low', 'no_pollen_data'],
  quality_class_counts: {high:628, low:940, no_pollen_data:307},
  no_pollen_data_display_posture: 'null_not_zero',
  layer_key: 'landclim-reveals-temporal-grid',
  dataset_id: '937075',
  default_metric_family_key: 'source_land_cover_types',
  metric_key: 'OL',
  metric_count: 47,
  value_unit: 'percentage_cover',
  metric_families: [
    {
      key: 'exact_taxa', label: 'Exact taxa', metric_count: 1,
      default_metric_key: 'Picea',
      metrics: [{key: 'Picea', label: 'Picea abies', source_label: 'Picea abies', definition: null}],
    },
    {
      key: 'source_pft_codes', label: 'Source PFT codes', metric_count: 1,
      default_metric_key: 'TBE1',
      metrics: [{key: 'TBE1', label: 'TBE1', source_label: 'TBE1', definition: 'Shade-tolerant evergreen trees'}],
    },
    {
      key: 'source_land_cover_types', label: 'Source land-cover types', metric_count: 1,
      default_metric_key: 'OL',
      metrics: [{key: 'OL', label: 'Open land', source_label: 'Open land (OL)', definition: 'Open land'}],
    },
  ],
  windows_oldest_to_present: Array.from({length: 25}, (_, index) => ({
    label: `window-${index}`,
    time_start_bp: 11200 - (index * 100),
    time_end_bp: 11700 - (index * 100),
    feature_count: 75,
  })),
  palette: [],
};
const initialState = {modeledFamily: null, modeledMetric: null};
const modeledContextPlayback = { setAttribute() {}, textContent: '' };
const modeledContextControls = { hidden: false };
const modeledContextFamily = { innerHTML: '' };
const modeledContextMetric = { innerHTML: '' };
const modeledContextWindow = { innerHTML: '' };
const modeledContextToggle = { setAttribute() {}, textContent: '' };
const modeledContextDownload = { disabled: false };
const modeledContextSummary = { textContent: '' };
const modeledContextState = { textContent: '' };
const activeLayerKeys = new Set();
const activeCountries = new Set(['Sweden']);
const POLYGON_LAYERS = [];
const window = { clearTimeout() {}, setTimeout() {} };
let timeStartBp = 321;
let timeIntervalYears = 654;
function stopTimePlayback() {}
async function renderMapState() {}
function escapeHtml(value) { return String(value); }
"""
        + block
        + """
(async () => {
  await selectModeledContextWindow(4);
  const active = {
    modeledContextActive,
    modeledContextFamilyKey,
    modeledContextMetricKey,
    timeStartBp,
    timeIntervalYears,
    layerEnabled: activeLayerKeys.has(MODELED_CONTEXT.layer_key),
  };
  deactivateModeledContext();
  console.log(JSON.stringify({
    active,
    inactive: { modeledContextActive, timeStartBp, timeIntervalYears },
  }));
})();
"""
    )

    assert result == {
        "active": {
            "modeledContextActive": True,
            "modeledContextFamilyKey": "source_land_cover_types",
            "modeledContextMetricKey": "OL",
            "timeStartBp": 10800,
            "timeIntervalYears": 500,
            "layerEnabled": True,
        },
        "inactive": {
            "modeledContextActive": False,
            "timeStartBp": 321,
            "timeIntervalYears": 654,
        },
    }


def test_modeled_window_selection_refuses_coercion_and_out_of_range_indexes() -> None:
    block = template_block(
        "function admittedModeledContextWindowIndex",
        "async function advanceModeledContextPlayback",
    )
    observed = run_node_json(
        """
const MODELED_CONTEXT_WINDOWS = Array.from({length:25}, (_, index) => ({index}));
const invalid = [null, undefined, '', '0', false, true, [], {}, -1, 1.5, 25, Number.NaN, Infinity];
"""
        + block
        + """
console.log(JSON.stringify({
  zero: admittedModeledContextWindowIndex(0),
  last: admittedModeledContextWindowIndex(24),
  invalid: invalid.map((value) => admittedModeledContextWindowIndex(value)),
}));
"""
    )

    assert observed == {
        "zero": 0,
        "last": 24,
        "invalid": [None] * 13,
    }


def test_generic_time_actions_deactivate_mode_and_normal_style_is_restored() -> None:
    assert "timeStartSlider.addEventListener('input', applyGlobalTimeStartInput)" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert (
        "timeIntervalSlider.addEventListener('input', applyGlobalTimeIntervalInput)"
        in MAP_DOCUMENT_TEMPLATE
    )
    assert (
        "stopTimePlayback();\n          deactivateModeledContext();\n          const preset"
        in MAP_DOCUMENT_TEMPLATE
    )
    assert (
        "stopTimePlayback();\n        deactivateModeledContext();\n        activeCountries"
        in MAP_DOCUMENT_TEMPLATE
    )
    assert (
        "if (modeledContextActive && isModeledContextFeature(layer, properties))"
        in MAP_DOCUMENT_TEMPLATE
    )
    assert (
        "fillOpacity: modeledContextActive ? 0.72 : 0.42" not in MAP_DOCUMENT_TEMPLATE
    )


def test_global_time_inputs_apply_user_value_after_mode_deactivation() -> None:
    handlers = template_block(
        "function applyGlobalTimeStartInput", "timePlaybackToggle.addEventListener"
    )
    observed = run_node_json(
        """
const calls=[];
const timeStartSlider={value:'400',addEventListener(){}};
const timeIntervalSlider={value:'250',addEventListener(){}};
let timeStartBp=700;
let timeIntervalYears=100;
function stopTimePlayback(){calls.push('stop')}
function deactivateModeledContext(){
  calls.push('deactivate');
  timeStartBp=700;
  timeIntervalYears=100;
}
function clampTimeStart(value, interval){
  calls.push(`start:${value}:${interval}`);
  return Number(value);
}
function clampTimeInterval(value){
  calls.push(`interval:${value}`);
  return Number(value);
}
function renderMapState(){calls.push('render')}
"""
        + handlers
        + """
applyGlobalTimeStartInput();
const startResult={timeStartBp,timeIntervalYears,calls:[...calls]};
calls.length=0;
timeStartBp=700;
timeIntervalYears=100;
applyGlobalTimeIntervalInput();
console.log(JSON.stringify({
  startResult,
  intervalResult:{timeStartBp,timeIntervalYears,calls},
}));
"""
    )

    assert observed == {
        "startResult": {
            "timeStartBp": 400,
            "timeIntervalYears": 100,
            "calls": ["stop", "deactivate", "start:400:100", "render"],
        },
        "intervalResult": {
            "timeStartBp": 700,
            "timeIntervalYears": 250,
            "calls": ["stop", "deactivate", "interval:250", "render"],
        },
    }


def test_hash_uses_one_unambiguous_modeled_or_generic_time_state() -> None:
    assert "modeledContext: params.get('modeled_context')" in MAP_DOCUMENT_TEMPLATE
    hash_block = template_block(
        "function syncHashState()", "function clearHighlightedPoint"
    )
    assert "params.set('modeled_context', modeledWindow.label)" in hash_block
    assert "params.set('modeled_family', modeledContextFamilyKey)" in hash_block
    assert "params.set('modeled_metric', modeledContextMetricKey)" in hash_block
    assert hash_block.index("} else {") < hash_block.index("params.set('time_start'")
    assert "sourceWindow.label === initialState.modeledContext" in MAP_DOCUMENT_TEMPLATE


def test_metric_selection_is_source_scoped_and_null_safe() -> None:
    helper_block = template_block(
        "function modeledContextFamilyByKey", "function stopModeledContextPlayback"
    )
    observed = run_node_json(
        """
const MODELED_CONTEXT = {
  layer_key: 'landclim-reveals-temporal-grid', dataset_id: '937075',
  default_metric_family_key: 'source_land_cover_types',
};
const MODELED_CONTEXT_FAMILIES = [
  {key:'exact_taxa',default_metric_key:'Picea',metrics:[{key:'Picea'}]},
  {key:'source_land_cover_types',default_metric_key:'OL',metrics:[{key:'OL'}]},
];
const initialState = {modeledFamily:'exact_taxa',modeledMetric:'Picea'};
"""
        + helper_block
        + """
const targetLayer={key:'landclim-reveals-temporal-grid'};
const otherDataset={dataset_id:'897303'};
const target={dataset_id:'937075',quality_class:'high',reconstruction_values:{OL:0,Picea:12.5},standard_errors:{OL:0,Picea:1.25}};
const noPollen={dataset_id:'937075',quality_class:'no_pollen_data',reconstruction_values:{OL:27,Picea:12.5},standard_errors:{OL:3,Picea:1.25}};
const hashRestored=[modeledContextFamilyKey,modeledContextMetricKey];
modeledContextFamilyKey='source_land_cover_types'; modeledContextMetricKey='OL';
const defaultValue=modeledContextEstimate(target);
modeledContextFamilyKey='exact_taxa'; modeledContextMetricKey='Picea';
console.log(JSON.stringify({
  hashRestored,
  defaultValue,
  selectedValue:modeledContextEstimate(target),
  selectedError:modeledContextStandardError(target),
  missingValue:modeledContextEstimate({dataset_id:'937075',reconstruction_values:{Picea:null}}),
  blankValue:modeledContextEstimate({dataset_id:'937075',quality_class:'high',reconstruction_values:{Picea:''}}),
  numericStringValue:modeledContextEstimate({dataset_id:'937075',quality_class:'high',reconstruction_values:{Picea:'0'}}),
  noPollenValue:modeledContextEstimate(noPollen),
  noPollenError:modeledContextStandardError(noPollen),
  noPollenFill:modeledContextFillColor(modeledContextEstimate(noPollen)),
  target:isModeledContextFeature(targetLayer,target),
  other:isModeledContextFeature(targetLayer,otherDataset),
}));
"""
    )

    assert observed == {
        "hashRestored": ["exact_taxa", "Picea"],
        "defaultValue": 0,
        "selectedValue": 12.5,
        "selectedError": 1.25,
        "missingValue": None,
        "blankValue": None,
        "numericStringValue": None,
        "noPollenValue": None,
        "noPollenError": None,
        "noPollenFill": "#cbd5e1",
        "target": True,
        "other": False,
    }


def test_quality_contract_and_legend_are_fail_closed_and_explicit() -> None:
    assert "modeledContextQualityContractIsValid()" in MAP_DOCUMENT_TEMPLATE
    assert "No pollen data · N/A, not 0" in MAP_DOCUMENT_TEMPLATE
    assert "explicitly have no pollen data and render as unavailable, never zero" in (
        MAP_DOCUMENT_TEMPLATE
    )
    assert "No pollen data — modeled values are N/A, not zero" in MAP_DOCUMENT_TEMPLATE


def test_visible_frame_masks_no_pollen_values_without_mutating_source() -> None:
    frame_block = template_block(
        "function modeledContextFrameFeatures", "function downloadModeledContextFrame"
    )
    observed = run_node_json(
        """
const MODELED_CONTEXT = {
  layer_key:'landclim-reveals-temporal-grid', dataset_id:'937075',
  dataset_doi:'doi', method_citation:'citation', method_doi:'method',
  value_unit:'percentage_cover', metric_count:47,
  estimate_standard_error_pair_count:88125,
  land_cover_pft_reconciliation_count:5625,
  download_schema_version:'modeled-context-visible-frame.v3',
  quality_classes:['high','low','no_pollen_data'],
  quality_class_counts:{high:628,low:940,no_pollen_data:307},
};
const sourceWindow={label:'0-100 BP'};
const family={key:'source_land_cover_types',label:'Land cover'};
const metric={key:'OL',label:'Open land',source_label:'Open land (OL)',definition:'Open land'};
const sourceFeatures=[
  {type:'Feature',geometry:{type:'Polygon',coordinates:[]},properties:{record_id:'high-zero',dataset_id:'937075',country:'Sweden',time_label:'0-100 BP',quality_class:'high',reconstruction_values:{OL:0,Picea:2},standard_errors:{OL:0,Picea:1}}},
  {type:'Feature',geometry:{type:'Polygon',coordinates:[]},properties:{record_id:'no-pollen',dataset_id:'937075',country:'Sweden',time_label:'0-100 BP',quality_class:'no_pollen_data',reconstruction_values:{OL:27,Picea:2},standard_errors:{OL:3,Picea:1}}},
  {type:'Feature',geometry:{type:'Polygon',coordinates:[]},properties:{record_id:'norway',dataset_id:'937075',country:'Norway',time_label:'0-100 BP',quality_class:'high',reconstruction_values:{OL:8},standard_errors:{OL:1}}},
  {type:'Feature',geometry:{type:'Polygon',coordinates:[]},properties:{record_id:'missing-country',dataset_id:'937075',time_label:'0-100 BP',quality_class:'high',reconstruction_values:{OL:9},standard_errors:{OL:1}}},
];
const POLYGON_LAYERS=[{key:'landclim-reveals-temporal-grid',geojson:{features:sourceFeatures}}];
const activeCountries=new Set(['Sweden']);
const modeledContextActive=true;
function currentModeledContextWindow(){return sourceWindow}
function currentModeledContextFamily(){return family}
function currentModeledContextMetric(){return metric}
function polygonGeometryIsAdmitted(){return true}
function isModeledContextFeature(layer,properties){return layer.key===MODELED_CONTEXT.layer_key && properties.dataset_id===MODELED_CONTEXT.dataset_id}
"""
        + frame_block
        + """
const frame=modeledContextFrameGeoJson();
console.log(JSON.stringify({
  schema:frame.schema_version,
  values:frame.features.map((feature)=>feature.properties.reconstruction_values),
  errors:frame.features.map((feature)=>feature.properties.standard_errors),
  qualityCounts:frame.modeled_context.quality_class_counts,
  denominator:frame.modeled_context.quality_class_count_denominator,
  sourceValues:sourceFeatures.map((feature)=>feature.properties.reconstruction_values),
}));
"""
    )

    assert observed == {
        "schema": "modeled-context-visible-frame.v3",
        "values": [{"OL": 0, "Picea": 2}, {"OL": None, "Picea": None}],
        "errors": [{"OL": 0, "Picea": 1}, {"OL": None, "Picea": None}],
        "qualityCounts": {"high": 1, "no_pollen_data": 1},
        "denominator": 2,
        "sourceValues": [
            {"OL": 0, "Picea": 2},
            {"OL": 27, "Picea": 2},
            {"OL": 8},
            {"OL": 9},
        ],
    }
