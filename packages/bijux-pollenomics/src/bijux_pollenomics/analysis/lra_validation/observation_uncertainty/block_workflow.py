"""Conditional observation draws for complete authenticated spatial-block units."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import cast

from ...lra.engine.discovery import load_engine
from ...lra.engine.errors import LRARefusal
from ...lra.outputs.identity import capture_code_identity, verify_code_identity
from ..contracts import ValidationRefusal, canonical_json
from ..experiments import read_spatial_block_predictions
from ..experiments.configuration import identity, object_list, object_mapping
from ..experiments.inputs import read_reference
from ..experiments.outputs import (
    ExperimentProduct,
    publish_phase,
    read_experiment_product,
    read_member,
    stage_directory,
    write_json,
)
from .block_contracts import (
    BLOCK_OBSERVATION_PROFILE,
    BlockEffortDeclaration,
    BlockObservationUncertaintyPlan,
)
from .workflow import _disjoint, implementation_identity

ParentKey = tuple[str, str, str]


def _validate_counting_design(
    value: dict[str, object], entry: BlockEffortDeclaration
) -> None:
    expected = {
        "schema_version": "lra-synthetic-counting-design.v1",
        "data_kind": "synthetic",
        "record_id": entry.record_id,
        "bin_id": entry.bin_id,
        "planned_effort": entry.effort,
        "effort_unit": "pollen_grains",
        "timing_declaration": "before_outcome_access",
    }
    if (
        set(value) != {*expected, "declaration_provenance"}
        or any(value[key] != expected_value for key, expected_value in expected.items())
        or type(value.get("planned_effort")) is not int
        or not isinstance(value.get("declaration_provenance"), str)
        or not cast(str, value["declaration_provenance"]).strip()
    ):
        raise ValidationRefusal("invalid_counting_design", entry.record_id)
    canonical_bytes = (canonical_json(value) + "\n").encode("utf-8")
    if hashlib.sha256(canonical_bytes).hexdigest() != entry.evidence_sha256:
        raise ValidationRefusal(
            "invalid_counting_design",
            f"{entry.record_id}: retained evidence differs from source bytes",
        )


def _effort_evidence(root: Path, entry: BlockEffortDeclaration) -> dict[str, object]:
    value = read_reference(root, entry.reference)
    _validate_counting_design(value, entry)
    return value


def validate_block_plan_parent(
    predictions: Path,
    plan: BlockObservationUncertaintyPlan,
) -> tuple[
    ExperimentProduct,
    dict[str, object],
    dict[ParentKey, dict[str, object]],
    dict[ParentKey, str],
]:
    """Authenticate the complete fold/record/method denominator before evidence."""
    try:
        product, manifest, folds, rows, methods = read_spatial_block_predictions(
            predictions,
            expected_manifest_sha256=plan.prediction_manifest_sha256,
        )
        scientific = object_mapping(
            manifest["scientific_payload"], "scientific_payload"
        )
        expected = {
            (fold_id, identity(record), method)
            for fold_id, fold in folds.items()
            for record in object_list(fold["test_record_ids"], "test_record_ids")
            for method in methods
        }
        if {entry.key for entry in plan.entries} != expected:
            raise ValidationRefusal(
                "observation_denominator_mismatch",
                "Require every block fold, target record and method",
            )
        statuses: dict[ParentKey, str] = dict.fromkeys(rows, "predicted")
        for value in object_list(scientific["failures"], "failures"):
            failure = object_mapping(value, "failure")
            key = (
                identity(failure["fold_id"]),
                identity(failure["record_id"]),
                identity(failure["method"]),
            )
            status = identity(failure["status"])
            if (
                key not in expected
                or key in statuses
                or status not in {"refused", "not_run"}
            ):
                raise ValidationRefusal(
                    "observation_denominator_mismatch",
                    "Parent status inventory is duplicate or contradictory",
                )
            statuses[key] = status
        if set(statuses) != expected:
            raise ValidationRefusal(
                "observation_denominator_mismatch",
                "Parent omits requested block units",
            )
        experiment = object_mapping(
            read_member(product, "experiment.json"), "experiment"
        )
        request = object_mapping(experiment["request"], "request")
        template = object_mapping(request["request_template"], "request_template")
        taxa = tuple(
            sorted(identity(value) for value in object_list(template["taxa"], "taxa"))
        )
        bins = object_list(
            object_mapping(template["temporal_matching"], "temporal_matching")["bins"],
            "bins",
        )
        if len(bins) != 1:
            raise ValidationRefusal(
                "unsupported_observation_bins",
                "Candidate requires one explicit shared bin",
            )
        bin_id = identity(object_mapping(bins[0], "bin")["bin_id"])
        for entry in plan.entries:
            fold = folds[entry.fold_id]
            if (
                entry.record_id
                not in object_list(fold["test_record_ids"], "test_record_ids")
                or entry.bin_id != bin_id
                or entry.taxa != taxa
            ):
                raise ValidationRefusal(
                    "observation_denominator_mismatch",
                    "Record, bin or taxa differ from the block parent",
                )
            parent = rows.get(entry.key)
            if parent is not None:
                pollen = object_mapping(parent["pollen_fraction"], "pollen_fraction")
                if (
                    parent["record_id"] != entry.record_id
                    or parent["bin_id"] != entry.bin_id
                    or set(pollen) != set(entry.taxa)
                ):
                    raise ValidationRefusal(
                        "observation_denominator_mismatch",
                        "Prediction scope differs from its declared block unit",
                    )
        expected_counts = {
            status: sum(value == status for value in statuses.values())
            for status in ("predicted", "refused", "not_run")
        }
        if expected_counts != {
            "predicted": scientific["generated_predictions"],
            "refused": scientific["refused_predictions"],
            "not_run": scientific["not_run_predictions"],
        }:
            raise ValidationRefusal(
                "observation_denominator_mismatch",
                "Parent predicted/refused/not-run counts differ",
            )
        return product, manifest, rows, statuses
    except ValidationRefusal:
        raise
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise ValidationRefusal("invalid_block_observation_parent", str(exc)) from exc


def generate_block_pollen_observation_uncertainty(
    predictions: Path,
    plan: BlockObservationUncertaintyPlan,
    *,
    evidence_root: Path,
    destination: Path,
    purpose: str = "exploratory",
) -> ExperimentProduct:
    """Generate conditional draws without accepting observations or policy claims."""
    if purpose != "exploratory":
        raise ValidationRefusal("unsupported_observation_purpose", purpose)
    if not isinstance(plan, BlockObservationUncertaintyPlan):
        raise ValidationRefusal(
            "invalid_block_observation_plan", "Require the typed block plan"
        )
    _disjoint(destination, predictions, evidence_root)
    parent, parent_manifest, parent_rows, parent_statuses = validate_block_plan_parent(
        predictions, plan
    )
    implementation = implementation_identity()
    evidence: dict[str, dict[str, object]] = {}
    evidence_failures: dict[ParentKey, ValidationRefusal] = {}
    for entry in plan.entries:
        try:
            evidence[entry.evidence_sha256] = _effort_evidence(evidence_root, entry)
        except ValidationRefusal as exc:
            evidence_failures[entry.key] = exc
    binding = load_engine()
    code = capture_code_identity(binding)
    if not callable(getattr(binding.api, "sample_pollen_observations", None)):
        raise ValidationRefusal(
            "observation_engine_unavailable",
            "Installed engine lacks the conditional sampler",
        )
    stage = stage_directory(destination)
    rows: list[dict[str, object]] = []
    interrupted = False
    for entry in plan.entries:
        parent_status = parent_statuses[entry.key]
        prediction = parent_rows.get(entry.key)
        row: dict[str, object] = {
            "entry": entry.as_dict(),
            "parent_status": parent_status,
            "prediction_sha256": (
                None if prediction is None else prediction["prediction_manifest_sha256"]
            ),
            "engine_result": None,
            "engine_result_sha256": None,
            "engine_result_canonical_json": None,
        }
        if parent_status == "refused":
            row.update(status="parent_refused", reason_code="parent_prediction_refused")
        elif parent_status == "not_run":
            row.update(status="parent_not_run", reason_code="parent_prediction_not_run")
        elif interrupted:
            row.update(
                status="not_run",
                reason_code="observation_generation_interrupted",
            )
        elif entry.key in evidence_failures:
            failure = evidence_failures[entry.key]
            row.update(
                status="effort_refused",
                reason_code=failure.reason_code,
                detail=str(failure),
            )
        else:
            assert prediction is not None
            try:
                result = binding.api.sample_pollen_observations(
                    prediction["pollen_fraction"],
                    effort=entry.effort,
                    repeats=plan.repeats,
                    seed=entry.seed,
                    coverage=plan.coverage,
                    prediction_sha256=row["prediction_sha256"],
                    effort_evidence_sha256=entry.evidence_sha256,
                )
                row.update(
                    status="generated",
                    engine_result=result.as_dict(),
                    engine_result_sha256=result.result_sha256,
                    engine_result_canonical_json=result.canonical_result_json,
                )
            except KeyboardInterrupt:
                interrupted = True
                row.update(
                    status="not_run",
                    reason_code="observation_generation_interrupted",
                )
            except (ValueError, LRARefusal) as exc:
                row.update(
                    status="sampler_refused",
                    reason_code=getattr(
                        exc, "reason_code", "observation_sampler_refused"
                    ),
                    detail=str(exc),
                )
        rows.append(row)
    statuses = sorted({cast(str, row["status"]) for row in rows})
    parent_counts = {
        status: sum(value == status for value in parent_statuses.values())
        for status in ("predicted", "refused", "not_run")
    }
    scientific: dict[str, object] = {
        "schema_version": "lra-spatial-block-observation-uncertainty.v1",
        "profile": BLOCK_OBSERVATION_PROFILE,
        "plan": plan.as_dict(),
        "plan_sha256": plan.sha256,
        "prediction_manifest_sha256": parent.manifest_sha256,
        "prediction_scientific_content_sha256": parent.scientific_content_sha256,
        "rows": rows,
        "requested_units": len(plan.entries),
        "parent_status_counts": parent_counts,
        "status_counts": {
            status: sum(row["status"] == status for row in rows) for status in statuses
        },
        "effort_evidence": evidence,
        "engine_identity": code.payload(),
        "implementation": implementation,
        "access_order": [
            "authenticate_block_parent",
            "verify_complete_fold_record_method_plan",
            "read_predeclared_counting_design",
            "load_engine",
            "conditional_sampling",
        ],
        "outcome_accesses": [],
        "declaration_timing_authenticated": False,
        "empirical_coverage_verified": False,
        "scientific_acceptance": "not_evaluated",
        "final_policy_approval": False,
        "uncertainty_scope": "conditional_observation_process_only",
        "conditioned_on": [
            "fixed_predicted_pollen_probabilities",
            "predeclared_sampling_effort",
        ],
    }
    write_json(stage, "plan.json", plan.as_dict())
    write_json(stage, "uncertainty.json", rows)
    write_json(stage, "effort_evidence.json", evidence)
    for entry in plan.entries:
        if entry.key not in evidence_failures:
            _effort_evidence(evidence_root, entry)
    read_experiment_product(
        predictions, expected_manifest_sha256=plan.prediction_manifest_sha256
    )
    if implementation_identity() != implementation:
        raise ValidationRefusal("observation_implementation_changed", str(stage))
    verify_code_identity(binding, code)
    return publish_phase(
        stage,
        destination,
        phase="observation_uncertainty",
        scientific=scientific,
        profile=cast(str, parent_manifest["profile"]),
    )
