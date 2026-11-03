"""Five fixed spatial predictions from one nine-owner source closure."""

from __future__ import annotations

import math
from typing import Any

from bijux_pollenomics.analysis.lra_validation.contracts import (
    ValidationRefusal,
    finite_number,
    manifest_sha256,
)
from bijux_pollenomics.analysis.lra_validation.metrics import closed_composition
from bijux_pollenomics.analysis.lra_validation.spatial.hellinger import (
    gaussian_distance_weights,
    hellinger_barycentre,
)
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.forward import forward_deposition

BASELINES = ("training_mean", "nearest_site", "inverse_distance_squared")
METHODS = (*BASELINES, "hellinger_20km", "hellinger_100km")
_REFERENCE_KEYS = {
    "training_record_ids",
    "forbidden_record_ids",
    "selected_fit_ids",
    "regional_owner_id",
    "support_id",
    "target_geometry_id",
}


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _identities(value: Any, count: int, label: str) -> set[str]:
    _require(
        type(value) in (list, tuple)
        and len(value) == count
        and all(type(item) is str and item and item == item.strip() for item in value)
        and len(set(value)) == count,
        f"Unique {count} {label} identities required",
    )
    return set(value)


def _sha(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _source_closure(context: dict[str, Any], taxa: list[str]) -> dict[str, Any]:
    """Admit exact ownership before any numerical forecast, without source I/O."""
    _require(
        type(taxa) is list
        and bool(taxa)
        and all(type(taxon) is str and taxon for taxon in taxa)
        and len(set(taxa)) == len(taxa),
        "Unique complete taxon axis required",
    )
    _require(
        context["kind"] == "outer"
        and context["target"] == context["outer_target"]
        and type(context["context_id"]) is str
        and bool(context["context_id"]),
        "One declared outer target required",
    )
    refs = context["scientific_refs"]
    _require(
        type(refs) is dict and set(refs) == _REFERENCE_KEYS,
        "Exact nine-owner scientific reference channel required",
    )
    training = _identities(refs["training_record_ids"], 9, "training")
    forbidden = _identities(refs["forbidden_record_ids"], 6, "forbidden")
    anchor = context["anchor"]
    _require(
        context["target"] in forbidden
        and not training & forbidden
        and anchor in training
        and refs["regional_owner_id"] == anchor,
        "Held or excluded owner entered scientific training ancestry",
    )
    fold = context["fold"]
    train_groups = _identities(fold["train_group_ids"], 9, "training group")
    test_groups = _identities(fold["test_group_ids"], 1, "test group")
    _require(
        _identities(fold["train_record_ids"], 9, "fold training") == training
        and _identities(fold["test_record_ids"], 1, "fold test") == {context["target"]}
        and not train_groups & test_groups,
        "New nine-to-one fold identity or whole-group exclusion differs",
    )
    predictors = context["predictors"]
    _require(
        type(predictors) is list and len(predictors) == 8,
        "Exactly eight local predictors required",
    )
    owners = _identities([row["record_id"] for row in predictors], 8, "predictor")
    groups = _identities([row["group_id"] for row in predictors], 8, "predictor group")
    _require(
        owners == training - {anchor}, "Predictors differ from allowed local owners"
    )
    selected = []
    for row in predictors:
        _require(
            _identities(row["scientific_parent_ids"], 2, "local fit parent")
            == {row["record_id"], anchor},
            "Held, excluded or foreign quantitative parent entered a local fit",
        )
        _require(
            type(row["covers_by_ring"]) is list
            and len(row["covers_by_ring"]) == 2
            and all(
                type(ring) is list and len(ring) == len(taxa)
                for ring in row["covers_by_ring"]
            )
            and _sha(row["request_sha256"])
            and type(row["selected_attempt_sha256s"]) is list
            and len(row["selected_attempt_sha256s"]) == 2
            and all(_sha(value) for value in row["selected_attempt_sha256s"])
            and type(row["fit_refs"]) is list
            and len(row["fit_refs"]) == 2
            and all(type(value) is str and value for value in row["fit_refs"]),
            "Both saved rings, their source references and full taxon axis required",
        )
        selected.append(row["fit_refs"][1])
    _require(
        _identities(refs["selected_fit_ids"], 8, "selected fit") == set(selected),
        "Selected ring-one fit references differ",
    )
    forward = context["forward"]
    _require(
        forward["outer_fold"] == fold
        and forward["regional_anchor_record_id"] == anchor
        and train_groups == groups | {forward["regional_anchor_group_id"]}
        and forward["regional_anchor_group_id"] not in groups
        and forward["regional_value_source_record_ids"] == [anchor]
        and _identities(
            forward["regional_identity_source_record_ids"],
            9,
            "regional identity source",
        )
        == training
        and forward["regional_identity_policy"]
        == "conservative_all_training_fit_receipts"
        and _identities(forward["predictor_group_ids"], 8, "forward predictor group")
        == groups
        and type(forward["distances_km"]) is dict
        and set(forward["distances_km"]) == groups
        and refs["target_geometry_id"]
        == "experiment-geometry:" + forward["target_geometry_sha256"]
        and _sha(forward["target_geometry_sha256"])
        and forward["forward_inputs"]["taxa"] == taxa
        and type(refs["support_id"]) is str
        and bool(refs["support_id"]),
        "Forward source, geometry, group or taxon ownership differs",
    )
    return {
        key: sorted(value)
        if key in {"training_record_ids", "forbidden_record_ids", "selected_fit_ids"}
        else value
        for key, value in refs.items()
    }


def _baseline_weights(distances: dict[str, Any], method: str) -> dict[str, float]:
    numeric = {
        group: finite_number(value) for group, value in sorted(distances.items())
    }
    nearest = min(numeric.values())
    if nearest < 0:
        raise ValidationRefusal("invalid_distance", "Distances cannot be negative")
    selected = list(numeric)
    if method == "nearest_site" or (
        method == "inverse_distance_squared" and nearest == 0
    ):
        selected = [group for group in numeric if numeric[group] == nearest]
    weights = {
        group: (nearest / numeric[group]) ** 2
        if method == "inverse_distance_squared" and nearest > 0
        else 1.0
        for group in selected
    }
    total = sum(weights.values())
    return {group: weights.get(group, 0.0) / total for group in numeric}


def predict_context(
    context: dict[str, Any], taxa: list[str], scales: list[float]
) -> list[dict[str, Any]]:
    """Retain all five prescribed slots; never fit, select or read outcomes."""
    _require(
        type(scales) is list
        and len(scales) == 2
        and all(
            type(value) in (int, float) and math.isfinite(value) for value in scales
        )
        and scales == [20.0, 100.0],
        "Exactly the prescribed unselected 20 and 100 km scales required",
    )
    refs = _source_closure(context, taxa)
    predictors = sorted(context["predictors"], key=lambda row: row["record_id"])
    compositions = {
        row["group_id"]: dict(zip(taxa, row["covers_by_ring"][1], strict=True))
        for row in predictors
    }
    predictor_sources = [
        {
            key: sorted(row[key]) if key == "scientific_parent_ids" else row[key]
            for key in (
                "record_id",
                "group_id",
                "request_sha256",
                "selected_attempt_sha256s",
                "fit_refs",
                "scientific_parent_ids",
            )
        }
        for row in predictors
    ]
    forward = context["forward"]
    inputs = {
        key: forward["forward_inputs"][key]
        for key in (
            "taxa",
            "regional_deposition",
            "local_k",
            "terrestrial_fraction",
            "ppe",
        )
    }
    results = []
    for method in METHODS:
        scale = (
            None
            if method in BASELINES
            else float(scales[0 if method == "hellinger_20km" else 1])
        )
        profile = (
            "arithmetic-spatial-baseline"
            if scale is None
            else "hellinger-frechet-gaussian-distance"
        )
        scientific = {
            "profile": profile,
            "context_id": context["context_id"],
            "method_id": method,
            "length_scale_km": scale,
            "source_references": refs,
            "training_compositions": compositions,
            "distances_km": forward["distances_km"],
            "forward_inputs": inputs,
            "predictor_sources": predictor_sources,
        }
        row = {
            "context_id": context["context_id"],
            "kind": context["kind"],
            "outer_target": context["outer_target"],
            "target": context["target"],
            "method_id": method,
            "profile": profile,
            "length_scale_km": scale,
            "scientific_input_sha256": manifest_sha256(scientific),
            "scientific_refs": refs,
            "uncertainty_status": "point_model_only",
        }
        try:
            admitted = {
                group: closed_composition(values)
                for group, values in compositions.items()
            }
            if scale is None:
                weights = _baseline_weights(forward["distances_km"], method)
                cover = [
                    sum(
                        admitted[group][taxon] * weight
                        for group, weight in weights.items()
                    )
                    for taxon in taxa
                ]
            else:
                weights = gaussian_distance_weights(
                    forward["distances_km"], length_scale_km=scale
                )
                composition = hellinger_barycentre(admitted, weights)
                cover = [composition[taxon] for taxon in taxa]
            result = forward_deposition(
                cover,
                inputs["regional_deposition"],
                inputs["local_k"],
                inputs["terrestrial_fraction"],
                inputs["ppe"],
            )
        except ValidationRefusal as error:
            results.append(
                {
                    **row,
                    "status": "refused",
                    "reason": error.reason_code,
                    "detail": str(error),
                }
            )
            continue
        except ValidationError as error:
            results.append(
                {
                    **row,
                    "status": "refused",
                    "reason": "forward_model_domain",
                    "native_reason_code": error.reason_code,
                    "detail": str(error),
                }
            )
            continue
        results.append(
            {
                **row,
                "status": "predicted",
                "weights": weights,
                "vegetation_fraction": cover,
                "pollen_fraction": result.pollen_fraction.tolist(),
                "local_deposition": result.local_deposition.tolist(),
                "total_deposition": result.total_deposition.tolist(),
            }
        )
    return results
