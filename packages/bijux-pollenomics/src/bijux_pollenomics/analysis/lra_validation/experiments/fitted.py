"""Actual train-only LRA reconstructions followed by an explicit fitted spatial model."""

from __future__ import annotations

from collections.abc import Mapping
import json
import os
from pathlib import Path
from typing import cast

from ...lra.api import LRABatchLimits, LRARefusal
from ...lra.engine.discovery import load_engine
from ...lra.outputs.identity import capture_code_identity, verify_code_identity
from ..contracts import Fold, ValidationRefusal, finite_number, manifest_sha256
from ..metrics import closed_composition
from ..prediction import ForwardModel
from ..spatial import SiteCoordinate, SpatialConfig, fit_spatial_model
from ..splits import assert_allowed_inputs, grouped_leave_one_out
from .configuration import (
    FITTED_METHOD,
    FITTED_PROFILE,
    FITTED_ROLES,
    ExperimentSite,
    FittedSpatialExperimentSpec,
    identity,
    object_list,
    object_mapping,
)
from .inputs import read_geometry, verify_consumed_sources
from .outputs import (
    ExperimentProduct,
    publish_phase,
    stage_directory,
    validate_fitted_preparation,
    write_json,
)
from .prediction import prepare_target_forward
from .reconstruction import FoldFits, reconstruct_fold
from .workflow import _implementation


def fitted_support(spec: FittedSpatialExperimentSpec) -> dict[str, object]:
    """Bind common declared spatial, taxonomic and time support without target outcomes."""
    template = spec.template()
    return {
        "support_profile": spec.support_profile,
        "local_support_radius_m": spec.local_support_radius_m,
        "taxa": template["taxa"],
        "temporal_matching": template["temporal_matching"],
        "versions": template["versions"],
    }


def predict_fitted_fold(
    spec: FittedSpatialExperimentSpec,
    fold: Fold,
    target: ExperimentSite,
    fits: FoldFits,
    group_by_record: dict[str, str],
    *,
    input_root: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    """Fit from training-only geography and inversion identities before target projection."""
    support = fitted_support(spec)
    support_id = "experiment-support:" + manifest_sha256(support)
    config = SpatialConfig(spec.length_scale_km, spec.ridge_penalty, support_id)
    coordinates = {}
    graph: dict[str, tuple[str, ...]] = dict.fromkeys(fold.train_record_ids, ())
    fit_ids = []
    for fitted in fits.fit_identities:
        record = identity(fitted["record_id"])
        if record not in fold.train_record_ids:
            raise ValidationRefusal("training_identity_mismatch", record)
        node = "experiment-fit:" + manifest_sha256(fitted)
        if node in graph:
            raise ValidationRefusal("experiment_identity_collision", node)
        graph[node] = (record, fits.anchor.record.record_id)
        fit_ids.append(node)
    for site in fits.predictors:
        geometry = read_geometry(input_root, site, spec)
        coordinates[group_by_record[site.record.record_id]] = SiteCoordinate(
            finite_number(geometry["latitude"]), finite_number(geometry["longitude"])
        )
    graph[support_id] = ()
    model = fit_spatial_model(
        fold,
        fits.compositions,
        coordinates,
        config=config,
        input_ids=(*fold.train_record_ids, *fit_ids, support_id),
        dependency_graph=graph,
        admitted_external_ids=(*fit_ids, support_id),
        predictor_group_ids=tuple(fits.compositions),
    )
    # Target geometry is opened only after the fitted model is frozen.
    binding, prepared, geometry, bin_id = prepare_target_forward(
        spec, target, fits.anchor, fits.regional_cover, input_root=input_root
    )
    spatial = model.predict(
        target_group_id=group_by_record[target.record.record_id],
        coordinate=SiteCoordinate(
            finite_number(geometry["latitude"]), finite_number(geometry["longitude"])
        ),
        support_id=support_id,
    )
    vegetation = dict(spatial.fractions)
    if set(vegetation) != set(prepared.taxa):
        raise ValidationRefusal("fitted_forward_taxa_mismatch", fold.fold_id)
    forward = cast(ForwardModel, binding.api.forward_deposition)(
        local_cover=tuple(vegetation[taxon] for taxon in prepared.taxa),
        regional_deposition=tuple(prepared.regional_deposition),
        local_k=tuple(tuple(ring) for ring in prepared.local_k),
        terrestrial_fraction=tuple(prepared.terrestrial_fraction),
        ppe=tuple(prepared.ppe),
    )
    if forward.method_profile != prepared.method_profile:
        raise ValidationRefusal("fitted_forward_profile_mismatch", fold.fold_id)
    row: dict[str, object] = {
        "profile": FITTED_PROFILE,
        "method": FITTED_METHOD,
        "method_kind": "fitted_spatial",
        "evaluation_roles": FITTED_ROLES,
        "fold_id": fold.fold_id,
        "outer_fold": fold.as_dict(),
        "record_id": target.record.record_id,
        "group_id": group_by_record[target.record.record_id],
        "bin_id": bin_id,
        "vegetation_fraction": vegetation,
        "pollen_fraction": closed_composition(
            dict(zip(prepared.taxa, forward.pollen_fraction, strict=True))
        ),
        "model_sha256": model.model_sha256,
        "fit_manifest": json.loads(model.fit_manifest_json),
        "spatial_prediction_sha256": spatial.prediction_sha256,
        "spatial_prediction_manifest": json.loads(spatial.prediction_manifest_json),
        "training_products": fits.fit_identities,
        "training_dependency_graph": graph,
        "training_input_ids": (*fold.train_record_ids, *fit_ids, support_id),
        "training_external_ids": (*fit_ids, support_id),
        "target_geometry_sha256": target.geometry.sha256,
        "regional_anchor_record_id": fits.anchor.record.record_id,
        "regional_anchor_group_id": group_by_record[fits.anchor.record.record_id],
        "regional_value_source_record_ids": [fits.anchor.record.record_id],
        "regional_identity_source_record_ids": fold.train_record_ids,
        "support": support,
        "uncertainty_status": "point_predictions_only_intervals_not_implemented",
        "scientific_acceptance": "not_evaluated",
    }
    preparation: dict[str, object] = {
        "preparation_profile": prepared.preparation_profile,
        "forward_method_profile": prepared.method_profile,
        "geometry_profile": prepared.geometry_profile,
        "deposition_units": prepared.deposition_units,
        "taxa": prepared.taxa,
        "local_k": [list(ring) for ring in prepared.local_k],
        "terrestrial_fraction": list(prepared.terrestrial_fraction),
        "ppe": list(prepared.ppe),
        "regional_deposition": list(prepared.regional_deposition),
        "regional_cover": list(prepared.regional_cover),
        "ring_bounds_m": [list(ring) for ring in prepared.ring_bounds_m],
        "regional_cutoff_m": prepared.regional_cutoff_m,
        "target_geometry_sha256": target.geometry.sha256,
        "declared_target_inversion_rings": geometry["inversion_rings"],
        "declared_target_forward_rings": geometry["forward_rings"],
    }
    row["forward_preparation"] = preparation
    row["prediction_manifest_sha256"] = manifest_sha256(row)
    return row, preparation


def prepare_fitted_spatial_predictions(
    spec: FittedSpatialExperimentSpec | Mapping[str, object],
    *,
    input_root: Path,
    cache_root: Path,
    destination: Path,
    workers: int = 1,
) -> ExperimentProduct:
    """Publish actual fitted predictions without accepting either target outcome inventory."""
    spec = (
        spec
        if isinstance(spec, FittedSpatialExperimentSpec)
        else FittedSpatialExperimentSpec(spec)
    )
    LRABatchLimits(max_workers=workers)
    if workers > (os.cpu_count() or 1):
        raise ValidationRefusal("experiment_worker_budget_exceeded", str(workers))
    folds = grouped_leave_one_out([site.record for site in spec.sites])
    by_record = {site.record.record_id: site for site in spec.sites}
    groups = {
        record: fold.test_group_ids[0]
        for fold in folds
        for record in fold.test_record_ids
    }
    implementation = _implementation()
    binding = load_engine()
    engine_identity = capture_code_identity(binding)
    stage = stage_directory(destination)
    predictions: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    operations: list[dict[str, object]] = []
    interrupted = False
    consumed_pollen: set[str] = set()
    consumed_geometry: set[str] = set()
    for index, fold in enumerate(folds):
        try:
            if interrupted:
                raise ValidationRefusal(
                    "experiment_interrupted", "Remaining fold not submitted"
                )
            if len(fold.test_record_ids) != 1:
                raise ValidationRefusal("unsupported_multi_record_target", fold.fold_id)
            fits = reconstruct_fold(
                spec,
                fold,
                groups,
                input_root=input_root,
                cache_root=cache_root,
                report_root=stage / "batches" / f"fold-{index:04}",
                workers=workers,
            )
            consumed_pollen.update(fold.train_record_ids)
            consumed_geometry.update((*fold.train_record_ids, fold.test_record_ids[0]))
            row, _ = predict_fitted_fold(
                spec,
                fold,
                by_record[fold.test_record_ids[0]],
                fits,
                groups,
                input_root=input_root,
            )
            predictions.append(row)
            operations.append(
                {"fold_id": fold.fold_id, "batch": fits.operational_batch}
            )
        except KeyboardInterrupt:
            interrupted = True
            failures.append(
                {
                    "fold_id": fold.fold_id,
                    "record_ids": fold.test_record_ids,
                    "status": "not_run",
                    "reason_code": "experiment_interrupted",
                }
            )
        except (ValidationRefusal, LRARefusal, ValueError) as exc:
            reason = getattr(exc, "reason_code", "experiment_fold_refused")
            interrupted = interrupted or reason == "experiment_interrupted"
            error: dict[str, object] = {
                "fold_id": fold.fold_id,
                "record_ids": fold.test_record_ids,
                "status": "not_run" if interrupted else "refused",
                "reason_code": reason,
                "detail": str(exc),
                "exception_type": type(exc).__name__,
            }
            if isinstance(exc, LRARefusal):
                error["original_error"] = exc.as_dict()
            failures.append(error)
    if _implementation() != implementation:
        raise ValidationRefusal("experiment_implementation_changed", str(stage))
    verify_code_identity(binding, engine_identity)
    fold_rows = [fold.as_dict() for fold in folds]
    scientific: dict[str, object] = {
        "profile": FITTED_PROFILE,
        "experiment": "all_target_pollen_withheld_fitted_spatial",
        "folds": fold_rows,
        "methods": [FITTED_METHOD],
        "evaluation_roles": FITTED_ROLES,
        "predictions": predictions,
        "failures": failures,
        "implementation": implementation,
        "engine_identity": engine_identity.payload(),
        "split_manifest_sha256": manifest_sha256(fold_rows),
        "requested_folds": len(folds),
        "requested_predictions": len(folds),
        "generated_predictions": len(predictions),
        "failed_folds": len(failures),
        "interrupted": interrupted,
        "all_predictions_generated": not failures,
        "uncertainty_status": "point_predictions_only_intervals_not_implemented",
    }
    write_json(
        stage,
        "experiment.json",
        {
            "profile": FITTED_PROFILE,
            "request_template": spec.template(),
            "support": fitted_support(spec),
            "regional_priority": spec.regional_priority,
            "method": {
                "profile": FITTED_METHOD,
                "length_scale_km": spec.length_scale_km,
                "ridge_penalty": spec.ridge_penalty,
            },
            "source_catalogue": [
                {
                    "record_id": site.record.record_id,
                    "site_id": site.record.site_id,
                    "identity_keys": site.record.identity_keys,
                    "raw_path": site.raw.path,
                    "raw_sha256": site.raw.sha256,
                    "geometry_path": site.geometry.path,
                    "geometry_sha256": site.geometry.sha256,
                }
                for site in spec.sites
            ],
        },
    )
    for name, value in (
        ("folds.json", fold_rows),
        ("predictions.json", predictions),
        ("failures.json", failures),
        ("operations.json", operations),
    ):
        write_json(stage, name, value)
    verify_consumed_sources(
        spec,
        input_root,
        pollen_record_ids=consumed_pollen,
        geometry_record_ids=consumed_geometry,
        template_used=bool(consumed_pollen),
    )
    return publish_phase(
        stage,
        destination,
        phase="predictions",
        scientific=scientific,
        profile=FITTED_PROFILE,
    )


def validate_fitted_prediction(
    row: dict[str, object], outer: dict[str, object]
) -> None:
    """Recheck method, model, source ancestry and target identity before outcome access."""
    try:
        if (
            row["profile"] != FITTED_PROFILE
            or row["method"] != FITTED_METHOD
            or row["method_kind"] != "fitted_spatial"
            or row["evaluation_roles"] != FITTED_ROLES
            or row["outer_fold"] != outer
            or outer["test_group_ids"] != [row["group_id"]]
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
        closure = assert_allowed_inputs(
            fold, inputs, graph, admitted_external_ids=external
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
            or set(groups) != set(fold.train_group_ids) - {anchor_group}
            or {identity(value["record_id"]) for value in products}
            != set(fold.train_record_ids) - {anchor}
            or len(products) != len(fold.train_record_ids) - 1
            or anchor_group not in fold.train_group_ids
            or row["regional_value_source_record_ids"] != [anchor]
            or set(
                object_list(
                    row["regional_identity_source_record_ids"],
                    "regional_identity_source_record_ids",
                )
            )
            != set(fold.train_record_ids)
            or row["scientific_acceptance"] != "not_evaluated"
            or row["uncertainty_status"]
            != "point_predictions_only_intervals_not_implemented"
            or config["profile"] != FITTED_METHOD
            or fit["schema_version"] != "lra-fitted-spatial-model.v1"
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
        closed_composition(
            {
                key: finite_number(value)
                for key, value in object_mapping(
                    row["pollen_fraction"], "pollen_fraction"
                ).items()
            }
        )
        if (
            not set(fold.train_record_ids).issubset(closure)
            or row["regional_anchor_record_id"] not in fold.train_record_ids
        ):
            raise ValidationRefusal(
                "incomplete_training_lineage",
                "Full outer training ancestry is required",
            )
    except ValidationRefusal:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise ValidationRefusal("invalid_fitted_prediction_product", str(exc)) from exc
