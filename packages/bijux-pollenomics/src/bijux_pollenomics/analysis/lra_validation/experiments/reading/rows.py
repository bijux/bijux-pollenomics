"""Separate outcome access after verified prediction publication."""

from __future__ import annotations

from ...contracts import Fold, ValidationRefusal, finite_number, manifest_sha256
from ...metrics import closed_composition
from ...splits import assert_allowed_inputs
from ..configuration import (
    BASELINES,
    FITTED_METHOD,
    FITTED_METHODS,
    FITTED_PROFILE,
    FITTED_ROLES,
    TRAINING_MEAN_METHOD,
    identity,
    object_list,
    object_mapping,
)


def _predictions(
    manifest: dict[str, object], rows: object
) -> tuple[
    dict[str, dict[str, object]],
    dict[tuple[str, str], dict[str, object]],
    tuple[str, ...],
]:
    scientific = object_mapping(manifest["scientific_payload"], "scientific_payload")
    if manifest["phase"] != "predictions" or rows != scientific["predictions"]:
        raise ValidationRefusal(
            "invalid_prediction_inventory", "Phase or scientific table differs"
        )
    folds = {}
    for value in object_list(scientific["folds"], "folds"):
        fold = object_mapping(value, "fold")
        key = identity(fold["fold_id"])
        if (
            key in folds
            or len(object_list(fold["test_group_ids"], "test_group_ids")) != 1
        ):
            raise ValidationRefusal(
                "invalid_prediction_inventory", "Invalid outer fold identities"
            )
        folds[key] = fold
    fitted = manifest["profile"] == FITTED_PROFILE
    paired = (
        fitted
        and scientific.get("schema_version")
        == "lra-grouped-outer-paired-predictions.v1"
    )
    method_field = "method" if fitted else "baseline"
    method_list = "methods" if fitted else "baselines"
    methods = tuple(
        identity(value) for value in object_list(scientific[method_list], method_list)
    )
    if (
        not methods
        or len(set(methods)) != len(methods)
        or (fitted and not paired and "schema_version" in scientific)
        or (fitted and methods != (FITTED_METHODS if paired else (FITTED_METHOD,)))
        or (not fitted and not set(methods).issubset(BASELINES))
        or (fitted and scientific.get("evaluation_roles") != FITTED_ROLES)
    ):
        raise ValidationRefusal(
            "invalid_prediction_methods", "Invalid methods or roles"
        )
    predictions = {}
    for value in object_list(rows, "predictions"):
        row = object_mapping(value, "prediction")
        prediction_key = (identity(row["fold_id"]), identity(row[method_field]))
        if (
            prediction_key in predictions
            or prediction_key[0] not in folds
            or prediction_key[1] not in methods
            or any(key.startswith("observed_") or "outcome" in key for key in row)
        ):
            raise ValidationRefusal(
                "invalid_prediction_inventory", "Duplicate or unknown prediction key"
            )
        if object_list(
            folds[prediction_key[0]]["test_record_ids"], "test_record_ids"
        ) != [row["record_id"]]:
            raise ValidationRefusal(
                "invalid_prediction_inventory",
                "Prediction target differs from the held-out record",
            )
        if fitted and prediction_key[1] == FITTED_METHOD:
            from ..fitted import validate_fitted_prediction

            validate_fitted_prediction(row, folds[prediction_key[0]])
        elif fitted and prediction_key[1] == TRAINING_MEAN_METHOD:
            from .training_mean import validate_training_mean_prediction

            validate_training_mean_prediction(row, folds[prediction_key[0]])
        else:
            _validate_baseline_prediction(row, folds[prediction_key[0]])
        predictions[prediction_key] = row
    failures = object_list(scientific["failures"], "failures")
    if paired:
        expected = {(fold, method) for fold in folds for method in methods}
        paired_failures: dict[tuple[str, str], str] = {}
        for value in failures:
            row = object_mapping(value, "failure")
            terminal_key = (identity(row["fold_id"]), identity(row["method"]))
            outer = folds.get(terminal_key[0])
            if (
                outer is None
                or terminal_key not in expected
                or terminal_key in predictions
                or terminal_key in paired_failures
                or object_list(row.get("record_ids"), "record_ids")
                != object_list(outer["test_record_ids"], "test_record_ids")
                or row.get("status") not in {"refused", "not_run"}
                or not isinstance(row.get("reason_code"), str)
                or not row["reason_code"]
                or any(
                    name.startswith("observed_") or "outcome" in name for name in row
                )
            ):
                raise ValidationRefusal(
                    "invalid_prediction_inventory",
                    "Duplicate, contradictory or malformed paired terminal",
                )
            status = identity(row["status"])
            if (status == "not_run") != (
                row["reason_code"] == "experiment_interrupted"
            ):
                raise ValidationRefusal(
                    "invalid_prediction_inventory",
                    "Paired interruption status and reason differ",
                )
            paired_failures[terminal_key] = status
        terminal = dict.fromkeys(predictions, "predicted")
        terminal.update(paired_failures)
        ordered = [(fold, method) for fold in folds for method in methods]
        first_not_run = next(
            (
                index
                for index, key in enumerate(ordered)
                if terminal.get(key) == "not_run"
            ),
            None,
        )
        counts = {
            "requested_folds": len(folds),
            "requested_predictions": len(expected),
            "generated_predictions": len(predictions),
            "failed_predictions": len(paired_failures),
            "refused_predictions": sum(
                value == "refused" for value in paired_failures.values()
            ),
            "not_run_predictions": sum(
                value == "not_run" for value in paired_failures.values()
            ),
            "failed_folds": len({terminal_key[0] for terminal_key in paired_failures}),
        }
        if (
            set(predictions) | set(paired_failures) != expected
            or (
                first_not_run is not None
                and any(
                    terminal.get(key) != "not_run" for key in ordered[first_not_run:]
                )
            )
            or any(
                type(scientific.get(field)) is not int or scientific[field] != count
                for field, count in counts.items()
            )
            or scientific.get("interrupted") is not (first_not_run is not None)
            or scientific.get("all_predictions_generated") is not (not paired_failures)
            or scientific.get("scientific_acceptance") != "not_evaluated"
        ):
            raise ValidationRefusal(
                "invalid_prediction_inventory",
                "Paired fold/method terminal accounting differs",
            )
        return folds, predictions, methods
    failed = {
        identity(object_mapping(value, "failure")["fold_id"]) for value in failures
    }
    complete = {
        fold
        for fold in folds
        if all((fold, method) in predictions for method in methods)
    }
    if (
        len(failed) != len(failures)
        or complete & failed
        or complete | failed != set(folds)
    ):
        raise ValidationRefusal(
            "invalid_prediction_inventory",
            "Every outer fold needs complete predictions or one refusal",
        )
    if any(fold in failed for fold, _ in predictions) or len(predictions) != len(
        complete
    ) * len(methods):
        raise ValidationRefusal(
            "invalid_prediction_inventory", "Partial prediction folds are not admitted"
        )
    return folds, predictions, methods


def _validate_baseline_prediction(
    row: dict[str, object], outer: dict[str, object]
) -> None:
    inner = object_mapping(row["prediction_manifest"], "prediction_manifest")
    if (
        manifest_sha256(inner) != row["prediction_manifest_sha256"]
        or inner["fold"] != outer
        or inner["schema_version"] != "lra-heldout-prediction.v1"
        or inner["experiment"] != "all_target_pollen_withheld"
        or inner["spatial_method"] != row["baseline"]
        or outer["test_group_ids"] != [inner["target_group_id"]]
        or inner["vegetation_fraction"] != row["vegetation_fraction"]
        or inner["pollen_fraction"] != row["pollen_fraction"]
        or inner["scientific_acceptance"] != "not_evaluated_by_prediction"
        or inner["uncertainty_status"]
        != "deterministic_point_prediction_no_predictive_intervals"
    ):
        raise ValidationRefusal(
            "baseline_prediction_identity_mismatch",
            "Wrapper, inner prediction or withheld role differs",
        )
    predictors = object_list(
        inner.get("predictor_group_ids", outer["train_group_ids"]),
        "predictor_group_ids",
    )
    if (
        not predictors
        or len(set(predictors)) != len(predictors)
        or not set(predictors).issubset(
            object_list(outer["train_group_ids"], "train_group_ids")
        )
    ):
        raise ValidationRefusal(
            "baseline_predictor_group_mismatch",
            "Predictors must be original training groups",
        )
    taxa = object_list(
        object_mapping(inner["forward_inputs"], "forward_inputs")["taxa"], "taxa"
    )
    for field in ("vegetation_fraction", "pollen_fraction"):
        values = object_mapping(row[field], field)
        if set(values) != set(taxa):
            raise ValidationRefusal("baseline_taxon_mismatch", field)
        closed_composition({key: finite_number(value) for key, value in values.items()})
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
    graph = {
        key: tuple(identity(parent) for parent in object_list(value, "parents"))
        for key, value in object_mapping(
            inner["input_lineage"], "input_lineage"
        ).items()
    }
    context = object_mapping(inner["forward_inputs"], "forward_inputs")
    external = tuple(
        identity(key)
        for field in ("regional_input_ids", "parameter_input_ids", "geometry_input_ids")
        for key in object_list(context[field], field)
    ) + (identity(context["temporal_support_id"]),)
    closure = assert_allowed_inputs(
        fold,
        tuple(
            identity(key)
            for key in object_list(
                inner["allowed_input_closure"], "allowed_input_closure"
            )
        ),
        graph,
        admitted_external_ids=external,
    )
    if list(closure) != inner["allowed_input_closure"] or not set(
        fold.train_record_ids
    ).issubset(closure):
        raise ValidationRefusal(
            "baseline_training_lineage_mismatch",
            "Complete original training ancestry is required",
        )
