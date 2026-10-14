"""Typed pair relations for explicitly compatible calendar ages and interval algebra."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .temporal_semantics import BpInterval

__all__ = [
    "TemporalComparisonBasis",
    "TemporalRelation",
    "TemporalRelationKind",
    "compare_bp_intervals",
    "bp_interval_relation_kind",
]


class TemporalRelationKind(StrEnum):
    """The direction of one eligible pair, or an explicit refusal to compare."""

    OVERLAPPING = "overlapping"
    LEFT_YOUNGER = "left_younger"
    LEFT_OLDER = "left_older"
    NOT_COMPARABLE = "not_comparable"


@dataclass(frozen=True)
class TemporalComparisonBasis:
    """Explicit source assertions; constructing this value authenticates no source.

    Epoch is a calendar CE year, never inferred from a BP label or publication.
    Unknown, radiocarbon, contextual and refused assertions remain distinct.
    """

    age_type: str | None
    reference_epoch_ce: int | None
    comparability_posture: str | None
    refusal_reason_code: str = ""


@dataclass(frozen=True)
class TemporalRelation:
    """A returned typed relation retaining original intervals and supplied bases.

    This value is not a JSON decoder or a source-authentication boundary.
    """

    kind: TemporalRelationKind
    left_interval: BpInterval | None
    right_interval: BpInterval | None
    overlap_interval: BpInterval | None = None
    separation_years: float | None = None
    left_basis: TemporalComparisonBasis | None = None
    right_basis: TemporalComparisonBasis | None = None
    refusal_reason_code: str = ""

    @property
    def comparable(self) -> bool:
        return (
            isinstance(self.kind, TemporalRelationKind)
            and self.kind is not TemporalRelationKind.NOT_COMPARABLE
        )


def compare_bp_intervals(
    left: BpInterval | None,
    right: BpInterval | None,
    *,
    left_basis: TemporalComparisonBasis | None = None,
    right_basis: TemporalComparisonBasis | None = None,
) -> TemporalRelation:
    """Compare explicit compatible calendar ages without guessing source eligibility.

    Matching explicit integer CE epochs and numeric comparability postures are
    required. Other age systems need their own governed transformation before
    they can use this calendar-year relation. Native assertions are retained;
    this function performs no conversion, calibration or source authentication.
    """
    reason = ""
    numeric_postures = {
        "numeric_interval",
        "numeric_interval_with_caveat",
        "mixed_interval_and_context",
    }
    if left is None or right is None:
        reason = "missing_interval"
    elif left_basis is None or right_basis is None:
        reason = "missing_comparison_basis"
    elif left_basis.refusal_reason_code or right_basis.refusal_reason_code:
        reason = "source_refused"
    elif (
        left_basis.comparability_posture not in numeric_postures
        or right_basis.comparability_posture not in numeric_postures
    ):
        reason = "non_numeric_comparability_posture"
    elif left_basis.age_type != right_basis.age_type:
        reason = "incomparable_age_types"
    elif left_basis.age_type != "calendar_bp":
        reason = "unsupported_or_unknown_age_type"
    elif (
        type(left_basis.reference_epoch_ce) is not int
        or type(right_basis.reference_epoch_ce) is not int
    ):
        reason = "unknown_reference_epoch"
    elif left_basis.reference_epoch_ce != right_basis.reference_epoch_ce:
        reason = "reference_epoch_mismatch"
    if reason:
        return TemporalRelation(
            TemporalRelationKind.NOT_COMPARABLE,
            left,
            right,
            left_basis=left_basis,
            right_basis=right_basis,
            refusal_reason_code=reason,
        )
    return _algebraic_bp_relation(
        left, right, left_basis=left_basis, right_basis=right_basis
    )


def _algebraic_bp_relation(
    left: BpInterval | None,
    right: BpInterval | None,
    *,
    left_basis: TemporalComparisonBasis | None = None,
    right_basis: TemporalComparisonBasis | None = None,
) -> TemporalRelation:
    """Classify already canonical values; this algebra does not admit source ages."""
    kind = bp_interval_relation_kind(left, right)
    if kind is TemporalRelationKind.NOT_COMPARABLE:
        return TemporalRelation(
            kind,
            left,
            right,
            left_basis=left_basis,
            right_basis=right_basis,
            refusal_reason_code="missing_interval",
        )
    assert left is not None and right is not None
    if kind is TemporalRelationKind.LEFT_YOUNGER:
        return TemporalRelation(
            kind,
            left,
            right,
            separation_years=right.younger_bp - left.older_bp,
            left_basis=left_basis,
            right_basis=right_basis,
        )
    if kind is TemporalRelationKind.LEFT_OLDER:
        return TemporalRelation(
            kind,
            left,
            right,
            separation_years=left.younger_bp - right.older_bp,
            left_basis=left_basis,
            right_basis=right_basis,
        )
    return TemporalRelation(
        kind,
        left,
        right,
        overlap_interval=BpInterval(
            max(left.younger_bp, right.younger_bp),
            min(left.older_bp, right.older_bp),
        ),
        separation_years=0.0,
        left_basis=left_basis,
        right_basis=right_basis,
    )


def bp_interval_relation_kind(
    left: BpInterval | None, right: BpInterval | None
) -> TemporalRelationKind:
    """Return a typed relation for canonical closed intervals as algebra only.

    This classifier requires already validated intervals, permits fractional
    endpoints and authenticates no source age type, epoch or comparability.
    Source-aware callers use compare_bp_intervals with explicit bases.
    """
    if left is None or right is None:
        return TemporalRelationKind.NOT_COMPARABLE
    if left.older_bp < right.younger_bp:
        return TemporalRelationKind.LEFT_YOUNGER
    if right.older_bp < left.younger_bp:
        return TemporalRelationKind.LEFT_OLDER
    return TemporalRelationKind.OVERLAPPING
