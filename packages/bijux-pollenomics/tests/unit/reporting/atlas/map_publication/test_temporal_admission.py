"""Shared map chronology admission contracts."""

from copy import deepcopy

import pytest

from bijux_pollenomics.reporting.context import build_external_point_layer
from bijux_pollenomics.reporting.context.time import feature_time_payload
from bijux_pollenomics.reporting.map_document.static_assets.indexes import (
    feature_interval as static_feature_interval,
)
from bijux_pollenomics.reporting.map_document.static_assets.indexes import (
    feature_temporal_admission as static_feature_temporal_admission,
)
from bijux_pollenomics.reporting.map_document.temporal_admission import (
    feature_interval,
    feature_temporal_admission,
)


def test_static_index_exports_share_the_canonical_temporal_admission() -> None:
    assert static_feature_interval is feature_interval
    assert static_feature_temporal_admission is feature_temporal_admission


def test_temporal_admission_preserves_zero_and_refuses_invalid_intervals() -> None:
    assert feature_temporal_admission(
        {
            "time_start_bp": 0,
            "time_end_bp": 100,
            "temporal_semantics": {
                "comparability_posture": "numeric_interval_with_caveat",
                "evidence_class": "direct_numeric_sample_date",
                "precision_posture": "sample_precise_interval",
            },
        }
    ) == (
        "admitted",
        (0.0, 100.0),
    )
    assert feature_temporal_admission({"time_start_bp": 0, "time_end_bp": 100}) == (
        "contextual",
        None,
    )
    assert feature_temporal_admission({"time_start_bp": None, "time_end_bp": None}) == (
        "absent",
        None,
    )
    for feature in (
        {"time_start_bp": 100, "time_end_bp": None},
        {"time_start_bp": -1, "time_end_bp": 100},
        {"time_start_bp": 200, "time_end_bp": 100},
        {"time_start_bp": "invalid", "time_end_bp": 100},
    ):
        assert feature_temporal_admission(feature) == ("refused", None)


def test_temporal_semantics_override_numeric_fields_consistently() -> None:
    feature = {
        "time_start_bp": 1,
        "time_end_bp": 999_999,
        "temporal_semantics": {
            "comparability_posture": "refused",
            "refusal_reason_code": "source_age_system_not_comparable",
        },
    }

    assert feature_temporal_admission(feature) == ("refused", None)
    assert feature_interval(feature) is None


@pytest.mark.parametrize(
    ("bounds", "nested"),
    (
        ((100, 110), {}),
        ((100, 110), {"time_start_bp": None, "time_end_bp": None}),
        ((100, 110), {"time_start_bp": 100, "time_end_bp": 110}),
        ((0, 0), {"time_start_bp": 0, "time_end_bp": 0}),
    ),
)
def test_optional_duplicate_bounds_preserve_generic_admission(
    bounds: tuple[int, int], nested: dict[str, object]
) -> None:
    feature = {
        "time_start_bp": bounds[0],
        "time_end_bp": bounds[1],
        "temporal_semantics": {
            "schema_version": "temporal-semantics.v1",
            "comparability_posture": "numeric_interval_with_caveat",
            "precision_posture": "source_reported_interval",
            **nested,
        },
    }
    original = deepcopy(feature)

    admitted = feature_temporal_admission(feature)
    qualified = feature_time_payload(feature)

    assert admitted == ("admitted", tuple(float(value) for value in bounds))
    assert (qualified["time_start_bp"], qualified["time_end_bp"]) == bounds
    assert feature == original
    assert qualified["source_record"] == original


@pytest.mark.parametrize(
    ("nested", "reason"),
    (
        ({"time_start_bp": 300, "time_end_bp": 310}, "conflicting_temporal_bounds"),
        ({"time_start_bp": 100}, "partial_interval"),
        ({"time_start_bp": 100, "time_end_bp": None}, "partial_interval"),
        ({"time_start_bp": "100", "time_end_bp": 110}, "non_finite"),
        ({"time_start_bp": -1, "time_end_bp": 110}, "negative_bp"),
        ({"time_start_bp": 110, "time_end_bp": 100}, "reversed_interval"),
        ({"time_start_bp": False, "time_end_bp": 110}, "non_finite"),
        ({"time_start_bp": float("inf"), "time_end_bp": 110}, "non_finite"),
    ),
)
def test_explicit_nested_bounds_cannot_be_laundered_by_flat_intake(
    nested: dict[str, object], reason: str
) -> None:
    properties = {
        "time_start_bp": 100,
        "time_end_bp": 110,
        "temporal_semantics": {
            "schema_version": "temporal-semantics.v1",
            "comparability_posture": "numeric_interval_with_caveat",
            "evidence_class": "controlled_numeric_fixture",
            "precision_posture": "source_reported_interval",
            **nested,
        },
        "record_id": "synthetic-support-1",
        "name": "Controlled synthetic support",
        "country": "Sweden",
        "layer_key": "controlled-source",
        "layer_label": "Controlled source",
    }
    collection: dict[str, object] = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [18, 59]},
                "properties": properties,
            }
        ],
    }
    original = deepcopy(collection)

    assert feature_temporal_admission(properties) == ("refused", None)
    qualified = feature_time_payload(properties)
    layer = build_external_point_layer(collection)

    assert collection == original
    assert qualified["source_record"] == properties
    assert qualified["time_start_bp"] is None and qualified["time_end_bp"] is None
    semantics = qualified["temporal_semantics"]
    assert isinstance(semantics, dict)
    assert semantics["comparability_posture"] == "refused"
    assert semantics["refusal_reason_code"] == reason
    assert semantics["precision_posture"] == "source_reported_interval"
    features = layer["features"]
    assert isinstance(features, list) and len(features) == 1
    assert feature_temporal_admission(features[0]) == ("refused", None)


def test_matching_duplicate_bounds_preserve_direct_fractional_domain() -> None:
    feature = {
        "time_start_bp": 100.5,
        "time_end_bp": 110.5,
        "temporal_semantics": {
            "comparability_posture": "numeric_interval_with_caveat",
            "time_start_bp": 100.5,
            "time_end_bp": 110.5,
        },
    }

    assert feature_temporal_admission(feature) == ("admitted", (100.5, 110.5))


@pytest.mark.parametrize("null_bounds", [False, True])
@pytest.mark.parametrize("key", ["time_mean_bp", "time_year_bp"])
@pytest.mark.parametrize("point", [105, 5000])
def test_generic_point_fallback_respects_populated_nested_support(
    null_bounds: bool, key: str, point: int
) -> None:
    properties: dict[str, object] = {
        key: point,
        "layer_key": "controlled-source",
        "layer_label": "Controlled source",
        "temporal_semantics": {
            "comparability_posture": "numeric_interval_with_caveat",
            "time_start_bp": 100,
            "time_end_bp": 110,
        },
    }
    if null_bounds:
        properties.update(time_start_bp=None, time_end_bp=None)
    original = deepcopy(properties)

    expected = ("admitted", (105.0, 105.0)) if point == 105 else ("refused", None)
    assert feature_temporal_admission(properties) == expected
    qualified = feature_time_payload(properties)
    collection: dict[str, object] = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [18, 59]},
                "properties": properties,
            }
        ],
    }
    layer = build_external_point_layer(collection)
    features = layer["features"]
    assert isinstance(features, list) and len(features) == 1
    # External intake supports mean fallback, not the direct map's year alias.
    intake_expected = expected if key == "time_mean_bp" else ("refused", None)
    assert feature_temporal_admission(qualified) == intake_expected
    assert feature_temporal_admission(features[0]) == intake_expected
    if key == "time_mean_bp" and point == 5000:
        semantics = qualified["temporal_semantics"]
        assert isinstance(semantics, dict)
        assert semantics["refusal_reason_code"] == "conflicting_temporal_bounds"
    assert properties == original
    assert qualified["source_record"] == original


@pytest.mark.parametrize(
    ("nested", "point"),
    (
        ({}, 5000),
        ({"time_start_bp": None, "time_end_bp": None}, 5000),
        ({"time_start_bp": 105, "time_end_bp": 105}, 105),
        ({"time_start_bp": 0, "time_end_bp": 0}, 0),
    ),
)
def test_point_fallback_keeps_optional_support_and_closed_endpoints(
    nested: dict[str, object], point: int
) -> None:
    properties: dict[str, object] = {
        "time_mean_bp": point,
        "temporal_semantics": {
            "comparability_posture": "numeric_interval_with_caveat",
            **nested,
        },
    }
    expected = ("admitted", (float(point), float(point)))

    assert feature_temporal_admission(properties) == expected
    assert feature_temporal_admission(feature_time_payload(properties)) == expected


def test_populated_nested_bounds_do_not_infer_missing_flat_support() -> None:
    properties: dict[str, object] = {
        "temporal_semantics": {
            "comparability_posture": "numeric_interval_with_caveat",
            "time_start_bp": 100,
            "time_end_bp": 110,
        },
    }

    assert feature_temporal_admission(properties) == ("refused", None)
    assert feature_temporal_admission(feature_time_payload(properties)) == (
        "refused",
        None,
    )


def test_text_flat_intake_matches_numeric_nested_bounds() -> None:
    properties: dict[str, object] = {
        "time_start_bp": "100",
        "time_end_bp": "110",
        "temporal_semantics": {
            "comparability_posture": "numeric_interval_with_caveat",
            "time_start_bp": 100,
            "time_end_bp": 110,
        },
    }
    original = deepcopy(properties)
    qualified = feature_time_payload(properties)

    assert feature_temporal_admission(qualified) == ("admitted", (100.0, 110.0))
    assert qualified["source_record"] == original
    assert properties == original
