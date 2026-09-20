"""Authenticate grouped and block training-mean prediction products."""

from __future__ import annotations

import json

from ...contracts import (
    Fold,
    TrainingAdmission,
    ValidationRefusal,
    canonical_json,
    finite_number,
    manifest_sha256,
)
from ...metrics import closed_composition
from ...splits import assert_training_inputs
from ..configuration import (
    BLOCK_PROFILE,
    FITTED_PROFILE,
    FITTED_ROLES,
    TRAINING_MEAN_METHOD,
    identity,
    object_list,
    object_mapping,
)
from ..outputs import validate_fitted_preparation


def _refuse_outcomes(row: dict[str, object]) -> None:
    if any(key.startswith("observed_") or "outcome" in key for key in row):
        raise ValidationRefusal(
            "training_mean_outcome_leakage",
            "Prediction rows cannot retain target outcomes or observations",
        )


def _fold(value: dict[str, object]) -> Fold:
    return Fold(
        identity(value["fold_id"]),
        *(
            tuple(identity(key) for key in object_list(value[field], field))
            for field in (
                "train_record_ids",
                "test_record_ids",
                "train_group_ids",
                "test_group_ids",
            )
        ),
    )


def _training_partition(
    fold: Fold,
    row: dict[str, object],
    products: list[dict[str, object]],
    *,
    admission_payload: object | None,
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, str], TrainingAdmission | None]:
    if admission_payload is not None:
        from ..fitted.admission import retained_training_admission

        admission = retained_training_admission(admission_payload, fold)
        return (
            admission.admitted_record_ids,
            admission.admitted_group_ids,
            dict(admission.record_groups),
            admission,
        )
    if "training_admission" in row:
        raise ValidationRefusal(
            "grouped_baseline_admission_mismatch",
            "Grouped outer folds cannot invent a block training admission",
        )
    ownership = {
        identity(product["record_id"]): identity(product["group_id"])
        for product in products
    }
    return fold.train_record_ids, fold.train_group_ids, ownership, None


def validate_training_mean_prediction(
    row: dict[str, object],
    outer: dict[str, object],
    *,
    admission_payload: object | None = None,
    expected_model_sha256: str | None = None,
) -> None:
    """Recompute training arithmetic and lineage without replaying the engine.

    The pollen vector remains authenticated by the exact row digest and the
    caller-pinned outer product. This validator independently recomputes the
    training mean, source closure, support shape and method identity.
    """
    _refuse_outcomes(row)
    block = admission_payload is not None
    profile = BLOCK_PROFILE if block else FITTED_PROFILE
    schema = (
        "lra-spatial-block-training-mean.v1"
        if block
        else "lra-grouped-outer-training-mean.v1"
    )
    reason = "block_baseline" if block else "grouped_baseline"
    inner = object_mapping(row["baseline_model_manifest"], "baseline_model_manifest")
    model_sha256 = manifest_sha256(inner)
    if (
        row["profile"] != profile
        or row["method"] != TRAINING_MEAN_METHOD
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
        or row["baseline_model_sha256"] != model_sha256
        or (expected_model_sha256 is not None and model_sha256 != expected_model_sha256)
        or inner.get("schema_version") != schema
        or inner.get("method") != TRAINING_MEAN_METHOD
        or inner.get("method_kind") != "admitted_reconstruction_training_mean"
        or inner.get("fold") != outer
        or inner.get("support") != row["support"]
        or inner.get("scientific_acceptance") != "not_evaluated"
        or inner.get("uncertainty_status")
        != "deterministic_point_baseline_no_intervals"
    ):
        raise ValidationRefusal(
            reason + "_identity_mismatch",
            "Method, posture, model or exact row identity differs",
        )
    fold = _fold(outer)
    record = identity(row["record_id"])
    group = identity(row["group_id"])
    products = [
        object_mapping(value, "training_product")
        for value in object_list(inner["training_products"], "training_products")
    ]
    training_records, training_groups, ownership, admission = _training_partition(
        fold, row, products, admission_payload=admission_payload
    )
    if block:
        assert admission is not None
        if (
            canonical_json(inner.get("training_admission"))
            != canonical_json(admission.as_dict())
            or row.get("training_admission") != admission_payload
            or ownership.get(record) != group
        ):
            raise ValidationRefusal(
                "block_baseline_admission_mismatch",
                "Target or retained training admission differs",
            )
    elif (
        "training_admission" in inner
        or record not in fold.test_record_ids
        or tuple(fold.test_group_ids) != (group,)
    ):
        raise ValidationRefusal(
            "grouped_baseline_admission_mismatch",
            "Grouped target or original fold differs",
        )
    anchor = identity(inner["regional_anchor_record_id"])
    anchor_group = identity(inner["regional_anchor_group_id"])
    if not block:
        ownership[anchor] = anchor_group
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
        or set(compositions) != set(training_groups) - {anchor_group}
        or anchor not in training_records
        or ownership.get(anchor) != anchor_group
        or set(product_records) != set(training_records) - {anchor}
        or any(
            ownership.get(source_record) != identity(product["group_id"])
            for source_record, product in zip(product_records, products, strict=True)
        )
        or inner["regional_value_source_record_ids"] != [anchor]
        or set(
            object_list(
                inner["regional_identity_source_record_ids"],
                "regional_identity_source_record_ids",
            )
        )
        != set(training_records)
    ):
        raise ValidationRefusal(
            reason + "_training_mismatch",
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
    expected_graph: dict[str, tuple[str, ...]] = dict.fromkeys(training_records, ())
    expected_graph.update(
        {
            fit_id: tuple(sorted((identity(product["record_id"]), anchor)))
            for fit_id, product in zip(fit_ids, products, strict=True)
        }
    )
    expected_graph[support_id] = ()
    if (
        graph != expected_graph
        or inputs != (*training_records, *fit_ids, support_id)
        or external != (*fit_ids, support_id)
        or object_list(inner["allowed_input_closure"], "allowed_input_closure")
        != list(closure)
    ):
        raise ValidationRefusal(
            reason + "_lineage_mismatch",
            "Input closure differs from reconstruction ancestry",
        )
    taxa = set(next(iter(compositions.values())))
    if any(set(values) != taxa for values in compositions.values()):
        raise ValidationRefusal(
            reason + "_taxon_mismatch", "Training denominators differ"
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
            reason + "_arithmetic_mismatch",
            "Vegetation differs from the training mean",
        )
    preparation = object_mapping(row["forward_preparation"], "forward_preparation")
    validate_fitted_preparation(
        row,
        {"taxa": object_list(preparation["taxa"], "taxa")},
    )
    if block:
        assert admission is not None
        try:
            criterion = object_mapping(
                json.loads(admission.criterion_json), "training_criterion"
            )
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValidationRefusal("invalid_block_criterion", str(exc)) from exc
        target_support = object_mapping(
            object_mapping(criterion["supports"], "supports")[record],
            "target_support",
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
