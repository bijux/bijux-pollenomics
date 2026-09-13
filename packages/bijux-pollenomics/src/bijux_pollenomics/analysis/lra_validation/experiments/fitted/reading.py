"""Actual train-only LRA reconstructions followed by an explicit fitted spatial model."""

from __future__ import annotations

from ...contracts import Fold, ValidationRefusal, finite_number, manifest_sha256
from ...metrics import closed_composition
from ...splits import assert_training_inputs
from ..configuration import (
    BLOCK_PROFILE,
    FITTED_METHOD,
    FITTED_PROFILE,
    FITTED_ROLES,
    identity,
    object_list,
    object_mapping,
)
from ..outputs import (
    validate_fitted_preparation,
)
from .admission import retained_training_admission, validate_prediction_support


def validate_fitted_prediction(
    row: dict[str, object], outer: dict[str, object]
) -> None:
    """Recheck method, model, source ancestry and target identity before outcome access."""
    try:
        block = row.get("profile") == BLOCK_PROFILE
        if (
            row["profile"] not in {FITTED_PROFILE, BLOCK_PROFILE}
            or row["method"] != FITTED_METHOD
            or row["method_kind"] != "fitted_spatial"
            or row["evaluation_roles"] != FITTED_ROLES
            or row["outer_fold"] != outer
            or (not block and outer["test_group_ids"] != [row["group_id"]])
            or row["group_id"]
            not in object_list(outer["test_group_ids"], "test_group_ids")
            or row["record_id"]
            not in object_list(outer["test_record_ids"], "test_record_ids")
            or manifest_sha256(
                {
                    key: value
                    for key, value in row.items()
                    if key != "prediction_manifest_sha256"
                }
            )
            != row["prediction_manifest_sha256"]
        ):
            raise ValidationRefusal(
                "fitted_prediction_identity_mismatch", "Invalid method/target envelope"
            )
        fit = object_mapping(row["fit_manifest"], "fit_manifest")
        spatial = object_mapping(
            row["spatial_prediction_manifest"], "spatial_prediction_manifest"
        )
        if (
            manifest_sha256(fit) != row["model_sha256"]
            or fit["fold"] != outer
            or manifest_sha256(spatial) != row["spatial_prediction_sha256"]
            or spatial["model_sha256"] != row["model_sha256"]
            or spatial["vegetation_fraction"] != row["vegetation_fraction"]
            or spatial["target_group_id"] != row["group_id"]
        ):
            raise ValidationRefusal(
                "fitted_model_identity_mismatch", "Fitted state or prediction differs"
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
        admission = (
            retained_training_admission(row["training_admission"], fold)
            if block
            else None
        )
        training_records = (
            fold.train_record_ids
            if admission is None
            else admission.admitted_record_ids
        )
        training_groups = (
            fold.train_group_ids if admission is None else admission.admitted_group_ids
        )
        graph = {
            key: tuple(identity(value) for value in object_list(parents, "parents"))
            for key, parents in object_mapping(
                row["training_dependency_graph"], "training_dependency_graph"
            ).items()
        }
        inputs = tuple(
            identity(value)
            for value in object_list(row["training_input_ids"], "training_input_ids")
        )
        external = tuple(
            identity(value)
            for value in object_list(
                row["training_external_ids"], "training_external_ids"
            )
        )
        closure = assert_training_inputs(
            fold,
            inputs,
            graph,
            admitted_external_ids=external,
            training_admission=admission,
        )
        expected_support = "experiment-support:" + manifest_sha256(row["support"])
        config = object_mapping(fit["configuration"], "configuration")
        products = [
            object_mapping(value, "training_product")
            for value in object_list(row["training_products"], "training_products")
        ]
        groups = tuple(
            identity(key)
            for key in object_list(fit["predictor_group_ids"], "predictor_group_ids")
        )
        compositions = {
            identity(value["group_id"]): value["composition"] for value in products
        }
        anchor, anchor_group = (
            identity(row["regional_anchor_record_id"]),
            identity(row["regional_anchor_group_id"]),
        )
        if (
            len(products) != len(compositions)
            or len(set(groups)) != len(groups)
            or set(groups) != set(compositions)
            or fit["training_compositions"] != compositions
            or set(groups) != set(training_groups) - {anchor_group}
            or {identity(value["record_id"]) for value in products}
            != set(training_records) - {anchor}
            or len(products) != len(training_records) - 1
            or anchor_group not in training_groups
            or row["regional_value_source_record_ids"] != [anchor]
            or set(
                object_list(
                    row["regional_identity_source_record_ids"],
                    "regional_identity_source_record_ids",
                )
            )
            != set(training_records)
            or row["scientific_acceptance"] != "not_evaluated"
            or row["uncertainty_status"]
            != "point_predictions_only_intervals_not_implemented"
            or config["profile"] != FITTED_METHOD
            or fit["schema_version"]
            != (
                "lra-fitted-spatial-model.v2"
                if block
                else "lra-fitted-spatial-model.v1"
            )
            or spatial["schema_version"] != "lra-fitted-spatial-prediction.v1"
            or spatial["profile"] != FITTED_METHOD
            or fit["scientific_acceptance"] != "not_evaluated"
            or fit["uncertainty_status"] != "point_fit_only"
            or spatial["scientific_acceptance"] != "not_evaluated"
            or spatial["uncertainty_status"] != "point_prediction_only"
        ):
            raise ValidationRefusal(
                "fitted_retained_contract_mismatch",
                "Predictor products, regional roles or exploratory posture differ",
            )
        if admission is not None:
            ownership = dict(admission.record_groups)
            if (
                fit.get("training_admission") != row["training_admission"]
                or ownership[identity(row["record_id"])] != row["group_id"]
                or ownership[anchor] != anchor_group
                or any(
                    ownership[identity(product["record_id"])] != product["group_id"]
                    for product in products
                )
            ):
                raise ValidationRefusal(
                    "block_admission_identity_mismatch", fold.fold_id
                )
        if admission is not None:
            validate_prediction_support(row, fit, spatial, admission)
        validate_fitted_preparation(row, fit)
        expected_external = {
            expected_support,
            *("experiment-fit:" + manifest_sha256(value) for value in products),
        }
        if (
            set(external) != expected_external
            or config["support_id"] != expected_support
            or spatial["support_id"] != expected_support
            or fit["allowed_input_closure"] != list(closure)
            or fit["input_lineage"] != {key: sorted(set(graph[key])) for key in closure}
        ):
            raise ValidationRefusal(
                "fitted_training_identity_mismatch",
                "Support or quantitative source lineage differs",
            )
        for value in products:
            node = "experiment-fit:" + manifest_sha256(value)
            if graph[node] != (value["record_id"], row["regional_anchor_record_id"]):
                raise ValidationRefusal("fitted_training_identity_mismatch", node)
        for field in ("vegetation_fraction", "pollen_fraction"):
            closed_composition(
                {
                    key: finite_number(value)
                    for key, value in object_mapping(row[field], field).items()
                }
            )
        if (
            not set(training_records).issubset(closure)
            or row["regional_anchor_record_id"] not in training_records
        ):
            raise ValidationRefusal(
                "incomplete_training_lineage",
                "Full outer training ancestry is required",
            )
    except ValidationRefusal:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationRefusal("invalid_fitted_prediction_product", str(exc)) from exc
