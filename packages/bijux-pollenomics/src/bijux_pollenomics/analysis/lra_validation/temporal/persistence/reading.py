"""Retained temporal transport admission through existing fitted and product authorities."""

from __future__ import annotations

import json
from pathlib import Path

from ...contracts import (
    ValidationRefusal,
    canonical_json,
    finite_number,
    manifest_sha256,
)
from ...experiments.configuration import identity, object_list, object_mapping
from ...experiments.fitted import validate_training_state
from ...experiments.outputs import (
    ExperimentProduct,
    read_experiment_product,
    read_member,
    validate_fitted_preparation,
)
from ...metrics import closed_composition
from ...spatial import SiteCoordinate
from ..admission import admit_forward_time_training
from .admission import TemporalSourceAdmission
from .configuration import METHOD, PROFILE, TemporalPersistenceSpec
from .provenance import validate_temporal_requests
from .workflow import ROLES, UNCERTAINTY, persistence_envelope


def _same(actual: object, expected: object, label: str) -> None:
    if canonical_json(actual) != canonical_json(expected):
        raise ValidationRefusal("temporal_product_identity_mismatch", label)


def _source_admission(
    spec: TemporalPersistenceSpec, value: object
) -> TemporalSourceAdmission | None:
    if value is None:
        return None
    row = object_mapping(value, "source_admission")
    result = TemporalSourceAdmission(
        spec,
        canonical_json(row["geometries"]),
        canonical_json(row["geometry_source_text"]),
    )
    _same(row, result.as_dict(), "source admission receipt")
    return result


def _prediction(
    spec: TemporalPersistenceSpec,
    source: TemporalSourceAdmission,
    state: dict[str, object],
    regional: object,
    row: dict[str, object],
) -> None:
    fold = spec.temporal_plan.fold
    groups = dict(spec.temporal_plan.record_groups)
    target = fold.test_record_ids[0]
    admission = source.decision.require_training_admission()
    anchor = spec.temporal_plan.required_regional_record_ids[0]
    geometries = {
        record: object_mapping(value, "geometry")
        for record, value in source.geometries().items()
    }
    coordinates = {
        groups[record]: SiteCoordinate(
            finite_number(geometries[record]["latitude"]),
            finite_number(geometries[record]["longitude"]),
        )
        for record in admission.admitted_record_ids
        if record != anchor
    }
    model = validate_training_state(
        spec.older_experiment, fold, admission, state, expected_coordinates=coordinates
    )
    geometry = geometries[target]
    spatial = model.predict(
        target_group_id=groups[target],
        coordinate=SiteCoordinate(
            finite_number(geometry["latitude"]), finite_number(geometry["longitude"])
        ),
        support_id=model.config.support_id,
    )
    taxa = tuple(
        identity(value)
        for value in object_list(spec.older_experiment.template()["taxa"], "taxa")
    )
    older_regional = tuple(
        finite_number(value)
        for value in object_list(regional, "older_regional_vegetation_fraction")
    )
    if len(older_regional) != len(taxa):
        raise ValidationRefusal("temporal_regional_denominator_mismatch", target)
    closed_composition(dict(zip(taxa, older_regional, strict=True)))
    expected = persistence_envelope(
        source,
        model_sha256=model.model_sha256,
        spatial=spatial,
        regional_cover=older_regional,
    )
    required = {
        "profile": PROFILE,
        "method": METHOD,
        "method_kind": "declared_no_change_temporal_persistence",
        "evaluation_roles": ROLES,
        "fold_id": fold.fold_id,
        "outer_fold": fold.as_dict(),
        "record_id": target,
        "group_id": groups[target],
        "bin_id": spec.younger_bin.bin_id,
        "vegetation_fraction": dict(spatial.fractions),
        "model_sha256": model.model_sha256,
        "older_spatial_prediction_manifest": json.loads(
            spatial.prediction_manifest_json
        ),
        "older_spatial_prediction_sha256": spatial.prediction_sha256,
        "persistence_envelope": expected,
        "persistence_envelope_sha256": manifest_sha256(expected),
        "target_geometry_sha256": next(
            site.geometry.sha256
            for site in spec.older_experiment.sites
            if site.record.record_id == target
        ),
        "support": state["support"],
        "uncertainty_status": UNCERTAINTY,
        "scientific_acceptance": "not_evaluated",
    }
    if set(row) != {
        *required,
        "pollen_fraction",
        "forward_preparation",
        "prediction_manifest_sha256",
    }:
        raise ValidationRefusal("temporal_prediction_shape_mismatch", target)
    for field, value in required.items():
        _same(row[field], value, field)
    _same(
        row["prediction_manifest_sha256"],
        manifest_sha256(
            {
                key: value
                for key, value in row.items()
                if key != "prediction_manifest_sha256"
            }
        ),
        "prediction hash",
    )
    pollen = {
        key: finite_number(value)
        for key, value in object_mapping(row["pollen_fraction"], "pollen").items()
    }
    if set(pollen) != set(taxa):
        raise ValidationRefusal("temporal_pollen_denominator_mismatch", target)
    closed_composition(pollen)
    validate_fitted_preparation(row, object_mapping(state["fit_manifest"], "fit"))
    prepared = object_mapping(row["forward_preparation"], "preparation")
    _same(
        prepared["supplied_regional_cover"], older_regional, "supplied regional values"
    )
    _same(
        prepared["declared_target_forward_rings"],
        geometry["forward_rings"],
        "target forward geometry",
    )
    _same(
        prepared["declared_target_inversion_rings"],
        geometry["inversion_rings"],
        "target inversion geometry",
    )
    parameter_ppe = {
        identity(row["taxon"]): finite_number(row["ppe"])
        for value in object_list(
            spec.older_experiment.template()["parameters"], "parameters"
        )
        if (row := object_mapping(value, "parameter"))
    }
    _same(prepared["ppe"], [parameter_ppe[taxon] for taxon in taxa], "fixed PPE order")


def read_temporal_persistence_predictions(
    directory: Path, *, expected_manifest_sha256: str
) -> tuple[ExperimentProduct, TemporalPersistenceSpec, dict[str, object]]:
    """Verify retained internal and byte closure; do not claim numerical regeneration."""
    product, manifest = read_experiment_product(
        directory, expected_manifest_sha256=expected_manifest_sha256
    )
    try:
        if manifest["profile"] != PROFILE or manifest["phase"] != "predictions":
            raise ValidationRefusal(
                "unsupported_temporal_product",
                "Require the distinct temporal prediction phase",
            )
        spec = TemporalPersistenceSpec.from_dict(
            read_member(product, "experiment.json")
        )
        scientific = object_mapping(
            manifest["scientific_payload"], "scientific_payload"
        )
        expected_fields = {
            "profile",
            "experiment",
            "spec_sha256",
            "folds",
            "methods",
            "evaluation_roles",
            "predictions",
            "failures",
            "temporal_decision",
            "source_admission",
            "older_training_state",
            "older_regional_vegetation_fraction",
            "implementation",
            "engine_identity",
            "requested_folds",
            "requested_predictions",
            "generated_predictions",
            "failed_folds",
            "interrupted",
            "all_predictions_generated",
            "uncertainty_status",
            "scientific_acceptance",
            "consumed_pollen_record_ids",
            "consumed_geometry_record_ids",
            "consumed_chronology_evidence_ids",
        }
        if set(scientific) != expected_fields:
            raise ValidationRefusal(
                "invalid_temporal_scientific_shape",
                "Require exact declared scope fields",
            )
        _same(
            scientific["temporal_decision"],
            admit_forward_time_training(spec.temporal_plan).as_dict(),
            "complete temporal decision",
        )
        fold = spec.temporal_plan.fold
        predictions = object_list(scientific["predictions"], "predictions")
        failures = object_list(scientific["failures"], "failures")
        if len(predictions) + len(failures) != 1:
            raise ValidationRefusal(
                "temporal_prediction_accounting_mismatch",
                "One original target requires exactly one prediction or failure",
            )
        required = {
            "profile": PROFILE,
            "experiment": "all_target_pollen_withheld_forward_time_persistence",
            "spec_sha256": spec.sha256,
            "folds": [fold.as_dict()],
            "methods": [METHOD],
            "evaluation_roles": ROLES,
            "requested_folds": 1,
            "requested_predictions": 1,
            "generated_predictions": len(predictions),
            "failed_folds": len(failures),
            "all_predictions_generated": not failures,
            "uncertainty_status": UNCERTAINTY,
            "scientific_acceptance": "not_evaluated",
        }
        for key, value in required.items():
            _same(scientific[key], value, key)
        for name, key in (
            ("folds.json", "folds"),
            ("predictions.json", "predictions"),
            ("failures.json", "failures"),
            ("admission.json", "source_admission"),
            ("training.json", "older_training_state"),
        ):
            _same(read_member(product, name), scientific[key], name)
        if type(scientific["interrupted"]) is not bool:
            raise ValidationRefusal(
                "invalid_temporal_interruption", "Require a boolean"
            )
        for value in failures:
            failure = object_mapping(value, "failure")
            _same(failure["fold_id"], fold.fold_id, "failed fold")
            _same(failure["record_ids"], fold.test_record_ids, "failed target")
            if failure["status"] not in {"refused", "not_run"} or (
                failure["status"] == "not_run"
            ) != (failure["reason_code"] == "experiment_interrupted"):
                raise ValidationRefusal(
                    "invalid_temporal_interruption", "Failure state and reason disagree"
                )
            _same(
                scientific["interrupted"],
                failure["status"] == "not_run",
                "interruption",
            )
        if predictions:
            _same(scientific["interrupted"], False, "completed prediction")
        decision = admit_forward_time_training(spec.temporal_plan)
        admission = decision.training_admission
        allowed = set() if admission is None else set(admission.admitted_record_ids)
        for field, eligible in (
            ("consumed_pollen_record_ids", allowed),
            (
                "consumed_geometry_record_ids",
                set() if admission is None else allowed | set(fold.test_record_ids),
            ),
        ):
            consumed = [
                identity(value) for value in object_list(scientific[field], field)
            ]
            if sorted(set(consumed)) != consumed or not set(consumed).issubset(
                eligible
            ):
                raise ValidationRefusal("temporal_consumed_source_mismatch", field)
            if predictions:
                _same(consumed, sorted(eligible), field)
        if (scientific["older_training_state"] is None) != (
            scientific["older_regional_vegetation_fraction"] is None
        ):
            raise ValidationRefusal(
                "temporal_regional_state_mismatch",
                "Regional values require the actual older fitted state",
            )
        if scientific["older_regional_vegetation_fraction"] is not None:
            taxa = tuple(
                identity(value)
                for value in object_list(
                    spec.older_experiment.template()["taxa"], "taxa"
                )
            )
            regional = tuple(
                finite_number(value)
                for value in object_list(
                    scientific["older_regional_vegetation_fraction"], "regional"
                )
            )
            if len(regional) != len(taxa):
                raise ValidationRefusal(
                    "temporal_regional_denominator_mismatch", fold.fold_id
                )
            closed_composition(dict(zip(taxa, regional, strict=True)))
        source = _source_admission(spec, scientific["source_admission"])
        validate_temporal_requests(product, manifest, spec, source, scientific)
        chronology = [
            identity(value)
            for value in object_list(
                scientific["consumed_chronology_evidence_ids"], "consumed chronology"
            )
        ]
        expected_chronology = (
            set()
            if source is None
            else {
                identity(
                    object_mapping(
                        object_mapping(value, "geometry")["sample_metadata"], "metadata"
                    )["chronology_evidence_id"]
                )
                for value in source.geometries().values()
            }
        )
        declared_chronology = {
            identity(row["evidence_id"])
            for value in object_list(
                spec.older_experiment.template()["evidence"], "evidence"
            )
            if (row := object_mapping(value, "evidence"))["role"] == "chronology"
        }
        if sorted(set(chronology)) != chronology or not set(chronology).issubset(
            declared_chronology
        ):
            raise ValidationRefusal(
                "temporal_consumed_source_mismatch", "chronology references"
            )
        if predictions:
            _same(chronology, sorted(expected_chronology), "consumed chronology")
            if scientific["engine_identity"] is None:
                raise ValidationRefusal(
                    "missing_temporal_engine_identity", fold.fold_id
                )
        if predictions:
            if source is None or scientific["older_training_state"] is None:
                raise ValidationRefusal("missing_temporal_training_state", fold.fold_id)
            _prediction(
                spec,
                source,
                object_mapping(scientific["older_training_state"], "training"),
                scientific["older_regional_vegetation_fraction"],
                object_mapping(predictions[0], "prediction"),
            )
        elif scientific["older_training_state"] is not None:
            if source is None:
                raise ValidationRefusal(
                    "missing_temporal_source_admission", fold.fold_id
                )
            state = object_mapping(scientific["older_training_state"], "training")
            training = source.decision.require_training_admission()
            geometries = source.geometries()
            groups = dict(spec.temporal_plan.record_groups)
            coordinates = {
                groups[record]: SiteCoordinate(
                    finite_number(
                        object_mapping(geometries[record], "geometry")["latitude"]
                    ),
                    finite_number(
                        object_mapping(geometries[record], "geometry")["longitude"]
                    ),
                )
                for record in training.admitted_record_ids
                if record not in spec.temporal_plan.required_regional_record_ids
            }
            validate_training_state(
                spec.older_experiment,
                fold,
                training,
                state,
                expected_coordinates=coordinates,
            )
        read_experiment_product(
            directory, expected_manifest_sha256=expected_manifest_sha256
        )
        return product, spec, scientific
    except ValidationRefusal:
        raise
    except (KeyError, TypeError, ValueError, OSError) as exc:
        raise ValidationRefusal("invalid_temporal_product", str(exc)) from exc
