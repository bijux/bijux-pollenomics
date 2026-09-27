"""Native threshold, chronology and sample sequence boundaries."""

from __future__ import annotations

from dataclasses import replace

import pytest

from bijux_pollenomics.analysis.propagation.event_estimation import (
    GovernedSample,
    estimate_first_observed,
)

from .network.support import event


def _samples() -> tuple[GovernedSample, ...]:
    return tuple(
        GovernedSample(
            observation_id=f"sample:{index}",
            source_record_id=f"record:{index}",
            source_family="source-native-fixture",
            source_snapshot_id="snapshot-1",
            feature_key="taxon:triticum_aestivum",
            site_id="site-template",
            collection_unit_id="core",
            sequence_position=index,
            value=value,
            measure_kind="count",
            source_unit="grains",
            measurement_semantics_id="presence.v1",
            chronology_claim_id=f"chronology:{index}",
            comparability_status="comparable",
            younger_bp=age,
            older_bp=age,
        )
        for index, (value, age) in enumerate(
            ((0, 5600), (2, 5500), (3, 5400), (4, 5300))
        )
    )


@pytest.mark.parametrize(
    ("profile", "selected", "support"),
    (
        ("reported_positive_v1", 5500, ("sample:1",)),
        ("count_ge_3_v1", 5400, ("sample:2",)),
        ("two_consecutive_positive_v1", 5500, ("sample:1", "sample:2")),
    ),
)
def test_fixed_profiles_preserve_selected_sample_and_support(
    profile: str, selected: int, support: tuple[str, ...]
) -> None:
    result = estimate_first_observed(
        _samples(), event_template=event("template"), threshold_profile_id=profile
    )
    assert result.event is not None
    assert result.event.younger_bp == selected
    assert result.event.older_bp == selected
    assert result.event.event_type == "derived_first_observed"
    assert result.supporting_observation_ids == support
    assert result.event.observation_ids == support
    assert result.establishes_continuous_presence is False
    assert result.establishes_global_first is False


@pytest.mark.parametrize(
    ("mutation", "expected"),
    (
        ("null_age", "chronology_unresolved"),
        ("overlap", "chronology_order_indeterminate"),
        ("duplicate_position", "ambiguous_sample_order"),
        ("different_collection", "incompatible_sample_sequence"),
        ("different_unit", "incompatible_measurement_semantics"),
        ("site_envelope", "sample_level_sequence_required"),
    ),
)
def test_ambiguous_or_incompatible_sequences_refuse(
    mutation: str, expected: str
) -> None:
    samples = list(_samples())
    if mutation == "null_age":
        samples[1] = replace(
            samples[1],
            younger_bp=None,
            older_bp=None,
            comparability_status="unresolved",
        )
    elif mutation == "overlap":
        samples[1] = replace(samples[1], younger_bp=5400, older_bp=5700)
    elif mutation == "duplicate_position":
        samples[1] = replace(samples[1], sequence_position=0)
    elif mutation == "different_collection":
        samples[1] = replace(samples[1], collection_unit_id="other")
    elif mutation == "different_unit":
        samples[1] = replace(samples[1], source_unit="items")
    else:
        samples[1] = replace(samples[1], subject_granularity="site")
    result = estimate_first_observed(samples, event_template=event("template"))
    assert result.event is None
    assert result.reason_code == expected
    assert result.input_sample_count == 4


def test_intervening_negative_breaks_persistence_and_no_gap_is_filled() -> None:
    samples = tuple(
        replace(row, value=5 if index in (1, 3) else 0)
        for index, row in enumerate(_samples())
    )
    result = estimate_first_observed(
        samples,
        event_template=event("template"),
        threshold_profile_id="two_consecutive_positive_v1",
    )
    assert result.event is None
    assert result.reason_code == "insufficient_persistence"


def test_omitted_sample_positions_do_not_manufacture_adjacent_positives() -> None:
    samples = (_samples()[1], _samples()[3])
    result = estimate_first_observed(
        samples,
        event_template=event("template"),
        threshold_profile_id="two_consecutive_positive_v1",
    )
    assert result.event is None
    assert result.reason_code == "nonadjacent_sample_sequence"


def test_zero_bp_is_a_valid_sample_age_and_input_order_is_explicit() -> None:
    samples = tuple(
        replace(row, younger_bp=3 - index, older_bp=3 - index)
        for index, row in enumerate(_samples())
    )
    expected = estimate_first_observed(samples, event_template=event("template"))
    reversed_input = estimate_first_observed(
        tuple(reversed(samples)), event_template=event("template")
    )
    assert expected == reversed_input
    zero = estimate_first_observed((samples[-1],), event_template=event("template"))
    assert zero.event is not None
    assert zero.event.younger_bp == 0


def test_percentage_requires_native_denominator_and_profile_compatible_kind() -> None:
    samples = tuple(
        replace(
            row,
            measure_kind="percentage",
            source_unit="percent",
            percentage_denominator=100,
        )
        for row in _samples()
    )
    good = estimate_first_observed(
        samples,
        event_template=event("template"),
        threshold_profile_id="percentage_ge_1_v1",
    )
    assert good.event is not None
    unknown = estimate_first_observed(
        tuple(replace(row, percentage_denominator=None) for row in samples),
        event_template=event("template"),
        threshold_profile_id="percentage_ge_1_v1",
    )
    assert unknown.reason_code == "percentage_denominator_unknown"
    incompatible = estimate_first_observed(
        samples, event_template=event("template"), threshold_profile_id="count_ge_3_v1"
    )
    assert incompatible.reason_code == "incompatible_threshold_measure"


@pytest.mark.parametrize("value", (-1.0, float("inf"), 2.5))
def test_invalid_native_counts_are_not_coerced(value: float) -> None:
    with pytest.raises(ValueError):
        replace(_samples()[0], value=value)


def test_context_only_age_cannot_be_promoted_to_canonical() -> None:
    with pytest.raises(ValueError, match="comparability"):
        replace(_samples()[0], comparability_status="context_only")
    context = replace(
        _samples()[0],
        comparability_status="context_only",
        younger_bp=None,
        older_bp=None,
        source_age_value=5600,
        source_age_unit="uncalibrated_radiocarbon_bp",
    )
    result = estimate_first_observed((context,), event_template=event("template"))
    assert result.event is None
    assert result.reason_code == "chronology_unresolved"
    assert context.source_age_value == 5600
    assert context.source_age_unit == "uncalibrated_radiocarbon_bp"


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    (
        ("feature_key", "taxon:hordeum", "incompatible_sample_feature"),
        ("source_family", "different-source", "incompatible_sample_source_family"),
        ("source_snapshot_id", "stale-snapshot", "incompatible_sample_source_snapshot"),
    ),
)
@pytest.mark.parametrize("changed_position", (0, 1, 3))
def test_every_sample_must_belong_to_claimed_feature_and_source(
    field: str,
    value: str,
    reason: str,
    changed_position: int,
) -> None:
    samples = tuple(
        replace(
            row,
            feature_key=value if field == "feature_key" else row.feature_key,
            source_family=value if field == "source_family" else row.source_family,
            source_snapshot_id=value
            if field == "source_snapshot_id"
            else row.source_snapshot_id,
        )
        if index == changed_position
        else row
        for index, row in enumerate(_samples())
    )
    result = estimate_first_observed(samples, event_template=event("template"))
    assert result.event is None
    assert result.reason_code == reason
    assert result.input_sample_count == 4


@pytest.mark.parametrize(
    "field", ("feature_key", "source_family", "source_snapshot_id")
)
def test_native_ownership_fields_are_required_nonempty(field: str) -> None:
    with pytest.raises(ValueError, match="nonempty"):
        sample = _samples()[0]
        replace(
            sample,
            feature_key="" if field == "feature_key" else sample.feature_key,
            source_family="" if field == "source_family" else sample.source_family,
            source_snapshot_id=""
            if field == "source_snapshot_id"
            else sample.source_snapshot_id,
        )
