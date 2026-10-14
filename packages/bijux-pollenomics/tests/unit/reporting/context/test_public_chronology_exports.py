"""Actual public serializers retain source eligibility through external and map readers."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from bijux_pollenomics.adna import AdnaLocalitySummary
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
    exported_record_semantics,
    locality_export_records,
)
from bijux_pollenomics.reporting.map_document.template import NATIVE_LRA_CONTROLLER
from bijux_pollenomics.reporting.map_document.temporal_admission import (
    feature_occurrence_intervals,
    feature_temporal_admission,
)
from bijux_pollenomics.reporting.rendering.record_exports import (
    build_samples_geojson,
    serialize_sample_record,
)

from ..map_document.browser_semantics.support import run_node_json, template_block
from ..map_document.browser_semantics.test_sample_occurrence_time import _feature
from ..rendering.test_sample_chronology_exports import _source_sample


def _record(
    posture: str = "sample_precise_interval", refusal: str = "", *, version: str = "v2"
) -> dict[str, Any]:
    sample = _source_sample(0, 0)
    sample = replace(
        sample,
        chronology=replace(
            sample.chronology, precision_posture=posture, refusal_reason_code=refusal
        ),
    )
    return serialize_sample_record(
        sample, schema_version="adna-sample-record-export." + version
    )


def _browser(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source = template_block(
        "function finiteTimeValue", "function pointFeatureInTimeWindow"
    )
    return cast(
        list[dict[str, Any]],
        run_node_json(
            source
            + "\nconsole.log(JSON.stringify("
            + json.dumps(features)
            + ".map(featureTimeAdmission)));"
        ),
    )


def _collection(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [18, 59]},
                "properties": {
                    **record,
                    "layer_key": "controlled-source",
                    "layer_label": "Controlled source",
                },
            }
        ],
    }


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


def _owned_locality_record() -> dict[str, Any]:
    from bijux_pollenomics.adna import AdnaChronology
    from bijux_pollenomics.adna.domain.models.localities import (
        AdnaSampleChronologySupport,
    )
    from bijux_pollenomics.reporting.rendering.record_exports import (
        serialize_locality_summary,
    )

    from ...analysis.fieldwork.ranking_examples import _locality

    locality = _locality("Controlled source locality", 59, 18, sample_count=4)
    supports = tuple(
        AdnaSampleChronologySupport(
            sample_id=identifier,
            chronology=AdnaChronology(
                original_text="retained source interval",
                time_start_bp=start,
                time_end_bp=end,
                time_mean_bp=None,
                dating_basis="bp_window",
                precision_posture="sample_precise_interval"
                if start is not None
                else "unresolved",
                evidence_class="controlled_numeric_sample_date",
            ),
            source_release="controlled-release",
            provenance_path="original/source.csv",
            provenance_locator=identifier,
        )
        for identifier, start, end in [
            ("young", 100, 110),
            ("also-young", 105, 110),
            ("old", 300, 310),
            ("missing", None, None),
        ]
    )
    locality = replace(
        locality,
        sample_ids=tuple(support.sample_id for support in supports),
        sample_chronologies=supports,
        chronology=replace(
            locality.chronology, time_start_bp=100, time_end_bp=310, time_mean_bp=200
        ),
    )
    return cast(dict[str, Any], serialize_locality_summary(locality))


def _extracted_locality(record: dict[str, Any]) -> ContextPointRecord:
    layer = build_external_point_layer(_collection(record))
    return cast(
        ContextPointRecord,
        extract_context_points(
            [layer], surface=SimpleNamespace(ContextPointRecord=ContextPointRecord)
        )[0],
    )


def test_real_locality_export_components_survive_atlas_analytics_without_hull_or_count_inflation() -> (
    None
):
    from bijux_pollenomics.analysis.fieldwork.evidence_richness.temporal import (
        _attach_temporal_context,
    )
    from bijux_pollenomics.analysis.fieldwork.ranking import build_candidate_context
    from bijux_pollenomics.collection.contracts.occurrence_chronology import (
        occurrence_support_intervals,
    )
    from bijux_pollenomics.core.temporal_semantics import BpInterval
    from bijux_pollenomics.evidence.scientific_review.chronology import _LayerIntervals

    from ...analysis.fieldwork.lake_fieldwork_preparation.support import _candidate
    from ...analysis.fieldwork.ranking_examples import _locality

    record = _owned_locality_record()
    point = _extracted_locality(record)
    assert point.source_record is not None
    assert point.source_record["sample_chronologies"] == record["sample_chronologies"]
    assert point.source_record["sample_ids"] == record["sample_ids"]
    assert point.record_count == 1 and point.occurrence_supports is not None
    assert len(point.occurrence_supports) == 4
    intervals = occurrence_support_intervals(
        temporal_semantics=point.temporal_semantics,
        time_start_bp=point.time_start_bp,
        time_end_bp=point.time_end_bp,
        occurrence_supports=point.occurrence_supports,
    )
    assert [(i.younger_bp, i.older_bp) for i in intervals] == [
        (100, 110),
        (105, 110),
        (300, 310),
    ]
    index = _LayerIntervals.from_points([point])
    assert not index.overlaps(BpInterval(200, 200))
    assert index.overlaps(BpInterval(110, 110))
    anchor = _locality("candidate", 59, 18, sample_count=1)
    support = anchor.sample_chronologies[0]

    def candidate_at(start: int, end: int) -> AdnaLocalitySummary:
        chronology = replace(
            support.chronology,
            time_start_bp=start,
            time_end_bp=end,
            time_mean_bp=start,
            precision_posture="sample_precise_interval",
            evidence_class="controlled_numeric_sample_date",
        )
        return replace(
            anchor, sample_chronologies=(replace(support, chronology=chronology),)
        )

    gap = build_candidate_context(candidate_at(200, 200), [point])
    assert gap.nearby_context_points == gap.time_aware_context_points == 1
    assert gap.temporal_overlap_points == 0
    young = build_candidate_context(candidate_at(105, 110), [point])
    assert young.temporal_overlap_points == 1
    candidate = _candidate(
        lake_name="Controlled lake",
        lake_label="Controlled lake",
        latitude=59,
        longitude=18,
        ambiguity_flags=(),
        direct_pollen_source_count=1,
    )
    attached = _attach_temporal_context(
        [candidate],
        pollen_points=[point],
        human_points=(),
        animal_points=(),
        sead_points=(),
    )[0]
    assert len(attached.temporal_context_points) == 1
    assert attached.temporal_context_points[0].record_count == 1
    assert attached.temporal_context_points[0].sample_count == 1


@pytest.mark.parametrize(
    "semantics",
    [
        {},
        {"comparability_posture": "contextual_label_only"},
        {"comparability_posture": "refused", "refusal_reason_code": "source_refusal"},
    ],
)
def test_explicit_outer_declaration_still_constrains_owned_components(
    semantics: dict[str, object],
) -> None:
    from bijux_pollenomics.collection.contracts.occurrence_chronology import (
        occurrence_support_intervals,
    )

    record = {**_owned_locality_record(), "temporal_semantics": semantics}
    point = _extracted_locality(record)
    assert (
        point.source_record is not None
        and point.source_record["sample_chronologies"] == record["sample_chronologies"]
    )
    assert not occurrence_support_intervals(
        temporal_semantics=point.temporal_semantics,
        time_start_bp=point.time_start_bp,
        time_end_bp=point.time_end_bp,
        occurrence_supports=point.occurrence_supports,
    )


def test_context_exports_preserve_named_source_and_components_with_legacy_bytes_unchanged(
    tmp_path: Path,
) -> None:
    import csv

    from bijux_pollenomics.collection.exports.context_points import (
        write_context_points_csv,
        write_context_points_geojson,
    )

    point = _extracted_locality(_owned_locality_record())
    geojson = tmp_path / "context.geojson"
    write_context_points_geojson(geojson, [point])
    payload = json.loads(geojson.read_text())
    properties = payload["features"][0]["properties"]
    assert properties["schema_version"] == "adna-locality-summary-export.v2"
    assert "temporal_semantics" not in properties
    roundtrip = cast(
        ContextPointRecord,
        extract_context_points(
            [build_external_point_layer(payload)],
            surface=SimpleNamespace(ContextPointRecord=ContextPointRecord),
        )[0],
    )
    assert roundtrip.occurrence_supports == point.occurrence_supports
    assert roundtrip.source_record is not None
    assert point.source_record is not None and point.occurrence_supports is not None
    assert (
        roundtrip.source_record["sample_chronologies"]
        == point.source_record["sample_chronologies"]
    )
    csv_path = tmp_path / "context.csv"
    write_context_points_csv(csv_path, [point])
    with csv_path.open(newline="") as stream:
        row = next(csv.DictReader(stream))
    assert json.loads(row["source_record_json"]) == point.source_record
    assert json.loads(row["occurrence_supports_json"]) == [
        support.as_dict() for support in point.occurrence_supports
    ]
    legacy = replace(point, source_record=None, occurrence_supports=None)
    write_context_points_csv(csv_path, [legacy])
    with csv_path.open(newline="") as stream:
        legacy_row = next(csv.DictReader(stream))
    assert (
        "source_record_json" not in legacy_row
        and "occurrence_supports_json" not in legacy_row
    )


def test_unknown_native_member_refuses_extracted_components_without_hull_fallback() -> (
    None
):
    from bijux_pollenomics.collection.contracts.occurrence_chronology import (
        occurrence_support_intervals,
    )

    record = _owned_locality_record()
    record["sample_chronologies"][0]["sample_id"] = "unknown-native-member"
    point = _extracted_locality(record)
    assert point.occurrence_supports == ()
    assert (
        point.source_record is not None
        and point.source_record["sample_chronologies"] == record["sample_chronologies"]
    )
    assert not occurrence_support_intervals(
        temporal_semantics=point.temporal_semantics,
        time_start_bp=point.time_start_bp,
        time_end_bp=point.time_end_bp,
        occurrence_supports=point.occurrence_supports,
    )


def test_refused_member_is_retained_without_suppressing_other_owned_intervals() -> None:
    from bijux_pollenomics.collection.contracts.occurrence_chronology import (
        occurrence_support_intervals,
    )

    record = _owned_locality_record()
    record["sample_chronologies"][0]["chronology"]["refusal_reason_code"] = (
        "source_refusal"
    )
    point = _extracted_locality(record)
    assert point.occurrence_supports is not None and len(point.occurrence_supports) == 4
    intervals = occurrence_support_intervals(
        temporal_semantics=point.temporal_semantics,
        time_start_bp=point.time_start_bp,
        time_end_bp=point.time_end_bp,
        occurrence_supports=point.occurrence_supports,
    )
    assert [(interval.younger_bp, interval.older_bp) for interval in intervals] == [
        (105, 110),
        (300, 310),
    ]
    assert (
        point.source_record is not None
        and point.source_record["sample_chronologies"] == record["sample_chronologies"]
    )


def test_preferred_singular_sample_keeps_native_identity_and_zero_after_extraction() -> (
    None
):
    from bijux_pollenomics.core.temporal_semantics import BpInterval
    from bijux_pollenomics.evidence.scientific_review.chronology import _LayerIntervals

    record = _record()
    point = _extracted_locality(record)
    assert (
        point.source_record is not None
        and point.source_record["sample_identity"] == record["sample_identity"]
    )
    assert point.occurrence_supports is None
    assert _LayerIntervals.from_points([point]).overlaps(BpInterval(0, 0))


def test_repeated_context_transport_preserves_semantics_and_literal_provenance(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.exports.context_points import (
        write_context_points_geojson,
    )
    from bijux_pollenomics.core.temporal_semantics import BpInterval
    from bijux_pollenomics.evidence.scientific_review.chronology import _LayerIntervals

    point = _extracted_locality(_owned_locality_record())
    for index in range(2):
        previous = point
        path = tmp_path / f"context-{index}.geojson"
        write_context_points_geojson(path, [previous])
        collection = json.loads(path.read_text())
        point = cast(
            ContextPointRecord,
            extract_context_points(
                [build_external_point_layer(collection)],
                surface=SimpleNamespace(ContextPointRecord=ContextPointRecord),
            )[0],
        )
        assert point.record_count == 1
        assert point.occurrence_supports == previous.occurrence_supports
        assert point.source_record is not None
        assert point.source_record["source_record"] == previous.source_record
        assert (
            point.source_record["schema_version"] == "adna-locality-summary-export.v2"
        )
        assert not _LayerIntervals.from_points([point]).overlaps(BpInterval(200, 200))
        assert _LayerIntervals.from_points([point]).overlaps(BpInterval(110, 110))


@pytest.mark.parametrize("wrapped", [False, True])
@pytest.mark.parametrize("political", ["Sweden", "Denmark", None])
def test_locality_native_identity_and_geography_survive_all_reader_projections(
    wrapped: bool, political: str | None
) -> None:
    record = _owned_locality_record()
    record["political_entity"] = political
    record["locality_identity"]["political_entity"] = political
    identity = deepcopy(record["locality_identity"])
    if wrapped:
        record["identity"] = record.pop("locality_identity")
        del record["political_entity"]
        record = locality_export_records(
            {"schema_version": record.pop("schema_version"), "localities": [record]}
        )[0]
    assert feature_temporal_admission(record)[0] == "admitted"
    assert _browser([record])[0]["status"] == "valid"
    layer = build_external_point_layer(_collection(record))
    mapped = cast(list[dict[str, Any]], layer["features"])[0]
    assert mapped["country"] == (political or "")
    key = "identity" if wrapped else "locality_identity"
    assert mapped[key] == identity
    assert mapped["source_record"][key] == identity
    point = _extracted_locality(record)
    assert point.country == (political or "")
    assert point.source_record is not None and point.source_record[key] == identity


@pytest.mark.parametrize(
    "change", ["geography", "token", "namespace", "anchors", "object", "dual"]
)
def test_conflicting_or_malformed_locality_native_identity_never_admits(
    change: str,
) -> None:
    record = _owned_locality_record()
    if change == "geography":
        record["political_entity"] = "conflicting declared geography"
    elif change == "token":
        record["locality_token"] = "conflicting token"
    elif change == "namespace":
        record["locality_namespace"] = "conflicting namespace"
    elif change == "anchors":
        record["locality_identity"]["source_anchor_tokens"] = [False]
    elif change == "object":
        record["locality_identity"] = []
    else:
        record["identity"] = {
            **record["locality_identity"],
            "stable_token": "conflicting token",
        }
    assert feature_temporal_admission(record) == ("refused", None)
    assert _browser([record])[0]["status"] == "refused"
    with pytest.raises(ValueError):
        build_external_point_layer(_collection(record))


def test_locality_csv_has_explicit_json_native_identity(tmp_path: Path) -> None:
    import csv

    from bijux_pollenomics.reporting.rendering.record_exports import (
        write_localities_csv,
    )

    from ...analysis.fieldwork.ranking_examples import _locality

    locality = _locality("Native locality", 59, 18)
    output = tmp_path / "localities.csv"
    write_localities_csv(output, [locality])
    with output.open(newline="") as handle:
        row = next(csv.DictReader(handle))
    assert json.loads(row["locality_identity"]) == locality.identity.as_dict()
    assert row["political_entity"] == (locality.identity.political_entity or "")


def test_locality_csv_nullable_geography_is_retained_without_inferred_null() -> None:
    record = _owned_locality_record()
    record["political_entity"] = ""
    record["locality_identity"]["political_entity"] = None
    assert feature_temporal_admission(record)[0] == "admitted"
    assert _browser([record])[0]["status"] == "valid"
    mapped = cast(
        list[dict[str, Any]],
        build_external_point_layer(_collection(record))["features"],
    )[0]
    assert mapped["country"] == ""
    assert mapped["source_record"]["political_entity"] == ""
    assert mapped["locality_identity"]["political_entity"] is None


@pytest.mark.parametrize("kind", ["sample", "locality"])
def test_colocated_same_name_exports_keep_distinct_native_operational_identity(
    kind: str,
) -> None:
    records = (
        [_record(), _record()]
        if kind == "sample"
        else [_owned_locality_record(), _owned_locality_record()]
    )
    pairs = [("a:b", "c"), ("a", "b:c")]
    for record, (namespace, token) in zip(records, pairs, strict=True):
        record["locality"] = "Same displayed locality"
        if kind == "sample":
            record["genetic_id"] = token
            record["sample_namespace"] = namespace
            record["sample_identity"].update(namespace=namespace, stable_token=token)
            record["sample_chronology"]["sample_id"] = token
        else:
            record["locality_identity"].update(namespace=namespace, stable_token=token)
    points = [_extracted_locality(record) for record in records]
    assert [json.loads(point.record_id) for point in points] == [
        list(pair) for pair in pairs
    ]
    assert len({point.record_id for point in points}) == 2
    assert {point.name for point in points} == {"Same displayed locality"}
    assert [
        point.source_record["locality"] for point in points if point.source_record
    ] == ["Same displayed locality"] * 2
    from bijux_pollenomics.analysis.fieldwork.evidence_richness.temporal import (
        _attach_temporal_context,
    )

    from ...analysis.fieldwork.lake_fieldwork_preparation.support import _candidate

    candidate = _candidate(
        lake_name="Controlled",
        lake_label="Controlled",
        latitude=59,
        longitude=18,
        ambiguity_flags=(),
        direct_pollen_source_count=0,
    )
    summaries = _attach_temporal_context(
        [candidate],
        pollen_points=points,
        human_points=(),
        animal_points=(),
        sead_points=(),
    )[0].temporal_context_points
    assert summaries
    assert all(len(summary.representative_source_records) == 2 for summary in summaries)


def test_generic_context_keeps_existing_title_identity_and_missing_locality_native_id_is_not_invented() -> (
    None
):
    generic = {"name": "Generic display", "record_id": "source-row"}
    mapped = build_external_point_layer(_collection(generic))
    point = extract_context_points(
        [mapped], surface=SimpleNamespace(ContextPointRecord=ContextPointRecord)
    )[0]
    assert point.record_id == "Generic display"
    legacy = _owned_locality_record()
    del legacy["locality_identity"]
    mapped = build_external_point_layer(_collection(legacy))
    raw = cast(list[dict[str, Any]], mapped["features"])[0]
    assert raw["evidence_row_id"] == ""


def test_actual_locality_csv_null_geography_reaches_typed_context_without_restoration(
    tmp_path: Path,
) -> None:
    import csv

    from bijux_pollenomics.reporting.rendering.record_exports import (
        write_localities_csv,
    )

    from ...analysis.fieldwork.ranking_examples import _locality

    locality = _locality("Native nullable geography", 59, 18, sample_count=2)
    locality = replace(
        locality, identity=replace(locality.identity, political_entity=None)
    )
    output = tmp_path / "native-locality.csv"
    write_localities_csv(output, [locality])
    with output.open(newline="") as handle:
        record: dict[str, Any] = dict(next(csv.DictReader(handle)))
    for key in ("sample_chronologies", "locality_identity"):
        record[key] = json.loads(record[key])
    for key in ("sample_count", "time_start_bp", "time_end_bp", "time_mean_bp"):
        record[key] = int(record[key]) if record[key] else None
    record["sample_ids"] = (
        record["sample_ids"].split(";") if record["sample_ids"] else []
    )
    assert record["political_entity"] == ""
    assert record["locality_identity"]["political_entity"] is None
    assert feature_temporal_admission(record)[0] == "admitted"
    assert _browser([record])[0]["status"] == "valid"
    point = _extracted_locality(record)
    assert point.country == ""
    assert point.source_record is not None
    assert point.source_record["political_entity"] == ""
    retained_identity = point.source_record["locality_identity"]
    assert isinstance(retained_identity, dict)
    assert retained_identity["political_entity"] is None
    assert point.occurrence_supports is not None
    assert [row.support_id for row in point.occurrence_supports] == list(
        locality.sample_ids
    )
