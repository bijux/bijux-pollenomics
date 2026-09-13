"""Retrospective readiness projection; never retroactively freeze a final experiment."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json

from ..contracts import ValidationRefusal, canonical_json, manifest_sha256
from ..experiments.configuration import identity, object_list, object_mapping
from ..experiments.reading.scores import ScoredExperimentEvidence
from .contracts import EvaluationScope


@dataclass(frozen=True)
class EvaluationAdapterAudit:
    """Immutable accounting and explicit gaps, not a final-evaluation result."""

    canonical_audit_json: str
    audit_sha256: str

    def __post_init__(self) -> None:
        try:
            value = object_mapping(json.loads(self.canonical_audit_json), "audit")
            if (
                canonical_json(value) != self.canonical_audit_json
                or manifest_sha256(value) != self.audit_sha256
                or value["schema_version"] != "pollenomics-evaluation-adapter-audit.v1"
                or value["final_evaluation_performed"] is not False
                or value["scientific_acceptance"] != "not_evaluated"
            ):
                raise ValueError("Unsupported readiness identity/posture")
        except (KeyError, ValueError, TypeError) as exc:
            raise ValidationRefusal(
                "invalid_evaluation_adapter_audit", str(exc)
            ) from exc


def audit_scored_evaluation_readiness(
    evidence: tuple[ScoredExperimentEvidence, ...],
    *,
    scope: EvaluationScope | None = None,
    frozen_evaluation_binding: Mapping[str, object] | None = None,
) -> EvaluationAdapterAudit:
    """Account for every retained target and identify prerequisites without approval.

    An optional future binding is retained only as an unverified declaration. This
    retrospective protocol cannot prove its chronology or repair absent timestamps.
    Original scopes remain unchanged; no folds or model identities are manufactured.
    """
    if not evidence:
        raise ValidationRefusal(
            "empty_scored_evidence", "At least one pinned score product is required"
        )
    seen: set[str] = set()
    rows: list[dict[str, object]] = []
    products: list[dict[str, object]] = []
    for item in evidence:
        checked = ScoredExperimentEvidence(
            item.canonical_evidence_json, item.evidence_sha256
        )
        value = object_mapping(json.loads(checked.canonical_evidence_json), "evidence")
        digest = identity(value["score_manifest_sha256"])
        if digest in seen:
            raise ValidationRefusal("duplicate_scored_evidence", digest)
        seen.add(digest)
        units = [
            object_mapping(unit, "unit")
            for unit in object_list(value["units"], "units")
        ]
        if value["requested_units"] != len(units) or not units:
            raise ValidationRefusal(
                "invalid_scored_evidence", "Incomplete requested unit ledger"
            )
        folds = [
            object_mapping(fold, "fold")
            for fold in object_list(value["folds"], "folds")
        ]
        original_targets = {
            identity(record)
            for fold in folds
            for record in object_list(fold["test_record_ids"], "test records")
        }
        gaps = [
            "retrospective_products_have_no_prospective_evaluator_binding",
            "first_outcome_access_utc_not_retained",
            "synthetic_observations_are_not_independent_measured_vegetation",
            "observational_support_reference_and_source_age_profile_not_admitted",
            "qualified_nonnull_policy_and_review_provenance_not_verified",
            "predictive_observation_intervals_not_bound",
        ]
        if scope is None:
            gaps.append("evaluation_scope_not_supplied")
        else:
            supplied_targets = {
                record for fold in scope.folds for record in fold.test_record_ids
            }
            if supplied_targets != original_targets:
                gaps.append("declared_scope_target_universe_differs")
            if canonical_json(
                [fold.as_dict() for fold in scope.folds]
            ) != canonical_json(folds):
                gaps.append("declared_scope_original_fold_identity_differs")
        if len(folds) != 1:
            bootstrap = (
                "refused_overlapping_training_folds_not_fixed_model_external_cohort"
            )
        elif len(original_targets) < 2:
            bootstrap = "refused_fewer_than_two_independent_test_units"
        else:
            bootstrap = "unverified_fixed_model_training_and_independent_support"
        products.append(
            {
                "score_manifest_sha256": digest,
                "evidence_sha256": checked.evidence_sha256,
                "prediction_manifest_sha256": value["prediction_manifest_sha256"],
                "profile": value["profile"],
                "requested_units": len(units),
                "readiness_gaps": gaps,
                "fixed_model_resampling_eligibility": bootstrap,
            }
        )
        for unit in units:
            target = identity(unit["target"])
            if target not in {"vegetation_cover", "pollen_composition"}:
                raise ValidationRefusal("invalid_scored_evidence", "Unknown target")
            rows.append(
                {
                    "score_manifest_sha256": digest,
                    "prediction_manifest_sha256": value["prediction_manifest_sha256"],
                    "fold_id": unit["fold_id"],
                    "record_id": unit["record_id"],
                    "group_id": unit["group_id"],
                    "method_id": unit["method_id"],
                    "target": target,
                    "status": unit["status"],
                    "evaluation_role": unit["evaluation_role"],
                    "heldout_target_kind": unit["eligible_target_kind"],
                    "source_metric": unit["metric"],
                    "composition_error_unit": "fraction",
                    "final_eligibility": "ineligible",
                    "eligibility_reasons": gaps
                    + (
                        []
                        if unit["eligible_target_kind"] is True
                        else ["in_sample_pollen_diagnostic_not_heldout_pollen"]
                    ),
                }
            )
    counts = {}
    for target in ("vegetation_cover", "pollen_composition"):
        selected = [row for row in rows if row["target"] == target]
        statuses = sorted({identity(row["status"]) for row in selected})
        counts[target] = {
            "requested": len(selected),
            "by_status": {
                status: sum(row["status"] == status for row in selected)
                for status in statuses
            },
            "in_sample_diagnostics": sum(
                row["heldout_target_kind"] is False for row in selected
            ),
        }
    payload = {
        "schema_version": "pollenomics-evaluation-adapter-audit.v1",
        "kind": "retrospective_readiness_only",
        "final_evaluation_performed": False,
        "scientific_acceptance": "not_evaluated",
        "review_authenticity_verified": False,
        "scope_sha256": None if scope is None else scope.scope_sha256,
        "split_sha256": None if scope is None else scope.split_sha256,
        "frozen_binding_declaration": None
        if frozen_evaluation_binding is None
        else dict(frozen_evaluation_binding),
        "frozen_binding_verification": "not_performed_no_prospective_protocol",
        "products": products,
        "rows": rows,
        "targets": counts,
        "uncertainty": "no_predictive_or_fixed_model_bootstrap_interval_inferred",
    }
    return EvaluationAdapterAudit(canonical_json(payload), manifest_sha256(payload))
