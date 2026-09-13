"""Separate younger observation access after retained temporal prediction verification."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ...contracts import ValidationRefusal, canonical_json, manifest_sha256
from ...experiments.configuration import (
    InputReference,
    identity,
    object_list,
    object_mapping,
)
from ...experiments.inputs import read_reference
from ...experiments.outputs import (
    ExperimentProduct,
    publish_phase,
    read_experiment_product,
    stage_directory,
    write_json,
)
from ...experiments.scoring import _score
from ..admission import admit_forward_time_training
from .configuration import METHOD, PROFILE, TemporalPersistenceSpec
from .reading import read_temporal_persistence_predictions
from .workflow import ROLES, UNCERTAINTY


def _inventory(
    inventory: Mapping[str, object], spec: TemporalPersistenceSpec, parent: str
) -> dict[str, InputReference]:
    row = object_mapping(inventory, "outcome_inventory")
    if (
        set(row)
        != {
            "schema_version",
            "data_kind",
            "purpose",
            "predictions_manifest_sha256",
            "records",
        }
        or row["schema_version"] != "lra-temporal-outcomes.v1"
        or row["data_kind"] != "synthetic"
        or row["purpose"] != "exploratory"
        or row["predictions_manifest_sha256"] != parent
    ):
        raise ValidationRefusal(
            "invalid_temporal_outcome_inventory",
            "Require exact synthetic exploratory parent identity",
        )
    result = {}
    for value in object_list(row["records"], "records"):
        record = object_mapping(value, "record")
        if set(record) != {"record_id", "observation"}:
            raise ValidationRefusal(
                "invalid_temporal_outcome_inventory",
                "Require explicit record and pinned observation",
            )
        key = identity(record["record_id"])
        if key not in spec.temporal_plan.fold.test_record_ids or key in result:
            raise ValidationRefusal(
                "invalid_temporal_outcome_inventory", "Unknown or duplicate target"
            )
        result[key] = InputReference.parse(record["observation"], "observation")
    return result


def _observation(
    value: dict[str, object], spec: TemporalPersistenceSpec, geometry: dict[str, object]
) -> dict[str, object]:
    target = spec.temporal_plan.fold.test_record_ids[0]
    site = next(
        site for site in spec.older_experiment.sites if site.record.record_id == target
    )
    expected = {
        "data_kind": "synthetic",
        "purpose": "exploratory",
        "record_id": target,
        "geometry_sha256": site.geometry.sha256,
        "sample_metadata": geometry["sample_metadata"],
        "taxa": spec.older_experiment.template()["taxa"],
    }
    if set(value) != {
        *expected,
        "vegetation_unit",
        "vegetation_fraction",
        "pollen_unit",
        "pollen_count",
    }:
        raise ValidationRefusal(
            "invalid_temporal_observation",
            "Require complete younger target observation fields",
        )
    for key, declared in expected.items():
        if canonical_json(value[key]) != canonical_json(declared):
            raise ValidationRefusal("temporal_observation_support_mismatch", key)
    for key in ("vegetation_fraction", "pollen_count"):
        if value[key] is not None and set(object_mapping(value[key], key)) != set(
            object_list(expected["taxa"], "taxa")
        ):
            raise ValidationRefusal("temporal_observation_denominator_mismatch", key)
    return value


def score_temporal_persistence_predictions(
    predictions: Path,
    *,
    expected_manifest_sha256: str,
    outcome_root: Path,
    outcome_inventory: Mapping[str, object],
    destination: Path,
    purpose: str = "exploratory",
) -> ExperimentProduct:
    """Evaluate both younger targets separately; no final policy or uncertainty claim."""
    if purpose != "exploratory":
        raise ValidationRefusal(
            "unsupported_temporal_scoring_purpose", "Final evaluation is not admitted"
        )
    product, spec, scientific = read_temporal_persistence_predictions(
        predictions, expected_manifest_sha256=expected_manifest_sha256
    )
    references = _inventory(outcome_inventory, spec, product.manifest_sha256)
    roots = [path.resolve() for path in (predictions, outcome_root, destination)]
    if any(
        a == b or a in b.parents or b in a.parents
        for index, a in enumerate(roots)
        for b in roots[index + 1 :]
    ):
        raise ValidationRefusal(
            "temporal_output_input_overlap",
            "Prediction, observation and output roots must be disjoint",
        )
    stage = stage_directory(destination)
    target = spec.temporal_plan.fold.test_record_ids[0]
    rows = object_list(scientific["predictions"], "predictions")
    prediction = None if not rows else object_mapping(rows[0], "prediction")
    observation = None
    refusal = None
    access: list[dict[str, object]] = []
    consumed: list[InputReference] = []
    if prediction is not None and target in references:
        reference = references[target]
        access.append(
            {
                "record_id": target,
                "path": reference.path,
                "sha256": reference.sha256,
                "predictions_manifest_sha256": product.manifest_sha256,
                "access_order": "after_retained_prediction_admission",
            }
        )
        write_json(stage, "outcome_access.json", access)
        try:
            actual = read_reference(outcome_root, reference)
            consumed.append(reference)
            source = object_mapping(scientific["source_admission"], "source_admission")
            geometry = object_mapping(
                object_mapping(source["geometries"], "geometries")[target], "target"
            )
            observation = _observation(actual, spec, geometry)
        except (ValidationRefusal, ValueError) as exc:
            refusal = {
                "reason_code": getattr(
                    exc, "reason_code", "invalid_temporal_observation"
                ),
                "detail": str(exc),
            }
    scores = []
    for kind in ("vegetation_cover", "pollen"):
        if prediction is None:
            metrics: dict[str, object] = {
                "status": "failed_prediction",
                "reason_code": "temporal_prediction_unavailable",
            }
        elif refusal is not None:
            metrics = {"status": "refused_observation", **refusal}
        else:
            try:
                metrics = _score(kind, prediction, observation)
            except (ValidationRefusal, ValueError, KeyError) as exc:
                metrics = {
                    "status": "refused_observation",
                    "reason_code": getattr(
                        exc, "reason_code", "invalid_temporal_observation"
                    ),
                    "detail": str(exc),
                }
        scores.append(
            {
                "fold_id": spec.temporal_plan.fold.fold_id,
                "record_id": target,
                "group_id": dict(spec.temporal_plan.record_groups)[target],
                "bin_id": spec.younger_bin.bin_id,
                "method": METHOD,
                "target": kind,
                "evaluation_role": ROLES[kind],
                "prediction_manifest_sha256": None
                if prediction is None
                else prediction["prediction_manifest_sha256"],
                "observation_reference": None
                if target not in references
                else {
                    "path": references[target].path,
                    "sha256": references[target].sha256,
                },
                "observation": observation,
                "metrics": metrics,
            }
        )
    denominators = {
        kind: {
            "requested": 1,
            "generated_prediction": int(prediction is not None),
            "status": object_mapping(row["metrics"], "metrics")["status"],
        }
        for kind, row in zip(("vegetation_cover", "pollen"), scores, strict=True)
    }
    payload: dict[str, object] = {
        "profile": PROFILE,
        "phase": "scores",
        "method": METHOD,
        "predictions_manifest_sha256": product.manifest_sha256,
        "predictions_scientific_content_sha256": product.scientific_content_sha256,
        "outcome_inventory_sha256": manifest_sha256(outcome_inventory),
        "scores": scores,
        "denominators": denominators,
        "temporal_plan": spec.temporal_plan.as_dict(),
        "temporal_admission": admit_forward_time_training(spec.temporal_plan).as_dict(),
        "older_spatial_distances_km": None
        if prediction is None
        else object_mapping(
            prediction["older_spatial_prediction_manifest"], "spatial prediction"
        )["distances_km"],
        "distance_scope": "unrounded_point_to_training_predictor_distances_not_support_buffer",
        "older_bin": spec.older_bin().as_dict(),
        "younger_bin": spec.younger_bin.as_dict(),
        "scientific_acceptance": "not_evaluated",
        "uncertainty_status": UNCERTAINTY,
        "final_policy_evaluation": "not_performed",
    }
    for name, value in (
        ("scores.json", scores),
        ("outcome_inventory.json", outcome_inventory),
        ("outcome_access.json", access),
    ):
        write_json(stage, name, value)
    for reference in consumed:
        read_reference(outcome_root, reference)
    read_experiment_product(
        predictions, expected_manifest_sha256=product.manifest_sha256
    )
    return publish_phase(
        stage, destination, phase="scores", scientific=payload, profile=PROFILE
    )
