from __future__ import annotations

from bijux_pollenomics.reporting.map_document.coordinates import point_coordinate_pair
from bijux_pollenomics.reporting.map_document.evidence import normalize_atlas_evidence
from bijux_pollenomics.reporting.map_document.state import build_map_document_state
from bijux_pollenomics.reporting.map_document.static_assets.indexes import build_indexes
from bijux_pollenomics.reporting.map_document.static_assets.nodes import (
    node_asset_selection,
)
from bijux_pollenomics.reporting.map_publication import MapScopePolicy


def _policy() -> MapScopePolicy:
    return MapScopePolicy(
        key="test",
        label="Test",
        eyebrow_label="Test",
        summary="Test",
        bounds_summary="Test",
        default_basemap="none",
        initial_diameter_km=0,
        minimum_bounds=((10.0, 10.0), (20.0, 20.0)),
        filter_surfaces=(),
        legend_sections=(),
        visible_caveats=(),
        engine_summary="Test",
    )


def test_coordinate_admission_preserves_zero_and_rejects_missing_or_impossible() -> (
    None
):
    assert point_coordinate_pair({"latitude": 0, "longitude": "0"}) == (0, 0)
    assert point_coordinate_pair({"latitude": -33.9, "longitude": -70.7}) == (
        -33.9,
        -70.7,
    )
    assert point_coordinate_pair({"latitude": None, "longitude": 0}) is None
    assert point_coordinate_pair({"latitude": False, "longitude": 0}) is None
    assert point_coordinate_pair({"latitude": 91, "longitude": 0}) is None
    assert point_coordinate_pair({"latitude": 0, "longitude": -181}) is None


def test_bounds_use_only_complete_admitted_coordinate_pairs() -> None:
    invalid_state = build_map_document_state(
        policy=_policy(),
        point_layers=[
            {
                "features": [
                    {"latitude": -50, "longitude": None},
                    {"latitude": None, "longitude": -50},
                    {"latitude": "nan", "longitude": ""},
                ]
            }
        ],
        polygon_layers=[],
    )
    zero_state = build_map_document_state(
        policy=_policy(),
        point_layers=[{"features": [{"latitude": 0, "longitude": 0}]}],
        polygon_layers=[],
    )

    assert invalid_state.bounds == [[10.0, 10.0], [20.0, 20.0]]
    assert zero_state.bounds == [[0.0, 0.0], [20.0, 20.0]]


def test_spatial_indexes_and_chunk_bounds_exclude_impossible_coordinates() -> None:
    features = [
        {"latitude": 0, "longitude": 0, "country": "Sweden"},
        {"latitude": 91, "longitude": 18, "country": "Sweden"},
        {"latitude": None, "longitude": 18, "country": "Sweden"},
    ]
    indexes = build_indexes([{"key": "sites", "features": features}])
    selection = node_asset_selection(
        {
            "layer_kind": "point",
            "layer_index": 0,
            "layer_key": "sites",
            "country_keys": ["Sweden"],
            "features": features,
        }
    )

    assert indexes["spatial_degree_feature_indexes"] == {"0:0": {"sites": [0]}}
    assert selection["bounds"] == [0.0, 0.0, 0.0, 0.0]


def test_null_interval_uses_valid_mean_age_across_state_and_static_metadata() -> None:
    feature = {
        "latitude": 59,
        "longitude": 18,
        "country": "Sweden",
        "time_start_bp": None,
        "time_end_bp": None,
        "time_mean_bp": 123.25,
    }
    state = build_map_document_state(
        policy=_policy(),
        point_layers=[{"key": "sites", "features": [feature]}],
        polygon_layers=[],
    )
    indexes = build_indexes([{"key": "sites", "features": [feature]}])
    selection = node_asset_selection(
        {
            "layer_kind": "point",
            "layer_index": 0,
            "layer_key": "sites",
            "country_keys": ["Sweden"],
            "features": [feature],
        }
    )

    assert (state.time_min_bp, state.time_max_bp) == (123, 124)
    assert indexes["time_interval_feature_indexes"] == [[123.25, 123.25, "sites", 0]]
    assert selection["time_min_bp"] == 123.25
    assert selection["time_max_bp"] == 123.25
    assert selection["untimed_record_count"] == 0


def test_post_1950_bp_interval_is_refused_from_static_time_metadata() -> None:
    feature = {
        "latitude": 68,
        "longitude": 19,
        "country": "Sweden",
        "time_start_bp": -54,
        "time_end_bp": -51,
    }
    state = build_map_document_state(
        policy=_policy(),
        point_layers=[{"key": "sites", "features": [feature]}],
        polygon_layers=[],
    )
    indexes = build_indexes([{"key": "sites", "features": [feature]}])
    selection = node_asset_selection(
        {
            "layer_kind": "point",
            "layer_index": 0,
            "layer_key": "sites",
            "country_keys": ["Sweden"],
            "features": [feature],
        }
    )

    assert not state.has_time_data
    assert (state.time_min_bp, state.time_max_bp) == (0, 0)
    assert indexes["time_interval_feature_indexes"] == []
    assert selection["time_min_bp"] is None
    assert selection["time_max_bp"] is None
    assert selection["untimed_record_count"] == 1


def test_invalid_declared_mean_does_not_fall_through_to_year_age() -> None:
    feature = {
        "latitude": 59,
        "longitude": 18,
        "country": "Sweden",
        "time_start_bp": None,
        "time_end_bp": None,
        "time_mean_bp": "bad",
        "time_year_bp": 123,
    }
    state = build_map_document_state(
        policy=_policy(),
        point_layers=[{"key": "sites", "features": [feature]}],
        polygon_layers=[],
    )
    indexes = build_indexes([{"key": "sites", "features": [feature]}])

    assert not state.has_time_data
    assert indexes["time_interval_feature_indexes"] == []


def test_subgroup_is_a_first_class_scientific_resolution() -> None:
    evidence = normalize_atlas_evidence(
        detail_records=[],
        edge_records=[],
        sequence_records=[],
        scientific_signals=[
            {
                "signal_id": "subgroup:cereals",
                "feature_key": "cereals",
                "label": "Cereals",
                "resolution": "subgroup",
                "status": "accepted",
            }
        ],
    )

    assert evidence.scientific_signals[0]["resolution"] == "subgroup"
