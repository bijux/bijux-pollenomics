"""Sample precision and ownership agree between Python and browser consumers."""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

import pytest

from bijux_pollenomics.adna.domain.locality import mapping_sample_intervals
from bijux_pollenomics.adna.domain.models import AdnaChronology
from bijux_pollenomics.adna.domain.models.localities import AdnaSampleChronologySupport
from bijux_pollenomics.reporting.map_document.temporal_admission import (
    feature_occurrence_intervals,
    feature_temporal_admission,
)

from ..support import run_node_json, template_block


def _feature(precision: str, refusal: str = "") -> dict[str, Any]:
    support = AdnaSampleChronologySupport(
        "source-sample",
        AdnaChronology(
            original_text="literal source interval",
            time_start_bp=100,
            time_end_bp=112,
            time_mean_bp=106,
            precision_posture=precision,
            evidence_class="source_declared_evidence",
            refusal_reason_code=refusal,
        ),
    )
    return {
        "source_family": "controlled",
        "sample_ids": ["source-sample"],
        "sample_count": 1,
        "sample_chronologies": [support.as_dict()],
        "chronology_role": "locality_sample_coverage_hull",
        "time_start_bp": 0,
        "time_end_bp": 1000,
    }


def _browser(feature: dict[str, Any]) -> dict[str, Any]:
    source = template_block("function finiteTimeValue", "function valueIsAvailable")
    source += template_block(
        "function featureTimeAdmission", "function featureTimeWindow"
    )
    result = run_node_json(
        source
        + "\nconsole.log(JSON.stringify(featureTimeAdmission("
        + json.dumps(feature)
        + "))); "
    )

    assert isinstance(result, dict)
    return result


@pytest.mark.parametrize(
    "precision,expected",
    [
        ("sample_precise_point", True),
        ("sample_precise_interval", True),
        ("sample_approximate_or_modeled", True),
        ("contextual_interval", True),
        ("unresolved", False),
        ("broad_period", False),
        ("unrecognized", False),
    ],
)
def test_precision_is_required_even_when_source_has_numeric_bounds(
    precision: str, expected: bool
) -> None:
    feature = _feature(precision)
    assert bool(mapping_sample_intervals(feature)) is expected
    observed = _browser(feature)
    assert (observed["status"] == "valid") is expected
    assert observed["window"] == ({"start": 100, "end": 112} if expected else None)
    assert (
        feature["sample_chronologies"][0]["chronology"]["evidence_class"]
        == "source_declared_evidence"
    )


@pytest.mark.parametrize(
    "case",
    [
        "refused",
        "bad_count",
        "bool_count",
        "empty_id",
        "fractional_mean",
        "string_start",
        "duplicate_support",
    ],
)
def test_malformed_or_refused_sample_cannot_enter_browser_or_python(case: str) -> None:
    feature = _feature("sample_precise_interval")
    support = feature["sample_chronologies"][0]
    if case == "refused":
        support["chronology"]["refusal_reason_code"] = (
            "source_age_system_not_comparable"
        )
    elif case == "bad_count":
        feature["sample_count"] = 2
    elif case == "bool_count":
        feature["sample_count"] = True
    elif case == "empty_id":
        feature["sample_ids"] = [""]
    elif case == "fractional_mean":
        support["chronology"]["time_mean_bp"] = 106.5
    elif case == "string_start":
        support["chronology"]["time_start_bp"] = "100"
    elif case == "duplicate_support":
        feature["sample_chronologies"].append(support)
    assert mapping_sample_intervals(feature) == ()
    assert _browser(feature)["status"] in {"contextual", "refused"}


@pytest.mark.parametrize(
    "schema,expected",
    [
        ("absent", True),
        ("temporal-semantics.v1", True),
        ("temporal-semantics.v9", False),
        (None, False),
    ],
)
@pytest.mark.parametrize("samples", [False, True])
def test_raw_feature_refuses_explicit_unsupported_semantic_schema(
    schema: object, expected: bool, samples: bool
) -> None:
    feature: dict[str, Any] = (
        _feature("sample_precise_interval")
        if samples
        else {"time_start_bp": 100, "time_end_bp": 112}
    )
    semantics: dict[str, object] = {"comparability_posture": "numeric_interval"}
    if schema != "absent":
        semantics["schema_version"] = schema
    feature["temporal_semantics"] = semantics
    assert (feature_temporal_admission(feature)[0] == "admitted") is expected
    assert bool(feature_occurrence_intervals(feature)) is expected
    assert (_browser(feature)["status"] == "valid") is expected


@pytest.mark.parametrize("posture", ["contextual_label_only", "unresolved"])
@pytest.mark.parametrize("schema", [None, "adna-locality-summary-export.v2"])
def test_owned_sample_precedes_contextual_display_hull(
    posture: str, schema: str | None
) -> None:
    feature = _feature("sample_precise_interval")
    feature["temporal_semantics"] = {
        "schema_version": "temporal-semantics.v1",
        "comparability_posture": posture,
        "evidence_class": "locality_sample_coverage_hull",
        "precision_posture": "display_coverage_only",
    }
    if schema is not None:
        feature["schema_version"] = schema
    original = deepcopy(feature)
    assert feature_temporal_admission(feature) == ("admitted", (100, 112))
    assert feature_occurrence_intervals(feature) == ((100, 112),)
    assert _browser(feature) == {
        "status": "valid",
        "window": {"start": 100, "end": 112},
        "windows": [{"start": 100, "end": 112, "sample_id": "source-sample"}],
    }
    assert feature == original
    del feature["sample_chronologies"]
    feature.pop("schema_version", None)
    assert feature_temporal_admission(feature) == ("contextual", None)
    assert _browser(feature) == {"status": "contextual", "window": None}


@pytest.mark.parametrize(
    "semantics",
    [
        None,
        [],
        {"comparability_posture": False},
        {"refusal_reason_code": []},
        {"schema_version": "temporal-semantics.v9"},
    ],
)
def test_owned_samples_do_not_bypass_malformed_generic_semantics(
    semantics: object,
) -> None:
    feature = _feature("sample_precise_interval")
    feature["temporal_semantics"] = semantics
    assert feature_temporal_admission(feature) == ("refused", None)
    assert feature_occurrence_intervals(feature) == ()
    assert _browser(feature) == {"status": "refused", "window": None}


@pytest.mark.parametrize(
    "kind",
    [
        "missing_packet",
        "empty_packets",
        "missing_ids",
        "null_ids",
        "wrong_role",
        "swapped_owner",
        "duplicate_owner",
        "signed_child",
    ],
)
def test_contextual_hull_does_not_hide_invalid_owner_population(kind: str) -> None:
    feature = _feature("sample_precise_interval")
    feature["temporal_semantics"] = {"comparability_posture": "contextual_label_only"}
    if kind == "missing_packet":
        feature["sample_ids"].append("undated-member")
        feature["sample_count"] = 2
    elif kind == "empty_packets":
        feature["sample_chronologies"] = []
    elif kind == "missing_ids":
        del feature["sample_ids"]
    elif kind == "null_ids":
        feature["sample_ids"] = None
        feature["sample_record_ids"] = ["source-sample"]
    elif kind == "wrong_role":
        feature["chronology_role"] = "singular_source_date"
    elif kind == "swapped_owner":
        feature["sample_chronologies"][0]["sample_id"] = "another-locality-owner"
    elif kind == "duplicate_owner":
        feature["sample_ids"] = ["source-sample", "source-sample"]
        feature["sample_count"] = 2
    else:
        feature["sample_chronologies"][0]["chronology"]["time_start_bp"] = -1
    assert feature_temporal_admission(feature) == ("refused", None)
    assert feature_occurrence_intervals(feature) == ()
    assert _browser(feature) == {"status": "refused", "window": None}


@pytest.mark.parametrize("state", ["undated", "refused", "unknown_precision"])
def test_nonoccurring_child_is_preserved_without_borrowing_display_hull(
    state: str,
) -> None:
    feature = _feature("sample_precise_interval")
    feature["temporal_semantics"] = {"comparability_posture": "contextual_label_only"}
    chronology = feature["sample_chronologies"][0]["chronology"]
    if state == "undated":
        chronology.update(time_start_bp=None, time_end_bp=None, time_mean_bp=None)
    elif state == "refused":
        chronology["refusal_reason_code"] = "source_age_system_not_comparable"
    else:
        chronology["precision_posture"] = "unrecognized"
    original = deepcopy(feature)
    assert feature_temporal_admission(feature) == ("contextual", None)
    assert feature_occurrence_intervals(feature) == ()
    assert _browser(feature) == {"status": "contextual", "window": None}
    assert feature == original


def test_out_of_bound_source_mean_does_not_replace_valid_sample_endpoints() -> None:
    feature = _feature("sample_precise_interval")
    feature["temporal_semantics"] = {"comparability_posture": "contextual_label_only"}
    feature["sample_chronologies"][0]["chronology"]["time_mean_bp"] = -1
    original = deepcopy(feature)
    assert feature_temporal_admission(feature) == ("admitted", (100, 112))
    assert feature_occurrence_intervals(feature) == ((100, 112),)
    assert _browser(feature)["windows"] == [
        {"start": 100, "end": 112, "sample_id": "source-sample"}
    ]
    assert feature == original


@pytest.mark.parametrize(
    "posture,reason",
    [("refused", ""), ("contextual_label_only", "source_age_system_not_comparable")],
)
def test_explicit_global_refusal_still_precedes_valid_child(
    posture: str, reason: str
) -> None:
    feature = _feature("sample_precise_interval")
    feature["temporal_semantics"] = {
        "comparability_posture": posture,
        "refusal_reason_code": reason,
    }
    for candidate in (
        feature,
        {key: value for key, value in feature.items() if key != "sample_chronologies"},
    ):
        assert feature_temporal_admission(candidate) == ("refused", None)
        assert feature_occurrence_intervals(candidate) == ()
        assert _browser(candidate) == {"status": "refused", "window": None}


def test_refused_member_does_not_supply_occurrence_but_remains_owned() -> None:
    feature = _feature("sample_precise_interval")
    refused = deepcopy(feature["sample_chronologies"][0])
    refused["sample_id"] = "refused-member"
    refused["chronology"].update(
        time_start_bp=300,
        time_end_bp=310,
        time_mean_bp=305,
        refusal_reason_code="source_age_system_not_comparable",
    )
    feature["sample_chronologies"].append(refused)
    feature["sample_ids"].append("refused-member")
    feature["sample_count"] = 2
    feature["temporal_semantics"] = {"comparability_posture": "contextual_label_only"}
    original = deepcopy(feature)
    assert feature_temporal_admission(feature) == ("admitted", (100, 112))
    assert feature_occurrence_intervals(feature) == ((100, 112),)
    assert _browser(feature)["windows"] == [
        {"start": 100, "end": 112, "sample_id": "source-sample"}
    ]
    assert feature == original


def test_owned_components_do_not_infer_signed_calendar_profile() -> None:
    feature = _feature("sample_precise_interval")
    feature["source_calendar_support"] = {"younger_bp": 100, "older_bp": 112}
    assert feature_temporal_admission(feature) == ("refused", None)
    assert _browser(feature) == {"status": "refused", "window": None}
