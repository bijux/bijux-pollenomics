"""Separate outcome access after verified prediction publication."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ..contracts import ValidationRefusal, finite_number, manifest_sha256
from ..metrics import score_pollen, score_vegetation
from .configuration import (
    BLOCK_PROFILE,
    FITTED_PROFILE,
    InputReference,
    identity,
    object_list,
    object_mapping,
)
from .inputs import read_reference
from .outputs import (
    ExperimentProduct,
    publish_phase,
    read_experiment_product,
    stage_directory,
    write_json,
)
from .reading import read_scoring_predictions
from .reading import read_withheld_predictions as read_withheld_predictions


def _score(
    target: str, prediction: dict[str, object], outcome: dict[str, object] | None
) -> dict[str, object]:
    if outcome is None:
        return {
            "status": "missing_observation",
            "mae_fraction": None,
            "reason": "target_not_supplied",
        }
    expected_unit = "fraction" if target == "vegetation_cover" else "count"
    unit_field = "vegetation_unit" if target == "vegetation_cover" else "pollen_unit"
    value_field = (
        "vegetation_fraction" if target == "vegetation_cover" else "pollen_count"
    )
    prediction_field = (
        "vegetation_fraction" if target == "vegetation_cover" else "pollen_fraction"
    )
    if outcome[unit_field] != expected_unit:
        raise ValidationRefusal("observation_unit_mismatch", target)
    if outcome[value_field] is None:
        return {
            "status": "missing_observation",
            "mae_fraction": None,
            "reason": "target_not_supplied",
        }
    predicted = {
        key: finite_number(value)
        for key, value in object_mapping(
            prediction[prediction_field], "prediction"
        ).items()
    }
    observed = object_mapping(outcome[value_field], value_field)
    if target == "vegetation_cover":
        values = {
            key: None if value is None else finite_number(value)
            for key, value in observed.items()
        }
        return score_vegetation(predicted, values).as_dict()
    counts: dict[str, int | None] = {}
    for key, value in observed.items():
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int)
        ):
            raise ValidationRefusal("invalid_pollen_counts", key)
        counts[key] = value
    return score_pollen(predicted, counts).as_dict()


def score_experiment_predictions(
    predictions: Path,
    *,
    expected_manifest_sha256: str,
    outcome_root: Path,
    outcome_inventory: Mapping[str, object],
    destination: Path,
    purpose: str = "exploratory",
) -> ExperimentProduct:
    """Score both synthetic targets separately; final mode is refused before access."""
    if purpose != "exploratory":
        raise ValidationRefusal(
            "final_experiment_not_implemented",
            "A qualified frozen policy/evaluator is required before final outcomes",
        )
    inventory = object_mapping(outcome_inventory, "outcome_inventory")
    if inventory.get("schema_version") == "lra-local-pollen-outcomes.v1":
        from .assimilation import _score_local_pollen_predictions

        return _score_local_pollen_predictions(
            predictions,
            expected_manifest_sha256=expected_manifest_sha256,
            outcome_root=outcome_root,
            outcome_inventory=inventory,
            destination=destination,
        )

    if (
        set(inventory) != {"schema_version", "data_kind", "records"}
        or inventory["schema_version"] != "lra-experiment-outcomes.v1"
        or inventory["data_kind"] != "synthetic"
    ):
        raise ValidationRefusal(
            "unsupported_experiment_outcomes",
            "Initial scoring inventory must explicitly declare synthetic data",
        )
    references = {
        identity(key): InputReference.parse(value, key)
        for key, value in object_mapping(inventory["records"], "records").items()
    }
    product, manifest, folds, prediction_rows, methods, ownership = (
        read_scoring_predictions(
            predictions, expected_manifest_sha256=expected_manifest_sha256
        )
    )
    catalogue = {
        identity(record)
        for fold in folds.values()
        for record in object_list(fold["test_record_ids"], "test_record_ids")
    }
    if not set(references).issubset(catalogue):
        raise ValidationRefusal(
            "unknown_experiment_outcome",
            "Outcome references must name held-out catalogue records",
        )
    profile = identity(manifest["profile"])
    method_field = (
        "method" if profile in {FITTED_PROFILE, BLOCK_PROFILE} else "baseline"
    )
    targets = ("vegetation_cover", "pollen_composition")
    stage = stage_directory(destination)
    scores: list[dict[str, object]] = []
    observations: dict[str, dict[str, object]] = {}
    observation_errors: dict[str, ValidationRefusal] = {}
    accesses: list[dict[str, object]] = []
    requested_targets = [
        (fold_id, identity(record))
        for fold_id, fold in sorted(folds.items())
        for record in object_list(fold["test_record_ids"], "test_record_ids")
    ]
    for fold_id, record_id in requested_targets:
        record_ids = [record_id]
        group_id = ownership[record_id]
        for method in methods:
            prediction = prediction_rows.get((fold_id, record_id, method))
            outcome = None
            if prediction is not None and record_id in references:
                assert record_id is not None
                if (
                    record_id not in observations
                    and record_id not in observation_errors
                ):
                    accesses.append(
                        {
                            "record_id": record_id,
                            "observation_sha256": references[record_id].sha256,
                            "prediction_manifest_sha256": product.manifest_sha256,
                            "ordering": "verified_published_predictions_before_outcome_open",
                        }
                    )
                    write_json(stage, "outcome_access.json", accesses)
                    try:
                        value = read_reference(outcome_root, references[record_id])
                        if (
                            set(value)
                            != {
                                "schema_version",
                                "data_kind",
                                "record_id",
                                "bin_id",
                                "vegetation_unit",
                                "pollen_unit",
                                "vegetation_fraction",
                                "pollen_count",
                            }
                            or value["schema_version"]
                            != "lra-experiment-observation.v1"
                            or value["data_kind"] != "synthetic"
                            or value["record_id"] != record_id
                            or value["bin_id"] != prediction["bin_id"]
                        ):
                            raise ValidationRefusal(
                                "observation_identity_mismatch", record_id
                            )
                        observations[record_id] = value
                    except ValidationRefusal as exc:
                        observation_errors[record_id] = exc
                outcome = observations.get(record_id)
            for target in targets:
                row: dict[str, object] = {
                    "fold_id": fold_id,
                    "group_id": group_id,
                    "record_id": record_id,
                    "record_ids": record_ids,
                    method_field: method,
                    "target": target,
                    "error_unit": "fraction",
                    "bin_id": None if prediction is None else prediction["bin_id"],
                }
                if profile in {FITTED_PROFILE, BLOCK_PROFILE}:
                    row.update(
                        method_kind="fitted_spatial",
                        evaluation_role="heldout_prediction",
                    )
                if prediction is None:
                    row["score"] = {"status": "prediction_failed", "mae_fraction": None}
                else:
                    try:
                        if record_id in observation_errors:
                            raise observation_errors[record_id]
                        row["score"] = _score(target, prediction, outcome)
                    except ValidationRefusal as exc:
                        row["score"] = {
                            "status": "observation_refused",
                            "reason_code": exc.reason_code,
                            "detail": str(exc),
                            "mae_fraction": None,
                        }
                    row["prediction_manifest_sha256"] = prediction[
                        "prediction_manifest_sha256"
                    ]
                    row["prediction"] = prediction[
                        "vegetation_fraction"
                        if target == "vegetation_cover"
                        else "pollen_fraction"
                    ]
                if record_id in references and outcome is not None:
                    row["observation_sha256"] = references[record_id].sha256
                    row["observation_reference"] = {
                        "path": references[record_id].path,
                        "sha256": references[record_id].sha256,
                    }
                    row["observation"] = outcome
                scores.append(row)
    summaries = []
    for method in methods:
        for target in targets:
            values = [
                object_mapping(row["score"], "score")
                for row in scores
                if row[method_field] == method and row["target"] == target
            ]
            statuses = sorted({identity(value["status"]) for value in values})
            finite_errors = [
                finite_number(value["mae_fraction"])
                for value in values
                if value["status"] == "scored"
            ]
            summaries.append(
                {
                    method_field: method,
                    "target": target,
                    "scoring_unit": "heldout_group_within_original_spatial_block"
                    if profile == BLOCK_PROFILE
                    else "outer_site_group",
                    "independence": "within_block_targets_correlated_and_training_blocks_overlap"
                    if profile == BLOCK_PROFILE
                    else "overlapping_training_cv_not_independent_fixed_model",
                    "requested": len(requested_targets),
                    "by_status": {
                        status: sum(value["status"] == status for value in values)
                        for status in statuses
                    },
                    "mean_mae_fraction": sum(finite_errors) / len(finite_errors)
                    if finite_errors
                    else None,
                    "scored": len(finite_errors),
                    "zero_probability_positive_count": sum(
                        value.get("zero_probability_positive_count") is True
                        for value in values
                    ),
                    "interval_coverage": None,
                    "uncertainty_status": "intervals_not_implemented",
                }
            )
    indexed = {
        (str(row["fold_id"]), str(row[method_field]), str(row["target"])): row
        for row in scores
    }
    paired = []
    if "training_mean" in methods:
        for row in scores:
            if row[method_field] == "training_mean":
                continue
            reference = indexed[
                (str(row["fold_id"]), "training_mean", str(row["target"]))
            ]
            actual_score, base_score = (
                object_mapping(row["score"], "score"),
                object_mapping(reference["score"], "score"),
            )
            if actual_score["status"] == base_score["status"] == "scored":
                paired.append(
                    {
                        "fold_id": row["fold_id"],
                        "group_id": row["group_id"],
                        "record_id": row["record_id"],
                        "baseline": row[method_field],
                        "reference_baseline": "training_mean",
                        "target": row["target"],
                        "mae_improvement_fraction": finite_number(
                            base_score["mae_fraction"]
                        )
                        - finite_number(actual_score["mae_fraction"]),
                    }
                )
    read_experiment_product(
        predictions, expected_manifest_sha256=expected_manifest_sha256
    )
    scientific: dict[str, object] = {
        "profile": profile,
        "prediction_manifest_sha256": product.manifest_sha256,
        "prediction_scientific_content_sha256": product.scientific_content_sha256,
        "outcome_inventory_sha256": manifest_sha256(inventory),
        "scores": scores,
        "summaries": summaries,
        "paired_baseline_differences": paired,
        "uncertainty_status": "intervals_not_implemented",
        "scientific_acceptance": "not_evaluated",
    }
    for name, member in (
        ("scores.json", scores),
        ("summaries.json", summaries),
        ("paired_baseline_differences.json", paired),
        ("outcome_inventory.json", inventory),
        ("outcome_access.json", accesses),
    ):
        write_json(stage, name, member)
    return publish_phase(
        stage, destination, phase="scores", scientific=scientific, profile=profile
    )
