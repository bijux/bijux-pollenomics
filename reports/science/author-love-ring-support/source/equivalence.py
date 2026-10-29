"""Exact ring-zero request projection and conditional homogeneous forward identity."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from typing import Any

import numpy as np


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def request_bridge(original: dict[str, Any], support: dict[str, Any]) -> dict[str, Any]:
    expected = deepcopy(original)
    if (
        original["configuration"]["love"]["max_ring"] != 2
        or support["configuration"]["love"]["max_ring"] != 1
    ):
        raise ValueError("Only two-to-one cumulative local ring projection supported")
    expected["configuration"]["love"]["max_ring"] = 1
    if expected != support or digest(original) == digest(support):
        raise ValueError("Changed whole request must differ only at love.max_ring")
    taxa, parameters, rings = (
        original["taxa"],
        original["parameters"],
        original["rings"],
    )
    if (
        len(taxa) != 30
        or len(set(taxa)) != 30
        or [r["taxon"] for r in parameters] != taxa
        or len(rings) != 3
    ):
        raise ValueError("Same complete thirty-axis and three inverse rows required")
    config = original["configuration"]
    if (
        original["method_profile"] != "ring-taxon-preserving"
        or original["operation"] != "lra"
        or config["seed"] != 7
    ):
        raise ValueError("Exact original paired profile and seed required")
    love = config["love"]
    if (
        any(
            config[role]["distance_weighting"] != "gpm neutral"
            or config[role]["stochastic"] is not False
            for role in ("reveals", "love")
        )
        or love["optimized_profile"] != "ring-taxon-preserving"
        or love["optimizer_backend"] != "scipy.slsqp-simplex-uniform"
        or (
            love["repeats"],
            love["optimizer_iterations"],
            love["optimizer_max_evaluations"],
            love["optimizer_tolerance"],
        )
        != (1, 300, 16000, 1e-8)
    ):
        raise ValueError(
            "Pinned deterministic nominal GPM fixed-start profile required"
        )
    for row in parameters:
        if (
            any(
                type(row[k]) not in (float, int) or not math.isfinite(row[k])
                for k in ("ppe", "ppe_sd", "fallspeed_m_s")
            )
            or row["ppe"] <= 0
            or row["ppe_sd"] < 0
            or not 0.01 <= row["fallspeed_m_s"] <= 0.15
        ):
            raise ValueError("Unchanged finite native parameter domain required")
    for role in ("local", "regional"):
        samples = original[role]["samples"]
        if (
            len(samples) != 1
            or len(samples[0]["counts"]) != 30
            or any(type(x) is not int or x < 0 for x in samples[0]["counts"])
            or sum(samples[0]["counts"]) <= 0
        ):
            raise ValueError("Same explicit integer training sample required")
    if (
        rings[0]["outer_m"] != 500
        or rings[1]["inner_m"] != 500
        or rings[1]["outer_m"] != 1000
        or rings[2]["inner_m"] != 1000
        or rings[2]["outer_m"] != 10000
    ):
        raise ValueError("Original complete inverse ring/background support required")
    return {
        "original_request_sha256": digest(original),
        "support_request_sha256": digest(support),
        "changed_field": "configuration.love.max_ring",
        "original_max_ring": 2,
        "support_max_ring": 1,
        "ring_index": 0,
        "ring_outer_m": 500,
        "request_projection_exact": True,
        "native_reuse_admitted": False,
    }


def configuration_bridge(
    binding: Any, original: dict[str, Any], support: dict[str, Any]
) -> dict[str, Any]:
    import pandas as pd

    from bijux_pollenomics.analysis.lra.execution.adapter import _configuration
    from bijux_pollenomics_lra.workflows.local import _prepare_love_params

    request_bridge(original, support)
    before, after = _configuration(binding, original), _configuration(binding, support)
    if before[0].as_dict() != after[0].as_dict():
        raise ValueError("Regional source configuration changed")
    old, new = before[1].as_dict(), after[1].as_dict()
    if old.pop("max_ring") != 2 or new.pop("max_ring") != 1 or old != new:
        raise ValueError("LOVE numerical configuration changed beyond local ring limit")
    if (
        before[2].seed != after[2].seed
        or before[2].couple_regional_draws != after[2].couple_regional_draws
    ):
        raise ValueError("Original paired seed/coupling changed")
    rows = pd.DataFrame(
        [
            {
                "Taxon": r["taxon"],
                "fallspeed": r["fallspeed_m_s"],
                "ppe": r["ppe"],
                "ppe.error": r["ppe_sd"],
            }
            for r in original["parameters"]
        ]
    )
    first = _prepare_love_params(rows, original["taxa"], before[1])
    second = _prepare_love_params(rows, support["taxa"], after[1])
    if set(first) != set(second) or any(
        not first[key].equals(second[key])
        if isinstance(first[key], pd.DataFrame)
        else first[key] != second[key]
        for key in first
    ):
        raise ValueError("Actual calK parameter inputs changed")
    return {
        "regional_configuration_equal": True,
        "love_configuration_only_max_ring_differs": True,
        "paired_seed_equal": True,
        "actual_prepare_love_params_equal": True,
        "calK_invocation_parameters_equal": True,
        "kernels_computed": 0,
    }


def forward_geometry_bridge(
    geometry: dict[str, Any], method: str = "gpm neutral"
) -> dict[str, Any]:
    import pandas as pd

    from bijux_pollenomics_lra.models.configuration import ForwardConfig
    from bijux_pollenomics_lra.workflows.forward import _geometry

    if method != "gpm neutral":
        raise ValueError("Only the named current GPM-neutral source branch is proved")
    if geometry["basin"]["site_type"] != "lake":
        raise ValueError(
            "Only the actual adopted local lake geometry profile is proved"
        )
    rows = geometry["forward_rings"]
    if (
        len(rows) != 4
        or rows[0]["outer_m"] != 500
        or rows[1]["inner_m"] != 500
        or rows[1]["outer_m"] != 1000
    ):
        raise ValueError("Exact four forward rows and moved500-to1000 cell required")
    frame = pd.DataFrame(
        [
            {
                "inner": r["inner_m"],
                "outer": r["outer_m"],
                "mean": r["mean_m"],
                "ring": r["ring_area_m2"],
                "terrestrial": r["terrestrial_area_m2"],
            }
            for r in rows
        ]
    )
    views = [
        _geometry(
            frame,
            ForwardConfig(
                local_ring_count=count,
                local_basin_diameter_m=geometry["basin"]["diameter_m"],
                distance_weighting=method,
                regional_cover_profile="disqover-rounded-fractions",
            ),
        )
        for count in (2, 1)
    ]
    if not views[0][0].equals(views[1][0]) or not np.array_equal(
        views[0][1], views[1][1]
    ):
        raise ValueError("Complete forward geometry or terrestrial fractions changed")
    # calK forces peatland and passes diameter=2*inner; this GPM source branch
    # subtracts remaining-airborne values at diameter and cutoff, so equal
    # distances imply an exact zero row without evaluating a physical kernel.
    if 2 * rows[1]["inner_m"] != rows[1]["outer_m"]:
        raise ValueError("Moved row is not the proved source-specific zero kernel")
    return {
        "forward_rings_retained": 4,
        "moved_ring_index": 1,
        "source_lower_distance_m": 1000,
        "source_upper_distance_m": 1000,
        "conditional_kernel_value": 0.0,
        "homogeneous_same_cover_required": True,
        "forward_inputs_equal_under_zero_row": True,
        "physical_rsap_validated": False,
        "kernels_computed": 0,
    }


def operator_bridge(first: dict[str, Any], second: dict[str, Any]) -> dict[str, bool]:
    keys = {
        "regional",
        "kernels",
        "fractions",
        "ppe",
        "observed",
        "starts",
        "solver_seed",
    }
    if set(first) != keys or set(second) != keys:
        raise ValueError("Complete ring-zero operator arguments required")
    for key in keys - {"solver_seed"}:
        before, after = (
            np.asarray(first[key], dtype=float),
            np.asarray(second[key], dtype=float),
        )
        if (
            not np.isfinite(before).all()
            or not np.isfinite(after).all()
            or not np.array_equal(before, after)
        ):
            raise ValueError("Ring-zero argument changed: " + key)
    if (
        type(first["solver_seed"]) is not int
        or first["solver_seed"] != second["solver_seed"]
    ):
        raise ValueError("Actual derived solver seed changed")
    kernels = np.asarray(first["kernels"], dtype=float)
    ppe = np.asarray(first["ppe"], dtype=float)
    regional = np.asarray(first["regional"], dtype=float)
    observed = np.asarray(first["observed"], dtype=float)
    fractions = np.asarray(first["fractions"], dtype=float)
    starts = np.asarray(first["starts"], dtype=float)
    if (
        kernels.shape != (3, 30)
        or ppe.shape != (30,)
        or regional.shape != (30,)
        or observed.shape != (30,)
        or fractions.shape != (3,)
        or starts.shape != (32, 30)
    ):
        raise ValueError("Exact original30taxa/3inverse/32starts dimensions required")
    if (
        np.any(kernels < 0)
        or np.any(ppe <= 0)
        or np.any(regional < 0)
        or np.any(fractions < 0)
        or np.any(fractions > 1)
        or np.any(observed < 0)
        or abs(float(observed.sum()) - 1) > 1e-12
        or np.any(starts <= 0)
        or np.any(np.abs(starts.sum(axis=1) - 1) > 1e-12)
    ):
        raise ValueError("Original finite feasible operator domain required")
    if abs(float(regional.sum()) - 1) > 30 * 0.000005 + 1e-12:
        raise ValueError("Raw rounded regional fraction units changed")
    return {
        "ring0_objective_arguments_equal": True,
        "ring0_jacobian_arguments_equal": True,
        "fixed_starts_and_seed_equal": True,
        "raw_regional_not_normalized": True,
        "forward_partition_identity_for_same_cover": bool(np.all(kernels[1] == 0)),
        "native_reuse_admitted": False,
    }


def bind_ring0_population(
    bridges: list[dict[str, Any]],
    records: dict[str, Any],
    ring0_attempts: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    if (
        len(bridges) != 39
        or len(records) != 39
        or len(ring0_attempts) != 39
        or len({r["original_request_sha256"] for r in bridges}) != 39
        or len({r["support_request_sha256"] for r in bridges}) != 39
    ):
        raise ValueError("Complete39 distinct original/new request identities required")
    mappings = []
    for bridge in bridges:
        key = bridge["original_request_sha256"]
        attempts = ring0_attempts[key]
        if (
            records[key]["request_sha256"] != key
            or len(attempts) != 32
            or len({r["start_id"] for r in attempts}) != 32
            or any(
                r["request_sha256"] != key
                or r["ring_index"] != 0
                or r["outer_m"] != 500
                or type(r["accepted"]) is not bool
                for r in attempts
            )
        ):
            raise ValueError(
                "Original complete32-start ring-zero identity population required"
            )
        selected = records[key]["selections"][0]
        accepted = [r for r in attempts if r["accepted"]]
        if accepted:
            if any(
                type(r["result"]["fun"]) not in (int, float)
                or not math.isfinite(r["result"]["fun"])
                for r in accepted
            ):
                raise ValueError("Finite accepted ring-zero objectives required")
            winner = min(accepted, key=lambda r: (r["result"]["fun"], r["start_id"]))
            if (
                selected is None
                or selected["selected_attempt_sha256"] != digest(winner)
                or selected["selected_start_id"] != winner["start_id"]
                or selected["selected_objective"] != winner["result"]["fun"]
            ):
                raise ValueError("Original ring-zero selected minimum changed")
        elif selected is not None:
            raise ValueError("Noaccepted ring must preserve its refusal")
        mappings.append(
            {
                "original_request_sha256": key,
                "support_request_sha256": bridge["support_request_sha256"],
                "original_ring0_attempts_sha256": digest(attempts),
                "attempts": 32,
                "accepted": len(accepted),
                "refused": 32 - len(accepted),
                "original_selection_sha256": digest(selected),
                "selection_disposition": "selected"
                if selected is not None
                else "refused",
            }
        )
    return {
        "request_bridges": mappings,
        "request_count": 39,
        "original_ring0_attempts": 1248,
        "new_optimizer_attempts": 0,
        "projection_only": True,
        "native_authority_status": "not_admitted_by_this_pure_function",
        "required_external_precondition": "Root must independently admit exact saved nominal39 products/source execution and full original lifecycle before using this mapping; preserve all actual native exits and post-body refusals.",
    }
