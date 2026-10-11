"""Older observed LRA fits followed by an explicit unchanged-cover temporal baseline."""

from __future__ import annotations

from collections.abc import Mapping
import json
import os
from pathlib import Path
from typing import cast

from ....lra.api import LRABatchLimits, LRARefusal
from ....lra.engine.discovery import EngineBinding, load_engine
from ....lra.outputs.identity import capture_code_identity, verify_code_identity
from ...contracts import ValidationRefusal, finite_number, manifest_sha256
from ...experiments.configuration import object_mapping
from ...experiments.fitted.model import (
    FittedTrainingState,
    fit_reconstructed_training,
    retained_training_state,
)
from ...experiments.inputs import read_reference, verify_consumed_sources
from ...experiments.outputs import (
    ExperimentProduct,
    publish_phase,
    stage_directory,
    write_json,
)
from ...experiments.prediction import prepare_forward_geometry
from ...experiments.reconstruction import reconstruct_fold
from ...experiments.workflow import _implementation
from ...metrics import closed_composition
from ...prediction import ForwardModel
from ...spatial import SiteCoordinate, SpatialPrediction
from ..admission import admit_forward_time_training
from .admission import TemporalSourceAdmission, _evidence, admit_temporal_sources
from .configuration import METHOD, PROFILE, TemporalPersistenceSpec

ROLES = {
    "vegetation_cover": "heldout_younger_vegetation",
    "pollen": "heldout_younger_pollen",
}
UNCERTAINTY = "point_persistence_fixed_parameters_no_joint_uncertainty"


def persistence_envelope(
    admitted: TemporalSourceAdmission,
    *,
    model_sha256: str,
    spatial: SpatialPrediction,
    regional_cover: tuple[float, ...],
) -> dict[str, object]:
    """Bind unchanged values to a declared transfer; this makes no younger inversion."""
    spec = admitted.spec
    target = spec.temporal_plan.fold.test_record_ids[0]
    site = next(
        site for site in spec.older_experiment.sites if site.record.record_id == target
    )
    return {
        "schema_version": "lra-no-change-persistence.v1",
        "profile": METHOD,
        "spec_sha256": spec.sha256,
        "source_admission_sha256": admitted.sha256,
        "model_sha256": model_sha256,
        "older_spatial_prediction_sha256": spatial.prediction_sha256,
        "original_fold": spec.temporal_plan.fold.as_dict(),
        "record_id": target,
        "group_id": dict(spec.temporal_plan.record_groups)[target],
        "target_geometry_sha256": site.geometry.sha256,
        "older_bin": spec.older_bin().as_dict(),
        "younger_bin": spec.younger_bin.as_dict(),
        "full_chronology_declarations": [
            row.as_dict() for row in spec.temporal_plan.chronologies
        ],
        "local_vegetation_fraction": dict(spatial.fractions),
        "regional_vegetation_fraction": regional_cover,
        "parameters_sha256": manifest_sha256(
            spec.older_experiment.template()["parameters"]
        ),
        "assumption": spec.as_dict()["assumption"],
        "conditioning": "fixed_taxa_ppe_and_declared_target_time_geometry",
        "younger_observation_access": "none",
        "uncertainty_status": UNCERTAINTY,
        "scientific_acceptance": "not_evaluated",
    }


def _predict(
    admitted: TemporalSourceAdmission,
    state: FittedTrainingState,
    binding: EngineBinding,
) -> dict[str, object]:
    spec = admitted.spec
    fold = spec.temporal_plan.fold
    target = fold.test_record_ids[0]
    site = next(
        site for site in spec.older_experiment.sites if site.record.record_id == target
    )
    geometry = object_mapping(admitted.geometries()[target], "target_geometry")
    support_id = "experiment-support:" + manifest_sha256(state.support)
    spatial = state.model.predict(
        target_group_id=dict(spec.temporal_plan.record_groups)[target],
        coordinate=SiteCoordinate(
            finite_number(geometry["latitude"]), finite_number(geometry["longitude"])
        ),
        support_id=support_id,
    )
    envelope = persistence_envelope(
        admitted,
        model_sha256=state.model.model_sha256,
        spatial=spatial,
        regional_cover=state.fits.regional_cover,
    )
    mapped_binding, prepared = prepare_forward_geometry(
        spec.older_experiment.template(),
        geometry,
        state.fits.regional_cover,
        local_ring_count=spec.older_experiment.local_ring_count,
    )
    if mapped_binding.as_dict() != binding.as_dict():
        raise ValidationRefusal("temporal_engine_identity_changed", target)
    vegetation = dict(spatial.fractions)
    if set(vegetation) != set(prepared.taxa):
        raise ValidationRefusal("temporal_forward_taxa_mismatch", target)
    forward = cast(ForwardModel, binding.api.forward_deposition)(
        local_cover=tuple(vegetation[taxon] for taxon in prepared.taxa),
        regional_deposition=tuple(prepared.regional_deposition),
        local_k=tuple(tuple(row) for row in prepared.local_k),
        terrestrial_fraction=tuple(prepared.terrestrial_fraction),
        ppe=tuple(prepared.ppe),
    )
    if forward.method_profile != prepared.method_profile:
        raise ValidationRefusal("temporal_forward_profile_mismatch", target)
    preparation = {
        "preparation_profile": prepared.preparation_profile,
        "forward_method_profile": prepared.method_profile,
        "geometry_profile": prepared.geometry_profile,
        "deposition_units": prepared.deposition_units,
        "supplied_regional_cover": state.fits.regional_cover,
        "taxa": prepared.taxa,
        "local_k": [list(row) for row in prepared.local_k],
        "terrestrial_fraction": list(prepared.terrestrial_fraction),
        "ppe": list(prepared.ppe),
        "regional_deposition": list(prepared.regional_deposition),
        "regional_cover": list(prepared.regional_cover),
        "ring_bounds_m": [list(row) for row in prepared.ring_bounds_m],
        "regional_cutoff_m": prepared.regional_cutoff_m,
        "target_geometry_sha256": site.geometry.sha256,
        "declared_target_inversion_rings": geometry["inversion_rings"],
        "declared_target_forward_rings": geometry["forward_rings"],
    }
    row: dict[str, object] = {
        "profile": PROFILE,
        "method": METHOD,
        "method_kind": "declared_no_change_temporal_persistence",
        "evaluation_roles": ROLES,
        "fold_id": fold.fold_id,
        "outer_fold": fold.as_dict(),
        "record_id": target,
        "group_id": dict(spec.temporal_plan.record_groups)[target],
        "bin_id": spec.younger_bin.bin_id,
        "vegetation_fraction": vegetation,
        "pollen_fraction": closed_composition(
            dict(zip(prepared.taxa, forward.pollen_fraction, strict=True))
        ),
        "model_sha256": state.model.model_sha256,
        "older_spatial_prediction_manifest": json.loads(
            spatial.prediction_manifest_json
        ),
        "older_spatial_prediction_sha256": spatial.prediction_sha256,
        "persistence_envelope": envelope,
        "persistence_envelope_sha256": manifest_sha256(envelope),
        "forward_preparation": preparation,
        "target_geometry_sha256": site.geometry.sha256,
        "support": state.support,
        "uncertainty_status": UNCERTAINTY,
        "scientific_acceptance": "not_evaluated",
    }
    row["prediction_manifest_sha256"] = manifest_sha256(row)
    return row


def prepare_temporal_persistence_predictions(
    spec: TemporalPersistenceSpec | Mapping[str, object],
    *,
    input_root: Path,
    cache_root: Path,
    destination: Path,
    workers: int = 1,
) -> ExperimentProduct:
    """Publish one original held-out site with explicit younger support and full failures."""
    spec = (
        spec
        if isinstance(spec, TemporalPersistenceSpec)
        else TemporalPersistenceSpec.from_dict(spec)
    )
    LRABatchLimits(max_workers=workers)
    if workers > (os.cpu_count() or 1):
        raise ValidationRefusal("experiment_worker_budget_exceeded", str(workers))
    roots = [path.resolve() for path in (input_root, cache_root, destination)]
    if any(
        a == b or a in b.parents or b in a.parents
        for index, a in enumerate(roots)
        for b in roots[index + 1 :]
    ):
        raise ValidationRefusal(
            "temporal_output_input_overlap",
            "Input, cache and publication roots must be disjoint",
        )
    implementation = _implementation()
    stage = stage_directory(destination)
    fold = spec.temporal_plan.fold
    groups = dict(spec.temporal_plan.record_groups)
    predictions: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    operations: list[dict[str, object]] = []
    admitted: TemporalSourceAdmission | None = None
    retained: dict[str, object] | None = None
    older_regional: tuple[float, ...] | None = None
    consumed_pollen: set[str] = set()
    consumed_geometry: set[str] = set()
    consumed_chronology: set[str] = set()
    binding = None
    engine_identity = None
    interrupted = False
    try:
        admitted = admit_temporal_sources(
            spec,
            input_root=input_root,
            consumed_geometry=consumed_geometry,
            consumed_chronology=consumed_chronology,
        )
        training = admitted.decision.require_training_admission()
        binding = load_engine()
        engine_identity = capture_code_identity(binding)
        fits = reconstruct_fold(
            spec.older_experiment,
            fold,
            groups,
            input_root=input_root,
            cache_root=cache_root,
            report_root=stage / "batches" / "older",
            workers=workers,
            training_admission=training,
            consumed_pollen=consumed_pollen,
            consumed_geometry=consumed_geometry,
        )
        operations.append({"fold_id": fold.fold_id, "batch": fits.operational_batch})
        state = fit_reconstructed_training(
            spec.older_experiment,
            fold,
            fits,
            groups,
            input_root=input_root,
            consumed_geometry=consumed_geometry,
            training_admission=training,
        )
        retained = retained_training_state(state, groups)
        older_regional = fits.regional_cover
        predictions.append(_predict(admitted, state, binding))
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
        reason = getattr(exc, "reason_code", "temporal_persistence_refused")
        interrupted = reason == "experiment_interrupted"
        failure: dict[str, object] = {
            "fold_id": fold.fold_id,
            "record_ids": fold.test_record_ids,
            "status": "not_run" if interrupted else "refused",
            "reason_code": reason,
            "detail": str(exc),
            "exception_type": type(exc).__name__,
        }
        if isinstance(exc, LRARefusal):
            failure["original_error"] = exc.as_dict()
        failures.append(failure)
    if _implementation() != implementation:
        raise ValidationRefusal("experiment_implementation_changed", str(stage))
    if binding is not None and engine_identity is not None:
        verify_code_identity(binding, engine_identity)
    scientific: dict[str, object] = {
        "profile": PROFILE,
        "experiment": "all_target_pollen_withheld_forward_time_persistence",
        "spec_sha256": spec.sha256,
        "folds": [fold.as_dict()],
        "methods": [METHOD],
        "evaluation_roles": ROLES,
        "predictions": predictions,
        "failures": failures,
        "temporal_decision": admit_forward_time_training(spec.temporal_plan).as_dict(),
        "source_admission": None if admitted is None else admitted.as_dict(),
        "older_training_state": retained,
        "older_regional_vegetation_fraction": older_regional,
        "implementation": implementation,
        "engine_identity": None
        if engine_identity is None
        else engine_identity.payload(),
        "requested_folds": 1,
        "requested_predictions": 1,
        "generated_predictions": len(predictions),
        "failed_folds": len(failures),
        "interrupted": interrupted,
        "all_predictions_generated": not failures,
        "uncertainty_status": UNCERTAINTY,
        "scientific_acceptance": "not_evaluated",
        "consumed_pollen_record_ids": sorted(consumed_pollen),
        "consumed_geometry_record_ids": sorted(consumed_geometry),
        "consumed_chronology_evidence_ids": sorted(consumed_chronology),
    }
    for name, value in (
        ("experiment.json", spec.as_dict()),
        ("folds.json", [fold.as_dict()]),
        ("predictions.json", predictions),
        ("failures.json", failures),
        ("operations.json", operations),
        ("admission.json", scientific["source_admission"]),
        ("training.json", retained),
    ):
        write_json(stage, name, value)
    verify_consumed_sources(
        spec.older_experiment,
        input_root,
        pollen_record_ids=consumed_pollen,
        geometry_record_ids=consumed_geometry,
        template_used=bool(consumed_pollen),
    )
    if consumed_chronology:
        references = _evidence(spec)
        for key in sorted(consumed_chronology):
            read_reference(input_root, references[key])
    if _implementation() != implementation:
        raise ValidationRefusal("experiment_implementation_changed", str(stage))
    if binding is not None and engine_identity is not None:
        verify_code_identity(binding, engine_identity)
    return publish_phase(
        stage, destination, phase="predictions", scientific=scientific, profile=PROFILE
    )
