"""Literal synthetic thinning packets, independent of the scientific producers."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any


def sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def synthetic() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    taxa = [f"taxon-{i:02d}" for i in range(30)]
    groups = {f"site-{i:02d}": f"group-{i:02d}" for i in range(15)}
    all_owners = sorted(groups)
    selected = all_owners[:10]
    matrix = {a: dict.fromkeys(all_owners, 0.0) for a in all_owners}
    support = {"profile": "literal"}
    packet: dict[str, Any] = {
        "schema_version": "author-lra-thinning-inputs.v1",
        "taxa": taxa,
        "groups": groups,
        "support": support,
        "contexts": [],
        "geometry_refs": {},
        "geometries": {},
        "observation_refs": [],
        "retained_reference_predictions": [],
    }
    for owner in all_owners:
        packet["geometries"][owner] = {"latitude": 50.0, "longitude": 0.0}
        packet["geometry_refs"][owner] = {
            "path": owner + "-geometry.json",
            "bytes": 10,
            "sha256": sha(owner),
        }
    steps = [
        {
            "step": i + 1,
            "record_id": owner,
            "criterion": "minimum_total_distance"
            if i == 0
            else "maximum_nearest_selected_distance",
            "value_m": 0.0,
            "candidate_values_m": dict.fromkeys(
                all_owners if i == 0 else all_owners[i:], 0.0
            ),
        }
        for i, owner in enumerate(selected)
    ]
    packet["cohort"] = {
        "distance_model": "nominal_wgs84_inverse",
        "tie_policy": "exact_metric_then_lexicographic_record_id",
        "coordinates": deepcopy(packet["geometries"]),
        "distance_matrix_m": matrix,
        "selection_order": selected,
        "selected": selected,
        "excluded": all_owners[10:],
        "steps": steps,
        "nearest_selected_distance_m": dict.fromkeys(all_owners, 0.0),
        "coverage_m": 0.0,
        "min_separation_m": 0.0,
    }
    protocol = {
        "schema_version": "author-lra-geographic-thinning.v1",
        "cohort": {
            "size": 10,
            "expected_selection_order": selected,
            "expected_distinct_pairs": 17,
        },
        "models": {
            "baselines": ["training_mean", "nearest_site", "inverse_distance_squared"],
            "hellinger_scales_km": [20.0, 100.0],
            "new_population": {
                "outer_folds": 10,
                "training_owners_per_fold": 9,
                "local_predictors_per_fold": 8,
                "new_prediction_slots": 50,
            },
        },
        "comparison_tolerances": {"absolute": 1e-12, "relative": 1e-10},
    }
    predictions = []
    pure = [1.0] + [0.0] * 29
    methods = (
        "training_mean",
        "nearest_site",
        "inverse_distance_squared",
        "hellinger_20km",
        "hellinger_100km",
    )
    for target in selected:
        train = sorted(set(selected) - {target})
        anchor = train[0]
        locals_ = sorted(set(train) - {anchor})
        fold = {
            "fold_id": groups[target],
            "train_record_ids": train,
            "test_record_ids": [target],
            "train_group_ids": sorted(groups[o] for o in train),
            "test_group_ids": [groups[target]],
        }
        predictors: list[dict[str, Any]] = []
        for local in locals_:
            request = sha([local, anchor])
            attempts = [sha([local, anchor, ring]) for ring in range(2)]
            fits = [
                "nominal-fit:" + sha({"request": request, "selected_attempt": a})
                for a in attempts
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
        numeric = {
            "taxa": taxa,
            "ppe": [2.0, 3.0] + [1.0] * 28,
            "regional_deposition": [3.0, 4.0] + [0.0] * 28,
            "local_k": [[1.0] * 30, [2.0] * 30],
            "terrestrial_fraction": [0.5, 1.0],
        }
        forward = {
            "outer_fold": fold,
            "regional_identity_source_record_ids": train,
            "regional_value_source_record_ids": [anchor],
            "regional_anchor_record_id": anchor,
            "target_geometry_sha256": sha(target),
            "distances_km": {groups[o]: 0.0 for o in locals_},
            "forward_inputs": numeric,
        }
        refs: dict[str, Any] = {
            "training_record_ids": train,
            "forbidden_record_ids": sorted(set(all_owners) - set(train)),
            "selected_fit_ids": [p["fit_refs"][1] for p in predictors],
            "regional_owner_id": anchor,
            "support_id": "experiment-support:" + sha(support),
            "target_geometry_id": "experiment-geometry:" + sha(target),
        }
        cid = "author-thinning:" + sha(
            {
                "fold": fold,
                "selected": selected,
                "forbidden": refs["forbidden_record_ids"],
            }
        )
        context = {
            "context_id": cid,
            "kind": "outer",
            "outer_target": target,
            "target": target,
            "fold": fold,
            "anchor": anchor,
            "predictors": predictors,
            "forward": forward,
            "scientific_refs": refs,
        }
        packet["contexts"].append(context)
        packet["observation_refs"].append(
            {
                "record_id": target,
                "path": target + "-raw.json",
                "bytes": 20,
                "sha256": sha([target, "raw"]),
            }
        )
        for method in methods:
            scale = (
                20.0
                if method == "hellinger_20km"
                else 100.0
                if method == "hellinger_100km"
                else None
            )
            profile = (
                "arithmetic-spatial-baseline"
                if scale is None
                else "hellinger-frechet-gaussian-distance"
            )
            normalized_refs = {
                **refs,
                "selected_fit_ids": sorted(refs["selected_fit_ids"]),
            }
            source_rows = [
                {
                    **{
                        k: p[k]
                        for k in (
                            "record_id",
                            "group_id",
                            "request_sha256",
                            "selected_attempt_sha256s",
                            "fit_refs",
                        )
                    },
                    "scientific_parent_ids": sorted(p["scientific_parent_ids"]),
                }
                for p in predictors
            ]
            literal = {
                "profile": profile,
                "context_id": cid,
                "method_id": method,
                "length_scale_km": scale,
                "source_references": normalized_refs,
                "training_compositions": {
                    groups[o]: dict(zip(taxa, pure, strict=True)) for o in locals_
                },
                "distances_km": forward["distances_km"],
                "forward_inputs": numeric,
                "predictor_sources": source_rows,
            }
            row = {
                "context_id": cid,
                "kind": "outer",
                "outer_target": target,
                "target": target,
                "method_id": method,
                "profile": profile,
                "length_scale_km": scale,
                "scientific_input_sha256": sha(literal),
                "scientific_refs": normalized_refs,
                "uncertainty_status": "point_model_only",
                "status": "predicted",
                "weights": dict.fromkeys(forward["distances_km"], 0.125),
                "vegetation_fraction": pure,
                "local_deposition": [5.0] + [0.0] * 29,
                "total_deposition": [8.0, 4.0] + [0.0] * 28,
                "pollen_fraction": [2 / 3, 1 / 3] + [0.0] * 28,
            }
            predictions.append(row)
            if method != "hellinger_100km":
                packet["retained_reference_predictions"].append(
                    {
                        "target": target,
                        "method_id": method,
                        "pollen_fraction": row["pollen_fraction"],
                    }
                )
    return packet, predictions, protocol
