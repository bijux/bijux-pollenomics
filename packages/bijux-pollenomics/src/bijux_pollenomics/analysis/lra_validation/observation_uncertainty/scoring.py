"""Separate marginal coverage from pinned predictions, draws and observed score rows."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from ...lra.engine.discovery import load_engine
from ...lra.outputs.identity import capture_code_identity, verify_code_identity
from ..contracts import ValidationRefusal, manifest_sha256
from ..experiments.configuration import object_list, object_mapping
from ..experiments.outputs import (
    ExperimentProduct,
    publish_phase,
    read_experiment_product,
    read_member,
    stage_directory,
    write_json,
)
from .contracts import PROFILE, EffortDeclaration, ObservationUncertaintyPlan
from .workflow import (
    _disjoint,
    implementation_identity,
    validate_counting_design,
    validate_plan_parent,
)


def _uncertainty_rows(
    product: ExperimentProduct,
    manifest: dict[str, object],
    plan: ObservationUncertaintyPlan,
    predictions: dict[tuple[str, str], dict[str, object]],
) -> list[dict[str, object]]:
    payload = object_mapping(manifest["scientific_payload"], "uncertainty")
    rows = object_list(read_member(product, "uncertainty.json"), "uncertainty")
    if (
        manifest["phase"] != "observation_uncertainty"
        or payload.get("schema_version") != "lra-observation-uncertainty.v1"
        or payload.get("profile") != PROFILE
        or payload.get("plan_sha256") != plan.sha256
        or payload.get("scientific_acceptance") != "not_evaluated"
        or payload.get("uncertainty_scope") != "conditional_observation_process_only"
        or payload.get("final_policy_approval") is not False
        or payload.get("declaration_timing_authenticated") is not False
        or payload.get("outcome_accesses") != []
        or rows != payload.get("rows")
        or len(rows) != len(plan.entries)
        or payload.get("requested_units") != len(plan.entries)
        or read_member(product, "plan.json") != payload.get("plan")
    ):
        raise ValidationRefusal(
            "invalid_observation_uncertainty", "Invalid retained phase, plan or posture"
        )
    evidence = object_mapping(
        read_member(product, "effort_evidence.json"), "effort_evidence"
    )
    if evidence != payload.get("effort_evidence"):
        raise ValidationRefusal(
            "invalid_observation_uncertainty", "Effort evidence differs"
        )
    result = []
    for value, entry in zip(rows, plan.entries, strict=True):
        row = object_mapping(value, "uncertainty_row")
        if manifest_sha256(row.get("entry")) != manifest_sha256(entry.as_dict()):
            raise ValidationRefusal(
                "observation_denominator_mismatch", "Retained row differs from plan"
            )
        parent = predictions.get(entry.key)
        expected = None if parent is None else parent["prediction_manifest_sha256"]
        if row.get("prediction_sha256") != expected:
            raise ValidationRefusal(
                "observation_prediction_identity_mismatch", entry.record_id
            )
        if row.get("status") not in {
            "generated",
            "prediction_refused",
            "effort_refused",
            "sampler_refused",
            "not_run",
        }:
            raise ValidationRefusal(
                "invalid_observation_uncertainty", "Unsupported status"
            )
        if parent is None and row["status"] not in {"prediction_refused", "not_run"}:
            raise ValidationRefusal(
                "invalid_observation_uncertainty",
                "Draws require a generated parent prediction",
            )
        if parent is not None and row["status"] == "prediction_refused":
            raise ValidationRefusal(
                "invalid_observation_uncertainty", "Generated parent cannot be absent"
            )
        if row["status"] != "generated" and (
            row.get("engine_result") is not None
            or row.get("engine_result_sha256") is not None
            or row.get("engine_result_canonical_json") is not None
        ):
            raise ValidationRefusal(
                "invalid_observation_uncertainty", "Refused rows cannot contain draws"
            )
        if row["status"] == "generated":
            validate_counting_design(
                object_mapping(evidence.get(entry.evidence_sha256), "effort_evidence"),
                entry,
            )
        result.append(row)
    statuses = sorted({cast(str, row["status"]) for row in result})
    if payload.get("status_counts") != {
        s: sum(row["status"] == s for row in result) for s in statuses
    }:
        raise ValidationRefusal(
            "observation_denominator_mismatch", "Retained counts differ"
        )
    return result


def _scored_pollen(
    product: ExperimentProduct,
    manifest: dict[str, object],
    parent: ExperimentProduct,
    plan: ObservationUncertaintyPlan,
) -> dict[tuple[str, str], dict[str, object]]:
    payload = object_mapping(manifest["scientific_payload"], "scores")
    rows = object_list(read_member(product, "scores.json"), "scores")
    if (
        manifest["phase"] != "scores"
        or payload.get("prediction_manifest_sha256") != parent.manifest_sha256
        or payload.get("prediction_scientific_content_sha256")
        != parent.scientific_content_sha256
        or rows != payload.get("scores")
    ):
        raise ValidationRefusal(
            "observation_score_parent_mismatch",
            "Scores belong to different predictions",
        )
    indexed: dict[tuple[str, str], dict[str, object]] = {}
    for value in rows:
        row = object_mapping(value, "score")
        if row.get("target") != "pollen_composition":
            continue
        method = row.get("method", row.get("baseline"))
        if not isinstance(row.get("fold_id"), str) or not isinstance(method, str):
            raise ValidationRefusal(
                "invalid_observation_score", "Missing fold or method"
            )
        key = cast(str, row["fold_id"]), method
        if key in indexed:
            raise ValidationRefusal(
                "observation_denominator_mismatch", "Duplicate pollen score"
            )
        indexed[key] = row
    if set(indexed) != {e.key for e in plan.entries}:
        raise ValidationRefusal(
            "observation_denominator_mismatch", "Scores omit requested pollen units"
        )
    return indexed


def _coverage(
    entry: EffortDeclaration,
    uncertainty: dict[str, object],
    score: dict[str, object],
    prediction: dict[str, object] | None,
) -> dict[str, object]:
    row: dict[str, object] = {
        "entry": entry.as_dict(),
        "status": "coverage_refused",
        "marginal_taxa": None,
    }
    if uncertainty["status"] != "generated":
        row.update(
            reason_code="uncertainty_not_generated",
            uncertainty_status=uncertainty["status"],
        )
        return row
    if (
        prediction is None
        or score.get("prediction_manifest_sha256")
        != prediction["prediction_manifest_sha256"]
        or score.get("record_id") != entry.record_id
        or score.get("bin_id") != entry.bin_id
        or score.get("prediction") != prediction["pollen_fraction"]
    ):
        raise ValidationRefusal(
            "observation_score_prediction_mismatch", entry.record_id
        )
    result = object_mapping(score.get("score"), "score")
    if result.get("status") != "scored":
        row.update(
            reason_code="observation_not_scored",
            observation_status=result.get("status"),
        )
        return row
    observation = object_mapping(score.get("observation"), "observation")
    if (
        observation.get("record_id") != entry.record_id
        or observation.get("bin_id") != entry.bin_id
        or observation.get("pollen_unit") != "count"
    ):
        raise ValidationRefusal("observation_score_scope_mismatch", entry.record_id)
    counts = observation.get("pollen_count")
    if not isinstance(counts, dict) or set(counts) != set(entry.taxa):
        row.update(reason_code="observation_taxa_mismatch")
        return row
    if any(v is None for v in counts.values()):
        row.update(reason_code="observation_count_missing")
        return row
    if any(type(v) is not int or v < 0 for v in counts.values()):
        row.update(reason_code="observation_count_invalid")
        return row
    total = sum(counts.values())
    row["observed_total"] = total
    if total != entry.effort:
        row.update(
            reason_code="observation_effort_mismatch", planned_effort=entry.effort
        )
        return row
    engine = object_mapping(uncertainty["engine_result"], "engine_result")
    intervals = object_mapping(engine["marginal_predictive_intervals"], "intervals")
    taxa_rows = []
    for taxon in entry.taxa:
        bounds = object_mapping(intervals[taxon], "bounds")
        lower, upper = (
            cast(int, bounds["lower_count"]),
            cast(int, bounds["upper_count"]),
        )
        taxa_rows.append(
            {
                "taxon": taxon,
                "observed_count": counts[taxon],
                "lower_count": lower,
                "upper_count": upper,
                "covered": lower <= counts[taxon] <= upper,
            }
        )
    row.update(
        status="coverage_scored",
        marginal_taxa=taxa_rows,
        covered_taxa=sum(t["covered"] is True for t in taxa_rows),
        requested_taxa=len(entry.taxa),
    )
    return row


def _score_pollen_observation_coverage(
    predictions: Path,
    uncertainty: Path,
    scores: Path,
    *,
    expected_uncertainty_sha256: str,
    expected_scores_sha256: str,
    destination: Path,
    purpose: str = "exploratory",
) -> ExperimentProduct:
    """Use existing heldout scores; never choose effort from heldout counts."""
    if purpose != "exploratory":
        raise ValidationRefusal("unsupported_observation_purpose", purpose)
    _disjoint(destination, predictions, uncertainty, scores)
    uncertainty_product, uncertainty_manifest = read_experiment_product(
        uncertainty, expected_manifest_sha256=expected_uncertainty_sha256
    )
    payload = object_mapping(uncertainty_manifest["scientific_payload"], "uncertainty")
    plan = ObservationUncertaintyPlan.from_dict(payload["plan"])
    parent, parent_manifest, predictions_by_key = validate_plan_parent(
        predictions, plan
    )
    if (
        uncertainty_manifest["profile"] != parent_manifest["profile"]
        or payload.get("prediction_manifest_sha256") != parent.manifest_sha256
        or payload.get("prediction_scientific_content_sha256")
        != parent.scientific_content_sha256
    ):
        raise ValidationRefusal(
            "observation_prediction_identity_mismatch", "Uncertainty parent differs"
        )
    retained = _uncertainty_rows(
        uncertainty_product, uncertainty_manifest, plan, predictions_by_key
    )
    scored_product, scored_manifest = read_experiment_product(
        scores, expected_manifest_sha256=expected_scores_sha256
    )
    if scored_manifest["profile"] != parent_manifest["profile"]:
        raise ValidationRefusal(
            "observation_score_parent_mismatch", "Score profile differs"
        )
    indexed = _scored_pollen(scored_product, scored_manifest, parent, plan)
    # Saved engine results reuse the authoritative constructor validation. This
    # requires the extra; it verifies content and constraints, not RNG replay.
    implementation = implementation_identity()
    binding = load_engine()
    code = capture_code_identity(binding)
    rows = []
    for entry, item in zip(plan.entries, retained, strict=True):
        if item["status"] == "generated":
            try:
                result = binding.api.PollenObservationDraws(
                    item["engine_result_canonical_json"], item["engine_result_sha256"]
                ).as_dict()
            except (ValueError, TypeError, AttributeError) as exc:
                raise ValidationRefusal("invalid_observation_draws", str(exc)) from exc
            if result != item["engine_result"]:
                raise ValidationRefusal(
                    "invalid_observation_draws",
                    "Retained engine bytes differ from displayed result",
                )
            declaration = object_mapping(result["declaration"], "declaration")
            expected = {
                "prediction_sha256": item["prediction_sha256"],
                "effort_evidence_sha256": entry.evidence_sha256,
                "effort": entry.effort,
                "seed": entry.seed,
                "repeats": plan.repeats,
                "coverage": plan.coverage,
                "taxa": list(entry.taxa),
                "input_pollen_fraction": predictions_by_key[entry.key][
                    "pollen_fraction"
                ],
            }
            if any(declaration[k] != v for k, v in expected.items()):
                raise ValidationRefusal(
                    "observation_draw_plan_mismatch", entry.record_id
                )
        rows.append(
            _coverage(
                entry, item, indexed[entry.key], predictions_by_key.get(entry.key)
            )
        )
    stage = stage_directory(destination)
    scientific: dict[str, object] = {
        "schema_version": "lra-pollen-marginal-coverage.v1",
        "profile": PROFILE,
        "prediction_manifest_sha256": parent.manifest_sha256,
        "uncertainty_manifest_sha256": uncertainty_product.manifest_sha256,
        "scores_manifest_sha256": scored_product.manifest_sha256,
        "plan_sha256": plan.sha256,
        "rows": rows,
        "requested_units": len(rows),
        "coverage_scored_units": sum(
            row["status"] == "coverage_scored" for row in rows
        ),
        "coverage_refused_units": sum(
            row["status"] == "coverage_refused" for row in rows
        ),
        "coverage_scope": "per_taxon_conditional_observation_marginals",
        "simultaneous_coverage_claimed": False,
        "independent_site_sampling_claimed": False,
        "scientific_acceptance": "not_evaluated",
        "final_policy_approval": False,
        "draw_validation": "engine_retained_schema_no_numerical_regeneration",
        "implementation": implementation,
        "engine_identity": code.payload(),
    }
    write_json(stage, "coverage.json", rows)
    for product in (parent, uncertainty_product, scored_product):
        read_experiment_product(
            product.directory, expected_manifest_sha256=product.manifest_sha256
        )
    if implementation_identity() != implementation:
        raise ValidationRefusal("observation_implementation_changed", str(stage))
    verify_code_identity(binding, code)
    return publish_phase(
        stage,
        destination,
        phase="observation_coverage",
        scientific=scientific,
        profile=cast(str, parent_manifest["profile"]),
    )


def score_pollen_observation_coverage(
    predictions: Path,
    uncertainty: Path,
    scores: Path,
    *,
    expected_uncertainty_sha256: str,
    expected_scores_sha256: str,
    destination: Path,
    purpose: str = "exploratory",
) -> ExperimentProduct:
    """Refuse malformed retained input without bypassing the original readers."""
    try:
        return _score_pollen_observation_coverage(
            predictions,
            uncertainty,
            scores,
            expected_uncertainty_sha256=expected_uncertainty_sha256,
            expected_scores_sha256=expected_scores_sha256,
            destination=destination,
            purpose=purpose,
        )
    except ValidationRefusal:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationRefusal("invalid_observation_coverage_input", str(exc)) from exc
