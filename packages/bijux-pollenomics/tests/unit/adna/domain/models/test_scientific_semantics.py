"""Null, temporal, serialization, and frozen-value contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import pickle

import pytest

from bijux_pollenomics.adna.domain.models import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
)


def test_unknown_coordinate_preserves_null_as_distinct_from_zero() -> None:
    coordinate = AdnaCoordinate(None, None, "", "")
    assert coordinate.as_dict() == {
        "latitude": None,
        "longitude": None,
        "latitude_text": "",
        "longitude_text": "",
        "confidence": "unknown",
    }


def test_text_only_chronology_preserves_null_numeric_semantics() -> None:
    chronology = AdnaChronology("context only", None, None, None)
    payload = chronology.as_temporal_semantics(source_family="ENA")
    assert payload["time_start_bp"] is None
    assert payload["time_end_bp"] is None
    assert payload["time_mean_bp"] is None
    assert payload["duration_years"] is None
    assert payload["comparability_posture"] == "contextual_label_only"
    assert payload["temporal_window_key"] == "unresolved"


def test_precise_chronology_preserves_canonical_bp_bounds_without_losing_mean() -> None:
    chronology = AdnaChronology(
        "2200-2700 BP",
        2200,
        2700,
        2450,
        evidence_class="direct_radiocarbon_date",
        precision_posture="sample_precise_interval",
    )
    payload = chronology.as_temporal_semantics(source_family="AADR")
    assert (payload["time_start_bp"], payload["time_end_bp"]) == (2200, 2700)
    assert payload["time_mean_bp"] == 2450
    assert payload["duration_years"] == 500
    assert payload["comparability_posture"] == "numeric_interval"


def test_reversed_chronology_is_not_silently_made_comparable() -> None:
    chronology = AdnaChronology(
        "source supplied reversed bounds",
        2700,
        2200,
        2450,
        evidence_class="direct_radiocarbon_date",
        precision_posture="sample_precise_interval",
    )

    payload = chronology.as_temporal_semantics(source_family="AADR")

    assert payload["comparability_posture"] == "contextual_label_only"
    assert payload["time_start_bp"] is None
    assert payload["time_end_bp"] is None
    assert payload["time_mean_bp"] is None


def test_reason_coded_chronology_refusal_preserves_source_mean() -> None:
    chronology = AdnaChronology(
        "historical",
        None,
        None,
        None,
        date_stddev_bp="89",
        source_mean_bp_text="146",
        dating_basis="bp_mean_and_stddev",
        evidence_class="direct_numeric_sample_date",
        precision_posture="sample_precise_interval",
        refusal_reason_code="negative_bp",
    )

    payload = chronology.as_temporal_semantics(source_family="AADR")

    assert payload["comparability_posture"] == "refused"
    assert payload["refusal_reason_code"] == "negative_bp"
    assert payload["time_start_bp"] is None
    assert payload["time_end_bp"] is None
    assert payload["time_mean_bp"] is None
    assert payload["original_labels"] == [
        "historical",
        "Source mean BP: 146",
    ]


def test_approximate_archaeological_interval_is_numeric_with_visible_caveat() -> None:
    chronology = AdnaChronology(
        "2800-2600 BC (source-published mean: 4700 BP)",
        4700,
        4700,
        4700,
        dating_basis="archaeological_context",
        evidence_class="archaeological_context_date",
        precision_posture="sample_approximate_or_modeled",
    )

    payload = chronology.as_temporal_semantics(source_family="animal_adna")

    assert payload["comparability_posture"] == "numeric_interval_with_caveat"
    assert (payload["time_start_bp"], payload["time_end_bp"]) == (4700, 4700)
    assert payload["time_mean_bp"] == 4700
    assert payload["temporal_window_key"] == "mid_holocene"
    assert "caution" in str(payload["comparison_note"])


def test_text_only_approximate_chronology_cannot_claim_numeric_comparability() -> None:
    chronology = AdnaChronology(
        "archaeological context only",
        None,
        None,
        None,
        dating_basis="archaeological_context",
        evidence_class="archaeological_context_date",
        precision_posture="sample_approximate_or_modeled",
    )

    payload = chronology.as_temporal_semantics(source_family="animal_adna")

    assert payload["comparability_posture"] == "contextual_label_only"
    assert payload["time_start_bp"] is None
    assert payload["time_end_bp"] is None
    assert payload["time_mean_bp"] is None
    assert payload["temporal_window_key"] == "unresolved"


def test_locality_serialization_preserves_source_anchor_order() -> None:
    identity = AdnaLocalityIdentity(
        "species:locality",
        "location-1",
        "Uppsala",
        "Sweden",
        ("paper", "archive", "sample"),
    )
    assert identity.as_dict()["source_anchor_tokens"] == [
        "paper",
        "archive",
        "sample",
    ]


def test_models_remain_frozen_and_pickle_through_the_legacy_module() -> None:
    coordinate = AdnaCoordinate(59.8586, 17.6389, "59.8586", "17.6389", "exact")
    assert type(coordinate).__module__ == "bijux_pollenomics.adna.domain.models"
    assert pickle.loads(pickle.dumps(coordinate, protocol=5)) == coordinate
    with pytest.raises(FrozenInstanceError):
        coordinate.latitude = None
