"""Linear data-support diagnostics, separate from ridge and physical identifiability."""

from __future__ import annotations

import json
from math import isfinite

from ..contracts import ValidationRefusal, manifest_sha256
from .configuration import SiteCoordinate, distance_km
from .model import FittedSpatialModel, _basis


def spatial_identifiability(
    model: FittedSpatialModel,
    *,
    target_group_id: str,
    coordinate: SiteCoordinate,
    support_id: str,
) -> dict[str, object]:
    """Report raw centred-feature rank and target row-span support only.

    Positive ridge makes the augmented solve unique without making its original
    columns independently identifiable. No ecological or inverse-LRA rank claim
    follows from this linear diagnostic or from nearby coordinates.
    """
    prediction = model.predict(
        target_group_id=target_group_id, coordinate=coordinate, support_id=support_id
    )
    import numpy as np

    features = np.asarray(
        [
            [
                _basis(distance_km(a, b), model.config.length_scale_km)
                for b in model.centres
            ]
            for a in model.centres
        ],
        dtype=np.float64,
    )
    design = features - np.asarray(model.feature_mean)
    target = np.asarray(
        [
            _basis(distance_km(coordinate, point), model.config.length_scale_km)
            for point in model.centres
        ]
    ) - np.asarray(model.feature_mean)
    try:
        _, singular, right = np.linalg.svd(design, full_matrices=False)
    except np.linalg.LinAlgError as exc:
        raise ValidationRefusal("spatial_identifiability_unresolved", str(exc)) from exc
    tolerance = float(
        np.finfo(float).eps * max(design.shape) * (singular[0] if len(singular) else 0)
    )
    rank = int(np.sum(singular > tolerance))
    projected = right[:rank].T @ (right[:rank] @ target)
    residual = float(np.linalg.norm(target - projected))
    threshold = float(
        np.finfo(float).eps
        * max(design.shape)
        * max(1.0, float(np.linalg.norm(target)))
    )
    if not all(isfinite(x) for x in (*singular, residual, threshold)):
        raise ValidationRefusal(
            "spatial_identifiability_unresolved", "Nonfinite raw-design diagnostic"
        )
    fitted = json.loads(model.fit_manifest_json)
    payload: dict[str, object] = {
        "schema_version": "lra-spatial-linear-identifiability.v1",
        "model_sha256": model.model_sha256,
        "prediction_sha256": prediction.prediction_sha256,
        "unpenalized_feature_count": len(model.groups),
        "unpenalized_rank": rank,
        "raw_singular_values": [float(x) for x in singular],
        "raw_rank_tolerance": tolerance,
        "ridge_augmented_rank": fitted["solver"]["rank"],
        "ridge_regularized_nonunique_features": rank < len(model.groups),
        "target_row_span_residual": residual,
        "target_row_span_tolerance": threshold,
        "target_linear_function_in_training_row_span": residual <= threshold,
        "nearest_training_distance_km": prediction.nearest_training_distance_km,
        "scope": "Numerical linear feature support under fixed declared CLR/ridge model only; no physical inverse identifiability, residual-process uncertainty, calibrated coverage or ecological validation.",
    }
    return {**payload, "diagnostic_sha256": manifest_sha256(payload)}
