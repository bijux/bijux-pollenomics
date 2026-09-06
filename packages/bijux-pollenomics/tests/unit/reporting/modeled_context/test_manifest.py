from __future__ import annotations

from copy import deepcopy
import json
from typing import cast

import pytest

from bijux_pollenomics.reporting.context.polygons import build_external_polygon_layer
from bijux_pollenomics.reporting.modeled_context import (
    ModeledContextContractError,
    build_modeled_context_manifest,
)
from bijux_pollenomics.reporting.modeled_context.contracts import (
    GITHUMBI_METHOD_DOI,
    PANGAEA_COUNTRY_CELL_COUNTS,
    PANGAEA_DATASET_DOI,
    PANGAEA_WINDOWS_PRESENT_TO_OLDEST,
)
from bijux_pollenomics.reporting.modeled_context.metric_families import (
    PANGAEA_METRIC_KEYS,
)
from tests.support.repository import REPOSITORY_ROOT


def _metric_values() -> dict[str, float]:
    values = dict.fromkeys(PANGAEA_METRIC_KEYS, 1.0)
    values.update({"ET": 6.0, "ST": 4.0, "OL": 3.0})
    return values


def _complete_layer() -> dict[str, object]:
    features: list[dict[str, object]] = []
    record_number = 0
    for label, start, end in PANGAEA_WINDOWS_PRESENT_TO_OLDEST:
        for country, count in PANGAEA_COUNTRY_CELL_COUNTS.items():
            for _ in range(count):
                record_number += 1
                quality_class = (
                    "high"
                    if record_number <= 628
                    else "low"
                    if record_number <= 1_568
                    else "no_pollen_data"
                )
                features.append(
                    {
                        "type": "Feature",
                        "properties": {
                            "record_id": f"modeled-{record_number:04d}",
                            "dataset_id": "937075",
                            "country": country,
                            "time_label": label,
                            "time_start_bp": start,
                            "time_end_bp": end,
                            "source_url": PANGAEA_DATASET_DOI,
                            "value_unit": "percentage_cover",
                            "quality_class": quality_class,
                            "temporal_comparability_posture": (
                                "numeric_interval_with_caveat"
                            ),
                            "bibliography_reference_keys": ["githumbi-et-al-2022"],
                            "reconstruction_values": _metric_values(),
                            "standard_errors": {
                                key: 2.25 for key in PANGAEA_METRIC_KEYS
                            },
                        },
                    }
                )
    return {
        "key": "landclim-reveals-temporal-grid",
        "geojson": {"type": "FeatureCollection", "features": features},
    }


def test_complete_inventory_builds_exact_oldest_to_present_contract() -> None:
    manifest = build_modeled_context_manifest([_complete_layer()])

    assert manifest["status"] == "available"
    assert manifest["feature_count"] == 1875
    assert manifest["schema_version"] == "modeled-context-manifest.v3"
    assert manifest["quality_classes"] == ["high", "low", "no_pollen_data"]
    assert manifest["quality_class_counts"] == {
        "high": 628,
        "low": 940,
        "no_pollen_data": 307,
    }
    assert manifest["no_pollen_data_display_posture"] == "null_not_zero"
    assert manifest["download_schema_version"] == "modeled-context-visible-frame.v3"
    assert manifest["cell_count"] == 75
    assert manifest["country_cell_counts"] == {
        "Denmark": 6,
        "Finland": 19,
        "Norway": 24,
        "Sweden": 26,
    }
    windows = manifest["windows_oldest_to_present"]
    assert isinstance(windows, list)
    assert len(windows) == 25
    assert windows[0] == {
        "label": "11200-11700 BP",
        "time_start_bp": 11200,
        "time_end_bp": 11700,
        "feature_count": 75,
        "country_counts": PANGAEA_COUNTRY_CELL_COUNTS,
    }
    assert windows[-1]["label"] == "0-100 BP"
    assert manifest["evidence_role"] == "context_only"
    assert manifest["propagation_use_allowed"] is False
    assert manifest["interpolation_allowed"] is False
    assert manifest["dataset_doi"] == PANGAEA_DATASET_DOI
    assert manifest["method_doi"] == GITHUMBI_METHOD_DOI
    assert manifest["default_metric_family_key"] == "source_land_cover_types"
    assert manifest["metric_key"] == "OL"
    assert manifest["metric_family_count"] == 3
    assert manifest["metric_count"] == 47
    assert manifest["estimate_standard_error_pair_count"] == 88_125
    assert manifest["land_cover_pft_reconciliation_count"] == 5_625
    families = cast(list[dict[str, object]], manifest["metric_families"])
    assert [family["metric_count"] for family in families] == [31, 13, 3]
    palette = cast(list[dict[str, object]], manifest["palette"])
    assert [entry["label"] for entry in palette] == [
        "0–20%",
        ">20–40%",
        ">40–60%",
        ">60–80%",
        ">80–100%",
    ]
    assert json.dumps(manifest, sort_keys=True, separators=(",", ":")) == json.dumps(
        build_modeled_context_manifest([_complete_layer()]),
        sort_keys=True,
        separators=(",", ":"),
    )


def test_missing_dataset_is_explicitly_unavailable() -> None:
    manifest = build_modeled_context_manifest([])

    assert manifest == {
        "schema_version": "modeled-context-manifest.v3",
        "status": "unavailable",
        "reason_code": "pangaea_937075_temporal_grid_not_available",
        "evidence_role": "context_only",
        "propagation_use_allowed": False,
        "metric_families": [],
        "windows_oldest_to_present": [],
    }


def test_landclim_i_rows_are_not_mistaken_for_pangaea_937075() -> None:
    layer = _complete_layer()
    geojson = cast(dict[str, object], layer["geojson"])
    features = cast(list[dict[str, object]], geojson["features"])
    features.insert(
        0,
        {
            "type": "Feature",
            "properties": {
                "record_id": "897303:first-row",
                "dataset_id": "897303",
                "value_unit": "proportion_of_grid_cell",
                "reconstruction_values": {
                    "land_cover_types": {"Open Grass/Herb": 0.375}
                },
                "standard_errors": {"land_cover_types": {"Open Grass/Herb": 0.0225}},
            },
        },
    )

    manifest = build_modeled_context_manifest([layer])

    assert manifest["dataset_id"] == "937075"
    assert manifest["value_unit"] == "percentage_cover"
    assert manifest["metric_key"] == "OL"
    assert manifest["feature_count"] == 1875


def _first_properties(layer: dict[str, object]) -> dict[str, object]:
    geojson = cast(dict[str, object], layer["geojson"])
    features = cast(list[dict[str, object]], geojson["features"])
    return cast(dict[str, object], features[0]["properties"])


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("estimate", "OL estimate must be a finite number"),
        ("comparability", "lacks modeled-time caveats"),
        ("doi", "has the wrong PANGAEA DOI"),
        ("quality", "has an unsupported or missing quality class"),
    ],
)
def test_scientifically_unsupported_rows_fail_closed(
    mutation: str, message: str
) -> None:
    layer = _complete_layer()
    row = _first_properties(layer)
    if mutation == "estimate":
        cast(dict[str, object], row["reconstruction_values"])["OL"] = None
    elif mutation == "comparability":
        row["temporal_comparability_posture"] = "comparable"
    elif mutation == "doi":
        row["source_url"] = ""
    else:
        row["quality_class"] = ""

    with pytest.raises(ModeledContextContractError, match=message):
        build_modeled_context_manifest([layer])


def test_incomplete_country_window_inventory_fails_closed() -> None:
    layer = deepcopy(_complete_layer())
    geojson = cast(dict[str, object], layer["geojson"])
    cast(list[object], geojson["features"]).pop()

    with pytest.raises(
        ModeledContextContractError,
        match="Nordic country/window inventory is incomplete",
    ):
        build_modeled_context_manifest([layer])


def test_quality_class_distribution_drift_fails_closed() -> None:
    layer = _complete_layer()
    geojson = cast(dict[str, object], layer["geojson"])
    features = cast(list[dict[str, object]], geojson["features"])
    row = cast(dict[str, object], features[-1]["properties"])
    assert row["quality_class"] == "no_pollen_data"
    row["quality_class"] = "high"

    with pytest.raises(
        ModeledContextContractError,
        match="quality-class inventory differs from the source workbook",
    ):
        build_modeled_context_manifest([layer])


@pytest.mark.parametrize("value_group", ["reconstruction_values", "standard_errors"])
def test_every_metric_requires_a_matching_estimate_and_error_key(
    value_group: str,
) -> None:
    layer = _complete_layer()
    row = _first_properties(layer)
    cast(dict[str, object], row[value_group]).pop("Picea")

    with pytest.raises(
        ModeledContextContractError,
        match="metric keys/order differ from the source header",
    ):
        build_modeled_context_manifest([layer])


def test_land_cover_totals_must_reconcile_to_source_pft_codes() -> None:
    layer = _complete_layer()
    row = _first_properties(layer)
    cast(dict[str, object], row["reconstruction_values"])["ISTS"] = 2.0

    with pytest.raises(
        ModeledContextContractError,
        match="ST does not reconcile to source PFT codes",
    ):
        build_modeled_context_manifest([layer])


def test_repository_pangaea_surface_matches_presentation_contract() -> None:
    source_path = (
        REPOSITORY_ROOT
        / "data/landclim/normalized/nordic_reveals_temporal_grid_cells.geojson"
    )
    geojson = json.loads(source_path.read_text(encoding="utf-8"))
    layer = build_external_polygon_layer(geojson, source_path=source_path)

    manifest = build_modeled_context_manifest([layer])

    assert manifest["status"] == "available"
    assert manifest["feature_count"] == 1875
    assert manifest["metric_count"] == 47
    assert manifest["estimate_standard_error_pair_count"] == 88_125
    assert manifest["land_cover_pft_reconciliation_count"] == 5_625
    assert manifest["quality_class_counts"] == {
        "high": 628,
        "low": 940,
        "no_pollen_data": 307,
    }
    assert len(manifest["windows_oldest_to_present"]) == 25
