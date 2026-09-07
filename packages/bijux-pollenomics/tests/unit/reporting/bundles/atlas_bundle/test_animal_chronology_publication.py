"""Animal source chronology integration and analytical-isolation contracts."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
from typing import cast

import pytest

from bijux_pollenomics.reporting.adna import build_animal_sample_chronology_context
from bijux_pollenomics.reporting.bundles.atlas_bundle import contracts
from bijux_pollenomics.reporting.geography import (
    GeographicScope,
    build_published_geography_plan,
)
from tests.support.repository import REPOSITORY_ROOT


def _animal_chronology_layer() -> dict[str, object]:
    return {
        "key": "animal-source-chronology",
        "label": "Animal source chronology",
        "source_name": "Governed animal sample evidence",
        "description": "Source-native sample chronology for display.",
        "group": "animal-chronology-context",
        "semantic_role": "animal_source_chronology_context",
        "contribution_role": "display_only",
        "default_enabled": False,
        "applies_time_filter": True,
        "candidate_ranking_eligible": False,
        "scientific_classification_eligible": False,
        "scientific_selection_enabled": False,
        "propagation_status": "refused",
        "propagation_reason_code": "display_only_source_chronology",
        "edge_count": 0,
        "features": [
            {
                "title": "sample-1",
                "subtitle": "Bos taurus",
                "country": "Sweden",
                "latitude": 59.3,
                "longitude": 18.1,
                "time_start_bp": 900,
                "time_end_bp": 1100,
                "time_mean_bp": 1000,
                "record_count": 1,
            }
        ],
    }


def _ordinary_context_layer() -> dict[str, object]:
    return {
        "key": "ordinary-context",
        "label": "Ordinary context",
        "source_name": "Context source",
        "features": [
            {
                "title": "context-1",
                "subtitle": "Archaeology",
                "country": "Sweden",
                "latitude": 59.4,
                "longitude": 18.2,
                "time_start_bp": 800,
                "time_end_bp": 1200,
                "record_count": 1,
            }
        ],
    }


@pytest.mark.parametrize(
    "field,value,message",
    (
        ("input_identity", {}, "input identity differs"),
        ("refusal_count", -1, "refusal count differs"),
    ),
)
def test_animal_chronology_publication_refuses_accountability_drift(
    field: str,
    value: object,
    message: str,
) -> None:
    projection = build_animal_sample_chronology_context(REPOSITORY_ROOT / "data")
    accountability = dict(projection.accountability)
    accountability[field] = value
    contradictory = SimpleNamespace(
        accountability=accountability,
        input_identity=projection.input_identity,
        refusals=projection.refusals,
        point_layers=projection.point_layers,
        corpus_identity=projection.corpus_identity,
    )

    with pytest.raises(ValueError, match=message):
        contracts._animal_chronology_publication(
            contradictory,
            artifact_name="animal-context.json",
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("global_count", "global_admitted_node_count differs from corpus identity"),
        ("projected_count", "projected count does not reconcile"),
        ("fabricated_norway", "governed_country_rows differs from corpus identity"),
    ),
)
def test_animal_chronology_publication_reconciles_denominators(
    mutation: str, message: str
) -> None:
    projection = build_animal_sample_chronology_context(REPOSITORY_ROOT / "data")
    accountability = deepcopy(projection.accountability)
    if mutation == "global_count":
        accountability["global_admitted_node_count"] = 999
        accountability["excluded_by_scope_count"] = 468
    elif mutation == "projected_count":
        accountability["projected_node_count"] = 998
    else:
        governed = cast(
            list[dict[str, object]], accountability["governed_country_rows"]
        )
        norway = next(row for row in governed if row["country_name"] == "Norway")
        norway.update({"node_count": 1, "time_min_bp": 100, "time_max_bp": 100})
    layers = [dict(layer) for layer in projection.point_layers]
    for layer in layers:
        layer["traceability_artifact"] = "animal-context.json"
    contradictory = SimpleNamespace(
        accountability=accountability,
        input_identity=projection.input_identity,
        refusals=projection.refusals,
        point_layers=layers,
        corpus_identity=projection.corpus_identity,
    )

    with pytest.raises(ValueError, match=message):
        contracts._animal_chronology_publication(
            contradictory,
            artifact_name="animal-context.json",
        )


def test_animal_chronology_publication_binds_exact_refusal_content() -> None:
    projection = build_animal_sample_chronology_context(REPOSITORY_ROOT / "data")
    layers = [dict(layer) for layer in projection.point_layers]
    for layer in layers:
        layer["traceability_artifact"] = "animal-context.json"
    refusals = list(projection.refusals)
    refusals[0] = replace(
        refusals[0], repo_stable_sample_id="fabricated-refusal-identity"
    )
    contradictory = SimpleNamespace(
        accountability=projection.accountability,
        input_identity=projection.input_identity,
        refusals=tuple(refusals),
        point_layers=layers,
        corpus_identity=projection.corpus_identity,
    )

    with pytest.raises(ValueError, match="refusal content identity differs"):
        contracts._animal_chronology_publication(
            contradictory,
            artifact_name="animal-context.json",
        )


def test_scoped_publication_binds_global_denominators_to_corpus_identity() -> None:
    scope = GeographicScope(
        key="nordic",
        kind="region",
        label="Nordic",
        slug="nordic",
        countries=("Denmark", "Finland", "Norway", "Sweden"),
        parent_key="world",
        output_dir_parts=("regions", "nordic"),
        map_title="Nordic",
    )
    projection = build_animal_sample_chronology_context(
        REPOSITORY_ROOT / "data", geography_scope=scope
    )
    accountability = deepcopy(projection.accountability)
    accountability["global_admitted_node_count"] = 532
    accountability["excluded_by_scope_count"] = 518
    source_counts = cast(dict[str, object], accountability["source_counts"])
    source_counts["admitted_node_count"] = 532
    source_counts["sample_master_row_count"] = 1476
    source_counts["sample_chronology_row_count"] = 1456
    source_counts["sample_site_row_count"] = 1456
    country_rows = cast(list[dict[str, object]], accountability["country_rows"])
    country_rows[0]["node_count"] = cast(int, country_rows[0]["node_count"]) + 1
    layers = [dict(layer) for layer in projection.point_layers]
    for layer in layers:
        layer["traceability_artifact"] = "animal-context.json"
    contradictory = SimpleNamespace(
        accountability=accountability,
        input_identity=projection.input_identity,
        refusals=projection.refusals,
        point_layers=layers,
        corpus_identity=projection.corpus_identity,
    )

    with pytest.raises(ValueError, match="source_counts differs from corpus identity"):
        contracts._animal_chronology_publication(
            contradictory,
            artifact_name="animal-context.json",
        )


def test_publication_requires_canonical_project_sample_feature_identity() -> None:
    projection = build_animal_sample_chronology_context(REPOSITORY_ROOT / "data")
    layers = deepcopy(projection.point_layers)
    for layer in layers:
        layer["traceability_artifact"] = "animal-context.json"
    first_features = cast(list[dict[str, object]], layers[0]["features"])
    first_features[0]["feature_id"] = "animal-source-chronology:fabricated"
    contradictory = SimpleNamespace(
        accountability=projection.accountability,
        input_identity=projection.input_identity,
        refusals=projection.refusals,
        point_layers=layers,
        corpus_identity=projection.corpus_identity,
    )

    with pytest.raises(ValueError, match="feature identity format differs"):
        contracts._animal_chronology_publication(
            contradictory,
            artifact_name="animal-context.json",
        )


def test_world_plan_country_filters_do_not_reduce_global_chronology() -> None:
    scope = build_published_geography_plan(
        ("Sweden", "Norway", "Finland", "Denmark")
    ).world_scope
    projection = build_animal_sample_chronology_context(
        REPOSITORY_ROOT / "data", geography_scope=scope
    )
    layers = [dict(layer) for layer in projection.point_layers]
    for layer in layers:
        layer["traceability_artifact"] = "animal-context.json"
    production_shaped = SimpleNamespace(
        accountability=projection.accountability,
        input_identity=projection.input_identity,
        refusals=projection.refusals,
        point_layers=layers,
        corpus_identity=projection.corpus_identity,
    )

    payload, _identity = contracts._animal_chronology_publication(
        production_shaped,
        artifact_name="animal-context.json",
    )

    accountability = cast(dict[str, object], payload["accountability"])
    assert accountability["scope"] == {
        "key": "world",
        "kind": "world",
        "countries": ["Sweden", "Norway", "Finland", "Denmark"],
    }
    assert accountability["projected_node_count"] == 531
