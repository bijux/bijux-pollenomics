"""Explicit synthetic calendar supports and an unchanged original site Fold."""

from __future__ import annotations

from dataclasses import dataclass
import re

from ..contracts import (
    Fold,
    TrainingAdmission,
    ValidationRefusal,
    canonical_json,
    finite_number,
    identity_values,
    manifest_sha256,
    required_identity,
)

PROFILE = "synthetic-forward-time-training-admission-v1"
MAX_COMPONENT_PAIRS = 100_000


def _number(value: object) -> float:
    number = finite_number(value)
    if type(value) is int and int(number) != value:
        raise ValidationRefusal(
            "inexact_temporal_coordinate",
            "Integer calendar support is not exactly representable",
        )
    return number


def _digest(value: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValidationRefusal("invalid_temporal_provenance", "Expected exact SHA-256")
    return value


@dataclass(frozen=True)
class CalendarSupport:
    """Preserve each supplied interval component; do not select or merge alternatives."""

    intervals_bp: tuple[tuple[float, float], ...]
    chronology_manifest_sha256: str
    chronology_model_id: str
    source_age_type: str = "calendar_bp"
    axis: str = "BP1950"

    def __post_init__(self) -> None:
        if (self.source_age_type, self.axis) != ("calendar_bp", "BP1950"):
            raise ValidationRefusal(
                "unsupported_temporal_age_type",
                "Synthetic calendar_bp on BP1950 is required; no conversion is implicit",
            )
        _digest(self.chronology_manifest_sha256)
        required_identity(self.chronology_model_id)
        if (
            not isinstance(self.intervals_bp, tuple)
            or not 1 <= len(self.intervals_bp) <= 32
        ):
            raise ValidationRefusal(
                "invalid_temporal_support", "Require 1–32 explicit interval components"
            )
        values = []
        for interval in self.intervals_bp:
            if not isinstance(interval, tuple) or len(interval) != 2:
                raise ValidationRefusal(
                    "invalid_temporal_support", "Expected younger/older pairs"
                )
            younger, older = (_number(value) for value in interval)
            if younger > older:
                raise ValidationRefusal(
                    "reversed_temporal_support", "Younger BP exceeds older BP"
                )
            values.append((younger, older))
        object.__setattr__(self, "intervals_bp", tuple(values))

    def as_dict(self) -> dict[str, object]:
        return {
            "intervals_bp": self.intervals_bp,
            "source_age_type": self.source_age_type,
            "axis": self.axis,
            "chronology_manifest_sha256": self.chronology_manifest_sha256,
            "chronology_model_id": self.chronology_model_id,
        }


@dataclass(frozen=True)
class RecordChronology:
    """An exact catalogue record with typed support or explicitly missing support."""

    record_id: str
    support: CalendarSupport | None

    def __post_init__(self) -> None:
        required_identity(self.record_id)
        if self.support is not None and not isinstance(self.support, CalendarSupport):
            raise ValidationRefusal(
                "invalid_temporal_support", "Require typed support or None"
            )

    def as_dict(self) -> dict[str, object]:
        return {
            "record_id": self.record_id,
            "support": None if self.support is None else self.support.as_dict(),
        }


@dataclass(frozen=True)
class TemporalAdmissionPlan:
    """Bounded caller declarations, not authentication of chronology or review."""

    fold: Fold
    record_groups: tuple[tuple[str, str], ...]
    chronologies: tuple[RecordChronology, ...]
    required_regional_record_ids: tuple[str, ...]
    minimum_embargo_years: float
    maximum_lead_years: float
    decision_manifest_sha256: str
    declaration_provenance: str
    profile: str = PROFILE
    data_kind: str = "synthetic"

    def __post_init__(self) -> None:
        if self.profile != PROFILE or self.data_kind != "synthetic":
            raise ValidationRefusal(
                "unsupported_temporal_profile",
                "Only the explicit synthetic admission profile is supported",
            )
        if not isinstance(self.fold, Fold):
            raise ValidationRefusal(
                "invalid_temporal_fold", "Require the original typed Fold"
            )
        # Reuse the sole canonical record/group authority; this temporary identity
        # check is not an admissibility decision and never opens observations.
        membership = TrainingAdmission(
            self.fold,
            self.record_groups,
            self.fold.train_group_ids,
            canonical_json({"profile": PROFILE}),
        )
        object.__setattr__(self, "record_groups", membership.record_groups)
        if (
            not isinstance(self.chronologies, tuple)
            or not 1 <= len(self.chronologies) <= 1000
            or any(not isinstance(row, RecordChronology) for row in self.chronologies)
        ):
            raise ValidationRefusal(
                "invalid_temporal_catalogue", "Require 1–1000 typed chronology rows"
            )
        expected = {*self.fold.train_record_ids, *self.fold.test_record_ids}
        if (
            len({row.record_id for row in self.chronologies}) != len(self.chronologies)
            or {row.record_id for row in self.chronologies} != expected
        ):
            raise ValidationRefusal(
                "temporal_catalogue_mismatch",
                "Every original record needs exactly one explicit chronology row",
            )
        if not isinstance(self.required_regional_record_ids, tuple):
            raise ValidationRefusal(
                "invalid_temporal_regional_sources",
                "Require explicit regional record tuple",
            )
        regional = identity_values(self.required_regional_record_ids)
        if (
            not regional
            or len(set(regional)) != len(regional)
            or not set(regional).issubset(self.fold.train_record_ids)
        ):
            raise ValidationRefusal(
                "invalid_temporal_regional_sources",
                "Required regional observations must name unique original training records",
            )
        embargo, lead = (
            _number(self.minimum_embargo_years),
            _number(self.maximum_lead_years),
        )
        if embargo < 0 or lead <= 0 or embargo > lead:
            raise ValidationRefusal(
                "invalid_temporal_lead_policy",
                "Require 0 <= embargo <= positive maximum lead",
            )
        _digest(self.decision_manifest_sha256)
        required_identity(self.declaration_provenance)
        components = {
            row.record_id: len(row.support.intervals_bp)
            if row.support is not None
            else 1
            for row in self.chronologies
        }
        pairs = sum(components[r] for r in self.fold.train_record_ids) * sum(
            components[r] for r in self.fold.test_record_ids
        )
        if pairs > MAX_COMPONENT_PAIRS:
            raise ValidationRefusal(
                "temporal_comparison_budget_exceeded",
                "More than 100000 component comparisons or unresolved support pairs requested",
            )
        object.__setattr__(
            self,
            "chronologies",
            tuple(sorted(self.chronologies, key=lambda row: row.record_id)),
        )
        object.__setattr__(
            self, "required_regional_record_ids", tuple(sorted(regional))
        )
        object.__setattr__(self, "minimum_embargo_years", embargo)
        object.__setattr__(self, "maximum_lead_years", lead)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "lra-temporal-admission-plan.v1",
            "profile": self.profile,
            "data_kind": self.data_kind,
            "original_fold": self.fold.as_dict(),
            "record_groups": dict(self.record_groups),
            "chronologies": [row.as_dict() for row in self.chronologies],
            "required_regional_record_ids": self.required_regional_record_ids,
            "minimum_embargo_years": self.minimum_embargo_years,
            "maximum_lead_years": self.maximum_lead_years,
            "decision_manifest_sha256": self.decision_manifest_sha256,
            "declaration_provenance": self.declaration_provenance,
            "source_age_authenticity": "not_verified",
            "reviewer_approval": "not_verified",
        }

    @property
    def sha256(self) -> str:
        return manifest_sha256(self.as_dict())
