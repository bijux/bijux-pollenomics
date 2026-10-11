"""Authenticate conditional observation intervals before freezing pollen predictions."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import cast

from ...lra.engine.discovery import load_engine
from ..contracts import finite_number, manifest_sha256
from ..experiments.configuration import (
    FITTED_METHOD,
    TRAINING_MEAN_METHOD,
    identity,
    object_list,
    object_mapping,
)
from ..experiments.outputs import read_experiment_product, read_member
from ..observation_uncertainty.contracts import (
    PROFILE as OBSERVATION_PROFILE,
)
from ..observation_uncertainty.contracts import (
    ObservationUncertaintyPlan,
)
from ..observation_uncertainty.workflow import (
    validate_counting_design,
    validate_plan_parent,
)
from .contracts import (
    EvaluationRow,
    PredictiveInterval,
    _authenticated_source_model,
    digest,
    freeze_evaluation_prediction,
    refuse,
)

AUTHENTICATED_CONDITIONAL_INTERVAL_PROFILE = (
    "pollenomics-authenticated-conditional-predictive-observation.v1"
)


def _authenticated_draws(
    predictions: Path,
    *,
    expected_prediction_manifest_sha256: str,
    uncertainty: Path,
    expected_uncertainty_manifest_sha256: str,
) -> tuple[
    ObservationUncertaintyPlan,
    dict[tuple[str, str], dict[str, object]],
    dict[tuple[str, str], dict[str, object]],
    dict[tuple[str, str], tuple[str, str | None]],
]:
    """Reopen every retained unit and preserve the complete requested denominator."""
    expected_parent = digest(expected_prediction_manifest_sha256)
    expected_uncertainty = digest(expected_uncertainty_manifest_sha256)
    product, manifest = read_experiment_product(
        uncertainty, expected_manifest_sha256=expected_uncertainty
    )
    payload = object_mapping(manifest["scientific_payload"], "uncertainty")
    plan = ObservationUncertaintyPlan.from_dict(payload.get("plan"))
    parent, parent_manifest, parent_rows = validate_plan_parent(predictions, plan)
    rows = [
        object_mapping(value, "uncertainty_row")
        for value in object_list(
            read_member(product, "uncertainty.json"), "uncertainty"
        )
    ]
    evidence = object_mapping(
        read_member(product, "effort_evidence.json"), "effort_evidence"
    )
    if (
        parent.manifest_sha256 != expected_parent
        or plan.prediction_manifest_sha256 != expected_parent
        or manifest["phase"] != "observation_uncertainty"
        or manifest["profile"] != parent_manifest["profile"]
        or payload.get("schema_version") != "lra-observation-uncertainty.v1"
        or payload.get("profile") != OBSERVATION_PROFILE
        or payload.get("plan_sha256") != plan.sha256
        or payload.get("prediction_manifest_sha256") != parent.manifest_sha256
        or payload.get("prediction_scientific_content_sha256")
        != parent.scientific_content_sha256
        or payload.get("uncertainty_scope") != "conditional_observation_process_only"
        or payload.get("outcome_accesses") != []
        or payload.get("scientific_acceptance") != "not_evaluated"
        or payload.get("final_policy_approval") is not False
        or payload.get("declaration_timing_authenticated") is not False
        or rows != payload.get("rows")
        or evidence != payload.get("effort_evidence")
        or manifest_sha256(read_member(product, "plan.json")) != plan.sha256
        or len(rows) != len(plan.entries)
        or payload.get("requested_units") != len(plan.entries)
    ):
        refuse("Uncertainty product, parent, plan or non-acceptance posture differs")
    binding = load_engine()
    retained: dict[tuple[str, str], dict[str, object]] = {}
    for entry, row in zip(plan.entries, rows, strict=True):
        if manifest_sha256(row.get("entry")) != manifest_sha256(entry.as_dict()):
            refuse("Uncertainty row differs from its exact plan entry")
        parent_row = parent_rows.get(entry.key)
        parent_sha256 = (
            None if parent_row is None else parent_row["prediction_manifest_sha256"]
        )
        if row.get("prediction_sha256") != parent_sha256:
            refuse("Uncertainty row belongs to a different parent prediction")
        status = row.get("status")
        if status not in {
            "generated",
            "prediction_refused",
            "effort_refused",
            "sampler_refused",
            "not_run",
        }:
            refuse("Unsupported uncertainty row status")
        if parent_row is None and status not in {"prediction_refused", "not_run"}:
            refuse("A missing parent must retain an explicit prediction refusal")
        if parent_row is not None and status == "prediction_refused":
            refuse("A generated parent cannot be recorded as prediction-refused")
        if status != "generated":
            if any(
                row.get(field) is not None
                for field in (
                    "engine_result",
                    "engine_result_sha256",
                    "engine_result_canonical_json",
                )
            ):
                refuse("A refused uncertainty row cannot retain draw output")
            retained[entry.key] = row
            continue
        if parent_row is None:
            refuse("Conditional draws require a generated parent prediction")
        design = object_mapping(evidence.get(entry.evidence_sha256), "effort_evidence")
        validate_counting_design(design, entry)
        canonical = row.get("engine_result_canonical_json")
        result_sha256 = row.get("engine_result_sha256")
        if not isinstance(canonical, str) or not isinstance(result_sha256, str):
            refuse("Generated uncertainty rows require canonical draw identities")
        try:
            result = binding.api.PollenObservationDraws(
                canonical, digest(result_sha256)
            ).as_dict()
        except (ValueError, TypeError, AttributeError) as exc:
            refuse(f"Invalid governed conditional observation result: {exc}")
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
                declaration.get(key) != value
                for key, value in expected_declaration.items()
            )
            or result.get("interval_kind") != "conditional_predictive_observation"
            or result.get("propagated_sources") != ["observation_process"]
            or result.get("conditioned_on")
            != ["fixed_pollen_probabilities", "predeclared_sampling_effort"]
            or result.get("empirical_coverage_verified") is not False
            or result.get("scientific_acceptance") != "not_evaluated"
        ):
            refuse("Conditional observation result scope or denominator differs")
        retained[entry.key] = row
    statuses = sorted({cast(str, row["status"]) for row in retained.values()})
    if payload.get("status_counts") != {
        status: sum(row["status"] == status for row in retained.values())
        for status in statuses
    }:
        refuse(
            "Uncertainty status counts differ from the complete retained denominator"
        )
    scientific = object_mapping(
        parent_manifest["scientific_payload"], "parent_scientific_payload"
    )
    methods_value = scientific.get("methods", scientific.get("baselines"))
    methods = tuple(
        identity(value) for value in object_list(methods_value, "parent_methods")
    )
    parent_statuses: dict[tuple[str, str], tuple[str, str | None]] = dict.fromkeys(
        parent_rows, ("predicted", None)
    )
    for value in object_list(scientific["failures"], "parent_failures"):
        failure = object_mapping(value, "parent_failure")
        fold_id = identity(failure["fold_id"])
        status = identity(failure["status"])
        reason = identity(failure["reason_code"])
        failure_methods = (
            (identity(failure["method"]),) if "method" in failure else methods
        )
        for method in failure_methods:
            key = fold_id, method
            if key in parent_statuses or status not in {"refused", "not_run"}:
                refuse("Parent prediction terminal accounting is contradictory")
            parent_statuses[key] = status, reason
    if set(parent_statuses) != {entry.key for entry in plan.entries}:
        refuse("Parent prediction terminals differ from the uncertainty plan")
    return plan, parent_rows, retained, parent_statuses


def _require_unfrozen_pollen_row(row: EvaluationRow) -> None:
    if not isinstance(row, EvaluationRow):
        refuse("A typed evaluation row is required")
    if (
        row.experiment != "all_target_pollen_withheld"
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
        or row.source_model is not None
        or row.reason is not None
        or row.model_id not in {FITTED_METHOD, TRAINING_MEAN_METHOD}
        or (row.model_id == FITTED_METHOD and row.fitted_model_sha256 is None)
        or (
            row.model_id == TRAINING_MEAN_METHOD and row.fitted_model_sha256 is not None
        )
    ):
        refuse("Require an outcome-free, unfrozen, all-target-withheld pollen row")


def freeze_authenticated_pollen_interval(
    row: EvaluationRow,
    *,
    predictions: Path,
    expected_prediction_manifest_sha256: str,
    uncertainty: Path,
    expected_uncertainty_manifest_sha256: str,
) -> EvaluationRow:
    """Attach one authenticated conditional pollen interval and freeze outcome-free bytes.

    The source remains conditional on fixed predicted pollen probabilities and a
    predeclared effort. This adapter does not authenticate review/timing, evaluate
    coverage or promote the exploratory source product to scientific acceptance.
    """
    _require_unfrozen_pollen_row(row)
    plan, parent_rows, retained, _ = _authenticated_draws(
        predictions,
        expected_prediction_manifest_sha256=expected_prediction_manifest_sha256,
        uncertainty=uncertainty,
        expected_uncertainty_manifest_sha256=expected_uncertainty_manifest_sha256,
    )
    return _freeze_authenticated_pollen_interval(
        row,
        plan=plan,
        parent_rows=parent_rows,
        retained=retained,
        expected_uncertainty_manifest_sha256=expected_uncertainty_manifest_sha256,
    )


def _freeze_authenticated_pollen_interval(
    row: EvaluationRow,
    *,
    plan: ObservationUncertaintyPlan,
    parent_rows: dict[tuple[str, str], dict[str, object]],
    retained: dict[tuple[str, str], dict[str, object]],
    expected_uncertainty_manifest_sha256: str,
) -> EvaluationRow:
    key = row.fold_id, row.model_id
    parent = parent_rows.get(key)
    source = retained.get(key)
    if parent is None or source is None or source.get("status") != "generated":
        refuse("The requested evaluation unit has no generated conditional interval")
    entry = next((entry for entry in plan.entries if entry.key == key), None)
    if entry is None or entry.record_id != row.record_id:
        refuse("Evaluation record differs from the frozen uncertainty plan")
    fitted = row.model_id == FITTED_METHOD
    model = (
        parent
        if fitted
        else object_mapping(
            parent.get("baseline_model_manifest"), "baseline_model_manifest"
        )
    )
    source_sha256 = digest(
        cast(
            str,
            parent.get("model_sha256")
            if fitted
            else parent.get("baseline_model_sha256"),
        )
    )
    inputs = tuple(
        identity(value)
        for value in object_list(model.get("training_input_ids"), "training_input_ids")
    )
    if (
        parent.get("method") != row.model_id
        or parent.get("record_id") != row.record_id
        or inputs != row.fit_input_ids
        or (fitted and row.fitted_model_sha256 != source_sha256)
        or (not fitted and row.fitted_model_sha256 is not None)
        or (
            not fitted and manifest_sha256(model) != parent.get("baseline_model_sha256")
        )
    ):
        refuse("Only an authenticated governed prediction can receive an interval")
    if row.prediction is None:
        refuse("Only a predicted grouped pollen row can receive an interval")
    prediction = dict(row.prediction)
    pollen = object_mapping(parent["pollen_fraction"], "pollen_fraction")
    if len(prediction) != len(row.prediction) or prediction != pollen:
        refuse(
            "Evaluation prediction values or taxon denominator differ from the parent"
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
        refuse("Interval taxa or nominal level differ from the exact plan denominator")
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
            f"{AUTHENTICATED_CONDITIONAL_INTERVAL_PROFILE}:"
            f"{digest(expected_uncertainty_manifest_sha256)}:{result_sha256}"
        ),
        nominal_coverage=plan.coverage,
        propagated_sources=("observation_process",),
        uncertainty_kind="predictive_observation",
        limits=tuple(limits),
    )
    source_model = _authenticated_source_model(
        "fitted_spatial" if fitted else "admitted_reconstruction_training_mean",
        source_sha256,
    )
    return freeze_evaluation_prediction(
        replace(row, interval=interval, source_model=source_model)
    )


def freeze_authenticated_pollen_rows(
    rows: tuple[EvaluationRow, ...],
    *,
    predictions: Path,
    expected_prediction_manifest_sha256: str,
    uncertainty: Path,
    expected_uncertainty_manifest_sha256: str,
) -> tuple[EvaluationRow, ...]:
    """Bind a complete grouped point ledger to one uncertainty denominator."""
    if not isinstance(rows, tuple) or not rows:
        refuse("A nonempty typed grouped pollen row ledger is required")
    keyed = {(row.fold_id, row.model_id): row for row in rows}
    if len(keyed) != len(rows) or any(
        not isinstance(row, EvaluationRow)
        or row.target != "pollen_composition"
        or row.experiment != "all_target_pollen_withheld"
        or row.model_id not in {FITTED_METHOD, TRAINING_MEAN_METHOD}
        for row in rows
    ):
        refuse("Grouped pollen row ledger identity or denominator is invalid")
    plan, parent_rows, retained, parent_statuses = _authenticated_draws(
        predictions,
        expected_prediction_manifest_sha256=expected_prediction_manifest_sha256,
        uncertainty=uncertainty,
        expected_uncertainty_manifest_sha256=expected_uncertainty_manifest_sha256,
    )
    if set(keyed) != set(retained) or set(keyed) != set(parent_statuses):
        refuse("Grouped pollen row ledger differs from the uncertainty denominator")
    result: list[EvaluationRow] = []
    for key, row in keyed.items():
        source_status = retained[key].get("status")
        parent_status, parent_reason = parent_statuses[key]
        if row.status == "predicted":
            if parent_status != "predicted" or source_status != "generated":
                refuse("Every predicted grouped pollen row requires an interval")
            _require_unfrozen_pollen_row(row)
            result.append(
                _freeze_authenticated_pollen_interval(
                    row,
                    plan=plan,
                    parent_rows=parent_rows,
                    retained=retained,
                    expected_uncertainty_manifest_sha256=(
                        expected_uncertainty_manifest_sha256
                    ),
                )
            )
            continue
        expected_reason = f"parent_{parent_status}:{parent_reason}"
        if (
            row.status != "prediction_failed"
            or parent_status not in {"refused", "not_run"}
            or source_status not in {"prediction_refused", "not_run"}
            or not isinstance(row.reason, str)
            or row.reason != expected_reason
            or row.prediction is not None
            or row.observation is not None
            or row.observation_reference_id is not None
            or row.observation_kind is not None
            or row.observation_support is not None
            or row.observed_pollen is not None
            or row.source_model is not None
            or row.interval is not None
            or row.prediction_sha256 is not None
            or row.prediction_manifest_json is not None
            or row.prediction_frozen_at is not None
            or row.fitted_model_sha256 is not None
            or row.fit_input_ids
        ):
            refuse("Failed grouped pollen row differs from its parent terminal")
        result.append(row)
    return tuple(result)
