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
    method: Literal["training_mean", "nearest_site"],
    input_ids: Iterable[str],
    dependency_graph: Mapping[str, Iterable[str]],
    admitted_external_ids: Iterable[str] = (),
    distances_km: Mapping[str, float] | None = None,
) -> BaselinePrediction:
    """Predict compatible cover using training-site mean or nearest-site mean.

    Keys are Fold.train_group_ids, with exactly one governed composition per site
    group. The caller documents upstream aggregation, matching temporal/footprint
    support and supplies unrounded WGS84 distances after coordinate admission.
    Equidistant nearest groups are averaged deterministically. This is a baseline,
    not LOVE at an unobserved site, and has no calibrated uncertainty promise.
    """
    if method not in {"training_mean", "nearest_site"}:
        raise ValidationRefusal("unsupported_baseline", "Unknown baseline method")
    if set(training_compositions) != set(fold.train_group_ids):
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
    if method == "nearest_site" and distances is None:
        raise ValidationRefusal(
            "missing_prediction_geometry",
            "Nearest-site prediction requires admitted site distances",
        )
    selected = tuple(
        key
        for key in compositions
        if method == "training_mean"
        or (distances is not None and distances[key] == nearest)
    )
    values = tuple(
        (taxon, sum(compositions[key][taxon] for key in selected) / len(selected))
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
        }
    )
    return BaselinePrediction(method, values, digest, selected, nearest)
