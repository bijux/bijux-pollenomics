"""Separate outcome access after verified prediction publication."""

from __future__ import annotations

from pathlib import Path

from ..contracts import Fold, ValidationRefusal, finite_number, manifest_sha256
from ..metrics import closed_composition
from ..splits import assert_allowed_inputs
from .configuration import (
    BASELINES,
    FITTED_METHOD,
    FITTED_PROFILE,
    FITTED_ROLES,
    PROFILE,
    identity,
    object_list,
    object_mapping,
)
from .outputs import (
    ExperimentProduct,
    read_experiment_product,
    read_member,
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
    method_field = "method" if fitted else "baseline"
    method_list = "methods" if fitted else "baselines"
    methods = tuple(
        identity(value) for value in object_list(scientific[method_list], method_list)
    )
    if (
        not methods
        or len(set(methods)) != len(methods)
        or not set(methods).issubset((FITTED_METHOD,) if fitted else BASELINES)
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
        if fitted:
            from .fitted import validate_fitted_prediction

            validate_fitted_prediction(row, folds[prediction_key[0]])
        else:
            _validate_baseline_prediction(row, folds[prediction_key[0]])
        predictions[prediction_key] = row
    failures = object_list(scientific["failures"], "failures")
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


def read_withheld_predictions(
    directory: Path,
    *,
    expected_manifest_sha256: str,
) -> tuple[
    ExperimentProduct,
    dict[str, object],
    dict[str, dict[str, object]],
    dict[tuple[str, str], dict[str, object]],
    tuple[str, ...],
]:
    """Authenticate owned-copy withheld rows; scientific authorship stays unverified."""
    product, manifest = read_experiment_product(
        directory, expected_manifest_sha256=expected_manifest_sha256
    )
    if manifest["profile"] not in {PROFILE, FITTED_PROFILE}:
        raise ValidationRefusal(
            "experiment_outcome_profile_mismatch",
            "Require an explicit all-target-pollen-withheld profile",
        )
    try:
        folds, predictions, methods = _predictions(
            manifest, read_member(product, "predictions.json")
        )
    except ValidationRefusal:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationRefusal("invalid_prediction_inventory", str(exc)) from exc
    return product, manifest, folds, predictions, methods


def read_spatial_block_predictions(
    directory: Path,
    *,
    expected_manifest_sha256: str,
) -> tuple[
    ExperimentProduct,
    dict[str, object],
    dict[str, dict[str, object]],
    dict[tuple[str, str, str], dict[str, object]],
    tuple[str, ...],
]:
    """Authenticate multi-target original blocks without changing singleton reader keys."""
    from .configuration import BLOCK_PROFILE

    product, manifest = read_experiment_product(
        directory, expected_manifest_sha256=expected_manifest_sha256
    )
    if manifest["profile"] != BLOCK_PROFILE:
        raise ValidationRefusal(
            "experiment_outcome_profile_mismatch",
            "Require the explicit spatial-block profile",
        )
    try:
        folds, rows = _block_predictions(
            manifest, read_member(product, "predictions.json")
        )
        from .fitted.metadata import validate_block_metadata

        validate_block_metadata(
            read_member(product, "experiment.json"),
            object_mapping(manifest["scientific_payload"], "scientific_payload"),
            folds,
            rows,
            read_member(product, "models.json"),
        )
    except ValidationRefusal:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationRefusal("invalid_block_prediction_inventory", str(exc)) from exc
    return product, manifest, folds, rows, (FITTED_METHOD,)


def _block_predictions(
    manifest: dict[str, object], rows: object
) -> tuple[dict[str, dict[str, object]], dict[tuple[str, str, str], dict[str, object]]]:
    from ..contracts import site_group_id
    from .fitted import validate_fitted_prediction
    from .fitted.admission import retained_training_admission

    scientific = object_mapping(manifest["scientific_payload"], "scientific_payload")
    if (
        manifest["phase"] != "predictions"
        or rows != scientific["predictions"]
        or scientific["methods"] != [FITTED_METHOD]
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
            (fold.fold_id, record, FITTED_METHOD) for record in fold.test_record_ids
        )
    if (
        not folds
        or not set(admissions).issubset(folds)
        or not set(models).issubset(admissions)
        or manifest_sha256(scientific["folds"]) != scientific["split_manifest_sha256"]
    ):
        raise ValidationRefusal(
            "invalid_block_fold_identity", "Block inventory differs"
        )
    predictions = {}
    for value in object_list(rows, "predictions"):
        row = object_mapping(value, "prediction")
        key = (
            identity(row["fold_id"]),
            identity(row["record_id"]),
            identity(row["method"]),
        )
        if (
            key not in expected
            or key in predictions
            or row["group_id"] != ownership[key[1]]
            or row["model_sha256"] != models.get(key[0])
            or row["training_admission"] != admissions.get(key[0])
        ):
            raise ValidationRefusal(
                "invalid_block_prediction_inventory",
                "Target, model or admission differs",
            )
        validate_fitted_prediction(row, folds[key[0]])
        predictions[key] = row
    failed = set()
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
        failed.add(key)
    counts = {
        "requested_folds": len(folds),
        "requested_predictions": len(expected),
        "generated_predictions": len(predictions),
        "failed_predictions": len(failed),
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


def read_scoring_predictions(
    directory: Path,
    *,
    expected_manifest_sha256: str,
) -> tuple[
    ExperimentProduct,
    dict[str, object],
    dict[str, dict[str, object]],
    dict[tuple[str, str, str], dict[str, object]],
    tuple[str, ...],
    dict[str, str],
]:
    """One authoritative intake for scoring; external singleton API stays unchanged."""
    from .configuration import BLOCK_PROFILE

    _, checked = read_experiment_product(
        directory, expected_manifest_sha256=expected_manifest_sha256
    )
    if checked["profile"] == BLOCK_PROFILE:
        product, manifest, folds, rows, methods = read_spatial_block_predictions(
            directory, expected_manifest_sha256=expected_manifest_sha256
        )
        ownership = {
            record: identity(group)
            for record, group in object_mapping(
                object_mapping(manifest["scientific_payload"], "scientific_payload")[
                    "record_groups"
                ],
                "record_groups",
            ).items()
        }
        return product, manifest, folds, rows, methods, ownership
    product, manifest, folds, singleton, methods = read_withheld_predictions(
        directory, expected_manifest_sha256=expected_manifest_sha256
    )
    rows = {
        (fold, identity(value["record_id"]), method): value
        for (fold, method), value in singleton.items()
    }
    ownership = {
        identity(object_list(fold["test_record_ids"], "test_record_ids")[0]): identity(
            object_list(fold["test_group_ids"], "test_group_ids")[0]
        )
        for fold in folds.values()
    }
    return product, manifest, folds, rows, methods, ownership
