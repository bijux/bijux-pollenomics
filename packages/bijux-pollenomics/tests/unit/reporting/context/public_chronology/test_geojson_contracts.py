"""Actual public serializers retain source eligibility through external and map readers."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.core.calendar_support import (
    SIGNED_CALENDAR_PROFILE,
    SignedCalendarSupport,
)
from bijux_pollenomics.reporting.bundles.atlas_bundle.context import (
    extract_context_points,
)
from bijux_pollenomics.reporting.context import build_external_point_layer
from bijux_pollenomics.reporting.context.points.fieldwork import (
    build_fieldwork_point_layer,
)
from bijux_pollenomics.reporting.context.points.shared import FIELDWORK_MEDIA_FILES
from bijux_pollenomics.reporting.context.time import (
    feature_has_time,
    feature_time_payload,
)
from bijux_pollenomics.reporting.map_document.adna_exports import (
    locality_export_records,
)
from bijux_pollenomics.reporting.map_document.template import NATIVE_LRA_CONTROLLER
from bijux_pollenomics.reporting.map_document.temporal_admission import (
    feature_occurrence_intervals,
    feature_temporal_admission,
)
from bijux_pollenomics.reporting.rendering.record_exports import (
    build_samples_geojson,
)

from ...map_document.browser_semantics.chronology.support import _feature
from ...map_document.browser_semantics.support import run_node_json, template_block
from ...rendering.test_sample_chronology_exports import _source_sample
from .support import _browser, _collection, _record


@pytest.mark.parametrize("where", ["collection", "feature", "properties"])
def test_geojson_wrapper_version_conflict_is_refused_before_mapping(where: str) -> None:
    sample = _source_sample(0, 0)
    payload = cast(dict[str, Any], build_samples_geojson([sample]))
    payload["features"][0]["properties"].update(
        layer_key="controlled", layer_label="Controlled"
    )
    if where == "collection":
        payload["schema_version"] = "adna-sample-geojson-collection.v1"
    elif where == "feature":
        payload["features"][0]["schema_version"] = "adna-sample-geojson.v1"
    else:
        payload["features"][0]["properties"]["schema_version"] = (
            "adna-sample-record-export.v1"
        )
    with pytest.raises(ValueError, match="schema"):
        build_external_point_layer(payload)


def test_named_locality_record_and_wrapper_preserve_components_and_refuse_hull_gap() -> (
    None
):
    record = {
        **_feature(),
        "schema_version": "adna-locality-summary-export.v2",
        "sample_count": 3,
    }
    wrapper = {
        "schema_version": "adna-locality-summary-export.v2",
        "localities": [record],
    }
    decoded = locality_export_records(wrapper)[0]
    assert feature_occurrence_intervals(decoded) == ((100, 110), (300, 310))
    assert feature_temporal_admission(wrapper)[0] == "refused"
    feature = cast(
        list[dict[str, Any]],
        build_external_point_layer(_collection(decoded))["features"],
    )[0]
    assert feature_occurrence_intervals(feature) == ((100, 110), (300, 310))
    assert feature["sample_chronologies"] == decoded["sample_chronologies"]
    source = template_block(
        "function finiteTimeValue", "function pointFeatureInTimeWindow"
    )
    observed = run_node_json(
        "const TIME_HAS_DATA=true;let timeStartBp=200;function timeWindowEndBp(){return 200}function timeFilterUsesFullExtent(){return false}"
        + source
        + "\nconst feature=localityExportRecords("
        + json.dumps(wrapper)
        + ")[0];console.log(JSON.stringify({admission:featureTimeAdmission(feature),gap:featureInTimeWindow({applies_time_filter:true},feature)}));"
    )
    assert observed["gap"] is False and len(observed["admission"]["windows"]) == 2
    legacy = {
        "schema_version": "adna-locality-summary-export.v1",
        "localities": [{k: v for k, v in record.items() if k != "schema_version"}],
    }
    assert (
        feature_temporal_admission(locality_export_records(legacy)[0])[0]
        == "contextual"
    )
    with pytest.raises(ValueError, match="schemas disagree"):
        locality_export_records({**legacy, "localities": [record]})


def test_raw_public_projection_and_owned_payload_are_retained_separately() -> None:
    record = _record("unresolved", "source_refusal")
    payload = feature_time_payload(record)
    assert payload["time_start_bp"] is None
    assert payload["source_record"] == record
    assert payload["sample_chronology"] == record["sample_chronology"]


def test_geojson_locality_occurrence_uses_components_after_envelope_validation() -> (
    None
):
    record = {
        **_feature(),
        "schema_version": "adna-locality-summary-export.v2",
        "sample_count": 3,
    }
    feature = _collection(record)["features"][0]
    assert feature_occurrence_intervals(feature) == ((100, 110), (300, 310))
    assert len(_browser([feature])[0]["windows"]) == 2


def test_duplicated_optional_native_identifier_must_match_identity_payload() -> None:
    record = _record()
    record["archive_native_sample_id"] = "invented-other-ID"
    assert feature_temporal_admission(record)[0] == "refused"
    assert _browser([record])[0]["status"] == "refused"


def test_signed_browser_feature_requires_the_same_synthetic_evidence_contract() -> None:
    feature = {
        "source_calendar_support": SignedCalendarSupport(
            -1, 0, support_kind="closed_age_support"
        ).as_dict(),
        "declared_calendar_support": SignedCalendarSupport(
            -2, 1, support_kind="declared_stationarity_envelope"
        ).as_dict(),
        "source_age_support_bp": [[-1, 0]],
        "time_start_bp": -2,
        "time_end_bp": 1,
        "age_type": "calendar_bp",
        "data_kind": "synthetic",
        "evidence_role": "model_output",
        "scientific_acceptance": "not_evaluated",
    }
    records = [
        feature,
        *[
            {k: v for k, v in feature.items() if k != missing}
            for missing in ("data_kind", "evidence_role", "scientific_acceptance")
        ],
    ]
    assert [
        feature_temporal_admission(record, temporal_profile=SIGNED_CALENDAR_PROFILE)[0]
        for record in records
    ] == ["admitted", "refused", "refused", "refused"]
    native = NATIVE_LRA_CONTROLLER[
        : NATIVE_LRA_CONTROLLER.index("function nativeSignedCalendarView")
    ]
    observed = run_node_json(
        "const signedNativeTime={};\n"
        + native
        + template_block(
            "function finiteTimeValue", "function pointFeatureInTimeWindow"
        )
        + "\nconsole.log(JSON.stringify("
        + json.dumps(records)
        + ".map(featureTimeAdmission)));"
    )
    assert [row["status"] for row in observed] == [
        "valid",
        "refused",
        "refused",
        "refused",
    ]


@pytest.mark.parametrize(
    "field", ["source_calendar_support", "declared_calendar_support"]
)
def test_signed_support_cannot_fall_through_the_generic_numeric_route(
    field: str,
) -> None:
    record = {
        "time_start_bp": 0,
        "time_end_bp": 1,
        "temporal_semantics": {"comparability_posture": "numeric_interval"},
        field: {},
    }
    assert feature_temporal_admission(record)[0] == "refused"
    assert _browser([record])[0]["status"] == "refused"
    assert not feature_has_time(record)
    assert feature_time_payload(record)["source_record"] == record


def test_spatial_external_point_reaches_atlas_context_without_inventing_semantics() -> (
    None
):
    raw: dict[str, object] = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [18, 59]},
                "properties": {
                    "layer_key": "spatial-only",
                    "layer_label": "Spatial-only context",
                    "source": "controlled",
                    "name": "Spatial source",
                },
            }
        ],
    }
    layer = build_external_point_layer(raw)
    record = extract_context_points(
        [layer], surface=SimpleNamespace(ContextPointRecord=ContextPointRecord)
    )[0]
    assert record.latitude == 59 and record.longitude == 18
    assert record.temporal_semantics is None
    assert record.time_start_bp is record.time_end_bp is record.time_mean_bp is None


def test_maintained_fieldwork_documentation_point_remains_spatial_only(
    tmp_path: Path,
) -> None:
    docs = tmp_path / "docs"
    gallery = docs / "gallery"
    gallery.mkdir(parents=True)
    (gallery / FIELDWORK_MEDIA_FILES[0][2]).write_bytes(b"controlled fieldwork media")
    layer = build_fieldwork_point_layer(docs / "report" / "atlas")
    assert layer is not None
    record = extract_context_points(
        [layer], surface=SimpleNamespace(ContextPointRecord=ContextPointRecord)
    )[0]
    assert record.temporal_semantics is None
    assert record.time_start_bp is record.time_end_bp is record.time_mean_bp is None


@pytest.mark.parametrize(
    "semantics",
    [{}, {"comparability_posture": "refused", "refusal_reason_code": "source_refusal"}],
)
def test_atlas_extraction_preserves_explicit_temporal_declarations(
    semantics: dict[str, object],
) -> None:
    layer = build_external_point_layer(_collection({"temporal_semantics": semantics}))
    record = extract_context_points(
        [layer], surface=SimpleNamespace(ContextPointRecord=ContextPointRecord)
    )[0]
    assert record.temporal_semantics is not None
    if semantics:
        assert record.temporal_semantics["refusal_reason_code"] == "source_refusal"


@pytest.mark.parametrize("version", ["v1", "v2"])
@pytest.mark.parametrize("political", ["Sweden", "Denmark", None])
def test_declared_sample_geography_survives_external_country_projection(
    version: str, political: str | None
) -> None:
    record = _record(version=version)
    record["political_entity"] = political
    layer = build_external_point_layer(_collection(record))
    feature = cast(list[dict[str, Any]], layer["features"])[0]
    assert feature["country"] == (political or "")
    assert layer["applies_country_filter"] is bool(political)
    assert feature["source_record"]["political_entity"] == political


def test_conflicting_declared_sample_geography_is_not_overwritten() -> None:
    record = {**_record(), "political_entity": "Sweden", "country": "Denmark"}
    with pytest.raises(ValueError, match="disagree"):
        build_external_point_layer(_collection(record))
