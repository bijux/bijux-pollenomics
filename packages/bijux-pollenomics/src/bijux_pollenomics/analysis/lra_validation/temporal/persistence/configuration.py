"""Typed synthetic older reconstruction and separately declared younger support."""

from __future__ import annotations

from dataclasses import dataclass

from ...contracts import Fold, ValidationRefusal, canonical_json, manifest_sha256
from ...experiments.configuration import (
    FITTED_METHOD,
    FITTED_PROFILE,
    TEMPORAL_PROFILE,
    FittedSpatialExperimentSpec,
    identity,
    object_list,
    object_mapping,
)
from ...splits import grouped_leave_one_out
from ..contracts import (
    CalendarSupport,
    RecordChronology,
    TemporalAdmissionPlan,
    _digest,
    _number,
)

PROFILE = TEMPORAL_PROFILE
METHOD = "no-change-persistence-v1"


@dataclass(frozen=True)
class YoungerCalendarBin:
    """A declared calendar bin; its boundaries never replace full age components."""

    bin_id: str
    younger_bp: float
    older_bp: float
    source_age_type: str = "calendar_bp"
    axis: str = "BP1950"

    def __post_init__(self) -> None:
        identity(self.bin_id)
        if (self.source_age_type, self.axis) != ("calendar_bp", "BP1950"):
            raise ValidationRefusal(
                "unsupported_temporal_age_type", "Require explicit calendar BP1950"
            )
        younger, older = _number(self.younger_bp), _number(self.older_bp)
        if younger > older:
            raise ValidationRefusal(
                "reversed_temporal_support", "Younger bin bound exceeds older"
            )
        object.__setattr__(self, "younger_bp", younger)
        object.__setattr__(self, "older_bp", older)

    def as_dict(self) -> dict[str, object]:
        return {
            "bin_id": self.bin_id,
            "younger_bp": self.younger_bp,
            "older_bp": self.older_bp,
            "source_age_type": self.source_age_type,
            "axis": self.axis,
        }


def _older_request(spec: FittedSpatialExperimentSpec) -> dict[str, object]:
    return {
        "schema_version": "lra-experiment.v1",
        "profile": FITTED_PROFILE,
        "sites": [
            {
                "record_id": site.record.record_id,
                "site_id": site.record.site_id,
                "identity_keys": site.record.identity_keys,
                "raw": {"path": site.raw.path, "sha256": site.raw.sha256},
                "geometry": {
                    "path": site.geometry.path,
                    "sha256": site.geometry.sha256,
                },
            }
            for site in spec.sites
        ],
        "regional_priority": spec.regional_priority,
        "local_ring_count": spec.local_ring_count,
        "local_support_radius_m": spec.local_support_radius_m,
        "support_profile": spec.support_profile,
        "request_template": spec.template(),
        "method": {
            "profile": FITTED_METHOD,
            "length_scale_km": spec.length_scale_km,
            "ridge_penalty": spec.ridge_penalty,
        },
    }


def _decode_plan(value: object) -> TemporalAdmissionPlan:
    row = object_mapping(value, "temporal_plan")
    outer = object_mapping(row["original_fold"], "original_fold")
    fold = Fold(
        identity(outer["fold_id"]),
        *(
            tuple(identity(key) for key in object_list(outer[field], field))
            for field in (
                "train_record_ids",
                "test_record_ids",
                "train_group_ids",
                "test_group_ids",
            )
        ),
    )
    ownership = object_mapping(row["record_groups"], "record_groups")
    chronologies = []
    for value in object_list(row["chronologies"], "chronologies"):
        item = object_mapping(value, "chronology")
        support = None
        if item["support"] is not None:
            declared = object_mapping(item["support"], "support")
            intervals = []
            for pair in object_list(declared["intervals_bp"], "intervals_bp"):
                interval = object_list(pair, "interval")
                if len(interval) != 2:
                    raise ValidationRefusal(
                        "invalid_temporal_support",
                        "Require complete younger/older components",
                    )
                intervals.append((_number(interval[0]), _number(interval[1])))
            support = CalendarSupport(
                tuple(intervals),
                identity(declared["chronology_manifest_sha256"]),
                identity(declared["chronology_model_id"]),
                identity(declared["source_age_type"]),
                identity(declared["axis"]),
            )
        chronologies.append(RecordChronology(identity(item["record_id"]), support))
    plan = TemporalAdmissionPlan(
        fold,
        tuple((record, identity(group)) for record, group in ownership.items()),
        tuple(chronologies),
        tuple(
            identity(key)
            for key in object_list(
                row["required_regional_record_ids"], "required_regional_record_ids"
            )
        ),
        _number(row["minimum_embargo_years"]),
        _number(row["maximum_lead_years"]),
        identity(row["decision_manifest_sha256"]),
        identity(row["declaration_provenance"]),
        identity(row["profile"]),
        identity(row["data_kind"]),
    )
    if canonical_json(plan.as_dict()) != canonical_json(row):
        raise ValidationRefusal(
            "temporal_plan_identity_mismatch",
            "Noncanonical or contradictory retained plan",
        )
    return plan


@dataclass(frozen=True)
class TemporalPersistenceSpec:
    """A distinct synthetic transport declaration; older requests keep their identity."""

    older_experiment: FittedSpatialExperimentSpec
    temporal_plan: TemporalAdmissionPlan
    younger_bin: YoungerCalendarBin
    assumption_manifest_sha256: str
    assumption_provenance: str

    def __post_init__(self) -> None:
        if (
            type(self.older_experiment) is not FittedSpatialExperimentSpec
            or not isinstance(self.temporal_plan, TemporalAdmissionPlan)
            or not isinstance(self.younger_bin, YoungerCalendarBin)
        ):
            raise ValidationRefusal(
                "invalid_temporal_persistence_spec",
                "Require typed older fitted experiment, temporal plan and younger bin",
            )
        _digest(self.assumption_manifest_sha256)
        identity(self.assumption_provenance)
        folds = grouped_leave_one_out(
            [site.record for site in self.older_experiment.sites]
        )
        plan = self.temporal_plan
        if plan.fold not in folds or len(plan.fold.test_record_ids) != 1:
            raise ValidationRefusal(
                "unsupported_temporal_target_fold",
                "Require one exact original whole-site singleton target fold",
            )
        ownership = {
            record: fold.test_group_ids[0]
            for fold in folds
            for record in fold.test_record_ids
        }
        if dict(plan.record_groups) != ownership:
            raise ValidationRefusal(
                "temporal_catalogue_mismatch",
                "Temporal ownership differs from the complete older catalogue",
            )
        if len(plan.required_regional_record_ids) != 1:
            raise ValidationRefusal(
                "unsupported_temporal_regional_sources",
                "First persistence profile requires one explicitly frozen regional anchor",
            )
        old_bin = self.older_bin()
        if old_bin.bin_id == self.younger_bin.bin_id:
            raise ValidationRefusal(
                "temporal_bin_identity_collision",
                "Older and younger bins require distinct identities",
            )

    def older_bin(self) -> YoungerCalendarBin:
        matching = object_mapping(
            self.older_experiment.template()["temporal_matching"], "temporal_matching"
        )
        bins = object_list(matching["bins"], "bins")
        if matching.get("rule") != "declared_bin_stationarity" or len(bins) != 1:
            raise ValidationRefusal(
                "unsupported_temporal_older_bin",
                "Older reconstruction requires one explicit stationarity bin",
            )
        row = object_mapping(bins[0], "bin")
        if set(row) != {"bin_id", "younger_bp", "older_bp"}:
            raise ValidationRefusal(
                "invalid_temporal_bin", "Require exact declared older bin fields"
            )
        return YoungerCalendarBin(
            identity(row["bin_id"]),
            _number(row["younger_bp"]),
            _number(row["older_bp"]),
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": "lra-temporal-persistence.v1",
            "profile": PROFILE,
            "data_kind": "synthetic",
            "purpose": "exploratory",
            "older_experiment": _older_request(self.older_experiment),
            "temporal_plan": self.temporal_plan.as_dict(),
            "younger_bin": self.younger_bin.as_dict(),
            "assumption": {
                "profile": METHOD,
                "manifest_sha256": self.assumption_manifest_sha256,
                "provenance": self.assumption_provenance,
                "scientific_approval": "not_verified",
            },
        }

    @property
    def sha256(self) -> str:
        return manifest_sha256(self.as_dict())

    @classmethod
    def from_dict(cls, payload: object) -> TemporalPersistenceSpec:
        try:
            row = object_mapping(payload, "temporal persistence")
            younger = object_mapping(row["younger_bin"], "younger_bin")
            assumption = object_mapping(row["assumption"], "assumption")
            result = cls(
                FittedSpatialExperimentSpec(
                    object_mapping(row["older_experiment"], "older_experiment")
                ),
                _decode_plan(row["temporal_plan"]),
                YoungerCalendarBin(
                    identity(younger["bin_id"]),
                    _number(younger["younger_bp"]),
                    _number(younger["older_bp"]),
                    identity(younger["source_age_type"]),
                    identity(younger["axis"]),
                ),
                identity(assumption["manifest_sha256"]),
                identity(assumption["provenance"]),
            )
            if canonical_json(result.as_dict()) != canonical_json(row):
                raise ValidationRefusal(
                    "temporal_persistence_identity_mismatch",
                    "Retained spec differs from its exact typed declaration",
                )
            return result
        except ValidationRefusal:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationRefusal(
                "invalid_temporal_persistence_spec", str(exc)
            ) from exc
