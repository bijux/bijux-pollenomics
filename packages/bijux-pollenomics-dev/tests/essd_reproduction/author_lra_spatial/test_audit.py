"""Literal complete populations and tamper controls for the independent audit."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from typing import Any

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.audit import (
    audit_predictions,
)


def sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def scientific_identity(context: dict[str, Any], taxa: list[str], scale: float) -> str:
    return sha(
        {
            "profile": "hellinger-frechet-gaussian-distance",
            "context_id": context["context_id"],
            "length_scale_km": scale,
            "source_references": context["scientific_refs"],
            "training_compositions": {
                row["group_id"]: dict(zip(taxa, row["covers_by_ring"][1], strict=True))
                for row in context["predictors"]
            },
            "distances_km": context["forward"]["distances_km"],
            "forward_inputs": context["forward"]["forward_inputs"],
        }
    )


@pytest.fixture(scope="module")
def complete() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """With pure taxon-one covers, the analytic vegetation mean is exactly pure."""
    taxa = [f"taxon-{index:02d}" for index in range(30)]
    groups = {f"site-{index:02d}": f"group-{index:02d}" for index in range(15)}
    support = {
        "support_profile": "same-outer-radius-homogeneous-v1",
        "local_support_radius_m": 1000,
        "taxa": taxa,
        "temporal_matching": {"mode": "fixed"},
        "versions": {"engine": "literal"},
    }
    packet: dict[str, Any] = {
        "schema_version": "author-lra-spatial-inputs.v1",
        "taxa": taxa,
        "groups": groups,
        "support": support,
        "contexts": [],
    }
    candidates = []
    pure = [1.0] + [0.0] * 29
    for outer in groups:
        for target in groups:
            kind = "outer" if outer == target else "inner"
            train = sorted(set(groups) - {outer, target})
            anchor = train[0]
            fold = {
                "fold_id": groups[target],
                "train_record_ids": train,
                "test_record_ids": [target],
                "train_group_ids": sorted(groups[owner] for owner in train),
                "test_group_ids": [groups[target]],
            }
            context_id = "author-spatial:" + sha(
                {"kind": kind, "outer_target": outer, "target": target, "fold": fold}
            )
            predictors, selected_fits = [], []
            for local in train[1:]:
                request = sha({"context": context_id, "local": local})
                attempts = [
                    sha({"request": request, "ring": ring}) for ring in range(2)
                ]
                fits = [
                    "nominal-fit:"
                    + sha({"request": request, "selected_attempt": attempt})
                    for attempt in attempts
                ]
                predictors.append(
                    {
                        "record_id": local,
                        "group_id": groups[local],
                        "covers_by_ring": [pure, pure],
                        "request_sha256": request,
                        "selected_attempt_sha256s": attempts,
                        "fit_refs": fits,
                        "scientific_parent_ids": [local, anchor],
                    }
                )
                selected_fits.append(fits[1])
            inputs: dict[str, Any] = {
                "taxa": taxa,
                "ppe": [2.0, 3.0] + [1.0] * 28,
                "regional_deposition": [3.0, 4.0] + [0.0] * 28,
                "local_k": [[1.0] * 30, [2.0] * 30],
                "terrestrial_fraction": [0.5, 1.0],
                "regional_input_ids": ["saved-regional"],
                "parameter_input_ids": ["saved-parameters"],
                "geometry_input_ids": ["saved-geometry"],
                "temporal_support_id": "saved-time",
                "method_profile": "gpm neutral",
                "engine_build_id": "saved-engine",
            }
            forward = {
                "outer_fold": fold,
                "regional_anchor_record_id": anchor,
                "regional_anchor_group_id": groups[anchor],
                "regional_value_source_record_ids": [anchor],
                "regional_identity_source_record_ids": train,
                "predictor_group_ids": [groups[owner] for owner in train[1:]],
                "distances_km": {groups[owner]: 1.0 for owner in train[1:]},
                "target_geometry_sha256": "a" * 64,
                "full_k": [*inputs["local_k"], [0.1] * 30],
                "full_terrestrial_fraction": [0.5, 1.0, 1.0],
                "forward_inputs": inputs,
            }
            refs = {
                "training_record_ids": train,
                "selected_fit_ids": selected_fits,
                "regional_owner_id": anchor,
                "support_id": "experiment-support:" + sha(support),
                "target_geometry_id": "experiment-geometry:" + "a" * 64,
            }
            context = {
                "context_id": context_id,
                "kind": kind,
                "outer_target": outer,
                "target": target,
                "fold": fold,
                "anchor": anchor,
                "predictors": predictors,
                "forward": forward,
                "scientific_refs": refs,
            }
            packet["contexts"].append(context)
            for scale in (20.0, 100.0):
                # local mass=2*(1*0.5+2*1)=5; regional [3,4] is already PPE weighted.
                candidates.append(
                    {
                        "context_id": context_id,
                        "kind": kind,
                        "outer_target": outer,
                        "target": target,
                        "length_scale_km": scale,
                        "scientific_input_sha256": scientific_identity(
                            context, taxa, scale
                        ),
                        "scientific_refs": deepcopy(refs),
                        "uncertainty_status": "point_model_only",
                        "status": "predicted",
                        "weights": dict.fromkeys(
                            forward["distances_km"], 1 / len(predictors)
                        ),
                        "vegetation_fraction": pure,
                        "pollen_fraction": [2 / 3, 1 / 3] + [0.0] * 28,
                        "local_deposition": [5.0] + [0.0] * 29,
                        "total_deposition": [8.0, 4.0] + [0.0] * 28,
                    }
                )
    return packet, candidates


def test_complete_literal_population_has_450_verified_predictions(
    complete: tuple[dict[str, Any], list[dict[str, Any]]],
) -> None:
    result = audit_predictions(*complete)
    assert result["contexts_verified"] == 225
    assert result["candidate_rows_verified"] == 450
    assert result["statuses"] == {"predicted": 450}


@pytest.mark.parametrize(
    "defect",
    [
        "missing_last",
        "duplicate",
        "wrong_scale",
        "target_training",
        "outer_training",
        "wrong_group",
        "selected_first_ring",
        "global_parent_hash",
        "weights",
        "vector",
        "invented_tiny_support",
        "status",
        "regional_double_ppe",
        "source_refs",
        "identity",
    ],
)
def test_population_source_role_identity_and_numerical_tampering_refuse(
    complete: tuple[dict[str, Any], list[dict[str, Any]]], defect: str
) -> None:
    packet, candidates = deepcopy(complete)
    context, row = packet["contexts"][0], candidates[0]
    if defect == "missing_last":
        candidates.pop()
    elif defect == "duplicate":
        candidates[-1] = candidates[0]
    elif defect == "wrong_scale":
        row["length_scale_km"] = 50.0
    elif defect == "target_training":
        context["predictors"][0]["record_id"] = context["target"]
    elif defect == "outer_training":
        inner = packet["contexts"][1]
        inner["fold"]["train_record_ids"][0] = inner["outer_target"]
    elif defect == "wrong_group":
        context["predictors"][0]["group_id"] = packet["groups"][context["target"]]
    elif defect == "selected_first_ring":
        context["scientific_refs"]["selected_fit_ids"][0] = context["predictors"][0][
            "fit_refs"
        ][0]
    elif defect == "global_parent_hash":
        context["scientific_refs"]["complete_source_sha256"] = "c" * 64
        row["scientific_refs"] = deepcopy(context["scientific_refs"])
        row["scientific_input_sha256"] = scientific_identity(
            context, packet["taxa"], 20.0
        )
    elif defect == "weights":
        row["weights"][next(iter(row["weights"]))] = 0.5
    elif defect == "vector":
        row["vegetation_fraction"] = [0.9, 0.1] + [0.0] * 28
    elif defect == "invented_tiny_support":
        row["vegetation_fraction"] = [1.0, 1e-20] + [0.0] * 28
    elif defect == "status":
        row["status"] = "refused"
    elif defect == "regional_double_ppe":
        row["total_deposition"] = [11.0, 12.0] + [0.0] * 28
        row["pollen_fraction"] = [11 / 23, 12 / 23] + [0.0] * 28
    elif defect == "source_refs":
        row["scientific_refs"]["target_geometry_id"] = "experiment-geometry:" + "d" * 64
    else:
        row["scientific_input_sha256"] = "e" * 64
    with pytest.raises(ValueError):
        audit_predictions(packet, candidates)


def test_weight_underflow_is_an_accounted_refusal_not_a_dropped_candidate(
    complete: tuple[dict[str, Any], list[dict[str, Any]]],
) -> None:
    packet, candidates = deepcopy(complete)
    context = packet["contexts"][0]
    distant = next(iter(context["forward"]["distances_km"]))
    context["forward"]["distances_km"][distant] = 1000.0
    for row in candidates[:2]:
        row["scientific_input_sha256"] = scientific_identity(
            context, packet["taxa"], row["length_scale_km"]
        )
    first = candidates[0]
    for key in (
        "weights",
        "vegetation_fraction",
        "pollen_fraction",
        "local_deposition",
        "total_deposition",
    ):
        del first[key]
    first.update(
        status="refused",
        reason="hellinger_weight_underflow",
        detail="Positive Gaussian relative weight underflow",
    )
    # At scale100 the distant weight is finite. All source compositions remain identical.
    tiny = math.exp(-0.5 * (1000.0**2 - 1) / 100.0**2)
    denominator = len(context["predictors"]) - 1 + tiny
    candidates[1]["weights"] = {
        group: tiny / denominator if group == distant else 1 / denominator
        for group in context["forward"]["distances_km"]
    }
    result = audit_predictions(packet, candidates)
    assert result["statuses"] == {"refused": 1, "predicted": 449}


def test_positive_weight_cannot_be_rounded_away_under_comparison_absolute_tolerance(
    complete: tuple[dict[str, Any], list[dict[str, Any]]],
) -> None:
    packet, candidates = deepcopy(complete)
    context = packet["contexts"][0]
    distant = next(iter(context["forward"]["distances_km"]))
    context["forward"]["distances_km"][distant] = 400.0
    for row in candidates[:2]:
        scale = row["length_scale_km"]
        row["scientific_input_sha256"] = scientific_identity(
            context, packet["taxa"], scale
        )
        relative = math.exp(-0.5 * (400**2 - 1) / scale**2)
        denominator = len(context["predictors"]) - 1 + relative
        row["weights"] = {
            group: relative / denominator if group == distant else 1 / denominator
            for group in context["forward"]["distances_km"]
        }
    assert 0 < candidates[0]["weights"][distant] < 1e-12
    candidates[0]["weights"][distant] = 0.0
    with pytest.raises(ValueError, match="support disagreement"):
        audit_predictions(packet, candidates)


def test_forward_zero_mass_refusal_retains_both_scale_slots_and_native_diagnostic(
    complete: tuple[dict[str, Any], list[dict[str, Any]]],
) -> None:
    packet, candidates = deepcopy(complete)
    context = packet["contexts"][0]
    context["forward"]["forward_inputs"]["local_k"] = [[0.0] * 30] * 2
    context["forward"]["forward_inputs"]["regional_deposition"] = [0.0] * 30
    context["forward"]["full_k"] = [[0.0] * 30] * 3
    for row in candidates[:2]:
        row["scientific_input_sha256"] = scientific_identity(
            context, packet["taxa"], row["length_scale_km"]
        )
        for key in (
            "weights",
            "vegetation_fraction",
            "pollen_fraction",
            "local_deposition",
            "total_deposition",
        ):
            del row[key]
        row.update(
            status="refused",
            reason="forward_model_domain",
            native_reason_code="invalid_input",
            detail="Saved forward coefficients give zero mass",
        )
    result = audit_predictions(packet, candidates)
    assert result["statuses"] == {"refused": 2, "predicted": 448}
