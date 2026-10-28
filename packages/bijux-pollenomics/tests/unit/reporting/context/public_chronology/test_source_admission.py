"""Actual public serializers retain source eligibility through external and map readers."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.context import build_external_point_layer
from bijux_pollenomics.reporting.context.time import (
    feature_has_time,
    feature_time_payload,
)
from bijux_pollenomics.reporting.map_document.adna_exports import (
    exported_record_semantics,
)
from bijux_pollenomics.reporting.map_document.temporal_admission import (
    feature_temporal_admission,
)
from bijux_pollenomics.reporting.rendering.record_exports import (
    build_samples_geojson,
)

from ...rendering.test_sample_chronology_exports import _source_sample
from .support import _browser, _collection, _record


@pytest.mark.parametrize(
    ("precision", "refusal", "expected"),
    [
        ("sample_precise_interval", "", "admitted"),
        ("sample_approximate_or_modeled", "", "admitted"),
        ("unresolved", "", "contextual"),
        ("broad_period", "", "contextual"),
        ("source-stated precision", "source_age_system_not_comparable", "refused"),
    ],
)
def test_preferred_public_source_semantics_survive_direct_external_and_browser(
    precision: str, refusal: str, expected: str
) -> None:
    record = _record(precision, refusal)
    original = deepcopy(record)
    assert feature_temporal_admission(record)[0] == expected
    observed = _browser([record])[0]
    assert observed["status"] == ("valid" if expected == "admitted" else expected)
    layer = build_external_point_layer(_collection(record))
    feature = cast(list[dict[str, Any]], layer["features"])[0]
    assert feature_temporal_admission(feature)[0] == expected
    assert feature_has_time(feature) == (expected == "admitted")
    assert layer["applies_time_filter"] == (expected == "admitted")
    assert (
        feature["source_record"]["sample_chronology"] == original["sample_chronology"]
    )
    assert feature["sample_identity"] == original["sample_identity"]
    assert feature["master_id"] != feature["genetic_id"]
    assert record == original
    if expected != "admitted":
        assert feature["time_start_bp"] is None
        assert feature["source_record"]["time_start_bp"] == 0
    else:
        assert feature["time_start_bp"] == 0


def test_existing_refused_zero_fixture_never_becomes_present_through_either_export_version() -> (
    None
):
    sample = _source_sample(0, 0)
    for version in ("v1", "v2"):
        collection = cast(
            dict[str, Any],
            build_samples_geojson(
                [sample], schema_version="adna-sample-geojson-collection." + version
            ),
        )
        collection["features"][0]["properties"].update(
            layer_key="controlled", layer_label="Controlled"
        )
        feature = cast(
            list[dict[str, Any]], build_external_point_layer(collection)["features"]
        )[0]
        assert not feature_has_time(feature)
        assert feature_temporal_admission(feature)[0] != "admitted"
        assert _browser([collection["features"][0]])[0]["status"] != "valid"
        assert feature["source_record"]["time_start_bp"] == 0
        if version == "v1":
            assert "not carried" in feature["temporal_semantics"]["comparison_note"]


@pytest.mark.parametrize(
    "case",
    [
        "flat_start",
        "flat_mean",
        "master",
        "group",
        "genetic",
        "support_id",
        "stable",
        "namespace",
        "lineage",
        "sample_alias",
        "fraction",
        "unsafe",
        "bool",
        "string",
        "partial",
        "reversed",
        "negative",
        "bad_support",
        "bad_identity",
        "unsupported",
        "semantics_version",
    ],
)
def test_public_source_conflicts_are_refused_across_all_actual_readers(
    case: str,
) -> None:
    record = _record()
    if case == "flat_start":
        record["time_start_bp"] = 1
    elif case == "flat_mean":
        record["time_mean_bp"] = 1
    elif case == "master":
        record["master_id"] = "different-native"
    elif case == "group":
        record["group_id"] = "different-project"
    elif case == "genetic":
        record["genetic_id"] = "different-stable"
    elif case == "support_id":
        record["sample_chronology"]["sample_id"] = "different-support"
    elif case == "stable":
        record["sample_identity"]["stable_token"] = "different-stable"
    elif case == "namespace":
        record["sample_identity"]["namespace"] = "different-namespace"
    elif case == "lineage":
        record["accession_lineage"] = []
    elif case == "sample_alias":
        record["sample_id"] = "different-alias"
    elif case in {"fraction", "unsafe", "bool", "string", "negative"}:
        value = {
            "fraction": 0.25,
            "unsafe": 2**53,
            "bool": True,
            "string": "0",
            "negative": -1,
        }[case]
        record["time_start_bp"] = record["sample_chronology"]["chronology"][
            "time_start_bp"
        ] = value
    elif case == "partial":
        record["time_end_bp"] = record["sample_chronology"]["chronology"][
            "time_end_bp"
        ] = None
    elif case == "reversed":
        record["time_start_bp"] = record["sample_chronology"]["chronology"][
            "time_start_bp"
        ] = 10
    elif case == "bad_support":
        record["sample_chronology"] = []
    elif case == "bad_identity":
        record["sample_identity"] = []
    elif case == "unsupported":
        record["schema_version"] = "adna-sample-record-export.v9"
    elif case == "semantics_version":
        record["temporal_semantics"] = {
            "schema_version": "temporal-semantics.v9",
            "comparability_posture": "numeric_interval",
        }
    assert feature_temporal_admission(record)[0] == "refused"
    assert _browser([record])[0]["status"] == "refused"
    feature = cast(
        list[dict[str, Any]],
        build_external_point_layer(_collection(record))["features"],
    )[0]
    assert not feature_has_time(feature)
    assert feature_temporal_admission(feature)[0] == "refused"
    assert feature["source_record"]["time_start_bp"] == record["time_start_bp"]


@pytest.mark.parametrize(
    "semantics",
    [
        {},
        {"comparability_posture": ""},
        {"comparability_posture": "unresolved"},
        {"comparability_posture": "contextual_label_only"},
    ],
)
def test_explicit_missing_or_contextual_posture_is_never_numeric_permission(
    semantics: dict[str, object],
) -> None:
    features = [
        {"time_start_bp": 0, "time_end_bp": 0, "temporal_semantics": semantics},
        {**_record(), "temporal_semantics": semantics},
    ]
    assert [feature_temporal_admission(feature)[0] for feature in features] == [
        "contextual",
        "contextual",
    ]
    assert [row["status"] for row in _browser(features)] == ["contextual", "contextual"]
    assert all(not feature_has_time(feature) for feature in features)


def test_schema_less_numeric_presence_and_distinct_pollen_schema_do_not_admit_comparison() -> (
    None
):
    raw = {"time_start_bp": 0, "time_end_bp": 0}
    assert feature_temporal_admission(raw) == ("contextual", None)
    assert not feature_has_time(raw)
    assert _browser([raw])[0]["status"] == "contextual"
    mapped = cast(
        list[dict[str, Any]], build_external_point_layer(_collection(raw))["features"]
    )[0]
    assert not feature_has_time(mapped)
    assert (
        mapped["time_start_bp"] is None
        and mapped["source_record"]["time_start_bp"] == 0
    )
    pollen = {
        "schema_version": "source-pollen-record-export.v1",
        "chronology_claims": [],
        "source_context": {"unit": "pollen"},
    }
    assert feature_temporal_admission(pollen) == ("absent", None)
    assert _browser([pollen])[0]["status"] == "absent"


@pytest.mark.parametrize("value", [0.0, 100.0])
def test_integral_json_number_projection_retains_exact_source_metadata(
    value: float,
) -> None:
    record = _record()
    for key in ("time_start_bp", "time_end_bp", "time_mean_bp"):
        record[key] = record["sample_chronology"]["chronology"][key] = value
    original = deepcopy(record)
    assert feature_temporal_admission(record) == ("admitted", (value, value))
    assert _browser([record])[0]["status"] == "valid"
    view = feature_time_payload(record)
    assert view["source_record"] == original
    assert (
        type(view["source_record"]["sample_chronology"]["chronology"]["time_start_bp"])
        is float
    )
    assert record == original


@pytest.mark.parametrize("refusal", [[], {}, 1, True, None])
def test_malformed_declared_refusal_cannot_become_empty_permission(
    refusal: object,
) -> None:
    semantics = {
        "comparability_posture": "numeric_interval",
        "refusal_reason_code": refusal,
    }
    records = [
        {"time_start_bp": 0, "time_end_bp": 0, "temporal_semantics": semantics},
        {**_record(), "temporal_semantics": semantics},
    ]
    assert [feature_temporal_admission(record)[0] for record in records] == [
        "refused",
        "refused",
    ]
    assert [row["status"] for row in _browser(records)] == ["refused", "refused"]
    assert all(not feature_has_time(record) for record in records)


def test_returned_public_metadata_does_not_alias_the_original_source() -> None:
    record = _record()
    original = deepcopy(record)
    result = cast(dict[str, Any], feature_time_payload(record))
    result["sample_identity"]["archive_native_sample_id"] = "mutation"
    result["sample_chronology"]["chronology"]["original_text"] = "mutation"
    result["accession_lineage"].append("mutation")
    assert record == original and result["source_record"] == original


@pytest.mark.parametrize("schema", [None, [], {}, 1, False])
def test_malformed_declared_schema_is_not_dropped_by_external_intake(
    schema: object,
) -> None:
    record = {"schema_version": schema, "time_start_bp": 0, "time_end_bp": 0}
    assert feature_temporal_admission(record)[0] == "refused"
    assert _browser([record])[0]["status"] == "refused"
    feature = cast(
        list[dict[str, Any]],
        build_external_point_layer(_collection(record))["features"],
    )[0]
    assert not feature_has_time(feature)
    assert feature["source_record"]["schema_version"] == schema
    assert feature["time_start_bp"] is None


@pytest.mark.parametrize(
    "schema",
    [
        "adna-sample-geojson.v1",
        "adna-sample-geojson.v2",
        "adna-sample-geojson-collection.v1",
        "adna-sample-geojson-collection.v2",
    ],
)
def test_reserved_geojson_schema_requires_its_actual_envelope(schema: str) -> None:
    malformed = {
        "schema_version": schema,
        "time_start_bp": 0,
        "time_end_bp": 0,
        "temporal_semantics": {"comparability_posture": "numeric_interval"},
    }
    assert feature_temporal_admission(malformed)[0] == "refused"
    assert _browser([malformed])[0]["status"] == "refused"
    assert not feature_has_time(malformed)


def test_wrong_reserved_feature_schema_cannot_unwrap_into_a_numeric_provider() -> None:
    provider = {
        "schema_version": "provider-window.v1",
        "time_start_bp": 0,
        "time_end_bp": 1,
        "temporal_semantics": {"comparability_posture": "numeric_interval"},
    }
    assert feature_temporal_admission(provider) == ("admitted", (0, 1))
    wrong = {
        "type": "Feature",
        "schema_version": "adna-sample-record-export.v2",
        "properties": provider,
    }
    assert feature_temporal_admission(wrong)[0] == "refused"
    assert _browser([wrong])[0]["status"] == "refused"


def test_declared_scalar_support_metadata_refuses_structures_and_retains_source() -> (
    None
):
    record = _record()
    record["sample_chronology"]["model"] = {"details": ["original"]}
    original = deepcopy(record)
    semantics = exported_record_semantics(record)
    assert semantics is not None
    assert semantics["comparability_posture"] == "refused"
    assert record == original
    view = cast(dict[str, Any], feature_time_payload(record))
    assert view["source_record"] == original
    view["source_record"]["sample_chronology"]["model"]["details"].append("mutation")
    assert record == original
