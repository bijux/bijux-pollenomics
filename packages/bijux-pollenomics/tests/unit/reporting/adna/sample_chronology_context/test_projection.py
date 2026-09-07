"""Display projection, scope, and analytical-isolation contracts."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.reporting.adna.sample_chronology_context import (
    AnimalSampleChronologyContextProjection,
    animal_sample_chronology_context_available,
    build_animal_sample_chronology_context,
)
from bijux_pollenomics.reporting.adna.sample_chronology_context.contracts import (
    AnimalSampleChronologyCorpus,
)
from bijux_pollenomics.reporting.adna.sample_chronology_context.projection import (
    project_animal_sample_chronology_context,
)
from bijux_pollenomics.reporting.adna.sample_chronology_context.repository import (
    load_animal_sample_chronology_corpus,
)
from bijux_pollenomics.reporting.geography import GeographicScope


def _data_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "data"
        if (candidate / "adna" / "governance").is_dir():
            return candidate
    raise AssertionError("repository data root is unavailable")


def test_chronology_context_is_available_only_when_project_registry_is_declared(
    tmp_path: Path,
) -> None:
    registry_path = (
        tmp_path
        / "adna"
        / "governance"
        / "source_library"
        / "project_registry.json"
    )
    assert not animal_sample_chronology_context_available(tmp_path)

    registry_path.parent.mkdir(parents=True)
    registry_path.write_text("{}\n", encoding="utf-8")

    assert animal_sample_chronology_context_available(tmp_path)


@pytest.fixture(scope="module")
def global_projection() -> AnimalSampleChronologyContextProjection:
    return build_animal_sample_chronology_context(_data_root())


def _features(
    projection: AnimalSampleChronologyContextProjection,
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for layer in projection.point_layers:
        value = layer["features"]
        assert isinstance(value, list)
        assert all(isinstance(row, dict) for row in value)
        result.extend(cast(list[dict[str, object]], value))
    return result


def test_global_projection_has_six_display_only_layers_and_531_unique_samples(
    global_projection: AnimalSampleChronologyContextProjection,
) -> None:
    projection = global_projection
    layers = projection.point_layers
    assert len(layers) == 6
    assert sum(cast(int, layer["count"]) for layer in layers) == 531
    features = _features(projection)
    assert len({feature["feature_id"] for feature in features}) == 531
    for row in [*layers, *features]:
        assert row["semantic_role"] == "animal_source_chronology_context"
        assert row["contribution_role"] == "display_only"
        assert row["candidate_ranking_eligible"] is False
        assert row["scientific_classification_eligible"] is False
        assert row["scientific_selection_enabled"] is False
        assert row["propagation_status"] == "refused"
        assert row["propagation_reason_code"] == "display_only_source_chronology"
        assert row["edge_count"] == 0
    assert all(layer["default_enabled"] is False for layer in layers)
    assert all(layer["circle_enabled"] is False for layer in layers)
    assert all(layer["group"] == "animal-chronology-context" for layer in layers)


def test_features_use_browser_admitted_numeric_temporal_postures(
    global_projection: AnimalSampleChronologyContextProjection,
) -> None:
    features = _features(global_projection)
    assert {
        cast(dict[str, object], feature["temporal_semantics"])["comparability_posture"]
        for feature in features
    } == {"numeric_interval", "numeric_interval_with_caveat"}
    for feature in features:
        semantics = cast(dict[str, object], feature["temporal_semantics"])
        assert semantics["schema_version"] == "temporal-semantics.v1"
        assert feature["chronology_scope"] == "source_sample_interval"
        assert feature["temporal_window_key"] == semantics["temporal_window_key"]
        assert feature["temporal_window_label"] == semantics["temporal_window_label"]
        assert (
            feature["temporal_comparability_posture"]
            == semantics["comparability_posture"]
        )
        assert (
            feature["temporal_window_assignment_policy"]
            == "source_normalized_interval_mean"
        )
    assert all(
        cast(int, feature["time_start_bp"])
        <= cast(int, feature["time_mean_bp"])
        <= cast(int, feature["time_end_bp"])
        for feature in features
    )


@pytest.mark.parametrize(
    ("mean_bp", "expected_key", "expected_label"),
    [
        (1000, "recent_historical", "Recent and historical (0-1000 BP)"),
        (1001, "late_holocene", "Late Holocene (1001-3000 BP)"),
        (3000, "late_holocene", "Late Holocene (1001-3000 BP)"),
        (3001, "mid_holocene", "Mid-Holocene (3001-6000 BP)"),
        (6000, "mid_holocene", "Mid-Holocene (3001-6000 BP)"),
        (
            6001,
            "early_holocene_and_older",
            "Early Holocene and older (6001+ BP)",
        ),
    ],
)
def test_temporal_windows_use_explicit_closed_midpoint_boundaries(
    mean_bp: int,
    expected_key: str,
    expected_label: str,
) -> None:
    corpus = load_animal_sample_chronology_corpus(_data_root())
    representatives = {node.project_species_latin_name: node for node in corpus.nodes}
    target_species = sorted(representatives)[0]
    representatives[target_species] = replace(
        representatives[target_species],
        chronology_text=f"{mean_bp} BP",
        chronology_precision_posture="sample_precise_point",
        chronology_normalization_status="normalized_point",
        younger_bp=mean_bp,
        older_bp=mean_bp,
        mean_bp=mean_bp,
    )
    boundary_corpus = AnimalSampleChronologyCorpus(
        nodes=tuple(representatives[species] for species in sorted(representatives)),
        refusals=corpus.refusals,
        input_identity=corpus.input_identity,
        source_counts=corpus.source_counts,
        refusal_counts=corpus.refusal_counts,
    )
    projection = project_animal_sample_chronology_context(
        boundary_corpus,
        geography_scope=None,
    )
    feature = next(
        feature
        for feature in _features(projection)
        if feature["project_species_latin_name"] == target_species
    )
    semantics = cast(dict[str, object], feature["temporal_semantics"])

    assert feature["temporal_window_key"] == expected_key
    assert feature["temporal_window_label"] == expected_label
    assert semantics["temporal_window_key"] == expected_key
    assert semantics["temporal_window_label"] == expected_label
    assert semantics["duration_years"] == 0
    assert "interval mean" in cast(str, semantics["comparison_note"])


def test_nordic_inclusion_is_country_membership_not_inference(
    global_projection: AnimalSampleChronologyContextProjection,
) -> None:
    features = _features(global_projection)
    by_country: dict[str, list[dict[str, object]]] = {}
    for feature in features:
        by_country.setdefault(cast(str, feature["country"]), []).append(feature)

    for country in ("Denmark", "Finland", "Sweden"):
        assert by_country[country]
        assert all(
            feature["nordic_inclusion"] is True for feature in by_country[country]
        )
        assert all(
            feature["nordic_inclusion_reason"]
            == "Source-sample country is one of Denmark, Finland, Norway, or Sweden."
            for feature in by_country[country]
        )
    assert all(
        feature["nordic_inclusion"] is False
        for country, country_features in by_country.items()
        if country not in {"Denmark", "Finland", "Norway", "Sweden", ""}
        for feature in country_features
    )
    assert all(feature["nordic_inclusion"] is False for feature in by_country[""])
    assert all(
        feature["nordic_inclusion_reason"]
        == "Source-sample country is unassigned; Nordic inclusion is not inferred."
        for feature in by_country[""]
    )


def test_projection_does_not_invent_scientific_classification_or_animal_scope(
    global_projection: AnimalSampleChronologyContextProjection,
) -> None:
    features = _features(global_projection)
    forbidden = {
        "animal_scope",
        "classification_id",
        "classification_status",
        "scientific_signal_ids",
        "species_common_name",
        "species_latin_name",
        "taxon_alignment_status",
        "taxon_alignment_statuses",
    }
    assert all(not forbidden.intersection(feature) for feature in features)
    unavailable = [
        feature
        for feature in features
        if feature["source_native_taxonomy_status"] == "unavailable"
    ]
    assert len(unavailable) == 485
    assert all(
        feature["source_native_scientific_name"] is None for feature in unavailable
    )


def test_projection_requires_the_exact_grounded_species_set() -> None:
    corpus = load_animal_sample_chronology_corpus(_data_root())
    nodes = tuple(
        replace(
            node,
            project_species_latin_name="Fabricatus animalis",
            project_species_common_name="fabricated animal",
        )
        if node.project_species_latin_name == "Bos taurus"
        else node
        for node in corpus.nodes
    )
    contradictory = replace(corpus, nodes=nodes)

    with pytest.raises(ValueError, match="grounded species differ"):
        project_animal_sample_chronology_context(
            contradictory,
            geography_scope=None,
        )


def test_four_country_scope_reconciles_zero_norway_and_null_bounds() -> None:
    scope = GeographicScope(
        key="nordic-four",
        kind="region",
        label="Nordic four",
        slug="nordic-four",
        countries=("Denmark", "Finland", "Norway", "Sweden"),
        parent_key="world",
        output_dir_parts=("regions", "nordic-four"),
        map_title="Nordic four",
    )
    projection = build_animal_sample_chronology_context(
        _data_root(), geography_scope=scope
    )
    accountability = projection.accountability
    assert accountability["projected_node_count"] == 14
    assert accountability["excluded_by_scope_count"] == 517
    assert (accountability["time_min_bp"], accountability["time_max_bp"]) == (
        340,
        9657,
    )
    rows = cast(list[dict[str, object]], accountability["governed_country_rows"])
    country_rows: dict[object, dict[str, object]] = {
        row["country_name"]: row for row in rows
    }
    assert {country: row["node_count"] for country, row in country_rows.items()} == {
        "Denmark": 7,
        "Finland": 2,
        "Norway": 0,
        "Sweden": 5,
    }
    assert country_rows["Norway"]["time_min_bp"] is None
    assert country_rows["Norway"]["time_max_bp"] is None


def test_global_unknown_country_is_visible_but_excluded_from_filtered_scope(
    global_projection: AnimalSampleChronologyContextProjection,
) -> None:
    global_rows = cast(
        list[dict[str, object]], global_projection.accountability["country_rows"]
    )
    unknown = next(row for row in global_rows if row["country_name"] is None)
    assert unknown["node_count"] == 5
    global_features = _features(global_projection)
    assert (
        sum(feature["country_status"] == "unassigned" for feature in global_features)
        == 5
    )

    scope = GeographicScope(
        key="sweden",
        kind="country",
        label="Sweden",
        slug="sweden",
        countries=("Sweden",),
        parent_key="nordic",
        output_dir_parts=("countries", "sweden"),
        map_title="Sweden",
    )
    sweden = build_animal_sample_chronology_context(_data_root(), geography_scope=scope)
    features = _features(sweden)
    assert len(features) == 5
    assert {feature["country"] for feature in features} == {"Sweden"}


def test_accountability_binds_counts_taxonomy_and_input_identity(
    global_projection: AnimalSampleChronologyContextProjection,
) -> None:
    accountability = global_projection.accountability
    assert accountability["global_admitted_node_count"] == 531
    assert accountability["projected_node_count"] == 531
    assert accountability["refusal_count"] == 944
    assert accountability["source_native_taxonomy"] == {
        "available_count": 46,
        "unavailable_count": 485,
        "denominator": 531,
    }
    input_identity = cast(dict[str, object], accountability["input_identity"])
    assert input_identity["artifact_count"] == 121
    assert accountability["analysis_policy"] == {
        "candidate_ranking_eligible": False,
        "scientific_classification_eligible": False,
        "propagation_status": "refused",
        "propagation_reason_code": "display_only_source_chronology",
        "edge_count": 0,
        "temporal_window_assignment_policy": "source_normalized_interval_mean",
    }
