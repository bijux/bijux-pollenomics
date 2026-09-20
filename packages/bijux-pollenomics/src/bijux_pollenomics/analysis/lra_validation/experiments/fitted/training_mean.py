"""Outcome-free training means over authenticated reconstruction products."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from ...contracts import Fold, TrainingAdmission, ValidationRefusal, manifest_sha256
from ...metrics import closed_composition
from ...prediction import ForwardModel
from ...splits import assert_training_inputs
from ..configuration import (
    BLOCK_PROFILE,
    FITTED_PROFILE,
    FITTED_ROLES,
    TRAINING_MEAN_METHOD,
    ExperimentSite,
    FittedSpatialExperimentSpec,
    identity,
)
from ..prediction import prepare_target_forward
from ..reconstruction import FoldFits
from .model import fitted_support


def training_mean_model(
    spec: FittedSpatialExperimentSpec,
    fold: Fold,
    fits: FoldFits,
    groups: dict[str, str],
    *,
    training_admission: TrainingAdmission | None = None,
) -> dict[str, object]:
    """Freeze the exact reconstructed compositions behind one training mean."""
    if training_admission is not None:
        training_admission.validate(fold)
        training_records = training_admission.admitted_record_ids
        training_groups = training_admission.admitted_group_ids
        ownership = dict(training_admission.record_groups)
        reason = "block_baseline_training_mismatch"
        schema = "lra-spatial-block-training-mean.v1"
    else:
        training_records = fold.train_record_ids
        training_groups = fold.train_group_ids
        ownership = groups
        reason = "grouped_baseline_training_mismatch"
        schema = "lra-grouped-outer-training-mean.v1"
    if any(ownership.get(record) != groups.get(record) for record in training_records):
        raise ValidationRefusal(reason, "Record/group ownership differs")
    support = fitted_support(spec)
    support_id = "experiment-support:" + manifest_sha256(support)
    fit_ids = tuple(
        "experiment-fit:" + manifest_sha256(value) for value in fits.fit_identities
    )
    inputs = (*training_records, *fit_ids, support_id)
    externals = (*fit_ids, support_id)
    anchor = fits.anchor.record.record_id
    product_records = tuple(
        identity(value.get("record_id")) for value in fits.fit_identities
    )
    if (
        anchor not in training_records
        or len(fit_ids) != len(set(fit_ids))
        or len(product_records) != len(set(product_records))
        or set(product_records) != set(training_records) - {anchor}
        or any(
            ownership[record] != identity(value.get("group_id"))
            for record, value in zip(product_records, fits.fit_identities, strict=True)
        )
    ):
        raise ValidationRefusal(
            reason,
            "Reconstruction products differ from admitted record/group ownership",
        )
    graph: dict[str, tuple[str, ...]] = dict.fromkeys(training_records, ())
    for node, value in zip(fit_ids, fits.fit_identities, strict=True):
        record = identity(value.get("record_id"))
        if record not in training_records or node in graph:
            raise ValidationRefusal(reason, record)
        graph[node] = (record, anchor)
    graph[support_id] = ()
    closure = assert_training_inputs(
        fold,
        inputs,
        graph,
        admitted_external_ids=externals,
        training_admission=training_admission,
    )
    compositions = {
        group: closed_composition(values)
        for group, values in sorted(fits.compositions.items())
    }
    if not compositions or set(compositions) != set(training_groups) - {
        ownership[anchor]
    }:
        raise ValidationRefusal(
            reason,
            "Require one reconstructed composition per admitted non-anchor group",
        )
    products = list(fits.fit_identities)
    if {
        identity(value.get("group_id")): value.get("composition") for value in products
    } != compositions:
        raise ValidationRefusal(
            reason,
            "Retained reconstruction products differ from baseline compositions",
        )
    model: dict[str, object] = {
        "schema_version": schema,
        "method": TRAINING_MEAN_METHOD,
        "method_kind": "admitted_reconstruction_training_mean",
        "fold": fold.as_dict(),
        "predictor_group_ids": sorted(compositions),
        "training_compositions": compositions,
        "training_products": products,
        "training_input_ids": list(inputs),
        "training_external_ids": list(externals),
        "allowed_input_closure": list(closure),
        "input_lineage": {key: sorted(set(graph[key])) for key in closure},
        "support": support,
        "regional_anchor_record_id": anchor,
        "regional_anchor_group_id": ownership[anchor],
        "regional_value_source_record_ids": [anchor],
        "regional_identity_source_record_ids": list(training_records),
        "uncertainty_status": "deterministic_point_baseline_no_intervals",
        "scientific_acceptance": "not_evaluated",
    }
    if training_admission is not None:
        # Preserve the established block wire exactly; grouped folds need no
        # invented support-buffer admission.
        model["training_admission"] = training_admission.as_dict()
    return model


def predict_training_mean_target(
    spec: FittedSpatialExperimentSpec,
    target: ExperimentSite,
    fold: Fold,
    fits: FoldFits,
    groups: dict[str, str],
    baseline_model: dict[str, object],
    *,
    input_root: Path,
    training_admission: TrainingAdmission | None = None,
    consumed_geometry: set[str] | None = None,
) -> dict[str, object]:
    """Project a training mean through the target's outcome-free forward support."""
    binding, prepared, geometry, bin_id = prepare_target_forward(
        spec,
        target,
        fits.anchor,
        fits.regional_cover,
        input_root=input_root,
        consumed_geometry=consumed_geometry,
    )
    compositions = {
        group: closed_composition(values) for group, values in fits.compositions.items()
    }
    taxa = tuple(prepared.taxa)
    block = training_admission is not None
    reason = "block_baseline" if block else "grouped_baseline"
    if not compositions or any(
        set(values) != set(taxa) for values in compositions.values()
    ):
        raise ValidationRefusal(
            reason + "_taxon_mismatch",
            "All admitted training reconstructions require the target taxon denominator",
        )
    vegetation = closed_composition(
        {
            taxon: sum(values[taxon] for values in compositions.values())
            / len(compositions)
            for taxon in taxa
        }
    )
    forward = cast(ForwardModel, binding.api.forward_deposition)(
        local_cover=tuple(vegetation[taxon] for taxon in taxa),
        regional_deposition=tuple(prepared.regional_deposition),
        local_k=tuple(tuple(ring) for ring in prepared.local_k),
        terrestrial_fraction=tuple(prepared.terrestrial_fraction),
        ppe=tuple(prepared.ppe),
    )
    if forward.method_profile != prepared.method_profile:
        raise ValidationRefusal(reason + "_forward_profile_mismatch", fold.fold_id)
    pollen = closed_composition(
        dict(zip(taxa, tuple(forward.pollen_fraction), strict=True))
    )
    preparation: dict[str, object] = {
        "preparation_profile": prepared.preparation_profile,
        "forward_method_profile": prepared.method_profile,
        "geometry_profile": prepared.geometry_profile,
        "deposition_units": prepared.deposition_units,
        "taxa": taxa,
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
    row: dict[str, object] = {
        "profile": BLOCK_PROFILE if block else FITTED_PROFILE,
        "method": TRAINING_MEAN_METHOD,
        "method_kind": "admitted_reconstruction_training_mean",
        "evaluation_roles": FITTED_ROLES,
        "fold_id": fold.fold_id,
        "outer_fold": fold.as_dict(),
        "record_id": target.record.record_id,
        "group_id": groups[target.record.record_id],
        "bin_id": bin_id,
        "vegetation_fraction": vegetation,
        "pollen_fraction": pollen,
        "baseline_model_sha256": manifest_sha256(baseline_model),
        "baseline_model_manifest": baseline_model,
        "support": baseline_model["support"],
        "target_geometry_sha256": target.geometry.sha256,
        "forward_preparation": preparation,
        "uncertainty_status": "deterministic_point_baseline_no_intervals",
        "scientific_acceptance": "not_evaluated",
    }
    if training_admission is not None:
        row["training_admission"] = training_admission.as_dict()
    row["prediction_manifest_sha256"] = manifest_sha256(row)
    return row
