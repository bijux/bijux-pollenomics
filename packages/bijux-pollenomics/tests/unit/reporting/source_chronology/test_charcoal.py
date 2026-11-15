"""Literal CHAR context retains observation identities without pollen admission."""

from __future__ import annotations

from copy import deepcopy
import importlib
import importlib.util
import json
from typing import Any

import pytest

from bijux_pollenomics.core.temporal_semantics import TEMPORAL_COMPARABILITY_POSTURES
from bijux_pollenomics.reporting.map_document.temporal_admission import (
    feature_temporal_admission,
)

from ..map_document.browser_semantics.support import run_node_json, template_block

SNAPSHOT = "sha256:" + "a" * 64
BUILD = "sha256:" + "b" * 64
SITE = "neotoma:site:20"
_MODULE = "bijux_pollenomics.reporting.source_chronology.charcoal"


def source() -> dict[str, tuple[list[dict[str, Any]], tuple[int, ...]]]:
    """One named sample, two retained ages and an exact native CHAR datum."""
    lineage = {
        "site_id": SITE,
        "country_code": "SE",
        "source_snapshot_id": SNAPSHOT,
        "build_id": BUILD,
    }
    parents = {"collection_unit_id": "core", "dataset_id": "dataset"}
    rows: dict[str, list[dict[str, Any]]] = {
        "sites": [
            {
                **lineage,
                "source_payload": {
                    "geography": json.dumps({"type": "Point", "coordinates": [18, 59]})
                },
            }
        ],
        "collection_units": [{**lineage, "collection_unit_id": "core"}],
        "datasets": [{**lineage, **parents}],
        "samples": [
            {
                **lineage,
                **parents,
                "sample_id": "sample",
                "source_depth": 10,
                "source_thickness": None,
            }
        ],
        "variables": [
            {
                "variable_id": "variable",
                "source_taxon_id": 99,
                "source_snapshot_id": SNAPSHOT,
                "build_id": BUILD,
            }
        ],
        "observations": [
            {
                **lineage,
                **parents,
                "observation_id": "observation",
                "sample_id": "sample",
                "variable_id": "variable",
                "source_taxon_id": 99,
                "source_reported_name": "Charcoal",
                "source_ecological_group": "CHAR",
                "source_element": ">25 µm",
                "source_element_type": ">25 µm",
                "source_unit": "NISP",
                "source_value": 0,
                "source_denominator": None,
                "denominator_status": "not_provided_by_source",
                "detection_status": "reported_value",
                "unit_family": "count",
                "source_context": None,
            }
        ],
        "chronologies": [
            {
                **lineage,
                "chronology_id": "model",
                "collection_unit_id": "core",
                "source_chronology_id": 7001,
            }
        ],
        "age_claims": [
            {
                **lineage,
                **parents,
                "chronology_claim_id": "claim-default",
                "subject_type": "sample",
                "subject_id": "sample",
                "source_record_id": "sample",
                "chronology_id": "model",
                "chronology_name": "Native model",
                "is_default_chronology": True,
                "comparability_status": "comparable",
                "younger_bp": 100,
                "older_bp": 120,
                "provenance_record_id": SNAPSHOT,
            }
        ],
    }
    rows["age_claims"].append(
        {
            **rows["age_claims"][0],
            "chronology_claim_id": "claim-alternative",
            "is_default_chronology": False,
            "younger_bp": 80,
            "older_bp": 90,
        }
    )
    return {name: (values, tuple(3 for _ in values)) for name, values in rows.items()}


def project(loaded: dict[str, Any], *, sites: set[str] | None = None) -> Any:
    assert importlib.util.find_spec(_MODULE) is not None, (
        "literal CHAR source context owner is unavailable"
    )
    return importlib.import_module(_MODULE).build_native_charcoal_atlas_projection(
        loaded,
        projected_site_ids={SITE} if sites is None else sites,
        source_snapshot_id=SNAPSHOT,
        build_id=BUILD,
    )


def test_literal_charcoal_keeps_one_observation_and_every_alternative_age() -> None:
    loaded = source()
    original = deepcopy(loaded)
    result = project(loaded)
    assert loaded == original
    assert len(result.point_layers) == 1
    layer = result.point_layers[0]
    assert layer["key"] == "neotoma-native-charcoal-context"
    assert layer["default_enabled"] is False
    assert layer["candidate_ranking_eligible"] is False
    assert layer["scientific_selection_enabled"] is False
    assert layer["scientific_classification_eligible"] is False
    assert layer["propagation_status"] == "refused" and layer["edge_count"] == 0
    assert layer["count"] == len(layer["features"]) == 1
    feature = layer["features"][0]
    assert feature["observation_id"] == "observation"
    assert feature["observation_denominator"] == feature["record_count"] == 1
    assert feature["source_age_claim_ids"] == ["claim-alternative", "claim-default"]
    assert feature["chronology_claim_id"] == "claim-default"
    assert (feature["time_start_bp"], feature["time_end_bp"]) == (100, 120)
    assert (
        feature["source_value"] == 0 and feature["detection_status"] == "reported_value"
    )
    assert feature["source_denominator"] is None
    assert feature["denominator_status"] == "not_provided_by_source"
    assert feature["source_depth"] == 10 and feature["source_depth_unit"] is None
    assert feature["source_part_number"] == 3
    assert (
        feature["source_observation_locator"]
        == "surfaces/observations/part-00003.json#observation_id=observation"
    )
    assert feature["record_id"] == SITE and feature["source_record_id"] == "sample"
    assert feature["candidate_generation_status"] == "refused"
    assert feature["propagation_eligible"] is False
    assert result.reconciliation["scientific_event_count"] == 0


@pytest.mark.parametrize(
    "younger,older,label", [(100, 120, "100–120 BP"), (100.25, 100.25, "100.25 BP")]
)
def test_actual_map_time_label_shows_selected_source_interval_without_conversion(
    younger: float, older: float, label: str
) -> None:
    loaded = source()
    loaded["age_claims"][0][0].update(younger_bp=younger, older_bp=older)
    feature = project(loaded).point_layers[0]["features"][0]
    output = run_node_json(
        template_block("function finiteTimeValue", "function pointFeatureInTimeWindow")
        + "const feature="
        + json.dumps(feature)
        + ";console.log(JSON.stringify({label:featureTimeLabel(feature),descriptor:featureTimeDescriptor(feature),admission:featureTimeAdmission(feature)}));"
    )
    assert label in output["label"]
    assert "display only" in output["label"]
    assert output["descriptor"] == {"label": "Date", "value": output["label"]}
    assert output["admission"] == {
        "status": "valid",
        "window": {"start": younger, "end": older},
    }
    assert feature_temporal_admission(feature) == ("admitted", (younger, older))


def test_untimed_native_observation_uses_owned_contextual_temporal_vocabulary() -> None:
    loaded = source()
    loaded["age_claims"] = ([], ())
    feature = project(loaded).point_layers[0]["features"][0]
    posture = feature["temporal_semantics"]["comparability_posture"]
    assert posture in TEMPORAL_COMPARABILITY_POSTURES
    assert posture == "contextual_label_only"
    assert feature_temporal_admission(feature) == ("contextual", None)


@pytest.mark.parametrize(
    "value,detection",
    [
        (None, "source_null"),
        (0, "reported_zero"),
        (-2, "below_detection"),
        (4, "reported_value"),
    ],
)
def test_native_values_and_detection_states_are_never_positive_pollen_filtered(
    value: object, detection: str
) -> None:
    loaded = source()
    loaded["observations"][0][0].update(source_value=value, detection_status=detection)
    result = project(loaded)
    feature = result.point_layers[0]["features"][0]
    assert feature["source_value"] == value and feature["detection_status"] == detection
    assert result.reconciliation["native_charcoal_observation_count"] == 1


def test_eight_native_material_tuples_remain_separate_unique_observations() -> None:
    loaded = source()
    tuples = [
        ("fragment", "fragment"),
        ("<10 µm", None),
        ("particle", "particle"),
        (">25 µm", ">25 µm"),
        ("fragments", "fragments"),
        ("10-25 µm", None),
        ("counted", "counted"),
        (">250 µm", ">250 µm"),
    ]
    original = loaded["observations"][0][0]
    loaded["observations"] = (
        [
            {
                **original,
                "observation_id": f"obs-{index}",
                "source_element": element,
                "source_element_type": kind,
            }
            for index, (element, kind) in enumerate(tuples)
        ],
        tuple(range(1, 9)),
    )
    result = project(loaded)
    features = result.point_layers[0]["features"]
    assert (
        len(features) == len({feature["observation_id"] for feature in features}) == 8
    )
    assert {
        (feature["source_element"], feature["source_element_type"])
        for feature in features
    } == set(tuples)
    assert (
        sum(
            row["observation_count"]
            for row in result.reconciliation["native_material_type_counts"]
        )
        == 8
    )


@pytest.mark.parametrize("code", ["TRSH", "CHAR ", "char", None])
def test_only_literal_char_is_admitted_to_this_display_layer(code: object) -> None:
    loaded = source()
    loaded["observations"][0][0]["source_ecological_group"] = code
    assert project(loaded).point_layers[0]["count"] == 0


@pytest.mark.parametrize(
    "field",
    [
        "dataset_id",
        "collection_unit_id",
        "site_id",
        "country_code",
        "source_snapshot_id",
        "build_id",
    ],
)
def test_foreign_sample_cannot_supply_charcoal_depth_or_age(field: str) -> None:
    loaded = source()
    loaded["samples"][0][0][field] = "foreign"
    result = project(loaded)
    feature = result.point_layers[0]["features"][0]
    assert feature["source_depth"] is None
    assert feature["time_start_bp"] is feature["time_end_bp"] is None
    assert feature["source_join_status"] == "refused"
    assert result.reconciliation["native_charcoal_observation_count"] == 1


@pytest.mark.parametrize(
    "damage", ["ambiguous", "foreign_claim", "unidentified_model", "missing"]
)
def test_unselected_age_keeps_a_single_untimed_native_observation(damage: str) -> None:
    loaded = source()
    claims = loaded["age_claims"][0]
    if damage == "ambiguous":
        claims[0]["is_default_chronology"] = False
    elif damage == "foreign_claim":
        claims[0]["dataset_id"] = "foreign"
    elif damage == "unidentified_model":
        loaded["chronologies"][0][0]["source_chronology_id"] = None
    else:
        loaded["age_claims"] = ([], ())
    result = project(loaded)
    feature = result.point_layers[0]["features"][0]
    assert result.point_layers[0]["count"] == 1
    assert feature["time_start_bp"] is feature["time_end_bp"] is None
    assert feature["chronology_claim_id"] is None
    assert feature["chronology_selection_posture"].startswith("refused_")


def test_population_reconciliation_includes_excluded_sites_without_calling_zero_absence() -> (
    None
):
    result = project(source(), sites=set())
    assert result.point_layers[0]["count"] == 0
    account = result.reconciliation
    assert account["native_charcoal_observation_count"] == 1
    assert account["published_observation_count"] == 0
    assert account["excluded_observation_count"] == 1
    assert account["excluded_reason_counts"] == {"site_outside_projection": 1}
    assert account["source_country_counts"] == {"DK": 0, "FI": 0, "NO": 0, "SE": 1}
    assert "captured source scope" in account["zero_count_semantics"]


@pytest.mark.parametrize("damage", ["duplicate", "part_count", "part_number"])
def test_ambiguous_identity_or_transport_locator_refuses_projection(
    damage: str,
) -> None:
    loaded = source()
    observations, _ = loaded["observations"]
    if damage == "duplicate":
        observations.append(deepcopy(observations[0]))
        loaded["observations"] = (observations, (1, 2))
    else:
        loaded["observations"] = (
            observations,
            () if damage == "part_count" else (True,),
        )
    with pytest.raises(ValueError, match="charcoal"):
        project(loaded)
