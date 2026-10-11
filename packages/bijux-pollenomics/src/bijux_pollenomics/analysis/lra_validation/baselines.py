"""Explicit spatial baselines over one admitted composition per training site."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Literal

from .contracts import (
    Fold,
    ValidationRefusal,
    finite_number,
    identity_values,
    manifest_sha256,
)
from .metrics import closed_composition
from .splits import assert_allowed_inputs


@dataclass(frozen=True)
class BaselinePrediction:
    """A baseline estimate, with its exact train-only numerical input identity."""

    method: str
    fractions: tuple[tuple[str, float], ...]
    training_manifest_sha256: str
    selected_group_ids: tuple[str, ...]
    nearest_training_distance_km: float | None


def predict_spatial_baseline(
    fold: Fold,
    training_compositions: Mapping[str, Mapping[str, float]],
    *,
    method: Literal["training_mean", "nearest_site", "inverse_distance_squared"],
    input_ids: Iterable[str],
    dependency_graph: Mapping[str, Iterable[str]],
    admitted_external_ids: Iterable[str] = (),
    distances_km: Mapping[str, float] | None = None,
    predictor_group_ids: Iterable[str] | None = None,
) -> BaselinePrediction:
    """Predict compatible cover using explicitly named training-only baselines.

    Keys are all Fold.train_group_ids by default, or an explicit predictor subset.
    Every outer training record remains required in the lineage, including a
    regional anchor that contributes no local composition. There is one composition per site
    group. The caller documents upstream aggregation, matching temporal/footprint
    support and supplies unrounded WGS84 distances after coordinate admission.
    Equidistant nearest groups are averaged deterministically. Inverse-distance-
    squared weights use all groups unless exact zero-distance ties exist; those
    colocated groups alone are averaged. Distances are not rounded or fitted here.
    The fixed exponent is a declared engineering profile, not a tuned optimum.
    Weights are scaled by the nearest positive distance to avoid overflow. This is a baseline,
    not LOVE at an unobserved site, and has no calibrated uncertainty promise.
    """
    if method not in {"training_mean", "nearest_site", "inverse_distance_squared"}:
        raise ValidationRefusal("unsupported_baseline", "Unknown baseline method")
    predictor_groups = (
        fold.train_group_ids
        if predictor_group_ids is None
        else identity_values(predictor_group_ids)
    )
    if (
        not predictor_groups
        or len(set(predictor_groups)) != len(predictor_groups)
        or not set(predictor_groups).issubset(fold.train_group_ids)
    ):
        raise ValidationRefusal(
            "invalid_predictor_groups",
            "Predictors must be a nonempty unique subset of outer training groups",
        )
    if set(training_compositions) != set(predictor_groups):
        raise ValidationRefusal(
            "baseline_group_mismatch",
            "Require exactly one composition per training site group",
        )
    graph = {key: identity_values(values) for key, values in dependency_graph.items()}
    closure = assert_allowed_inputs(
        fold, input_ids, graph, admitted_external_ids=admitted_external_ids
    )
    if not set(fold.train_record_ids).issubset(closure):
        raise ValidationRefusal(
            "incomplete_training_lineage",
            "Baseline must declare all contributing training records",
        )
    compositions = {
        key: closed_composition(values)
        for key, values in sorted(training_compositions.items())
    }
    taxa = set(next(iter(compositions.values())))
    if any(set(values) != taxa for values in compositions.values()):
        raise ValidationRefusal(
            "taxon_denominator_mismatch",
            "All baseline sites require identical taxon denominators",
        )
    distances = None
    nearest = None
    if distances_km is not None:
        if set(distances_km) != set(compositions):
            raise ValidationRefusal(
                "baseline_distance_mismatch",
                "Distances must identify each training site group",
            )
        distances = {
            key: finite_number(value) for key, value in sorted(distances_km.items())
        }
        if any(value < 0 for value in distances.values()):
            raise ValidationRefusal("invalid_distance", "Distances cannot be negative")
        nearest = min(distances.values())
    if method != "training_mean" and distances is None:
        raise ValidationRefusal(
            "missing_prediction_geometry",
            "Distance-based prediction requires admitted site distances",
        )
    selected = tuple(
        key
        for key in compositions
        if method == "training_mean"
        or (method == "inverse_distance_squared" and nearest != 0)
        or (distances is not None and distances[key] == nearest)
    )
    values = tuple(
        (taxon, sum(compositions[key][taxon] for key in selected) / len(selected))
        for taxon in sorted(taxa)
    )
    if method == "inverse_distance_squared" and nearest != 0:
        assert distances is not None and nearest is not None
        weights = {key: (nearest / distances[key]) ** 2 for key in selected}
        total_weight = sum(weights.values())
        values = tuple(
            (
                taxon,
                sum(compositions[key][taxon] * weights[key] for key in selected)
                / total_weight,
            )
            for taxon in sorted(taxa)
        )
    digest = manifest_sha256(
        {
            "schema_version": "lra-spatial-baseline-inputs.v1",
            "method": method,
            "fold": fold.as_dict(),
            "training_compositions": compositions,
            "allowed_input_closure": closure,
            "input_lineage": {key: sorted(set(graph[key])) for key in closure},
            "distances_km": distances,
            **(
                {"predictor_group_ids": sorted(predictor_groups)}
                if predictor_group_ids is not None
                else {}
            ),
        }
    )
    return BaselinePrediction(method, values, digest, selected, nearest)
