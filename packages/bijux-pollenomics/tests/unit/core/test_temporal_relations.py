"""Typed relations distinguish numeric direction from source comparability."""

from __future__ import annotations

from dataclasses import replace

from hypothesis import given, settings
from hypothesis import strategies as st
import pytest

from bijux_pollenomics.core.chronology.relations import (
    TemporalComparisonBasis,
    TemporalRelationKind,
    compare_bp_intervals,
)
from bijux_pollenomics.core.temporal_semantics import (
    BpInterval,
    InvalidBpIntervalError,
    closed_bp_intervals_overlap,
)

BASIS = TemporalComparisonBasis("calendar_bp", 1950, "numeric_interval")


def test_raw_interval_algebra_does_not_guess_source_comparability() -> None:
    left, right = BpInterval(0.25, 1.25), BpInterval(1, 2)
    result = compare_bp_intervals(left, right)
    assert result.kind is TemporalRelationKind.NOT_COMPARABLE
    assert result.refusal_reason_code == "missing_comparison_basis"
    assert result.left_interval is left and result.right_interval is right
    assert result.overlap_interval is None and result.separation_years is None
    assert closed_bp_intervals_overlap(left, right)


@pytest.mark.parametrize(
    ("left", "right", "kind", "overlap", "separation"),
    [
        (
            BpInterval(0, 0),
            BpInterval(0, 0),
            TemporalRelationKind.OVERLAPPING,
            BpInterval(0, 0),
            0,
        ),
        (
            BpInterval(0.25, 1.25),
            BpInterval(1.25, 2.25),
            TemporalRelationKind.OVERLAPPING,
            BpInterval(1.25, 1.25),
            0,
        ),
        (
            BpInterval(0.25, 1.25),
            BpInterval(1, 2),
            TemporalRelationKind.OVERLAPPING,
            BpInterval(1, 1.25),
            0,
        ),
        (
            BpInterval(0.25, 1.25),
            BpInterval(3.5, 4),
            TemporalRelationKind.LEFT_YOUNGER,
            None,
            2.25,
        ),
        (
            BpInterval(3.5, 4),
            BpInterval(0.25, 1.25),
            TemporalRelationKind.LEFT_OLDER,
            None,
            2.25,
        ),
    ],
)
def test_explicit_comparable_intervals_keep_exact_support_and_direction(
    left: BpInterval,
    right: BpInterval,
    kind: TemporalRelationKind,
    overlap: BpInterval | None,
    separation: float,
) -> None:
    result = compare_bp_intervals(left, right, left_basis=BASIS, right_basis=BASIS)
    assert result.kind is kind and result.comparable
    assert result.overlap_interval == overlap
    assert result.separation_years == separation
    assert result.left_interval is left and result.right_interval is right
    assert result.left_basis is BASIS and result.right_basis is BASIS
    assert not result.refusal_reason_code
    assert closed_bp_intervals_overlap(left, right) == (
        kind is TemporalRelationKind.OVERLAPPING
    )


@pytest.mark.parametrize(
    "left,right", [(None, BpInterval(0, 0)), (BpInterval(0, 0), None), (None, None)]
)
def test_missing_interval_is_not_zero_or_numeric_separation(
    left: BpInterval | None, right: BpInterval | None
) -> None:
    result = compare_bp_intervals(left, right, left_basis=BASIS, right_basis=BASIS)
    assert result.kind is TemporalRelationKind.NOT_COMPARABLE
    assert result.refusal_reason_code == "missing_interval"
    assert result.overlap_interval is None and result.separation_years is None


@pytest.mark.parametrize(
    ("basis", "reason"),
    [
        (None, "missing_comparison_basis"),
        (
            replace(BASIS, refusal_reason_code="source_age_system_not_comparable"),
            "source_refused",
        ),
        (
            replace(BASIS, comparability_posture="contextual_label_only"),
            "non_numeric_comparability_posture",
        ),
        (
            replace(BASIS, comparability_posture="unresolved"),
            "non_numeric_comparability_posture",
        ),
        (replace(BASIS, age_type="radiocarbon_bp"), "incomparable_age_types"),
        (replace(BASIS, age_type=None), "incomparable_age_types"),
        (replace(BASIS, reference_epoch_ce=None), "unknown_reference_epoch"),
        (replace(BASIS, reference_epoch_ce=True), "unknown_reference_epoch"),
        (replace(BASIS, reference_epoch_ce=2000), "reference_epoch_mismatch"),
    ],
)
def test_source_basis_refusals_preserve_original_assertions(
    basis: TemporalComparisonBasis | None,
    reason: str,
) -> None:
    interval = BpInterval(10.25, 11.75)
    result = compare_bp_intervals(
        interval, interval, left_basis=BASIS, right_basis=basis
    )
    assert result.kind is TemporalRelationKind.NOT_COMPARABLE
    assert result.refusal_reason_code == reason
    assert result.right_basis is basis
    assert result.left_interval is interval and result.right_interval is interval
    assert result.separation_years is None and result.overlap_interval is None


@pytest.mark.parametrize(
    "age_type", [None, "", "not_separately_declared", "radiocarbon_bp", "cal_bp"]
)
def test_matching_unknown_or_other_age_types_do_not_invent_calendar_conversion(
    age_type: str | None,
) -> None:
    basis = replace(BASIS, age_type=age_type)
    result = compare_bp_intervals(
        BpInterval(0, 1), BpInterval(0, 1), left_basis=basis, right_basis=basis
    )
    assert result.kind is TemporalRelationKind.NOT_COMPARABLE
    assert result.refusal_reason_code == "unsupported_or_unknown_age_type"


@pytest.mark.parametrize(
    "posture", ["numeric_interval_with_caveat", "mixed_interval_and_context"]
)
def test_caveated_basis_is_retained_in_the_relation(posture: str) -> None:
    basis = replace(BASIS, comparability_posture=posture)
    result = compare_bp_intervals(
        BpInterval(0, 1), BpInterval(0.25, 0.75), left_basis=BASIS, right_basis=basis
    )
    assert result.comparable and result.right_basis is basis
    assert result.right_basis.comparability_posture == posture


def test_reversed_input_is_refused_by_the_existing_canonical_constructor() -> None:
    with pytest.raises(InvalidBpIntervalError):
        BpInterval(2, 1)


@settings(max_examples=80, database=None)
@given(st.tuples(*(st.integers(0, 100000) for _ in range(4))))
def test_pair_direction_reverses_and_overlap_support_is_symmetric(
    values: tuple[int, int, int, int],
) -> None:
    a, b, c, d = (v / 4 for v in values)
    left, right = BpInterval(min(a, b), max(a, b)), BpInterval(min(c, d), max(c, d))
    forward = compare_bp_intervals(left, right, left_basis=BASIS, right_basis=BASIS)
    backward = compare_bp_intervals(right, left, left_basis=BASIS, right_basis=BASIS)
    reverse = {
        TemporalRelationKind.OVERLAPPING: TemporalRelationKind.OVERLAPPING,
        TemporalRelationKind.LEFT_OLDER: TemporalRelationKind.LEFT_YOUNGER,
        TemporalRelationKind.LEFT_YOUNGER: TemporalRelationKind.LEFT_OLDER,
    }
    assert backward.kind is reverse[forward.kind]
    assert backward.overlap_interval == forward.overlap_interval
    assert backward.separation_years == forward.separation_years


@settings(max_examples=80, database=None)
@given(st.tuples(*(st.integers(0, 100000) for _ in range(5))))
def test_translation_preserves_relation_without_rounding_fractional_support(
    values: tuple[int, int, int, int, int],
) -> None:
    a, b, c, d, delta = (v / 4 for v in values)
    left, right = BpInterval(min(a, b), max(a, b)), BpInterval(min(c, d), max(c, d))
    result = compare_bp_intervals(left, right, left_basis=BASIS, right_basis=BASIS)
    shifted = compare_bp_intervals(
        BpInterval(left.younger_bp + delta, left.older_bp + delta),
        BpInterval(right.younger_bp + delta, right.older_bp + delta),
        left_basis=BASIS,
        right_basis=BASIS,
    )
    assert result.kind is shifted.kind
    assert result.separation_years == shifted.separation_years
    if result.overlap_interval is not None:
        assert shifted.overlap_interval == BpInterval(
            result.overlap_interval.younger_bp + delta,
            result.overlap_interval.older_bp + delta,
        )


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (None, BpInterval(0, 0), TemporalRelationKind.NOT_COMPARABLE),
        (BpInterval(0, 0), None, TemporalRelationKind.NOT_COMPARABLE),
        (BpInterval(0, 0), BpInterval(0, 0), TemporalRelationKind.OVERLAPPING),
        (BpInterval(0, 0.25), BpInterval(0.25, 0.5), TemporalRelationKind.OVERLAPPING),
        (BpInterval(0, 0.25), BpInterval(0.5, 1), TemporalRelationKind.LEFT_YOUNGER),
        (BpInterval(0.5, 1), BpInterval(0, 0.25), TemporalRelationKind.LEFT_OLDER),
    ],
)
def test_algebraic_kind_api_preserves_missing_touching_and_fractional_bounds(
    left: BpInterval | None,
    right: BpInterval | None,
    expected: TemporalRelationKind,
) -> None:
    from bijux_pollenomics.core.chronology.relations import bp_interval_relation_kind

    assert bp_interval_relation_kind(left, right) is expected
    if left is not None and right is not None:
        assert closed_bp_intervals_overlap(left, right) is (
            expected is TemporalRelationKind.OVERLAPPING
        )
