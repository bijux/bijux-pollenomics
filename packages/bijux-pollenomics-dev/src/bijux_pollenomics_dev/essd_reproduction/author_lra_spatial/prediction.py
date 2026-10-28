"""Forward a declared Hellinger spatial mean through qualified saved kernels."""

from __future__ import annotations

from typing import Any

from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.spatial.hellinger import (
    gaussian_distance_weights,
    hellinger_barycentre,
)
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.forward import forward_deposition

from .inputs import digest, require

PROFILE = "hellinger-frechet-gaussian-distance"


def predict_context(
    context: dict[str, Any], taxa: list[str], length_scale_km: float
) -> dict[str, Any]:
    """Use only the context's allowed local covers, parameters and geography."""
    training = context["scientific_refs"]["training_record_ids"]
    require(
        context["target"] not in training and context["outer_target"] not in training,
        "A withheld target entered spatial training",
    )
    owners = [row["record_id"] for row in context["predictors"]]
    require(
        len(owners) == len(set(owners))
        and set(owners) <= set(training)
        and context["target"] not in owners
        and context["outer_target"] not in owners,
        "Predictor owners must belong to allowed training ancestry",
    )
    compositions = {
        row["group_id"]: dict(zip(taxa, row["covers_by_ring"][1], strict=True))
        for row in context["predictors"]
    }
    require(
        len(compositions) == len(context["predictors"])
        and set(compositions) == set(context["forward"]["distances_km"]),
        "Spatial groups and saved distances differ",
    )
    inputs = context["forward"]["forward_inputs"]
    scientific_inputs = {
        "profile": PROFILE,
        "context_id": context["context_id"],
        "length_scale_km": length_scale_km,
        "source_references": context["scientific_refs"],
        "training_compositions": compositions,
        "distances_km": context["forward"]["distances_km"],
        "forward_inputs": inputs,
    }
    row = {
        "context_id": context["context_id"],
        "kind": context["kind"],
        "outer_target": context["outer_target"],
        "target": context["target"],
        "length_scale_km": length_scale_km,
        "scientific_input_sha256": digest(scientific_inputs),
        "scientific_refs": context["scientific_refs"],
        "uncertainty_status": "point_model_only",
    }
    try:
        weights = gaussian_distance_weights(
            context["forward"]["distances_km"], length_scale_km=length_scale_km
        )
        composition = hellinger_barycentre(compositions, weights)
        cover = [composition[taxon] for taxon in taxa]
        forward = forward_deposition(
            cover,
            inputs["regional_deposition"],
            inputs["local_k"],
            inputs["terrestrial_fraction"],
            inputs["ppe"],
        )
    except ValidationRefusal as error:
        return {
            **row,
            "status": "refused",
            "reason": error.reason_code,
            "detail": str(error),
        }
    except ValidationError as error:
        return {
            **row,
            "status": "refused",
            "reason": "forward_model_domain",
            "native_reason_code": error.reason_code,
            "detail": str(error),
        }
    return {
        **row,
        "status": "predicted",
        "weights": weights,
        "vegetation_fraction": cover,
        "pollen_fraction": forward.pollen_fraction.tolist(),
        "local_deposition": forward.local_deposition.tolist(),
        "total_deposition": forward.total_deposition.tolist(),
    }
