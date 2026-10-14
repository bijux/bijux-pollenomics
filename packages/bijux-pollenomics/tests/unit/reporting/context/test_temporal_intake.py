"""External source text intake preserves integer projection refusals and metadata."""

from __future__ import annotations

from typing import cast

import pytest

from bijux_pollenomics.reporting.context.time import (
    bp_refusal_reason,
    feature_has_time,
    feature_time_payload,
    parse_year_bp,
)


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        (0.25, "fractional_bp"),
        ("9007199254740990.1", "fractional_bp"),
        ("0.0000000000000000000000000000000000000001", "fractional_bp"),
        (-(10**1000), "negative_bp"),
        ("0.25", "fractional_bp"),
        (1.25, "fractional_bp"),
        (-0.25, "negative_bp"),
        (float("inf"), "non_finite"),
        (True, "non_finite"),
        (10**1000, "unsafe_integer_bp"),
        (2**53, "unsafe_integer_bp"),
        (str(2**53), "unsafe_integer_bp"),
    ],
)
def test_integer_source_projection_refuses_before_rounding(
    value: object, reason: str
) -> None:
    assert parse_year_bp(value) is None
    assert bp_refusal_reason(value) == reason
    source: dict[str, object] = {
        "time_start_bp": value,
        "time_end_bp": 100,
        "time_label": "original source",
    }
    result = feature_time_payload(source)
    assert result["time_start_bp"] is None
    assert (
        cast(dict[str, object], result["temporal_semantics"])["refusal_reason_code"]
        == reason
    )
    assert result["time_label"] == "original source"
    assert source["time_start_bp"] is value
    assert not feature_has_time(source)


@pytest.mark.parametrize("value", [0, 0.0, "0", " 0.0 ", 10, "10"])
def test_explicit_source_text_intake_retains_supported_zero_and_integer_values(
    value: object,
) -> None:
    assert parse_year_bp(value) == int(float(cast(str | float | int, value)))
    assert not feature_has_time({"time_mean_bp": value})
    assert feature_has_time(
        {
            "time_mean_bp": value,
            "temporal_semantics": {
                "comparability_posture": "numeric_interval",
                "evidence_class": "controlled_numeric_fixture",
                "precision_posture": "controlled_integer_point",
            },
        }
    )


@pytest.mark.parametrize(
    "semantics",
    [
        {
            "comparability_posture": "contextual_label_only",
            "precision_posture": "period_label",
        },
        {"comparability_posture": "unresolved"},
        {"comparability_posture": "refused"},
        {
            "comparability_posture": "numeric_interval",
            "refusal_reason_code": "source_refusal",
        },
        {
            "comparability_posture": "numeric_interval",
            "time_start_bp": -1,
            "time_end_bp": 10,
        },
        {
            "schema_version": "temporal-semantics.v9",
            "comparability_posture": "numeric_interval",
        },
    ],
)
def test_external_numeric_properties_cannot_override_source_context_or_refusal(
    semantics: dict[str, object],
) -> None:
    source: dict[str, object] = {
        "time_start_bp": 0,
        "time_end_bp": 10,
        "temporal_semantics": semantics,
    }
    result = feature_time_payload(source)
    assert result["time_start_bp"] is None and result["time_mean_bp"] is None
    assert source["time_start_bp"] == 0
    assert not feature_has_time(source)


def test_external_intake_preserves_explicit_unknowns_and_source_provenance() -> None:
    source: dict[str, object] = {
        "time_start_bp": "0",
        "time_end_bp": "10",
        "temporal_semantics": {
            "comparability_posture": "numeric_interval_with_caveat",
            "reference_epoch": None,
            "calibration_status": "source_not_declared",
            "model": {"version": None},
            "source_record_ids": ["Native:01"],
            "chronology_claim_ids": ["claim:01"],
        },
    }
    result = feature_time_payload(source)
    semantics = cast(dict[str, object], result["temporal_semantics"])
    assert semantics["reference_epoch"] is None
    assert semantics["source_record_ids"] == ["Native:01"]
    assert semantics["model"] == {"version": None}
    assert result["time_start_bp"] == 0
    assert feature_has_time(source)
