"""Strict retained intake for grouped-outer local-pollen predictions."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from ....contracts import ValidationRefusal, canonical_json
from ....splits import grouped_leave_one_out
from ...configuration import (
    LOCAL_EVALUATION_ROLES,
    LOCAL_METHOD,
    LOCAL_PROFILE,
    identity,
    object_list,
    object_mapping,
)
from ...outputs import (
    ExperimentProduct,
    local_prediction_rows,
    read_experiment_product,
    read_member,
)
from .batch import batch_evidence
from .evidence import specification, validate_prediction_evidence

_SCIENTIFIC_FIELDS = set(
    "profile method method_kind evaluation_roles "
    "pollen_eligible_for_heldout_acceptance "
    "folds predictions failures requested_folds requested_predictions "
    "generated_predictions failed_folds interrupted all_predictions_generated "
    "implementation engine_identity uncertainty_status".split()
)
_FAILURE_FIELDS = set(
    "fold_id record_ids status reason_code detail batch_item_id".split()
)


def _terminal_accounting(
    scientific: dict[str, object],
    folds: dict[str, dict[str, object]],
    predictions: dict[str, dict[str, object]],
) -> None:
    ordered = tuple(folds)
    failures: dict[str, str] = {}
    for value in object_list(scientific["failures"], "failures"):
        row = object_mapping(value, "failure")
        fold_id = identity(row["fold_id"])
        status = row.get("status")
        reason = row.get("reason_code")
        if (
            not {"fold_id", "record_ids", "status", "reason_code"}.issubset(row)
            or not set(row).issubset(_FAILURE_FIELDS)
            or fold_id not in folds
            or fold_id in predictions
            or fold_id in failures
            or row.get("record_ids") != folds[fold_id]["test_record_ids"]
            or status not in {"refused", "not_run"}
            or (status == "not_run") is not (reason == "experiment_interrupted")
        ):
            raise ValidationRefusal("invalid_local_prediction_failure", fold_id)
        identity(reason)
        failures[fold_id] = cast(str, status)
    terminal = {key: "predicted" for key in predictions}
    terminal.update(failures)
    first_not_run = next(
        (index for index, key in enumerate(ordered) if terminal.get(key) == "not_run"),
        None,
    )
    counts = {
        "requested_folds": len(folds),
        "requested_predictions": len(folds),
        "generated_predictions": len(predictions),
        "failed_folds": len(failures),
    }
    if (
        set(terminal) != set(folds)
        or any(
            type(scientific.get(key)) is not int or scientific.get(key) != value
            for key, value in counts.items()
        )
        or scientific.get("interrupted")
        is not any(status == "not_run" for status in failures.values())
        or scientific.get("all_predictions_generated") is not (not failures)
        or (
            first_not_run is not None
            and any(terminal[key] != "not_run" for key in ordered[first_not_run:])
        )
    ):
        raise ValidationRefusal(
            "incomplete_local_prediction_accounting", "Terminal denominator differs"
        )


def read_local_pollen_predictions(
    directory: Path,
    *,
    expected_manifest_sha256: str,
) -> tuple[
    ExperimentProduct,
    dict[str, object],
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
]:
    """Authenticate complete grouped-local inputs and outputs without outcomes."""
    product, manifest = read_experiment_product(
        directory, expected_manifest_sha256=expected_manifest_sha256
    )
    if manifest["profile"] != LOCAL_PROFILE:
        raise ValidationRefusal(
            "experiment_outcome_profile_mismatch",
            "Require grouped local-pollen profile",
        )
    try:
        scientific = object_mapping(manifest["scientific_payload"], "scientific")
        metadata = object_mapping(read_member(product, "experiment.json"), "experiment")
        spec, catalogue = specification(
            metadata, profile=LOCAL_PROFILE, method=LOCAL_METHOD
        )
        records = [site.record for site in spec.sites]
        generated_folds = grouped_leave_one_out(records)
        expected_folds = {fold.fold_id: fold.as_dict() for fold in generated_folds}
        predictions_value = read_member(product, "predictions.json")
        failures_value = read_member(product, "failures.json")
        folds_value = read_member(product, "folds.json")
        operations_value = read_member(product, "operations.json")
        if (
            set(scientific) != _SCIENTIFIC_FIELDS
            or manifest["phase"] != "predictions"
            or scientific["profile"] != LOCAL_PROFILE
            or scientific["method"] != LOCAL_METHOD
            or scientific["method_kind"] != "local_pollen_assimilation"
            or scientific["evaluation_roles"] != LOCAL_EVALUATION_ROLES
            or scientific["pollen_eligible_for_heldout_acceptance"] is not False
            or scientific["uncertainty_status"]
            != "point_predictions_only_intervals_not_implemented"
            or predictions_value != scientific["predictions"]
            or failures_value != scientific["failures"]
            or folds_value != scientific["folds"]
            or canonical_json(folds_value)
            != canonical_json([fold.as_dict() for fold in generated_folds])
        ):
            raise ValidationRefusal(
                "invalid_local_prediction_inventory", "Product posture differs"
            )
        object_mapping(scientific["implementation"], "implementation")
        object_mapping(scientific["engine_identity"], "engine_identity")
        folds, predictions = local_prediction_rows(
            manifest, predictions_value, metadata["observation_channels"]
        )
        if canonical_json(folds) != canonical_json(expected_folds):
            raise ValidationRefusal(
                "invalid_local_prediction_inventory", "Fold identities differ"
            )
        expected_records = tuple(fold.test_record_ids[0] for fold in generated_folds)
        requests, results = batch_evidence(
            product,
            manifest,
            operations_value,
            expected_records=expected_records,
        )
        terminal_records = {
            identity(object_list(fold["test_record_ids"], "test_records")[0])
            for fold in folds.values()
        }
        if set(requests) - terminal_records or set(results) != set(requests):
            raise ValidationRefusal(
                "invalid_local_batch_evidence", "Batch target universe differs"
            )
        for fold_id, row in predictions.items():
            fold = folds[fold_id]
            record = identity(row["record_id"])
            request = requests.get(record)
            operation = results.get(record)
            if request is None or operation is None:
                raise ValidationRefusal(
                    "invalid_local_batch_evidence", "Prediction lacks batch evidence"
                )
            validate_prediction_evidence(
                row,
                spec=spec,
                catalogue=catalogue,
                fold=fold,
                request=request,
                operation=operation,
            )
        _terminal_accounting(scientific, folds, predictions)
        return product, manifest, folds, predictions
    except ValidationRefusal:
        raise
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        raise ValidationRefusal("invalid_local_prediction_inventory", str(exc)) from exc
