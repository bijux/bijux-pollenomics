"""Sample precision and ownership agree between Python and browser consumers."""

from __future__ import annotations

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
