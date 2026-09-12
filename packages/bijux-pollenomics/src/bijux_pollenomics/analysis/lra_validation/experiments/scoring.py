"""Separate outcome access after verified prediction publication."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ..contracts import Fold, ValidationRefusal, finite_number, manifest_sha256
from ..metrics import closed_composition, score_pollen, score_vegetation
from ..splits import assert_allowed_inputs
from .configuration import (
    FITTED_METHOD,
    FITTED_PROFILE,
    FITTED_ROLES,
    PROFILE,
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
    read_member,
    stage_directory,
    write_json,
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
    if fitted and (
        methods != (FITTED_METHOD,)
        or scientific.get("evaluation_roles") != FITTED_ROLES
    ):
        raise ValidationRefusal(
            "invalid_fitted_prediction_product",
            "Fitted methods and target roles differ",
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
    product, manifest, folds, prediction_rows, methods = read_withheld_predictions(
        predictions, expected_manifest_sha256=expected_manifest_sha256
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
    method_field = "method" if profile == FITTED_PROFILE else "baseline"
    targets = ("vegetation_cover", "pollen_composition")
    stage = stage_directory(destination)
    scores: list[dict[str, object]] = []
    observations: dict[str, dict[str, object]] = {}
    observation_errors: dict[str, ValidationRefusal] = {}
    accesses: list[dict[str, object]] = []
    for fold_id, fold in sorted(folds.items()):
        record_ids = object_list(fold["test_record_ids"], "test_record_ids")
        record_id = identity(record_ids[0]) if len(record_ids) == 1 else None
        group_id = identity(object_list(fold["test_group_ids"], "test_group_ids")[0])
        for method in methods:
            prediction = prediction_rows.get((fold_id, method))
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
                if profile == FITTED_PROFILE:
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
                    "scoring_unit": "outer_site_group",
                    "independence": "overlapping_training_cv_not_independent_fixed_model",
                    "requested": len(folds),
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
