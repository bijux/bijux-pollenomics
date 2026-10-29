"""Train-only fixed-start attempts and explicit unrounded diagnostic compositions."""

from __future__ import annotations

from collections.abc import Callable
import json
import time
from typing import Any

import numpy as np

from bijux_pollenomics.analysis.lra_validation.metrics import closed_composition

REUSED = ("author:CUTHILL2", "author:LONGBREACH")


def _accepted(row: dict[str, Any]) -> bool:
    result = row.get("result")
    if not isinstance(result, dict):
        return False
    x = np.asarray(result["x"], dtype=float)
    return bool(
        result["success"] is True
        and np.isfinite(result["fun"])
        and x.shape == (30,)
        and np.isfinite(x).all()
        and np.all(x >= 0)
        and np.all(x <= 1)
        and abs(float(x.sum()) - 1) <= 1e-6
    )


def _composition(
    row: dict[str, Any], taxa: list[str]
) -> tuple[dict[str, float], dict[str, Any]]:
    if not _accepted(row) or row["accepted"] is not True:
        raise ValueError(
            "Only originally converged host-certified candidates may supply cover"
        )
    raw = np.asarray(row["result"]["x"], dtype=float)
    normalized = raw / raw.sum()
    composition = closed_composition(dict(zip(taxa, normalized.tolist(), strict=True)))
    return composition, {
        "raw_x": raw.tolist(),
        "raw_sum": float(raw.sum()),
        "composition": composition,
        "composition_sum": sum(composition.values()),
        "transform": "Explicit unrounded diagnostic adapter: x/x.sum(), the same normalization used by tf and canonical LOVEoptim. No clamp or four-decimal rounding; no host LRAProduct/publication claim.",
    }


def _reuse(
    prior: dict[str, Any], ledger: bytes
) -> dict[tuple[str, int], list[dict[str, Any]]]:
    rows = prior["attempts"]
    events = [json.loads(line) for line in ledger.splitlines()]
    if len(rows) != 128 or len(events) != 256:
        raise ValueError("Exact prior128 attempts and256 lifecycle rows required")
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for index, row in enumerate(rows):
        started, completed = events[2 * index : 2 * index + 2]
        if (
            started.pop("event") != "attempt_started"
            or completed.pop("event") != "attempt_completed"
            or completed != row
        ):
            raise ValueError("Prior attempt/ledger disagreement")
        if any(
            started[key] != row[key]
            for key in (
                "item_id",
                "request_sha256",
                "ring_index",
                "outer_m",
                "start_id",
                "start",
            )
        ) or row["accepted"] != _accepted(row):
            raise ValueError("Prior lifecycle or convergence gate differs")
        grouped.setdefault((row["item_id"], row["ring_index"]), []).append(row)
    if set(grouped) != {(item, ring) for item in REUSED for ring in range(2)} or any(
        len(value) != 32 for value in grouped.values()
    ):
        raise ValueError("Prior source population differs")
    return grouped


def _new_attempts(
    helper: dict[str, Any],
    original: dict[str, Any],
    item: Any,
    payload: dict[str, Any],
    regional: Any,
    ppe: Any,
    kernels: Any,
    terrestrial: Any,
    observed: Any,
    seed: int,
    ring: int,
    emit: Callable[[dict[str, Any]], None],
) -> list[dict[str, Any]]:
    local_fraction, local_k = terrestrial[: ring + 1], kernels[: ring + 1]
    background = np.sum(
        kernels[ring + 1 :] * (regional * ppe)[None, :] * terrestrial[ring + 1 :, None],
        axis=0,
    )
    coefficient = ppe * np.sum(local_k * local_fraction[:, None], axis=0)
    attempts = []
    for start_id, start in helper["_starts"](observed, regional):
        row: dict[str, Any] = {
            "item_id": item.item_id,
            "request_sha256": item.request_sha256,
            "ring_index": ring,
            "outer_m": payload["rings"][ring]["outer_m"],
            "start_id": start_id,
            "start": start.tolist(),
            "execution": "new",
        }
        emit({"event": "attempt_started", **row})
        calls = {"objective": 0, "jacobian": 0}
        objective, jacobian = helper["_functions"](
            original,
            background,
            local_k,
            local_fraction,
            observed,
            ppe,
            coefficient,
            calls,
        )
        began = time.perf_counter()
        try:
            result = original["optimize_box"](
                objective,
                np.zeros(30),
                np.ones(30),
                maxiter=300,
                tolerance=1e-8,
                max_evaluations=16000,
                optimizer=helper["FixedStartSLSQP"](
                    jacobian, start, original["OptimizationResult"]
                ),
                rng=seed,
            )
            row["result"] = result.as_dict()
            row["accepted"] = _accepted(row)
        except ValueError as error:
            row.update(
                accepted=False, refusal_type=type(error).__name__, refusal=str(error)
            )
        row.update(observed_calls=calls, elapsed_seconds=time.perf_counter() - began)
        row = helper["_finite_json"](row)
        emit({"event": "attempt_completed", **row})
        attempts.append(row)
    return attempts
