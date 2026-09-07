from __future__ import annotations

from copy import deepcopy
import json

from bijux_pollenomics.reporting.context.polygons import build_external_polygon_layer
from bijux_pollenomics.reporting.map_document.payload import build_map_document_payload
from bijux_pollenomics.reporting.map_document.template import MAP_DOCUMENT_TEMPLATE
from bijux_pollenomics.reporting.map_publication import resolve_map_scope_policy
from tests.support.repository import REPOSITORY_ROOT

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
    validation_block = template_block(
        "const MODELED_CONTEXT_WINDOWS",
        "function stopModeledContextPlayback",
    )
    observed = run_node_json(
        f"""
const MODELED_CONTEXT={json.dumps(manifest)};
const initialState={{modeledFamily:null,modeledMetric:null}};
{validation_block}
console.log(JSON.stringify({{available:modeledContextAvailable()}}));
"""
    )
    assert observed == {"available": True}


def test_activation_selects_exact_source_window_and_hide_restores_generic_time() -> (
    None
):
    block = template_block(
        "const MODELED_CONTEXT_WINDOWS",
        "let activeCountries",
    )
    result = run_node_json(
        f"const MODELED_CONTEXT = {json.dumps(_browser_modeled_context_manifest())};\n"
        """
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
            "timeStartBp": 10000,
            "timeIntervalYears": 500,
            "layerEnabled": True,
        },
        "inactive": {
            "modeledContextActive": False,
            "timeStartBp": 321,
            "timeIntervalYears": 654,
        },
    }


def test_modeled_context_contract_refuses_malformed_windows_and_palette() -> None:
    validation_block = template_block(
        "const MODELED_CONTEXT_WINDOWS",
        "function stopModeledContextPlayback",
    )
    valid = _browser_modeled_context_manifest()
    cases: dict[str, dict[str, object]] = {"valid": valid}

    for label, value in (
        ("null_endpoint", None),
        ("blank_endpoint", ""),
        ("string_endpoint", "0"),
        ("boolean_endpoint", False),
        ("array_endpoint", [0]),
        ("object_endpoint", {}),
    ):
        manifest = deepcopy(valid)
        windows = manifest["windows_oldest_to_present"]
        assert isinstance(windows, list)
        window = windows[0]
        assert isinstance(window, dict)
        window["time_start_bp"] = value
        cases[label] = manifest

    missing_endpoint = deepcopy(valid)
    missing_windows = missing_endpoint["windows_oldest_to_present"]
    assert isinstance(missing_windows, list)
    missing_window = missing_windows[0]
    assert isinstance(missing_window, dict)
    del missing_window["time_start_bp"]
    cases["missing_endpoint"] = missing_endpoint

    malformed_windows = deepcopy(valid)
    malformed_windows["windows_oldest_to_present"] = {}
    cases["non_array_windows"] = malformed_windows

    duplicate_label = deepcopy(valid)
    duplicate_windows = duplicate_label["windows_oldest_to_present"]
    assert isinstance(duplicate_windows, list)
    assert isinstance(duplicate_windows[0], dict)
    assert isinstance(duplicate_windows[1], dict)
    duplicate_windows[1]["label"] = duplicate_windows[0]["label"]
    cases["duplicate_label"] = duplicate_label

    chronology_gap = deepcopy(valid)
    gap_windows = chronology_gap["windows_oldest_to_present"]
    assert isinstance(gap_windows, list)
    assert isinstance(gap_windows[1], dict)
    gap_windows[1]["time_end_bp"] = 11999
    cases["chronology_gap"] = chronology_gap

    feature_drift = deepcopy(valid)
    drift_windows = feature_drift["windows_oldest_to_present"]
    assert isinstance(drift_windows, list)
    assert isinstance(drift_windows[0], dict)
    drift_windows[0]["feature_count"] = 74
    cases["feature_drift"] = feature_drift

    quality_swap = deepcopy(valid)
    quality_windows = quality_swap["windows_oldest_to_present"]
    assert isinstance(quality_windows, list)
    assert isinstance(quality_windows[0], dict)
    assert isinstance(quality_windows[1], dict)
    first_quality = quality_windows[0]["quality_class_counts"]
    second_quality = quality_windows[1]["quality_class_counts"]
    assert isinstance(first_quality, dict)
    assert isinstance(second_quality, dict)
    first_quality.update({"high": 75, "low": 0})
    second_quality.update({"high": 73, "low": 2})
    cases["quality_swap_with_stable_global_total"] = quality_swap

    country_drift = deepcopy(valid)
    country_windows = country_drift["windows_oldest_to_present"]
    assert isinstance(country_windows, list)
    assert isinstance(country_windows[0], dict)
    first_country_counts = country_windows[0]["country_counts"]
    assert isinstance(first_country_counts, dict)
    first_country_counts.update({"Denmark": 7, "Finland": 18})
    cases["country_drift"] = country_drift

    for label, value in (
        ("null_palette_maximum", None),
        ("blank_palette_maximum", ""),
        ("string_palette_maximum", "20"),
        ("array_palette_maximum", [20]),
    ):
        manifest = deepcopy(valid)
        palette = manifest["palette"]
        assert isinstance(palette, list)
        entry = palette[0]
        assert isinstance(entry, dict)
        entry["maximum"] = value
        cases[label] = manifest

    incomplete_palette = deepcopy(valid)
    palette = incomplete_palette["palette"]
    assert isinstance(palette, list)
    final_entry = palette[-1]
    assert isinstance(final_entry, dict)
    final_entry["maximum"] = 99
    cases["incomplete_palette"] = incomplete_palette

    non_array_families = deepcopy(valid)
    non_array_families["metric_families"] = {}
    cases["non_array_families"] = non_array_families

    null_family = deepcopy(valid)
    families = null_family["metric_families"]
    assert isinstance(families, list)
    families[2] = None
    cases["null_family"] = null_family

    non_array_metrics = deepcopy(valid)
    families = non_array_metrics["metric_families"]
    assert isinstance(families, list)
    family = families[2]
    assert isinstance(family, dict)
    family["metrics"] = {}
    cases["non_array_metrics"] = non_array_metrics

    null_metric = deepcopy(valid)
    families = null_metric["metric_families"]
    assert isinstance(families, list)
    family = families[2]
    assert isinstance(family, dict)
    metrics = family["metrics"]
    assert isinstance(metrics, list)
    metrics[0] = None
    cases["null_metric"] = null_metric

    missing_default_family = deepcopy(valid)
    missing_default_family["default_metric_family_key"] = "unavailable"
    cases["missing_default_family"] = missing_default_family

    missing_default_metric = deepcopy(valid)
    families = missing_default_metric["metric_families"]
    assert isinstance(families, list)
    family = families[2]
    assert isinstance(family, dict)
    family["default_metric_key"] = "unavailable"
    cases["missing_default_metric"] = missing_default_metric

    duplicate_family_key = deepcopy(valid)
    families = duplicate_family_key["metric_families"]
    assert isinstance(families, list)
    assert isinstance(families[0], dict)
    assert isinstance(families[1], dict)
    families[1]["key"] = families[0]["key"]
    cases["duplicate_family_key"] = duplicate_family_key

    duplicate_metric_key = deepcopy(valid)
    families = duplicate_metric_key["metric_families"]
    assert isinstance(families, list)
    assert isinstance(families[0], dict)
    assert isinstance(families[1], dict)
    first_metrics = families[0]["metrics"]
    second_metrics = families[1]["metrics"]
    assert isinstance(first_metrics, list)
    assert isinstance(second_metrics, list)
    assert isinstance(first_metrics[0], dict)
    assert isinstance(second_metrics[0], dict)
    second_metrics[0]["key"] = first_metrics[0]["key"]
    families[1]["default_metric_key"] = first_metrics[0]["key"]
    cases["duplicate_metric_key"] = duplicate_metric_key

    metric_count_drift = deepcopy(valid)
    families = metric_count_drift["metric_families"]
    assert isinstance(families, list)
    assert isinstance(families[0], dict)
    families[0]["metric_count"] = 2
    cases["metric_count_drift"] = metric_count_drift

    family_count_drift = deepcopy(valid)
    family_count_drift["metric_family_count"] = 4
    cases["family_count_drift"] = family_count_drift

    global_metric_count_drift = deepcopy(valid)
    global_metric_count_drift["metric_count"] = 4
    cases["global_metric_count_drift"] = global_metric_count_drift

    observed = run_node_json(
        f"""
const validatorSource={json.dumps(validation_block)};
const evaluate=new Function('MODELED_CONTEXT','initialState',`${{validatorSource}}\nreturn {{available:modeledContextAvailable(),zeroFill:modeledContextFillColor(0)}};`);
const cases={json.dumps(cases)};
console.log(JSON.stringify(Object.fromEntries(Object.entries(cases).map(([key,manifest])=>[
  key,
  evaluate(manifest,{{modeledFamily:null,modeledMetric:null}}),
]))));
"""
    )

    assert observed["valid"] == {"available": True, "zeroFill": "#1b4332"}
    assert all(
        not outcome["available"]
        for label, outcome in observed.items()
        if label != "valid"
    )
    assert all(
        observed[label]["zeroFill"] == "#cbd5e1"
        for label in (
            "null_palette_maximum",
            "blank_palette_maximum",
            "string_palette_maximum",
            "array_palette_maximum",
            "incomplete_palette",
        )
    )
