"""Separate outcome access after verified prediction publication."""

from __future__ import annotations

import json

from ...contracts import (
    Fold,
    ValidationRefusal,
    canonical_json,
    finite_number,
    manifest_sha256,
)
from ...metrics import closed_composition
from ...splits import assert_training_inputs
from ..configuration import (
    BLOCK_BASELINE_METHOD,
    BLOCK_METHODS,
    FITTED_METHOD,
    FITTED_ROLES,
    identity,
    object_list,
    object_mapping,
)
from ..outputs import validate_fitted_preparation


def _block_predictions(
    manifest: dict[str, object], rows: object
) -> tuple[dict[str, dict[str, object]], dict[tuple[str, str, str], dict[str, object]]]:
    from ...contracts import site_group_id
    from ..fitted import validate_fitted_prediction
    from ..fitted.admission import retained_training_admission

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
            _validate_block_baseline(
                row,
                folds[key[0]],
                admissions[key[0]],
                identity(baseline_models[key[0]]),
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
    """Authenticate an outcome-free mean over exact admitted reconstructions.

    Vegetation arithmetic and all source/support lineage are recomputed here. The
    optional numerical forward engine is intentionally not replayed after product
    publication: pollen bytes are authenticated by the exact row digest inside the
    predictions member and the caller-pinned outer product manifest. Rehashing a
    changed pollen vector therefore creates a different product identity rather
    than retroactively validating it against a potentially different engine build.
    """
    from ..fitted.admission import retained_training_admission

    _refuse_outcome_fields(row)
    inner = object_mapping(row["baseline_model_manifest"], "baseline_model_manifest")
    if (
        row["profile"] != "synthetic-spatial-block-fitted-v1"
        or row["method"] != BLOCK_BASELINE_METHOD
        or row["method_kind"] != "admitted_reconstruction_training_mean"
        or row["evaluation_roles"] != FITTED_ROLES
        or row["outer_fold"] != outer
        or row["scientific_acceptance"] != "not_evaluated"
        or row["uncertainty_status"] != "deterministic_point_baseline_no_intervals"
        or manifest_sha256(
            {
                key: value
                for key, value in row.items()
                if key != "prediction_manifest_sha256"
            }
        )
        != row["prediction_manifest_sha256"]
        or manifest_sha256(inner) != row["baseline_model_sha256"]
        or row["baseline_model_sha256"] != expected_model_sha256
    ):
        raise ValidationRefusal(
            "block_baseline_identity_mismatch",
            "Method, posture, model or exact row identity differs",
        )
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
    admission = retained_training_admission(admission_payload, fold)
    ownership = dict(admission.record_groups)
    record = identity(row["record_id"])
    group = identity(row["group_id"])
    if (
        record not in fold.test_record_ids
        or ownership[record] != group
        or inner.get("schema_version") != "lra-spatial-block-training-mean.v1"
        or inner.get("method") != BLOCK_BASELINE_METHOD
        or inner.get("method_kind") != "admitted_reconstruction_training_mean"
        or inner.get("fold") != outer
        or canonical_json(inner.get("training_admission"))
        != canonical_json(admission.as_dict())
        or inner.get("support") != row["support"]
        or inner.get("scientific_acceptance") != "not_evaluated"
        or inner.get("uncertainty_status")
        != "deterministic_point_baseline_no_intervals"
    ):
        raise ValidationRefusal(
            "block_baseline_admission_mismatch",
            "Target, fold, support or training admission differs",
        )
    anchor = identity(inner["regional_anchor_record_id"])
    anchor_group = identity(inner["regional_anchor_group_id"])
    products = [
        object_mapping(value, "training_product")
        for value in object_list(inner["training_products"], "training_products")
    ]
    compositions = {
        identity(group_id): closed_composition(
            {
                identity(taxon): finite_number(value)
                for taxon, value in object_mapping(values, "composition").items()
            }
        )
        for group_id, values in object_mapping(
            inner["training_compositions"], "training_compositions"
        ).items()
    }
    retained = {
        identity(value["group_id"]): closed_composition(
            {
                identity(taxon): finite_number(fraction)
                for taxon, fraction in object_mapping(
                    value["composition"], "composition"
                ).items()
            }
        )
        for value in products
    }
    product_records = tuple(identity(value["record_id"]) for value in products)
    predictor_groups = tuple(
        identity(value)
        for value in object_list(inner["predictor_group_ids"], "predictor_group_ids")
    )
    if (
        not compositions
        or len(products) != len(retained)
        or len(products) != len(set(product_records))
        or retained != compositions
        or tuple(sorted(compositions)) != predictor_groups
        or set(compositions) != set(admission.admitted_group_ids) - {anchor_group}
        or anchor not in admission.admitted_record_ids
        or ownership[anchor] != anchor_group
        or set(product_records) != set(admission.admitted_record_ids) - {anchor}
        or any(
            ownership[record] != identity(product["group_id"])
            for record, product in zip(product_records, products, strict=True)
        )
        or inner["regional_value_source_record_ids"] != [anchor]
        or set(
            object_list(
                inner["regional_identity_source_record_ids"],
                "regional_identity_source_record_ids",
            )
        )
        != set(admission.admitted_record_ids)
    ):
        raise ValidationRefusal(
            "block_baseline_training_mismatch",
            "Training products, groups or regional ancestry differ",
        )
    graph = {
        identity(key): tuple(
            identity(parent) for parent in object_list(value, "lineage_parents")
        )
        for key, value in object_mapping(
            inner["input_lineage"], "input_lineage"
        ).items()
    }
    inputs = tuple(
        identity(value)
        for value in object_list(inner["training_input_ids"], "training_input_ids")
    )
    external = tuple(
        identity(value)
        for value in object_list(
            inner["training_external_ids"], "training_external_ids"
        )
    )
    closure = assert_training_inputs(
        fold,
        inputs,
        graph,
        admitted_external_ids=external,
        training_admission=admission,
    )
    support_id = "experiment-support:" + manifest_sha256(inner["support"])
    fit_ids = tuple("experiment-fit:" + manifest_sha256(value) for value in products)
    expected_graph: dict[str, tuple[str, ...]] = dict.fromkeys(
        admission.admitted_record_ids, ()
    )
    expected_graph.update(
        {
            fit_id: tuple(sorted((identity(product["record_id"]), anchor)))
            for fit_id, product in zip(fit_ids, products, strict=True)
        }
    )
    expected_graph[support_id] = ()
    if (
        graph != expected_graph
        or inputs != (*admission.admitted_record_ids, *fit_ids, support_id)
        or external != (*fit_ids, support_id)
        or object_list(inner["allowed_input_closure"], "allowed_input_closure")
        != list(closure)
    ):
        raise ValidationRefusal(
            "block_baseline_lineage_mismatch",
            "Input closure differs from admitted reconstruction ancestry",
        )
    taxa = set(next(iter(compositions.values())))
    if any(set(values) != taxa for values in compositions.values()):
        raise ValidationRefusal(
            "block_baseline_taxon_mismatch", "Training denominators differ"
        )
    expected_vegetation = closed_composition(
        {
            taxon: sum(values[taxon] for values in compositions.values())
            / len(compositions)
            for taxon in taxa
        }
    )
    if (
        object_mapping(row["vegetation_fraction"], "vegetation_fraction")
        != expected_vegetation
    ):
        raise ValidationRefusal(
            "block_baseline_arithmetic_mismatch",
            "Vegetation differs from the admitted training mean",
        )
    preparation = object_mapping(row["forward_preparation"], "forward_preparation")
    validate_fitted_preparation(
        row,
        {"taxa": object_list(preparation["taxa"], "taxa")},
    )
    try:
        criterion = object_mapping(
            json.loads(admission.criterion_json), "training_criterion"
        )
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValidationRefusal("invalid_block_criterion", str(exc)) from exc
    target_support = object_mapping(
        object_mapping(criterion["supports"], "supports")[record], "target_support"
    )
    target_footprint = object_mapping(target_support["target"], "target_footprint")
    if (
        target_support["geometry_sha256"] != row["target_geometry_sha256"]
        or finite_number(target_footprint["radius_m"])
        != finite_number(
            object_mapping(row["support"], "support")["local_support_radius_m"]
        )
        or finite_number(preparation["regional_cutoff_m"])
        > finite_number(target_support["source_integration_cutoff_m"])
    ):
        raise ValidationRefusal(
            "block_baseline_support_mismatch",
            "Target geometry or buffered integration support differs",
        )
    closed_composition(
        {
            identity(taxon): finite_number(value)
            for taxon, value in object_mapping(
                row["pollen_fraction"], "pollen_fraction"
            ).items()
        }
    )
