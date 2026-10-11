"""Explicit signed calendar support values; no source chronology conversion."""

from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
import math
from typing import Literal, Self

SIGNED_CALENDAR_PROFILE = "calendar-bp1950-signed.v1"
SupportKind = Literal[
    "closed_age_support", "declared_stationarity_envelope", "calendar_time_support"
]


def _number(value: object) -> int | float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Calendar endpoints require finite numeric values")
    if abs(value) > 2**53 - 1:
        raise ValueError("Calendar endpoint exceeds the supported browser domain")
    if not math.isfinite(value):
        raise ValueError("Calendar endpoint is not finite")
    return value


@dataclass(frozen=True)
class SignedCalendarSupport:
    """A typed BP1950 support preserving endpoint values and explicit closure.

    The calendar declaration is synthetic metadata. Neither this representation
    nor its null calibration fields assert source authentication or calibration.
    """

    younger_bp: int | float
    older_bp: int | float
    _: KW_ONLY
    support_kind: SupportKind
    younger_inclusive: bool = True
    older_inclusive: bool = True

    def __post_init__(self) -> None:
        _number(self.younger_bp)
        _number(self.older_bp)
        if self.support_kind not in (
            "closed_age_support",
            "declared_stationarity_envelope",
            "calendar_time_support",
        ):
            raise ValueError("Unsupported calendar support kind")
        if (
            type(self.younger_inclusive) is not bool
            or type(self.older_inclusive) is not bool
        ):
            raise ValueError("Calendar closure must be explicitly boolean")
        if self.younger_bp > self.older_bp:
            raise ValueError("Calendar support endpoints are reversed")
        if self.support_kind != "calendar_time_support" and not (
            self.younger_inclusive and self.older_inclusive
        ):
            raise ValueError("Age support and stationarity envelopes must be closed")
        if self.younger_bp == self.older_bp and not (
            self.younger_inclusive and self.older_inclusive
        ):
            raise ValueError("An open equal-endpoint calendar support is empty")

    def as_dict(self) -> dict[str, object]:
        """Return an independently owned exact wire object without numeric coercion."""
        return {
            "profile": SIGNED_CALENDAR_PROFILE,
            "axis": "BP1950",
            "source_age_type": "calendar_bp",
            "original_source_age_type": "calendar_bp",
            "support_kind": self.support_kind,
            "younger_bp": self.younger_bp,
            "older_bp": self.older_bp,
            "younger_inclusive": self.younger_inclusive,
            "older_inclusive": self.older_inclusive,
            "calibration_status": "not_recorded_in_saved_request",
            "calibration_evidence": None,
            "native_calendar_label": None,
            "native_calendar_convention": None,
        }

    @classmethod
    def from_dict(cls, value: object) -> Self:
        """Refuse missing, extra, relabelled or unsupported support declarations."""
        if not isinstance(value, dict):
            raise ValueError("Calendar support must be an object")
        kind = value.get("support_kind")
        if kind not in (
            "closed_age_support",
            "declared_stationarity_envelope",
            "calendar_time_support",
        ):
            raise ValueError("Unsupported calendar support kind")
        # Explicit narrowing preserves the closed typed support-kind domain.
        support_kind: SupportKind
        if kind == "closed_age_support":
            support_kind = "closed_age_support"
        elif kind == "declared_stationarity_envelope":
            support_kind = "declared_stationarity_envelope"
        else:
            support_kind = "calendar_time_support"
        younger_inclusive = value.get("younger_inclusive")
        older_inclusive = value.get("older_inclusive")
        if type(younger_inclusive) is not bool or type(older_inclusive) is not bool:
            raise ValueError("Calendar closure must be explicitly boolean")
        result = cls(
            _number(value.get("younger_bp")),
            _number(value.get("older_bp")),
            support_kind=support_kind,
            younger_inclusive=younger_inclusive,
            older_inclusive=older_inclusive,
        )
        if value != result.as_dict():
            raise ValueError("Calendar support fields or source posture disagree")
        return result

    def contains(self, value: int | float) -> bool:
        """Evaluate a point against actual endpoint closure without rounding."""
        point = _number(value)
        return (
            point > self.younger_bp
            or (point == self.younger_bp and self.younger_inclusive)
        ) and (
            point < self.older_bp or (point == self.older_bp and self.older_inclusive)
        )

    def overlaps(self, other: SignedCalendarSupport) -> bool:
        """Evaluate nonempty intersection, preserving touching-boundary closure."""
        if not isinstance(other, SignedCalendarSupport):
            raise ValueError("Calendar overlap requires typed support")
        lower = max(self.younger_bp, other.younger_bp)
        upper = min(self.older_bp, other.older_bp)
        return lower < upper or (
            lower == upper and self.contains(lower) and other.contains(lower)
        )


def optional_calendar_support(
    younger_bp: int | float | None,
    older_bp: int | float | None,
    *,
    support_kind: SupportKind,
    younger_inclusive: bool = True,
    older_inclusive: bool = True,
) -> SignedCalendarSupport | None:
    """Keep complete absence separate from partial/refused support and BP zero."""
    if younger_bp is None and older_bp is None:
        return None
    if younger_bp is None or older_bp is None:
        raise ValueError("Calendar support is partially absent")
    return SignedCalendarSupport(
        younger_bp,
        older_bp,
        support_kind=support_kind,
        younger_inclusive=younger_inclusive,
        older_inclusive=older_inclusive,
    )


__all__ = [
    "SIGNED_CALENDAR_PROFILE",
    "SignedCalendarSupport",
    "SupportKind",
    "optional_calendar_support",
]
