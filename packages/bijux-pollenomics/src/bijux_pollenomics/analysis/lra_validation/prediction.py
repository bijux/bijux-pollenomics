"""Train-only spatial prediction followed by an injected numerical pollen engine.

This host boundary does not implement a dispersal or inversion equation. It keeps
held-out outcomes outside the predictor and binds the numerical call to admitted
source, parameter, geometry and time identities before scores can be computed.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Literal, Protocol

from .baselines import predict_spatial_baseline
from .contracts import (
    Fold,
    ValidationRefusal,
    canonical_json,
    finite_number,
    identity_values,
    manifest_sha256,
    required_identity,
)
from .metrics import closed_composition
from .splits import assert_allowed_inputs


class ForwardOutput(Protocol):
    """Minimal read-only numerical output consumed from the optional LRA engine."""

    @property
    def pollen_fraction(self) -> Iterable[float]:
        """Return predicted pollen fractions in the declared taxon order."""
        ...

    @property
    def method_profile(self) -> str:
        """Identify the actual numerical observation-model profile."""
        ...


class ForwardModel(Protocol):
    """An engine callable; local/regional deposition calculations remain in engine."""

    def __call__(
        self,
        local_cover: tuple[float, ...],
        regional_deposition: tuple[float, ...],
        local_k: tuple[tuple[float, ...], ...],
        terrestrial_fraction: tuple[float, ...],
        ppe: tuple[float, ...],
    ) -> ForwardOutput:
        """Map spatially predicted cover and declared deposition inputs to pollen."""
        ...


@dataclass(frozen=True)
class ForwardInputs:
    """Governed homogeneous-local forward context with no held-out pollen counts.

    ``regional_deposition`` is already PPE-weighted pollen deposition on the same
    numerical scale as K*cover*PPE*terrestrial_fraction. It is not regional pollen
    composition. The engine validates its numerical domains. Callers must admit
    kernel/geometry/time support explicitly; a named reference is not its review.
    """

    taxa: tuple[str, ...]
    regional_deposition: tuple[float, ...]
    local_k: tuple[tuple[float, ...], ...]
    terrestrial_fraction: tuple[float, ...]
    ppe: tuple[float, ...]
    regional_input_ids: tuple[str, ...]
    parameter_input_ids: tuple[str, ...]
    geometry_input_ids: tuple[str, ...]
    temporal_support_id: str
    method_profile: str
    engine_build_id: str

    def __post_init__(self) -> None:
        taxa = identity_values(self.taxa)
        if not taxa or len(set(taxa)) != len(taxa):
            raise ValidationRefusal(
                "invalid_taxon_identity", "Forward taxa must be nonempty and unique"
            )
        object.__setattr__(self, "taxa", taxa)
        for name in ("regional_input_ids", "parameter_input_ids", "geometry_input_ids"):
            values = tuple(sorted(set(identity_values(getattr(self, name)))))
            if not values:
                raise ValidationRefusal(
                    "missing_forward_lineage",
                    f"{name} must identify the governed numerical inputs",
                )
            object.__setattr__(self, name, values)
        for name in ("temporal_support_id", "method_profile", "engine_build_id"):
            required_identity(getattr(self, name))
        for name in ("regional_deposition", "terrestrial_fraction", "ppe"):
            object.__setattr__(
                self, name, tuple(finite_number(value) for value in getattr(self, name))
            )
        object.__setattr__(
            self,
            "local_k",
            tuple(
                tuple(finite_number(value) for value in ring) for ring in self.local_k
            ),
        )

    def as_dict(self) -> dict[str, object]:
        """Persist exact numerical inputs separately from scientific admission claims."""
        return {field: getattr(self, field) for field in self.__dataclass_fields__}


@dataclass(frozen=True)
class HeldoutPrediction:
    """Immutable paired target predictions frozen before any outcome is supplied."""

    target_group_id: str
    vegetation_fraction: tuple[tuple[str, float], ...]
    pollen_fraction: tuple[tuple[str, float], ...]
    spatial_method: str
    forward_method_profile: str
    input_manifest_json: str
    prediction_manifest_sha256: str
    uncertainty_status: str = "deterministic_point_prediction_no_predictive_intervals"


def predict_withheld_site(
    fold: Fold,
    target_group_id: str,
    training_compositions: Mapping[str, Mapping[str, float]],
    context: ForwardInputs,
    forward_model: ForwardModel,
    *,
    spatial_method: Literal[
        "training_mean", "nearest_site", "inverse_distance_squared"
    ],
    training_input_ids: Iterable[str],
    dependency_graph: Mapping[str, Iterable[str]],
    admitted_external_ids: Iterable[str],
    distances_km: Mapping[str, float] | None = None,
) -> HeldoutPrediction:
    """Freeze p10 vegetation and pollen predictions using admitted training data.

    Baseline compositions must be one reconstruction per training site group.
    All preprocessing/model fitting is upstream and included in the dependency
    graph. Outcome-free target geometry/time support need explicit external IDs;
    external admission can never override withheld ancestry. No target observation
    or total pollen count is accepted by this prediction interface.

    Homogeneous local cover is an explicit baseline assumption. There is no LOVE
    inversion at p10 and no uncertainty interval without propagated draws. Kernel
    and PPE numerical failures propagate as refusals; no fallback model is used.
    """
    if target_group_id not in fold.test_group_ids:
        raise ValidationRefusal(
            "target_not_held_out", "Prediction target must be a held-out site group"
        )
    graph = {key: identity_values(values) for key, values in dependency_graph.items()}
    training_ids = identity_values(training_input_ids)
    externals = identity_values(admitted_external_ids)
    forward_ids = (
        *context.regional_input_ids,
        *context.parameter_input_ids,
        *context.geometry_input_ids,
        context.temporal_support_id,
    )
    closure = assert_allowed_inputs(
        fold, (*training_ids, *forward_ids), graph, admitted_external_ids=externals
    )
    baseline = predict_spatial_baseline(
        fold,
        training_compositions,
        method=spatial_method,
        input_ids=training_ids,
        dependency_graph=graph,
        admitted_external_ids=externals,
        distances_km=distances_km,
    )
    vegetation = dict(baseline.fractions)
    if set(vegetation) != set(context.taxa):
        raise ValidationRefusal(
            "taxon_denominator_mismatch",
            "Spatial prediction and forward model taxa must match exactly",
        )
    try:
        predicted = forward_model(
            tuple(vegetation[taxon] for taxon in context.taxa),
            context.regional_deposition,
            context.local_k,
            context.terrestrial_fraction,
            context.ppe,
        )
    except ValueError as exc:
        raise ValidationRefusal("forward_model_refused", str(exc)) from exc
    if predicted.method_profile != context.method_profile:
        raise ValidationRefusal(
            "forward_profile_mismatch",
            "Actual engine method differs from the frozen requested profile",
        )
    values = tuple(predicted.pollen_fraction)
    if len(values) != len(context.taxa):
        raise ValidationRefusal(
            "forward_taxon_dimension_mismatch",
            "Engine output must preserve the exact taxon dimension",
        )
    pollen = closed_composition(dict(zip(context.taxa, values, strict=True)))
    manifest = {
        "schema_version": "lra-heldout-prediction.v1",
        "experiment": "all_target_pollen_withheld",
        "target_group_id": target_group_id,
        "fold": fold.as_dict(),
        "spatial_method": baseline.method,
        "spatial_input_sha256": baseline.training_manifest_sha256,
        "nearest_training_distance_km": baseline.nearest_training_distance_km,
        "forward_inputs": context.as_dict(),
        "allowed_input_closure": closure,
        "input_lineage": {key: sorted(set(graph[key])) for key in closure},
        "vegetation_fraction": vegetation,
        "pollen_fraction": pollen,
        "uncertainty_status": "deterministic_point_prediction_no_predictive_intervals",
        "scientific_acceptance": "not_evaluated_by_prediction",
    }
    return HeldoutPrediction(
        target_group_id,
        tuple(sorted(vegetation.items())),
        tuple(sorted(pollen.items())),
        baseline.method,
        context.method_profile,
        canonical_json(manifest),
        manifest_sha256(manifest),
    )
