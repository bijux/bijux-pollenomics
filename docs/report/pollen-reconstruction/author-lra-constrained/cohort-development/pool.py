"""Fixed numerical requests shared only after exact fold ancestry reconstruction."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from typing import Any

import numpy as np

TRAINING = "docs/report/pollen-reconstruction/author-lra-constrained/development-fold/training.py"


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def prior_attempts(
    math: dict[str, Any],
    previous: dict[str, Any],
    events: bytes,
    first: dict[str, Any],
    first_events: bytes,
) -> dict[tuple[str, int], list[dict[str, Any]]]:
    """Admit the complete prior832 lifecycle without copying its vectors per fold."""
    reused = math["_reuse"](first, first_events)
    rows = previous["new_attempts"]
    ledger = [json.loads(line) for line in events.splitlines()]
    if (
        len(rows) != 704
        or len(ledger) != 1408
        or previous["total_attempts"] != 832
        or previous["failures"]
    ):
        raise ValueError("Exact admitted complete832 population required")
    for index, row in enumerate(rows):
        start, finish = ledger[2 * index : 2 * index + 2]
        if (
            start.pop("event") != "attempt_started"
            or finish.pop("event") != "attempt_completed"
            or finish != row
        ):
            raise ValueError("Prior704 lifecycle differs")
        if any(
            start[key] != row[key]
            for key in (
                "item_id",
                "request_sha256",
                "ring_index",
                "outer_m",
                "start_id",
                "start",
                "execution",
            )
        ) or row["accepted"] != math["_accepted"](row):
            raise ValueError("Prior704 request or convergence certification differs")
        reused.setdefault((row["item_id"], row["ring_index"]), []).append(row)
    grouped = {}
    for (_, ring), attempts in reused.items():
        hashes = {row["request_sha256"] for row in attempts}
        if len(attempts) != 32 or len(hashes) != 1:
            raise ValueError("Prior complete fixed-start request population differs")
        grouped[(next(iter(hashes)), ring)] = attempts
    if len(grouped) != 26 or len(previous["training"]) != 13:
        raise ValueError("Prior832 must provide26 distinct ring objectives")
    return grouped


def fit_request(
    original: dict[str, Any],
    helper: dict[str, Any],
    math: dict[str, Any],
    item: Any,
    prepared: Any,
    reused: dict[tuple[str, int], list[dict[str, Any]]],
    prior_training: dict[str, Any],
    emit: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    validated = original["validate_lra_inputs"](item.payload(), input_root=prepared)
    payload = validated.payload()
    binding = original["load_engine"](
        required_capability=original["required_capability_for_profile"](
            payload["method_profile"]
        )
    )
    reveals, love, paired = original["_configuration"](binding, payload)
    if (
        len(payload["taxa"]),
        len(payload["rings"]),
        love.max_ring,
        love.repeats,
        love.optimizer_iterations,
        love.optimizer_max_evaluations,
        love.optimizer_tolerance,
    ) != (30, 3, 2, 1, 300, 16000, 1e-8):
        raise ValueError("Original scientific dimensions or budgets changed")
    rs, ls = np.random.SeedSequence(paired.seed).spawn(2)
    reveals = replace(
        reveals, seed=int(rs.generate_state(1, dtype=np.uint32)[0]), retain_samples=True
    )
    love = replace(love, seed=int(ls.generate_state(1, dtype=np.uint32)[0]))
    pollen, parameters, rings = original["_tables"](payload)
    regional_result = original["run_reveals"](pollen["regional"], parameters, reveals)
    if regional_result.samples is None or regional_result.samples.shape[0] != 1:
        raise ValueError("Single original regional sample required")
    regional = regional_result.samples[0, 0, :] / 100
    params = original["_prepare_love_params"](parameters, payload["taxa"], love)
    kernels = original["calK"](rings, params).to_numpy(dtype=float)
    terrestrial = (rings["terrestrial"] / rings["ring"]).to_numpy(dtype=float)
    ppe = parameters["ppe"].to_numpy(dtype=float)
    counts = np.asarray(payload["local"]["samples"][0]["counts"], dtype=float)
    observed = counts / counts.sum()
    selections: list[dict[str, Any] | None] = []
    new: list[dict[str, Any]] = []
    for ring in range(2):
        key = (item.request_sha256, ring)
        reused_here = key in reused
        if reused_here:
            rows = reused[key]
            previous = next(
                row
                for row in prior_training["training"]
                if row["request_sha256"] == item.request_sha256
            )
            if not np.array_equal(previous["regional_cover"], regional):
                raise ValueError("Prior raw rounded regional background differs")
            for row, (name, start) in zip(
                rows, helper["_starts"](observed, regional), strict=True
            ):
                if (
                    row["item_id"] != item.item_id
                    or row["request_sha256"] != item.request_sha256
                    or row["start_id"] != name
                    or not np.array_equal(row["start"], start)
                    or row["outer_m"] != payload["rings"][ring]["outer_m"]
                ):
                    raise ValueError("Prior fixed-start numerical request differs")
                if row["accepted"]:
                    fraction, local_k = terrestrial[: ring + 1], kernels[: ring + 1]
                    background = np.sum(
                        kernels[ring + 1 :]
                        * (regional * ppe)[None, :]
                        * terrestrial[ring + 1 :, None],
                        axis=0,
                    )
                    value = original["tf"](
                        np.asarray(row["result"]["x"]),
                        background,
                        local_k,
                        fraction,
                        observed,
                        ppe,
                    )
                    if not np.isclose(
                        value, row["result"]["fun"], rtol=1e-12, atol=1e-12
                    ):
                        raise ValueError(
                            "Reused accepted objective no longer certifies"
                        )
        else:
            rows = math["_new_attempts"](
                helper,
                original,
                item,
                payload,
                regional,
                ppe,
                kernels,
                terrestrial,
                observed,
                love.seed,
                ring,
                emit,
            )
            new.extend(rows)
        accepted = [row for row in rows if row["accepted"]]
        if not accepted:
            selections.append(None)
            continue
        chosen = min(accepted, key=lambda row: (row["result"]["fun"], row["start_id"]))
        composition, transform = math["_composition"](chosen, payload["taxa"])
        evidence = {
            "item_id": item.item_id,
            "request_sha256": item.request_sha256,
            "ring_index": ring,
            "attempted": 32,
            "accepted": len(accepted),
            "refused": 32 - len(accepted),
            "selected_start_id": chosen["start_id"],
            "selected_objective": chosen["result"]["fun"],
            "selected_attempt_sha256": _digest(chosen),
            "execution": "reused" if reused_here else "new",
            **transform,
        }
        if reused_here and {
            key: value for key, value in evidence.items() if key != "execution"
        } != {
            key: value
            for key, value in previous["selections"][ring].items()
            if key != "execution"
        }:
            raise ValueError("Prior ring minimum or diagnostic transform differs")
        selections.append(evidence)
    return {
        "item_id": item.item_id,
        "request_sha256": item.request_sha256,
        "taxa": payload["taxa"],
        "regional_cover": regional.tolist(),
        "regional_fraction_sum": float(regional.sum()),
        "regional_percent_precision_decimals": 3,
        "selections": selections,
        "execution": "reused" if (item.request_sha256, 0) in reused else "new",
    }, new
