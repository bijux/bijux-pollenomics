"""Training-only CLR ridge fitting and separately evaluated target coordinates."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import json
from math import exp, fsum, isfinite

from ..contracts import (
    Fold,
    TrainingAdmission,
    ValidationRefusal,
    canonical_json,
    identity_values,
    manifest_sha256,
    required_identity,
)
from ..metrics import closed_composition
from ..splits import assert_training_inputs
from .configuration import PROFILE, SiteCoordinate, SpatialConfig, distance_km


@dataclass(frozen=True)
class SpatialPrediction:
    """A fitted spatial point prediction; no predictive interval is implied."""

    fractions: tuple[tuple[str, float], ...]
    model_sha256: str
    prediction_manifest_json: str
    prediction_sha256: str
    nearest_training_distance_km: float
    method: str = PROFILE


@dataclass(frozen=True)
class FittedSpatialModel:
    """Immutable fitted state with its exact training evidence and solver values."""

    fold: Fold
    config: SpatialConfig
    groups: tuple[str, ...]
    taxa: tuple[str, ...]
    centres: tuple[SiteCoordinate, ...]
    feature_mean: tuple[float, ...]
    clr_mean: tuple[float, ...]
    coefficients: tuple[tuple[float, ...], ...]
    fit_manifest_json: str
    model_sha256: str
    training_admission: TrainingAdmission | None = None

    def __post_init__(self) -> None:
        self._verify_identity()

    def _verify_identity(self) -> None:
        """Bind every predictive state field, including dataclass replacements."""
        try:
            payload = json.loads(self.fit_manifest_json)
            state = {
                "configuration": self.config.as_dict(),
                "fold": self.fold.as_dict(),
                "predictor_group_ids": self.groups,
                "training_coordinates": {
                    group: centre.as_dict()
                    for group, centre in zip(self.groups, self.centres, strict=True)
                },
                "taxa": self.taxa,
                "feature_mean": self.feature_mean,
                "clr_mean": self.clr_mean,
                "coefficients": self.coefficients,
            }
            schema = "lra-fitted-spatial-model.v1"
            if self.training_admission is not None:
                if not isinstance(self.training_admission, TrainingAdmission):
                    raise ValueError("Training admission must be typed")
                self.training_admission.validate(self.fold)
                state["training_admission"] = self.training_admission.as_dict()
                schema = "lra-fitted-spatial-model.v2"
                if not set(self.groups).issubset(
                    self.training_admission.admitted_group_ids
                ):
                    raise ValueError("Predictors include excluded training groups")
                closure = assert_training_inputs(
                    self.fold,
                    payload["allowed_input_closure"],
                    payload["input_lineage"],
                    training_admission=self.training_admission,
                    admitted_external_ids=payload["admitted_external_ids"],
                )
                if not set(self.training_admission.admitted_record_ids).issubset(
                    closure
                ):
                    raise ValueError("Incomplete admitted training ancestry")
            if (
                manifest_sha256(payload) != self.model_sha256
                or canonical_json({key: payload[key] for key in state})
                != canonical_json(state)
                or payload["schema_version"] != schema
                or payload["scientific_acceptance"] != "not_evaluated"
                or payload["uncertainty_status"] != "point_fit_only"
            ):
                raise ValueError("Fitted state differs from its identity")
        except (ValueError, TypeError, KeyError) as exc:
            raise ValidationRefusal(
                "spatial_model_identity_mismatch", str(exc)
            ) from exc

    def predict(
        self, *, target_group_id: str, coordinate: SiteCoordinate, support_id: str
    ) -> SpatialPrediction:
        """Accept target geography only after fitting; no target outcome argument."""
        self._verify_identity()
        required_identity(target_group_id)
        if target_group_id not in self.fold.test_group_ids:
            raise ValidationRefusal("spatial_target_not_withheld", target_group_id)
        if support_id != self.config.support_id:
            raise ValidationRefusal("spatial_support_mismatch", support_id)
        distances = tuple(distance_km(coordinate, centre) for centre in self.centres)
        features = tuple(_basis(d, self.config.length_scale_km) for d in distances)
        logits = tuple(
            self.clr_mean[t]
            + fsum(
                (features[g] - self.feature_mean[g]) * self.coefficients[g][t]
                for g in range(len(self.groups))
            )
            for t in range(len(self.taxa))
        )
        if not all(isfinite(value) for value in logits):
            raise ValidationRefusal("spatial_prediction_nonfinite", target_group_id)
        masses = tuple(exp(value - max(logits)) for value in logits)
        total = fsum(masses)
        fractions = tuple(
            (taxon, value / total)
            for taxon, value in zip(self.taxa, masses, strict=True)
        )
        if any(value <= 0 for _, value in fractions):
            raise ValidationRefusal("spatial_prediction_underflow", target_group_id)
        payload = {
            "schema_version": "lra-fitted-spatial-prediction.v1",
            "profile": PROFILE,
            "model_sha256": self.model_sha256,
            "target_group_id": target_group_id,
            "coordinate": coordinate.as_dict(),
            "support_id": support_id,
            "distances_km": dict(zip(self.groups, distances, strict=True)),
            "vegetation_fraction": dict(fractions),
            "uncertainty_status": "point_prediction_only",
            "scientific_acceptance": "not_evaluated",
        }
        return SpatialPrediction(
            fractions,
            self.model_sha256,
            canonical_json(payload),
            manifest_sha256(payload),
            min(distances),
        )


def _basis(distance: float, scale: float) -> float:
    ratio = distance / scale
    # At this distance the correctly rounded binary64 exponential is zero.
    # Avoid overflow when squaring an otherwise valid large ratio.
    return 0.0 if ratio > 40 else exp(-0.5 * ratio * ratio)


def fit_spatial_model(
    fold: Fold,
    training_compositions: Mapping[str, Mapping[str, float]],
    training_coordinates: Mapping[str, SiteCoordinate],
    *,
    config: SpatialConfig,
    input_ids: Iterable[str],
    dependency_graph: Mapping[str, Iterable[str]],
    admitted_external_ids: Iterable[str] = (),
    predictor_group_ids: Iterable[str] | None = None,
    training_admission: TrainingAdmission | None = None,
) -> FittedSpatialModel:
    """Fit equally weighted CLR responses with unpenalized intercept and ridge.

    Features are WGS84 radial distances to training centres, not an assumed
    positive-definite geographic covariance kernel. Hyperparameters and support
    are supplied declarations. Their scientific selection must be reviewed by
    the surrounding experiment policy. No zero replacement or tuning occurs.
    """
    if training_admission is not None:
        if not isinstance(training_admission, TrainingAdmission):
            raise ValidationRefusal(
                "invalid_training_admission", "Require a typed admission"
            )
        training_admission.validate(fold)
    training_groups = (
        fold.train_group_ids
        if training_admission is None
        else training_admission.admitted_group_ids
    )
    training_records = (
        fold.train_record_ids
        if training_admission is None
        else training_admission.admitted_record_ids
    )
    groups = identity_values(
        training_groups if predictor_group_ids is None else predictor_group_ids
    )
    if (
        not 2 <= len(groups) <= 128
        or len(set(groups)) != len(groups)
        or not set(groups).issubset(training_groups)
    ):
        raise ValidationRefusal(
            "spatial_group_mismatch", "Require 2–128 unique training predictor groups"
        )
    groups = tuple(sorted(groups))
    if set(training_compositions) != set(groups) or set(training_coordinates) != set(
        groups
    ):
        raise ValidationRefusal(
            "spatial_group_mismatch",
            "Coordinates and compositions must match every declared predictor",
        )
    graph = {key: identity_values(values) for key, values in dependency_graph.items()}
    external_ids = identity_values(admitted_external_ids)
    closure = assert_training_inputs(
        fold,
        input_ids,
        graph,
        admitted_external_ids=external_ids,
        training_admission=training_admission,
    )
    if not set(training_records).issubset(closure):
        raise ValidationRefusal(
            "incomplete_training_lineage",
            "Full outer training ancestry is required"
            if training_admission is None
            else "Complete admitted training ancestry is required",
        )
    compositions = {
        group: closed_composition(training_compositions[group]) for group in groups
    }
    taxa = tuple(sorted(compositions[groups[0]]))
    if len(taxa) < 2 or any(
        set(values) != set(taxa) for values in compositions.values()
    ):
        raise ValidationRefusal(
            "taxon_denominator_mismatch",
            "Require the same two or more taxa at every predictor",
        )
    if any(value <= 0 for values in compositions.values() for value in values.values()):
        raise ValidationRefusal(
            "spatial_zero_composition_unsupported",
            "CLR requires positive fractions; no replacement is implicit",
        )
    centres = tuple(training_coordinates[group] for group in groups)
    distances = tuple(
        tuple(distance_km(left, right) for right in centres) for left in centres
    )
    try:
        import numpy as np
    except ImportError as exc:
        raise ValidationRefusal(
            "spatial_backend_unavailable", "Install the governed LRA extra for NumPy"
        ) from exc
    features = np.asarray(
        [[_basis(d, config.length_scale_km) for d in row] for row in distances],
        dtype=np.float64,
    )
    logs = np.log(
        np.asarray(
            [[compositions[g][t] for t in taxa] for g in groups], dtype=np.float64
        )
    )
    responses = logs - logs.mean(axis=1, keepdims=True)
    feature_mean = features.mean(axis=0)
    clr_mean = responses.mean(axis=0)
    design = features - feature_mean
    centred_response = responses - clr_mean
    augmented = np.vstack((design, np.sqrt(config.ridge_penalty) * np.eye(len(groups))))
    rhs = np.vstack((centred_response, np.zeros((len(groups), len(taxa)))))
    try:
        coefficients, _, rank, singular = np.linalg.lstsq(augmented, rhs, rcond=None)
    except np.linalg.LinAlgError as exc:
        raise ValidationRefusal("spatial_solver_failed", str(exc)) from exc
    if rank != len(groups) or not np.isfinite(coefficients).all():
        raise ValidationRefusal(
            "spatial_solver_unresolved",
            "Augmented fit is numerically rank deficient or nonfinite",
        )
    residual = design @ coefficients - centred_response
    gradient = design.T @ residual + config.ridge_penalty * coefficients
    scale = max(1.0, float(np.linalg.norm(design.T @ centred_response)))
    stationarity = float(np.linalg.norm(gradient)) / scale
    if not isfinite(stationarity) or stationarity > 1e-10:
        raise ValidationRefusal(
            "spatial_solver_unresolved",
            "Ridge stationarity residual exceeds numerical tolerance",
        )
    coefficient_rows = tuple(
        tuple(float(value) for value in row) for row in coefficients
    )
    feature_values = tuple(float(value) for value in feature_mean)
    response_values = tuple(float(value) for value in clr_mean)
    payload = {
        "schema_version": "lra-fitted-spatial-model.v1",
        "configuration": config.as_dict(),
        "fold": fold.as_dict(),
        "predictor_group_ids": groups,
        "training_compositions": compositions,
        "training_coordinates": {g: training_coordinates[g].as_dict() for g in groups},
        "allowed_input_closure": closure,
        "input_lineage": {key: sorted(set(graph[key])) for key in closure},
        "taxa": taxa,
        "feature_mean": feature_values,
        "clr_mean": response_values,
        "coefficients": coefficient_rows,
        "solver": {
            "library": "numpy",
            "version": np.__version__,
            "method": "augmented-least-squares-svd",
            "rank": int(rank),
            "singular_values": [float(value) for value in singular],
            "scaled_stationarity_residual": stationarity,
            "objective": float(
                np.sum(residual**2) + config.ridge_penalty * np.sum(coefficients**2)
            ),
        },
        "uncertainty_status": "point_fit_only",
        "scientific_acceptance": "not_evaluated",
    }
    if training_admission is not None:
        payload["schema_version"] = "lra-fitted-spatial-model.v2"
        payload["training_admission"] = training_admission.as_dict()
        payload["admitted_external_ids"] = tuple(sorted(set(external_ids)))
    # The canonical payload owns fitted values and their complete input identity.
    encoded = canonical_json(payload)
    return FittedSpatialModel(
        fold,
        config,
        groups,
        taxa,
        centres,
        feature_values,
        response_values,
        coefficient_rows,
        encoded,
        manifest_sha256(payload),
        training_admission,
    )
