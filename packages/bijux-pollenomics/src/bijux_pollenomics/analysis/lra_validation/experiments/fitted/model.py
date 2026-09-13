"""Actual train-only LRA reconstructions followed by an explicit fitted spatial model."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import cast

from ...contracts import (
    Fold,
    TrainingAdmission,
    ValidationRefusal,
    finite_number,
    manifest_sha256,
)
from ...metrics import closed_composition
from ...prediction import ForwardModel
from ...spatial import (
    FittedSpatialModel,
    SiteCoordinate,
    SpatialConfig,
    fit_spatial_model,
)
from ..configuration import (
    BLOCK_PROFILE,
    FITTED_METHOD,
    FITTED_PROFILE,
    FITTED_ROLES,
    ExperimentSite,
    FittedSpatialExperimentSpec,
    identity,
)
from ..inputs import read_geometry
from ..prediction import prepare_target_forward
from ..reconstruction import FoldFits


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


@dataclass(frozen=True)
class FittedTrainingState:
    """One frozen fitted model and actual admitted inversion ancestry for all block targets."""

    model: FittedSpatialModel
    fits: FoldFits
    support: dict[str, object]
    graph: dict[str, tuple[str, ...]]
    fit_ids: tuple[str, ...]
    training_records: tuple[str, ...]


def fit_reconstructed_training(
    spec: FittedSpatialExperimentSpec,
    fold: Fold,
    fits: FoldFits,
    group_by_record: dict[str, str],
    *,
    input_root: Path,
    consumed_geometry: set[str] | None = None,
    training_admission: TrainingAdmission | None = None,
) -> FittedTrainingState:
    """Fit once from the explicit training subpartition, with full original Fold retained."""
    support = fitted_support(spec)
    support_id = "experiment-support:" + manifest_sha256(support)
    config = SpatialConfig(spec.length_scale_km, spec.ridge_penalty, support_id)
    if training_admission is not None:
        training_admission.validate(fold)
    training_records = (
        fold.train_record_ids
        if training_admission is None
        else training_admission.admitted_record_ids
    )
    coordinates = {}
    graph: dict[str, tuple[str, ...]] = dict.fromkeys(training_records, ())
    fit_ids = []
    for fitted in fits.fit_identities:
        record = identity(fitted["record_id"])
        if record not in training_records:
            raise ValidationRefusal("training_identity_mismatch", record)
        node = "experiment-fit:" + manifest_sha256(fitted)
        if node in graph:
            raise ValidationRefusal("experiment_identity_collision", node)
        graph[node] = (record, fits.anchor.record.record_id)
        fit_ids.append(node)
    for site in fits.predictors:
        geometry = read_geometry(
            input_root, site, spec, consumed_geometry=consumed_geometry
        )
        coordinates[group_by_record[site.record.record_id]] = SiteCoordinate(
            finite_number(geometry["latitude"]), finite_number(geometry["longitude"])
        )
    graph[support_id] = ()
    model = fit_spatial_model(
        fold,
        fits.compositions,
        coordinates,
        config=config,
        input_ids=(*training_records, *fit_ids, support_id),
        dependency_graph=graph,
        admitted_external_ids=(*fit_ids, support_id),
        predictor_group_ids=tuple(fits.compositions),
        training_admission=training_admission,
    )
    return FittedTrainingState(
        model, fits, support, graph, tuple(fit_ids), training_records
    )


def predict_fitted_target(
    spec: FittedSpatialExperimentSpec,
    target: ExperimentSite,
    state: FittedTrainingState,
    group_by_record: dict[str, str],
    *,
    input_root: Path,
    consumed_geometry: set[str] | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    """Project a frozen block model through each target's own outcome-free geometry."""
    model, fits, support, graph = state.model, state.fits, state.support, state.graph
    fold, fit_ids, training_records = model.fold, state.fit_ids, state.training_records
    support_id = "experiment-support:" + manifest_sha256(support)
    # Target geometry is opened only after the fitted model is frozen.
    binding, prepared, geometry, bin_id = prepare_target_forward(
        spec,
        target,
        fits.anchor,
        fits.regional_cover,
        input_root=input_root,
        consumed_geometry=consumed_geometry,
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
        "profile": FITTED_PROFILE
        if model.training_admission is None
        else BLOCK_PROFILE,
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
        "training_input_ids": (*training_records, *fit_ids, support_id),
        "training_external_ids": (*fit_ids, support_id),
        "target_geometry_sha256": target.geometry.sha256,
        "regional_anchor_record_id": fits.anchor.record.record_id,
        "regional_anchor_group_id": group_by_record[fits.anchor.record.record_id],
        "regional_value_source_record_ids": [fits.anchor.record.record_id],
        "regional_identity_source_record_ids": training_records,
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
    if model.training_admission is not None:
        row["training_admission"] = model.training_admission.as_dict()
    row["prediction_manifest_sha256"] = manifest_sha256(row)
    return row, preparation


def predict_fitted_fold(
    spec: FittedSpatialExperimentSpec,
    fold: Fold,
    target: ExperimentSite,
    fits: FoldFits,
    group_by_record: dict[str, str],
    *,
    input_root: Path,
    consumed_geometry: set[str] | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    """Preserve the singleton workflow through the shared fit and projection boundaries."""
    state = fit_reconstructed_training(
        spec,
        fold,
        fits,
        group_by_record,
        input_root=input_root,
        consumed_geometry=consumed_geometry,
    )
    return predict_fitted_target(
        spec,
        target,
        state,
        group_by_record,
        input_root=input_root,
        consumed_geometry=consumed_geometry,
    )


def retained_training_state(
    state: FittedTrainingState, groups: dict[str, str]
) -> dict[str, object]:
    """Retain actual fitted state independently of whether any target projection succeeds."""
    model, fits = state.model, state.fits
    support_id = "experiment-support:" + manifest_sha256(state.support)
    record: dict[str, object] = {
        "model_sha256": model.model_sha256,
        "fit_manifest": json.loads(model.fit_manifest_json),
        "training_products": fits.fit_identities,
        "training_dependency_graph": state.graph,
        "training_input_ids": (*state.training_records, *state.fit_ids, support_id),
        "training_external_ids": (*state.fit_ids, support_id),
        "regional_anchor_record_id": fits.anchor.record.record_id,
        "regional_anchor_group_id": groups[fits.anchor.record.record_id],
        "regional_value_source_record_ids": [fits.anchor.record.record_id],
        "regional_identity_source_record_ids": state.training_records,
        "support": state.support,
    }
    if model.training_admission is not None:
        record["training_admission"] = model.training_admission.as_dict()
    return record
