"""Attach conditional engine draws to admitted predictions without opening outcomes."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from ...lra.engine.discovery import load_engine
from ...lra.engine.errors import LRARefusal
from ...lra.outputs.identity import (
    capture_code_identity,
    file_inventory,
    verify_code_identity,
)
from ..contracts import ValidationRefusal
from ..experiments import read_withheld_predictions
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
from .contracts import PROFILE, EffortDeclaration, ObservationUncertaintyPlan


def implementation_identity() -> dict[str, str]:
    """Reuse the host file-inventory owner across validation and its shared readers."""
    return file_inventory(Path(__file__).parents[1])


def _validate_plan_parent(
    predictions: Path,
    plan: ObservationUncertaintyPlan,
) -> tuple[
    ExperimentProduct, dict[str, object], dict[tuple[str, str], dict[str, object]]
]:
    """Authenticate parent and complete requested units before evidence or engine access."""
    product, manifest, folds, rows, methods = read_withheld_predictions(
        predictions,
        expected_manifest_sha256=plan.prediction_manifest_sha256,
    )
    expected = {(fold, method) for fold in folds for method in methods}
    if {e.key for e in plan.entries} != expected:
        raise ValidationRefusal(
            "observation_denominator_mismatch",
            "Require every requested Fold and method",
        )
    experiment = object_mapping(read_member(product, "experiment.json"), "experiment")
    template = object_mapping(experiment["request_template"], "request_template")
    taxa = tuple(sorted(identity(t) for t in object_list(template["taxa"], "taxa")))
    temporal = object_mapping(template["temporal_matching"], "temporal_matching")
    bins = object_list(temporal["bins"], "bins")
    if len(bins) != 1:
        raise ValidationRefusal(
            "unsupported_observation_bins",
            "Initial profile requires one explicit shared bin",
        )
    bin_id = object_mapping(bins[0], "bin")["bin_id"]
    for entry in plan.entries:
        fold = folds[entry.fold_id]
        if (
            fold["test_record_ids"] != [entry.record_id]
            or entry.bin_id != bin_id
            or entry.taxa != taxa
        ):
            raise ValidationRefusal(
                "observation_denominator_mismatch", "Record/bin/taxa differ from parent"
            )
        if entry.key in rows:
            row = rows[entry.key]
            pollen = object_mapping(row["pollen_fraction"], "pollen_fraction")
            if (
                row["record_id"] != entry.record_id
                or row["bin_id"] != entry.bin_id
                or set(pollen) != set(entry.taxa)
            ):
                raise ValidationRefusal(
                    "observation_denominator_mismatch", "Prediction scope differs"
                )
    return product, manifest, rows


def validate_plan_parent(
    predictions: Path,
    plan: ObservationUncertaintyPlan,
) -> tuple[
    ExperimentProduct, dict[str, object], dict[tuple[str, str], dict[str, object]]
]:
    """Translate malformed retained templates to a stable refusal before evidence."""
    try:
        return _validate_plan_parent(predictions, plan)
    except ValidationRefusal:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationRefusal("invalid_observation_parent", str(exc)) from exc


def effort_evidence(root: Path, entry: EffortDeclaration) -> dict[str, object]:
    """Read one pinned synthetic design declaration, never an observed total."""
    value = read_reference(root, entry.reference)
    validate_counting_design(value, entry)
    return value


def validate_counting_design(
    value: dict[str, object], entry: EffortDeclaration
) -> None:
    """Recheck retained design semantics without asserting original file formatting."""
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
        or any(value[k] != v for k, v in expected.items())
        or type(value.get("planned_effort")) is not int
    ):
        raise ValidationRefusal("invalid_counting_design", entry.record_id)
    provenance = value["declaration_provenance"]
    if not isinstance(provenance, str) or not provenance.strip():
        raise ValidationRefusal(
            "invalid_counting_design", "Require explicit declaration provenance"
        )


def _disjoint(destination: Path, *inputs: Path) -> None:
    target = destination.resolve()
    for path in inputs:
        root = path.resolve()
        if target == root or target in root.parents or root in target.parents:
            raise ValidationRefusal("observation_output_overlap", str(path))


def generate_pollen_observation_uncertainty(
    predictions: Path,
    plan: ObservationUncertaintyPlan,
    *,
    evidence_root: Path,
    destination: Path,
    purpose: str = "exploratory",
) -> ExperimentProduct:
    """Generate complete conditional-only rows; no outcome arguments are accepted."""
    if purpose != "exploratory":
        raise ValidationRefusal("unsupported_observation_purpose", purpose)
    if not isinstance(plan, ObservationUncertaintyPlan):
        raise ValidationRefusal(
            "invalid_observation_plan", "Require immutable typed plan"
        )
    _disjoint(destination, predictions, evidence_root)
    parent, manifest, predictions_by_key = validate_plan_parent(predictions, plan)
    implementation = implementation_identity()
    evidence: dict[str, dict[str, object]] = {}
    evidence_failures: dict[tuple[str, str], ValidationRefusal] = {}
    for entry in plan.entries:
        try:
            evidence[entry.evidence_sha256] = effort_evidence(evidence_root, entry)
        except ValidationRefusal as exc:
            evidence_failures[entry.key] = exc
    # Even a missing extension is an explicit refusal. No rolling provider fallback.
    binding = load_engine()
    code = capture_code_identity(binding)
    if not callable(getattr(binding.api, "sample_pollen_observations", None)):
        raise ValidationRefusal(
            "observation_engine_unavailable",
            "Installed engine lacks conditional sampler",
        )
    stage = stage_directory(destination)
    rows: list[dict[str, object]] = []
    interrupted = False
    for entry in plan.entries:
        row: dict[str, object] = {
            "entry": entry.as_dict(),
            "prediction_sha256": None,
            "engine_result": None,
            "engine_result_sha256": None,
            "engine_result_canonical_json": None,
        }
        prediction = predictions_by_key.get(entry.key)
        if prediction is not None:
            row["prediction_sha256"] = prediction["prediction_manifest_sha256"]
        if interrupted:
            row.update(
                status="not_run", reason_code="observation_generation_interrupted"
            )
        elif prediction is None:
            row.update(
                status="prediction_refused",
                reason_code="parent_prediction_not_generated",
            )
        elif entry.key in evidence_failures:
            failure = evidence_failures[entry.key]
            row.update(
                status="effort_refused",
                reason_code=failure.reason_code,
                detail=str(failure),
            )
        else:
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
                    status="not_run", reason_code="observation_generation_interrupted"
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
    scientific: dict[str, object] = {
        "schema_version": "lra-observation-uncertainty.v1",
        "profile": PROFILE,
        "plan": plan.as_dict(),
        "plan_sha256": plan.sha256,
        "prediction_manifest_sha256": parent.manifest_sha256,
        "prediction_scientific_content_sha256": parent.scientific_content_sha256,
        "rows": rows,
        "requested_units": len(plan.entries),
        "status_counts": {
            status: sum(row["status"] == status for row in rows) for status in statuses
        },
        "effort_evidence": evidence,
        "engine_identity": code.payload(),
        "implementation": implementation,
        "access_order": [
            "authenticate_parent",
            "verify_complete_plan",
            "read_counting_design",
            "load_engine",
            "conditional_sampling",
        ],
        "outcome_accesses": [],
        "declaration_timing_authenticated": False,
        "scientific_acceptance": "not_evaluated",
        "final_policy_approval": False,
        "uncertainty_scope": "conditional_observation_process_only",
    }
    write_json(stage, "plan.json", plan.as_dict())
    write_json(stage, "uncertainty.json", rows)
    write_json(stage, "effort_evidence.json", evidence)
    # Repeat every successfully consumed reference, including aliases sharing a hash.
    for entry in plan.entries:
        if entry.key not in evidence_failures:
            effort_evidence(evidence_root, entry)
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
        profile=cast(str, manifest["profile"]),
    )
