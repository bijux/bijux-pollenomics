"""Authenticate spatial-block conditional intervals before outcome access."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import cast

from ...lra.engine.discovery import load_engine
from ...lra.outputs.identity import capture_code_identity
from ..contracts import finite_number, manifest_sha256
from ..experiments.configuration import (
    BLOCK_BASELINE_METHOD,
    BLOCK_PROFILE,
    FITTED_METHOD,
    identity,
    object_list,
    object_mapping,
)
from ..experiments.outputs import read_experiment_product, read_member
from ..observation_uncertainty.block_contracts import (
    BLOCK_OBSERVATION_PROFILE,
    BlockObservationUncertaintyPlan,
)
from ..observation_uncertainty.block_workflow import (
    _validate_counting_design,
    validate_block_plan_parent,
)
from ..observation_uncertainty.workflow import implementation_identity
from .contracts import (
    EvaluationRow,
    PredictiveInterval,
    _authenticated_source_model,
    digest,
    freeze_evaluation_prediction,
    refuse,
)

AUTHENTICATED_BLOCK_CONDITIONAL_INTERVAL_PROFILE = (
    "pollenomics-authenticated-spatial-block-conditional-observation.v1"
)

_BLOCK_UNCERTAINTY_PAYLOAD_FIELDS = {
    "schema_version",
    "profile",
    "plan",
    "plan_sha256",
    "prediction_manifest_sha256",
    "prediction_scientific_content_sha256",
    "rows",
    "requested_units",
    "parent_status_counts",
    "status_counts",
    "effort_evidence",
    "engine_identity",
    "implementation",
    "access_order",
    "outcome_accesses",
    "declaration_timing_authenticated",
    "empirical_coverage_verified",
    "scientific_acceptance",
    "final_policy_approval",
    "uncertainty_scope",
    "conditioned_on",
}

_BLOCK_UNCERTAINTY_ACCESS_ORDER = [
    "authenticate_block_parent",
    "verify_complete_fold_record_method_plan",
    "read_predeclared_counting_design",
    "load_engine",
    "conditional_sampling",
]


def _authenticated_block_draws(
    predictions: Path,
    *,
    expected_prediction_manifest_sha256: str,
    uncertainty: Path,
    expected_uncertainty_manifest_sha256: str,
) -> tuple[
    BlockObservationUncertaintyPlan,
    dict[tuple[str, str, str], dict[str, object]],
    dict[tuple[str, str, str], dict[str, object]],
]:
    expected_parent = digest(expected_prediction_manifest_sha256)
    expected_uncertainty = digest(expected_uncertainty_manifest_sha256)
    product, manifest = read_experiment_product(
        uncertainty, expected_manifest_sha256=expected_uncertainty
    )
    payload = object_mapping(manifest["scientific_payload"], "uncertainty")
    plan = BlockObservationUncertaintyPlan.from_dict(payload.get("plan"))
    parent, parent_manifest, parent_rows, parent_statuses = validate_block_plan_parent(
        predictions, plan
    )
    rows = object_list(read_member(product, "uncertainty.json"), "uncertainty")
    evidence = object_mapping(
        read_member(product, "effort_evidence.json"), "effort_evidence"
    )
    if (
        set(payload) != _BLOCK_UNCERTAINTY_PAYLOAD_FIELDS
        or parent.manifest_sha256 != expected_parent
        or plan.prediction_manifest_sha256 != expected_parent
        or parent_manifest["profile"] != BLOCK_PROFILE
        or manifest["phase"] != "observation_uncertainty"
        or manifest["profile"] != BLOCK_PROFILE
        or payload.get("schema_version")
        != "lra-spatial-block-observation-uncertainty.v1"
        or payload.get("profile") != BLOCK_OBSERVATION_PROFILE
        or payload.get("plan_sha256") != plan.sha256
        or payload.get("prediction_manifest_sha256") != parent.manifest_sha256
        or payload.get("prediction_scientific_content_sha256")
        != parent.scientific_content_sha256
        or payload.get("uncertainty_scope") != "conditional_observation_process_only"
        or payload.get("conditioned_on")
        != [
            "fixed_predicted_pollen_probabilities",
            "predeclared_sampling_effort",
        ]
        or payload.get("outcome_accesses") != []
        or payload.get("declaration_timing_authenticated") is not False
        or payload.get("empirical_coverage_verified") is not False
        or payload.get("scientific_acceptance") != "not_evaluated"
        or payload.get("final_policy_approval") is not False
        or rows != payload.get("rows")
        or evidence != payload.get("effort_evidence")
        or manifest_sha256(read_member(product, "plan.json")) != plan.sha256
        or len(rows) != len(plan.entries)
        or payload.get("requested_units") != len(plan.entries)
    ):
        refuse("Block uncertainty product, parent or non-acceptance posture differs")
    expected_parent_counts = {
        status: sum(value == status for value in parent_statuses.values())
        for status in ("predicted", "refused", "not_run")
    }
    if payload.get("parent_status_counts") != expected_parent_counts:
        refuse("Block uncertainty parent denominator counts differ")
    binding = load_engine()
    if (
        payload.get("engine_identity") != capture_code_identity(binding).payload()
        or payload.get("implementation") != implementation_identity()
        or payload.get("access_order") != _BLOCK_UNCERTAINTY_ACCESS_ORDER
    ):
        refuse("Block uncertainty implementation or access provenance differs")
    retained: dict[tuple[str, str, str], dict[str, object]] = {}
    for entry, value in zip(plan.entries, rows, strict=True):
        row = object_mapping(value, "uncertainty_row")
        if manifest_sha256(row.get("entry")) != manifest_sha256(entry.as_dict()):
            refuse("Block uncertainty row differs from its plan entry")
        parent_status = parent_statuses[entry.key]
        parent_row = parent_rows.get(entry.key)
        parent_sha256 = (
            None if parent_row is None else parent_row["prediction_manifest_sha256"]
        )
        if (
            row.get("parent_status") != parent_status
            or row.get("prediction_sha256") != parent_sha256
        ):
            refuse("Block uncertainty row belongs to another parent unit")
        status = row.get("status")
        if status not in {
            "generated",
            "parent_refused",
            "parent_not_run",
            "effort_refused",
            "sampler_refused",
            "not_run",
        }:
            refuse("Unsupported block uncertainty status")
        base_fields = {
            "entry",
            "parent_status",
            "prediction_sha256",
            "engine_result",
            "engine_result_sha256",
            "engine_result_canonical_json",
            "status",
        }
        expected_fields = set(base_fields)
        if status in {"parent_refused", "parent_not_run", "not_run"}:
            expected_fields.add("reason_code")
        elif status in {"effort_refused", "sampler_refused"}:
            expected_fields.update(("reason_code", "detail"))
        if set(row) != expected_fields:
            refuse("Block uncertainty row contains undeclared fields")
        reason = row.get("reason_code")
        if (
            (status == "parent_refused" and reason != "parent_prediction_refused")
            or (status == "parent_not_run" and reason != "parent_prediction_not_run")
            or (status == "not_run" and reason != "observation_generation_interrupted")
            or (
                status in {"effort_refused", "sampler_refused"}
                and (not isinstance(reason, str) or not reason)
            )
            or (
                "detail" in expected_fields
                and (not isinstance(row.get("detail"), str) or not row["detail"])
            )
        ):
            refuse("Block uncertainty status detail differs")
        if (
            (parent_status == "refused" and status != "parent_refused")
            or (parent_status == "not_run" and status != "parent_not_run")
            or (
                parent_status == "predicted"
                and status in {"parent_refused", "parent_not_run"}
            )
        ):
            refuse("Uncertainty status contradicts the exact parent status")
        if status != "generated":
            if any(
                row.get(field) is not None
                for field in (
                    "engine_result",
                    "engine_result_sha256",
                    "engine_result_canonical_json",
                )
            ):
                refuse("A refused block uncertainty row cannot retain draws")
            retained[entry.key] = row
            continue
        if parent_row is None or parent_status != "predicted":
            refuse("Conditional block draws require a generated parent prediction")
        design = object_mapping(evidence.get(entry.evidence_sha256), "effort_evidence")
        _validate_counting_design(design, entry)
        canonical = row.get("engine_result_canonical_json")
        result_sha256 = row.get("engine_result_sha256")
        if not isinstance(canonical, str) or not isinstance(result_sha256, str):
            refuse("Generated block uncertainty requires canonical draw identities")
        try:
            result = binding.api.PollenObservationDraws(
                canonical, digest(result_sha256)
            ).as_dict()
        except (ValueError, TypeError, AttributeError) as exc:
            refuse(f"Invalid governed block conditional result: {exc}")
        declaration = object_mapping(result["declaration"], "declaration")
        pollen = object_mapping(parent_row["pollen_fraction"], "pollen_fraction")
        expected_declaration = {
            "prediction_sha256": parent_sha256,
            "effort_evidence_sha256": entry.evidence_sha256,
            "effort": entry.effort,
            "seed": entry.seed,
            "repeats": plan.repeats,
            "coverage": plan.coverage,
            "taxa": list(entry.taxa),
            "input_pollen_fraction": pollen,
        }
        if (
            row.get("engine_result") != result
            or any(
                declaration.get(key) != expected_value
                for key, expected_value in expected_declaration.items()
            )
            or result.get("interval_kind") != "conditional_predictive_observation"
            or result.get("propagated_sources") != ["observation_process"]
            or result.get("conditioned_on")
            != ["fixed_pollen_probabilities", "predeclared_sampling_effort"]
            or result.get("empirical_coverage_verified") is not False
            or result.get("scientific_acceptance") != "not_evaluated"
        ):
            refuse("Block conditional result scope or denominator differs")
        retained[entry.key] = row
    statuses = sorted({cast(str, row["status"]) for row in retained.values()})
    if payload.get("status_counts") != {
        status: sum(row["status"] == status for row in retained.values())
        for status in statuses
    }:
        refuse("Block uncertainty status counts differ from the retained denominator")
    return plan, parent_rows, retained


def freeze_authenticated_block_pollen_interval(
    row: EvaluationRow,
    *,
    predictions: Path,
    expected_prediction_manifest_sha256: str,
    uncertainty: Path,
    expected_uncertainty_manifest_sha256: str,
) -> EvaluationRow:
    """Attach an authenticated block interval without making acceptance claims.

    The adapter mints the generic source identity only after reopening the exact
    caller-pinned block parent. A training-mean baseline remains non-fitted.
    """
    if not isinstance(row, EvaluationRow):
        refuse("A typed evaluation row is required")
    if (
        row.model_id not in {FITTED_METHOD, BLOCK_BASELINE_METHOD}
        or row.experiment != "all_target_pollen_withheld"
        or row.target != "pollen_composition"
        or row.status != "predicted"
        or row.prediction is None
        or row.interval is not None
        or row.observation is not None
        or row.observation_reference_id is not None
        or row.observation_kind is not None
        or row.observation_support is not None
        or row.prediction_sha256 is not None
        or row.prediction_manifest_json is not None
        or row.prediction_frozen_at is not None
        or row.observed_pollen is not None
        or row.reason is not None
        or row.source_model is not None
        or (row.model_id == FITTED_METHOD and row.fitted_model_sha256 is None)
        or (
            row.model_id == BLOCK_BASELINE_METHOD
            and row.fitted_model_sha256 is not None
        )
    ):
        refuse("Require an outcome-free unfrozen typed spatial-block pollen row")
    plan, parent_rows, retained = _authenticated_block_draws(
        predictions,
        expected_prediction_manifest_sha256=expected_prediction_manifest_sha256,
        uncertainty=uncertainty,
        expected_uncertainty_manifest_sha256=expected_uncertainty_manifest_sha256,
    )
    key = row.fold_id, row.record_id, row.model_id
    parent = parent_rows.get(key)
    source = retained.get(key)
    if parent is None or source is None or source.get("status") != "generated":
        refuse("The exact block evaluation unit has no generated conditional interval")
    entry = next((entry for entry in plan.entries if entry.key == key), None)
    if entry is None:
        refuse("Evaluation unit differs from the frozen block uncertainty plan")
    if parent.get("method") != row.model_id or parent.get("record_id") != row.record_id:
        refuse("Evaluation row differs from the authenticated block parent")
    if row.model_id == FITTED_METHOD:
        source_kind = "fitted_spatial"
        source_sha256 = digest(cast(str, parent.get("model_sha256")))
        model_input_ids = tuple(
            identity(value)
            for value in object_list(
                parent.get("training_input_ids"), "training_input_ids"
            )
        )
        if row.fitted_model_sha256 != source_sha256:
            refuse("Evaluation fitted identity differs from the block parent")
    else:
        source_kind = "admitted_reconstruction_training_mean"
        if parent.get("method_kind") != source_kind:
            refuse("Baseline block method kind differs from its governed producer")
        source_sha256 = digest(cast(str, parent.get("baseline_model_sha256")))
        baseline = object_mapping(
            parent.get("baseline_model_manifest"), "baseline_model_manifest"
        )
        model_input_ids = tuple(
            identity(value)
            for value in object_list(
                baseline.get("training_input_ids"), "training_input_ids"
            )
        )
    if model_input_ids != row.fit_input_ids:
        refuse("Evaluation model inputs differ from the authenticated block parent")
    prediction = dict(row.prediction)
    pollen = object_mapping(parent["pollen_fraction"], "pollen_fraction")
    if len(prediction) != len(row.prediction) or prediction != pollen:
        refuse(
            "Evaluation pollen values or taxon denominator differ from the block parent"
        )
    result = object_mapping(source["engine_result"], "engine_result")
    declaration = object_mapping(result["declaration"], "declaration")
    intervals = object_mapping(
        result["marginal_predictive_intervals"], "marginal_predictive_intervals"
    )
    if (
        tuple(sorted(prediction)) != entry.taxa
        or declaration.get("taxa") != list(entry.taxa)
        or declaration.get("coverage") != plan.coverage
        or set(intervals) != set(entry.taxa)
    ):
        refuse("Block interval taxa or nominal level differ from the plan")
    limits = []
    for taxon in entry.taxa:
        bounds = object_mapping(intervals[taxon], "bounds")
        lower = finite_number(bounds["lower_fraction"])
        upper = finite_number(bounds["upper_fraction"])
        if not 0 <= lower <= upper <= 1:
            refuse("Predictive fraction bounds are outside the closed unit interval")
        limits.append((taxon, lower, upper))
    result_sha256 = digest(cast(str, source["engine_result_sha256"]))
    interval = PredictiveInterval(
        profile_id=(
            f"{AUTHENTICATED_BLOCK_CONDITIONAL_INTERVAL_PROFILE}:"
            f"{digest(expected_uncertainty_manifest_sha256)}:{result_sha256}"
        ),
        nominal_coverage=plan.coverage,
        propagated_sources=("observation_process",),
        uncertainty_kind="predictive_observation",
        limits=tuple(limits),
    )
    source_model = _authenticated_source_model(source_kind, source_sha256)
    return freeze_evaluation_prediction(
        replace(row, interval=interval, source_model=source_model)
    )
