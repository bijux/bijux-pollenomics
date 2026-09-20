"""Separate outcome access after verified prediction publication."""

from __future__ import annotations

from ...contracts import Fold, ValidationRefusal, manifest_sha256
from ..configuration import (
    BLOCK_BASELINE_METHOD,
    BLOCK_METHODS,
    FITTED_METHOD,
    FITTED_ROLES,
    identity,
    object_list,
    object_mapping,
)


def _block_predictions(
    manifest: dict[str, object], rows: object
) -> tuple[dict[str, dict[str, object]], dict[tuple[str, str, str], dict[str, object]]]:
    from ...contracts import site_group_id
    from ..fitted import validate_fitted_prediction
    from ..fitted.admission import retained_training_admission
    from .training_mean import validate_training_mean_prediction

    scientific = object_mapping(manifest["scientific_payload"], "scientific_payload")
    if (
        manifest["phase"] != "predictions"
        or rows != scientific["predictions"]
        or scientific["methods"] != list(BLOCK_METHODS)
        or scientific["evaluation_roles"] != FITTED_ROLES
        or scientific["scientific_acceptance"] != "not_evaluated"
    ):
        raise ValidationRefusal(
            "invalid_block_prediction_inventory",
            "Profile, roles or numerical table differs",
        )
    ownership = {
        record: identity(group)
        for record, group in object_mapping(
            scientific["record_groups"], "record_groups"
        ).items()
    }
    folds: dict[str, dict[str, object]] = {}
    expected: set[tuple[str, str, str]] = set()
    admissions = object_mapping(scientific["block_admissions"], "block_admissions")
    models = object_mapping(scientific["block_model_sha256"], "block_model_sha256")
    baseline_models = object_mapping(
        scientific["block_baseline_model_sha256"], "block_baseline_model_sha256"
    )
    for value in object_list(scientific["folds"], "folds"):
        outer = object_mapping(value, "fold")
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
        if (
            fold.fold_id in folds
            or set(ownership) != {*fold.train_record_ids, *fold.test_record_ids}
            or {ownership[key] for key in fold.train_record_ids}
            != set(fold.train_group_ids)
            or {ownership[key] for key in fold.test_record_ids}
            != set(fold.test_group_ids)
        ):
            raise ValidationRefusal("invalid_block_fold_identity", fold.fold_id)
        for group in {*fold.train_group_ids, *fold.test_group_ids}:
            members = tuple(
                record for record, owner in ownership.items() if owner == group
            )
            if site_group_id(members) != group or len(members) != 1:
                raise ValidationRefusal("invalid_block_fold_identity", group)
        if fold.fold_id in admissions:
            admission = retained_training_admission(admissions[fold.fold_id], fold)
            if dict(admission.record_groups) != ownership:
                raise ValidationRefusal(
                    "block_admission_identity_mismatch", fold.fold_id
                )
        folds[fold.fold_id] = outer
        expected.update(
            (fold.fold_id, record, method)
            for record in fold.test_record_ids
            for method in BLOCK_METHODS
        )
    if (
        not folds
        or not set(admissions).issubset(folds)
        or not set(models).issubset(admissions)
        or not set(baseline_models).issubset(admissions)
        or not set(models).issubset(baseline_models)
        or manifest_sha256(scientific["folds"]) != scientific["split_manifest_sha256"]
    ):
        raise ValidationRefusal(
            "invalid_block_fold_identity", "Block inventory differs"
        )
    predictions = {}
    for value in object_list(rows, "predictions"):
        row = object_mapping(value, "prediction")
        _refuse_outcome_fields(row)
        key = (
            identity(row["fold_id"]),
            identity(row["record_id"]),
            identity(row["method"]),
        )
        if (
            key not in expected
            or key in predictions
            or row["group_id"] != ownership[key[1]]
            or row["training_admission"] != admissions.get(key[0])
            or (key[2] == FITTED_METHOD and row["model_sha256"] != models.get(key[0]))
            or (
                key[2] == BLOCK_BASELINE_METHOD
                and row["baseline_model_sha256"] != baseline_models.get(key[0])
            )
        ):
            raise ValidationRefusal(
                "invalid_block_prediction_inventory",
                "Target, model or admission differs",
            )
        if key[2] == FITTED_METHOD:
            validate_fitted_prediction(row, folds[key[0]])
        else:
            validate_training_mean_prediction(
                row,
                folds[key[0]],
                admission_payload=admissions[key[0]],
                expected_model_sha256=identity(baseline_models[key[0]]),
            )
        predictions[key] = row
    failed = set()
    refused = 0
    not_run = 0
    for value in object_list(scientific["failures"], "failures"):
        row = object_mapping(value, "failure")
        key = (
            identity(row["fold_id"]),
            identity(row["record_id"]),
            identity(row["method"]),
        )
        if (
            key not in expected
            or key in predictions
            or key in failed
            or row["group_id"] != ownership[key[1]]
            or row["status"] not in {"refused", "not_run"}
        ):
            raise ValidationRefusal(
                "invalid_block_prediction_inventory",
                "Duplicate or contradictory refusal",
            )
        identity(row["reason_code"])
        refused += row["status"] == "refused"
        not_run += row["status"] == "not_run"
        failed.add(key)
    counts = {
        "requested_folds": len(folds),
        "requested_predictions": len(expected),
        "generated_predictions": len(predictions),
        "failed_predictions": len(failed),
        "refused_predictions": refused,
        "not_run_predictions": not_run,
        "failed_folds": len({key[0] for key in failed}),
    }
    if (
        set(predictions) | failed != expected
        or any(
            type(scientific[field]) is not int or scientific[field] != number
            for field, number in counts.items()
        )
        or scientific["all_predictions_generated"] is not (not failed)
    ):
        raise ValidationRefusal(
            "incomplete_block_accounting", "Every target requires exactly one result"
        )
    return folds, predictions


def _refuse_outcome_fields(row: dict[str, object]) -> None:
    """Apply the outcome-free prediction boundary before method dispatch."""
    if any(key.startswith("observed_") or "outcome" in key for key in row):
        raise ValidationRefusal(
            "block_prediction_outcome_leakage",
            "Prediction rows cannot retain target outcomes or observations",
        )


def _validate_block_baseline(
    row: dict[str, object],
    outer: dict[str, object],
    admission_payload: object,
    expected_model_sha256: str,
) -> None:
    """Compatibility wrapper around the shared training-mean validator."""
    from .training_mean import validate_training_mean_prediction

    validate_training_mean_prediction(
        row,
        outer,
        admission_payload=admission_payload,
        expected_model_sha256=expected_model_sha256,
    )
