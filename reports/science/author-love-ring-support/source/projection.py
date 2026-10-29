"""Bind saved ring-zero starts and conditional 500 m prediction-value projections."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def manifest_predictor_lineage(
    manifest: dict[str, Any], geometry: dict[str, Any]
) -> bool:
    """Match the maintained sorted complete eligible-predictor serialization."""
    named: list[str] = manifest["predictor_group_ids"]
    original: list[str] = geometry["predictor_group_ids"]
    return len(named) == len(set(named)) == len(original) and named == sorted(original)


def saved_population(
    records: dict[str, Any], attempts: dict[tuple[str, int], list[dict[str, Any]]]
) -> dict[str, Any]:
    """Read exact admitted minima, preserving every original accepted/refused start."""
    require(
        len(records) == 39 and len(attempts) == 78, "Complete admitted39/78 population"
    )
    accepted = refused = equal = 0
    rows = {}
    for key, record in records.items():
        population = attempts[(key, 0)]
        require(
            len(population) == 32
            and len({row["start_id"] for row in population}) == 32,
            "Original32 ring-zero starts",
        )
        require(
            all(
                row["request_sha256"] == key
                and row["ring_index"] == 0
                and row["outer_m"] == 500
                and type(row["accepted"]) is bool
                for row in population
            ),
            "Original ring-zero identities",
        )
        selected, outer = record["selections"]
        eligible = [row for row in population if row["accepted"]]
        require(
            bool(eligible) and selected is not None and outer is not None,
            "Actual nominal admitted selected rings",
        )
        minimum = min(eligible, key=lambda row: (row["result"]["fun"], row["start_id"]))
        require(
            selected["selected_attempt_sha256"] == digest(minimum)
            and selected["selected_start_id"] == minimum["start_id"]
            and selected["selected_objective"] == minimum["result"]["fun"],
            "Exact original selected ring-zero minimum",
        )
        same = selected["composition"] == outer["composition"]
        accepted += len(eligible)
        refused += 32 - len(eligible)
        equal += same
        rows[key] = {
            "attempts_sha256": digest(population),
            "selection_sha256": digest(selected),
            "accepted": len(eligible),
            "refused": 32 - len(eligible),
            "ring0_equals_ring1_cover": same,
        }
    return {
        "requests": 39,
        "ring0_attempts": 1248,
        "accepted": accepted,
        "refused": refused,
        "equal_selected_covers": equal,
        "records": rows,
        "new_optimizer_calls": 0,
    }


def ring_arguments(
    eq: dict[str, Any],
    libraries: dict[str, Any],
    original: dict[str, Any],
    support: dict[str, Any],
    record: dict[str, Any],
    attempts: list[dict[str, Any]],
    binding: Any,
) -> dict[str, Any]:
    """Prove deterministic call congruence; do not evaluate kernels or objectives."""
    bridge = eq["request_bridge"](original, support)
    configuration = eq["configuration_bridge"](binding, original, support)
    counts = np.asarray(original["local"]["samples"][0]["counts"], dtype=float)
    observed = counts / counts.sum()
    regional = np.asarray(record["regional_cover"], dtype=float)
    starts = libraries["starts"]["_starts"](observed, regional)
    require(len(starts) == len(attempts) == 32, "Complete original starts")
    for row, (name, start) in zip(attempts, starts, strict=True):
        require(
            row["start_id"] == name and np.array_equal(row["start"], start),
            "Actual saved start identity",
        )
    require(
        bool(np.isfinite(regional).all())
        and regional.shape == (30,)
        and bool(np.all(regional >= 0))
        and abs(float(regional.sum()) - 1) <= 30 * 0.000005 + 1e-12,
        "Original rounded regional fractions",
    )
    # The pinned _new_attempts always receives explicit ring_index0. Its full
    # radii, normalized calK parameters, raw regional vector, PPE, observed
    # fraction, seed and starts are identical; max_ring is not an argument to
    # tf/Jacobian or those fixed-ring expressions. No invented kernel is used.
    return {
        **bridge,
        "configuration": configuration,
        "proof_kind": "source-bound deterministic argument congruence",
        "ring0_objective_arguments_equal": True,
        "ring0_jacobian_arguments_equal": True,
        "fixed_starts_equal": True,
        "raw_regional_sha256": digest(record["regional_cover"]),
        "kernel_calls": 0,
        "objective_calls": 0,
        "optimizer_calls": 0,
    }


def prediction_projection(
    slots: list[dict[str, Any]],
    contexts: list[dict[str, Any]],
    groups: dict[str, str],
    records: dict[str, Any],
    pair_hashes: dict[tuple[str, str], str],
    aliases: dict[str, str],
    geometries: dict[str, Any],
    taxa: list[str],
    baselines: tuple[str, ...],
    ppe: list[float],
    temporal_matching: dict[str, Any],
) -> dict[str, Any]:
    """Use original numerical zero rows plus equal covers, without relabelling manifests."""
    contexts_by = {
        (row["kind"], row["outer"].test_record_ids[0], row["target"]): row
        for row in contexts
    }
    require(
        len(contexts_by) == 225 and len(slots) == 675,
        "Complete225contexts/675nominal slots",
    )
    seen = set()
    projections = []
    for slot in slots:
        key = (slot["kind"], slot["outer_target"], slot["target"], slot["baseline"])
        require(
            key not in seen
            and slot["baseline"] in baselines
            and slot["method"] == "gpm neutral"
            and slot["status"] == "predicted",
            "Exact current nominal predicted population",
        )
        seen.add(key)
        context = contexts_by[key[:3]]
        require(
            digest(slot["fold"]) == digest(context["fold"].as_dict()),
            "Original outer/inner fold identity",
        )
        anchor = context["anchor"]
        request_ids = [pair_hashes[(name, anchor)] for name in context["predictors"]]
        require(
            all(
                records[name]["selections"][0]["composition"]
                == records[name]["selections"][1]["composition"]
                for name in request_ids
            ),
            "Actual selected ring-zero and outer covers differ",
        )
        geo = slot["geometry"]
        source = geometries[slot["target"]]["data"]
        geometry_sha = geometries[slot["target"]]["sha256"]
        kernels = np.asarray(geo["full_k"], dtype=float)
        fractions = np.asarray(geo["full_terrestrial_fraction"], dtype=float)
        inputs = geo["forward_inputs"]
        prediction = slot["prediction"]
        require(
            kernels.shape == (4, 30)
            and bool(np.isfinite(kernels).all())
            and bool(np.all(kernels >= 0))
            and bool(np.all(kernels[1] == 0))
            and fractions.shape == (4,)
            and bool(np.all(fractions == 1)),
            "Actual saved moved kernel row must be exactly zero",
        )
        require(
            geo["declared_target_forward_rings"] == source["forward_rings"]
            and geo["declared_target_inversion_rings"] == source["inversion_rings"]
            and geo["target_geometry_sha256"] == geometry_sha
            and geo["ring_bounds_m"]
            == [[row["inner_m"], row["outer_m"]] for row in source["forward_rings"]]
            and geo["local_support_radius_m"] == 1000
            and geo["regional_anchor_record_id"] == anchor
            and digest(geo["outer_fold"]) == digest(context["fold"].as_dict())
            and geo["predictor_group_ids"]
            == [groups[name] for name in context["predictors"]],
            "Original target geometry/anchor/predictor/time support",
        )
        require(
            inputs["taxa"] == taxa
            and inputs["ppe"] == ppe
            and inputs["geometry_input_ids"] == ["experiment-geometry:" + geometry_sha]
            and inputs["temporal_support_id"]
            == "experiment-time:"
            + digest(
                {"metadata": source["sample_metadata"], "matching": temporal_matching}
            )
            and inputs["local_k"] == geo["full_k"][:2]
            and inputs["terrestrial_fraction"] == geo["full_terrestrial_fraction"][:2]
            and all(
                records[name]["regional_cover"] == geo["regional_cover"]
                for name in request_ids
            ),
            "Same full source forward arguments and raw background",
        )
        manifest = prediction["prediction_manifest"]
        require(
            digest(manifest) == prediction["prediction_manifest_sha256"]
            and digest(manifest["fold"]) == digest(slot["fold"])
            and manifest["spatial_method"] == slot["baseline"]
            and manifest_predictor_lineage(manifest, geo)
            and manifest["forward_inputs"] == inputs
            and manifest["pollen_fraction"] == prediction["pollen_fraction"]
            and manifest["vegetation_fraction"] == prediction["vegetation_fraction"],
            "Original frozen prediction and manifest identity",
        )
        # Full geometry and calK call inputs remain identical. Moving the saved
        # zero row between local and regional sums contributes exactly zero.
        # Spatial weights see identical geometry and compositions, so this is
        # a value projection, not execution of a new 500 m prediction manifest.
        projected = {
            "kind": slot["kind"],
            "outer_target": slot["outer_target"],
            "target": slot["target"],
            "baseline": slot["baseline"],
            "original_slot_sha256": digest(slot),
            "original_prediction_manifest_sha256": prediction[
                "prediction_manifest_sha256"
            ],
            "original_pollen_fraction_sha256": digest(prediction["pollen_fraction"]),
            "support_request_sha256s": [aliases[name] for name in request_ids],
            "local_ring_count": 1,
            "local_support_radius_m": 500,
            "probability_values_equal_by_source_projection": True,
            "new_prediction_manifest_executed": False,
        }
        projections.append(
            {**projected, "support_projection_sha256": digest(projected)}
        )
    require(
        len(seen) == 675 and sum(row["kind"] == "outer" for row in projections) == 45,
        "All45outer/630inner nominal baseline slots",
    )
    return {
        "slots": projections,
        "nominal_slots": 675,
        "outer_slots": 45,
        "inner_slots": 630,
        "new_forward_calls": 0,
        "new_score_calls": 0,
        "new_prediction_manifests_executed": False,
    }
