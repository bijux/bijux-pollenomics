from __future__ import annotations

from copy import deepcopy

from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE

from ..browser_semantics.support import run_node_json, template_block


def _browser_modeled_context_manifest() -> dict[str, object]:
    country_counts = {"Denmark": 6, "Finland": 19, "Norway": 24, "Sweden": 26}
    quality_classes = ["high", "low", "no_pollen_data"]
    window_country_quality_counts = {
        "Denmark": {"high": 5, "low": 1, "no_pollen_data": 0},
        "Finland": {"high": 19, "low": 0, "no_pollen_data": 0},
        "Norway": {"high": 24, "low": 0, "no_pollen_data": 0},
        "Sweden": {"high": 26, "low": 0, "no_pollen_data": 0},
    }
    windows = []
    for index in range(25):
        start = (24 - index) * 500
        end = start + 500
        windows.append(
            {
                "label": f"{start}-{end} BP",
                "time_start_bp": start,
                "time_end_bp": end,
                "feature_count": 75,
                "no_pollen_data_count": 0,
                "quality_class_counts": {
                    "high": 74,
                    "low": 1,
                    "no_pollen_data": 0,
                },
                "country_counts": dict(country_counts),
                "country_quality_class_counts": deepcopy(window_country_quality_counts),
            }
        )
    return {
        "status": "available",
        "schema_version": "modeled-context-manifest.v3",
        "cell_count": 75,
        "feature_count": 1875,
        "quality_classes": quality_classes,
        "quality_class_counts": {
            "high": 1850,
            "low": 25,
            "no_pollen_data": 0,
        },
        "country_cell_counts": dict(country_counts),
        "country_quality_class_counts": {
            "Denmark": {"high": 125, "low": 25, "no_pollen_data": 0},
            "Finland": {"high": 475, "low": 0, "no_pollen_data": 0},
            "Norway": {"high": 600, "low": 0, "no_pollen_data": 0},
            "Sweden": {"high": 650, "low": 0, "no_pollen_data": 0},
        },
        "no_pollen_data_display_posture": "null_not_zero",
        "layer_key": "landclim-reveals-temporal-grid",
        "dataset_id": "937075",
        "default_metric_family_key": "source_land_cover_types",
        "metric_key": "OL",
        "metric_family_count": 3,
        "metric_count": 3,
        "value_unit": "percentage_cover",
        "metric_families": [
            {
                "key": "exact_taxa",
                "label": "Exact taxa",
                "metric_count": 1,
                "default_metric_key": "Picea",
                "metrics": [
                    {
                        "key": "Picea",
                        "label": "Picea abies",
                        "source_label": "Picea abies",
                        "definition": None,
                    }
                ],
            },
            {
                "key": "source_pft_codes",
                "label": "Source PFT codes",
                "metric_count": 1,
                "default_metric_key": "TBE1",
                "metrics": [
                    {
                        "key": "TBE1",
                        "label": "TBE1",
                        "source_label": "TBE1",
                        "definition": "Shade-tolerant evergreen trees",
                    }
                ],
            },
            {
                "key": "source_land_cover_types",
                "label": "Source land-cover types",
                "metric_count": 1,
                "default_metric_key": "OL",
                "metrics": [
                    {
                        "key": "OL",
                        "label": "Open land",
                        "source_label": "Open land (OL)",
                        "definition": "Open land",
                    }
                ],
            },
        ],
        "windows_oldest_to_present": windows,
        "palette": [
            {"maximum": 20, "color": "#1b4332", "label": "0–20%"},
            {"maximum": 40, "color": "#52796f", "label": ">20–40%"},
            {"maximum": 60, "color": "#a7c957", "label": ">40–60%"},
            {"maximum": 80, "color": "#f2cc8f", "label": ">60–80%"},
            {"maximum": 100, "color": "#d97706", "label": ">80–100%"},
        ],
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
const MODELED_CONTEXT_PALETTE = [{maximum:100,color:'#d97706',label:'0–100%'}];
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
  arrayValue:modeledContextEstimate({dataset_id:'937075',quality_class:'high',reconstruction_values:{Picea:[0]}}),
  negativeValue:modeledContextEstimate({dataset_id:'937075',quality_class:'high',reconstruction_values:{Picea:-1}}),
  excessiveValue:modeledContextEstimate({dataset_id:'937075',quality_class:'high',reconstruction_values:{Picea:101}}),
  negativeError:modeledContextStandardError({dataset_id:'937075',quality_class:'high',standard_errors:{Picea:-1}}),
  noPollenValue:modeledContextEstimate(noPollen),
  noPollenError:modeledContextStandardError(noPollen),
  noPollenFill:modeledContextFillColor(modeledContextEstimate(noPollen)),
  arrayFill:modeledContextFillColor([]),
  objectFill:modeledContextFillColor({}),
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
        "arrayValue": None,
        "negativeValue": None,
        "excessiveValue": None,
        "negativeError": None,
        "noPollenValue": None,
        "noPollenError": None,
        "noPollenFill": "#cbd5e1",
        "arrayFill": "#cbd5e1",
        "objectFill": "#cbd5e1",
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
