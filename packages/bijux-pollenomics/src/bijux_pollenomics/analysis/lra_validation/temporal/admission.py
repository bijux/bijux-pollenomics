"""Evaluate declared full calendar support without reading quantitative outcomes."""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
import json
from math import isfinite
from typing import cast

from ..contracts import (
    TrainingAdmission,
    ValidationRefusal,
    canonical_json,
    manifest_sha256,
)
from .contracts import CalendarSupport, TemporalAdmissionPlan


def _pairs(
    source: CalendarSupport,
    target: CalendarSupport,
    target_id: str,
    plan: TemporalAdmissionPlan,
) -> list[dict[str, object]]:
    pairs: list[dict[str, object]] = []
    for source_index, (source_young, source_old) in enumerate(source.intervals_bp):
        for target_index, (target_young, target_old) in enumerate(target.intervals_bp):
            minimum = source_young - target_old
            maximum = source_old - target_young
            reasons = []
            if not isfinite(minimum) or not isfinite(maximum):
                reasons.append("temporal_difference_out_of_range")
            else:
                exact_minimum = Fraction(source_young) - Fraction(target_old)
                exact_maximum = Fraction(source_old) - Fraction(target_young)
                if exact_minimum <= 0:
                    reasons.append("positive_temporal_order_not_established")
                if exact_minimum < Fraction(plan.minimum_embargo_years):
                    reasons.append("temporal_embargo_not_met")
                if exact_maximum > Fraction(plan.maximum_lead_years):
                    reasons.append("maximum_temporal_lead_exceeded")
            pairs.append(
                {
                    "target_record_id": target_id,
                    "source_component_index": source_index,
                    "target_component_index": target_index,
                    "minimum_lead_years": minimum if isfinite(minimum) else None,
                    "maximum_lead_years": maximum if isfinite(maximum) else None,
                    "eligible": not reasons,
                    "reason_codes": reasons,
                }
            )
    return pairs


def _record_rows(plan: TemporalAdmissionPlan) -> list[dict[str, object]]:
    supports = {row.record_id: row.support for row in plan.chronologies}
    rows: list[dict[str, object]] = []
    for record_id in plan.fold.train_record_ids:
        source = supports[record_id]
        comparisons: list[dict[str, object]] = []
        reasons: set[str] = set()
        if source is None:
            reasons.add("missing_training_chronology")
        for target_id in plan.fold.test_record_ids:
            target = supports[target_id]
            if target is None:
                reasons.add("missing_target_chronology")
            if source is None or target is None:
                comparisons.append(
                    {
                        "target_record_id": target_id,
                        "status": "unresolved",
                        "source_support_missing": source is None,
                        "target_support_missing": target is None,
                        "component_pairs": [],
                    }
                )
                continue
            pairs = _pairs(source, target, target_id, plan)
            for pair in pairs:
                reasons.update(cast(list[str], pair["reason_codes"]))
            comparisons.append(
                {
                    "target_record_id": target_id,
                    "status": "evaluated",
                    "source_support_missing": False,
                    "target_support_missing": False,
                    "component_pairs": pairs,
                }
            )
        rows.append(
            {
                "record_id": record_id,
                "eligible": not reasons,
                "reason_codes": sorted(reasons),
                "target_comparisons": comparisons,
            }
        )
    return rows


def _evaluate(
    plan: TemporalAdmissionPlan,
) -> tuple[dict[str, object], TrainingAdmission | None]:
    rows = _record_rows(plan)
    eligible_records = {cast(str, row["record_id"]) for row in rows if row["eligible"]}
    groups: list[dict[str, object]] = []
    eligible_groups = []
    for group in plan.fold.train_group_ids:
        members = tuple(
            record for record, owner in plan.record_groups if owner == group
        )
        excluded = tuple(record for record in members if record not in eligible_records)
        if not excluded:
            eligible_groups.append(group)
        groups.append(
            {
                "group_id": group,
                "record_ids": members,
                "eligible": not excluded,
                "individually_excluded_record_ids": excluded,
                "reason_codes": ["group_member_temporally_excluded"]
                if excluded
                else [],
            }
        )
    whole_records = tuple(
        record for record, group in plan.record_groups if group in eligible_groups
    )
    missing_regional = sorted(
        set(plan.required_regional_record_ids) - set(whole_records)
    )
    reasons = []
    if missing_regional:
        reasons.append("required_regional_source_excluded")
    if not eligible_groups:
        reasons.append("no_temporally_eligible_training_groups")
    usable = not reasons
    report: dict[str, object] = {
        "schema_version": "lra-temporal-admission-result.v1",
        "plan": plan.as_dict(),
        "plan_sha256": plan.sha256,
        "status": "admitted" if usable else "refused",
        "reason_codes": reasons,
        "numeric_profile": "exact-binary64-endpoint-comparison-v1",
        "reported_lead_values": "binary64-rounded; admission uses exact endpoint ratios",
        "minimum_lead_rule": "strictly_positive_and_at_least_declared_embargo",
        "maximum_lead_rule": "at_most_declared_maximum",
        "record_decisions": rows,
        "group_decisions": groups,
        "eligible_group_ids": eligible_groups,
        "eligible_record_ids": whole_records,
        "excluded_group_ids": sorted(
            set(plan.fold.train_group_ids) - set(eligible_groups)
        ),
        "excluded_record_ids": sorted(
            set(plan.fold.train_record_ids) - set(whole_records)
        ),
        "excluded_required_regional_record_ids": missing_regional,
        "denominators": {
            "training_records": len(plan.fold.train_record_ids),
            "training_groups": len(plan.fold.train_group_ids),
            "target_records": len(plan.fold.test_record_ids),
            "target_groups": len(plan.fold.test_group_ids),
            "individually_eligible_records": len(eligible_records),
            "individually_excluded_records": len(plan.fold.train_record_ids)
            - len(eligible_records),
            "whole_group_eligible_records": len(whole_records),
            "whole_group_excluded_records": len(plan.fold.train_record_ids)
            - len(whole_records),
            "eligible_groups": len(eligible_groups),
            "excluded_groups": len(plan.fold.train_group_ids) - len(eligible_groups),
            "usable_training_records": len(whole_records) if usable else 0,
            "usable_training_groups": len(eligible_groups) if usable else 0,
            "required_regional_records": len(plan.required_regional_record_ids),
            "excluded_required_regional_records": len(missing_regional),
        },
        "scope": {
            "quantitative_outcome_access": "none",
            "chronology_authenticity": "not_verified",
            "reviewer_approval": "not_verified",
            "prediction": "not_performed",
            "uncertainty_propagation": "not_performed",
            "spatial_support_admission": "not_performed",
        },
    }
    admission = None
    if usable:
        criterion = {
            "profile": plan.profile,
            "temporal_receipt": report,
            "temporal_receipt_sha256": manifest_sha256(report),
        }
        admission = TrainingAdmission(
            plan.fold,
            plan.record_groups,
            tuple(eligible_groups),
            canonical_json(criterion),
        )
    return report, admission


@dataclass(frozen=True)
class TemporalAdmissionResult:
    """An owned deterministic decision computed from a typed plan, not imported claims.

    Consumers must still validate the actual quantitative dependency closure with
    the shared ``assert_training_inputs`` authority using ``training_admission``.
    """

    plan: TemporalAdmissionPlan
    training_admission: TrainingAdmission | None = field(init=False)
    _report_json: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.plan, TemporalAdmissionPlan):
            raise ValidationRefusal(
                "invalid_temporal_plan", "Require a typed temporal admission plan"
            )
        report, admission = _evaluate(self.plan)
        report["training_admission"] = (
            admission.as_dict() if admission is not None else None
        )
        object.__setattr__(self, "training_admission", admission)
        object.__setattr__(self, "_report_json", canonical_json(report))

    def as_dict(self) -> dict[str, object]:
        """Return an independent mutable copy of the immutable decision receipt."""
        return cast(dict[str, object], json.loads(self._report_json))

    @property
    def sha256(self) -> str:
        return manifest_sha256(self.as_dict())

    def require_training_admission(self) -> TrainingAdmission:
        """Refuse unusable plans while retaining all exclusions in ``as_dict``."""
        if self.training_admission is None:
            raise ValidationRefusal(
                "temporal_training_unavailable",
                "Temporal decision has no usable training admission; inspect receipt",
            )
        return self.training_admission


def admit_forward_time_training(plan: TemporalAdmissionPlan) -> TemporalAdmissionResult:
    """Evaluate all component pairs and exclude entire original physical groups."""
    return TemporalAdmissionResult(plan)
