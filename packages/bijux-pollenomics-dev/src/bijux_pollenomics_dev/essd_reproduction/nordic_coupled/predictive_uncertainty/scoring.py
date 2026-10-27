"""Joint prediction moments and post-freeze exposed-outcome diagnostics."""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray

from .inputs import METHODS
from .predictions import ensemble_summary
from .products import StudyError


def joint_predictions(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Retain cross-place dependence on aligned replicate identities."""
    cases = sorted(cases, key=lambda row: row["case_id"])
    if len(cases) != 3 or len({row["case_id"] for row in cases}) != 3:
        raise StudyError("Three distinct active cases required")
    result = {}
    for method in METHODS:
        rows = [case["methods"][method] for case in cases]
        physical = np.concatenate(
            [np.asarray(row["pollen"], dtype=float) for row in rows], axis=1
        )
        direct = np.concatenate(
            [np.asarray(row["direct_pollen"], dtype=float) for row in rows], axis=1
        )
        complete = np.logical_and.reduce(
            [np.asarray(row["valid_mask"], dtype=bool) for row in rows]
        )
        result[method] = {
            "case_ids": [row["case_id"] for row in cases],
            "physical": ensemble_summary(physical, complete),
            "direct_all_replicates": ensemble_summary(direct),
            "direct_on_physical_defined": ensemble_summary(direct, complete),
            "physical_minus_direct": ensemble_summary(physical - direct, complete),
        }
    return result


def _losses(
    prediction: NDArray[np.float64], observation: NDArray[np.float64]
) -> NDArray[np.float64]:
    delta = prediction - observation
    absolute = np.abs(delta)
    mae = np.mean(absolute, axis=1)
    tv = np.sum(absolute, axis=1) / 2
    hellinger = np.sqrt(
        np.sum((np.sqrt(prediction) - np.sqrt(observation)) ** 2, axis=1) / 2
    )
    return np.column_stack((mae, tv, hellinger))


def score_diagnostics(
    packet: dict[str, Any], predictions: dict[str, Any]
) -> dict[str, Any]:
    """Decode previously exposed observations only after prediction readback."""
    cases = sorted(predictions["cases"], key=lambda row: row["case_id"])
    owners = {row["owner_id"]: row for row in packet["owners"]}
    lineage = packet["accounting"]["owner_lineage"]
    observations = []
    summaries = []
    losses: dict[
        str, list[tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.bool_]]]
    ] = {method: [] for method in METHODS}
    for case in cases:
        owner = owners[case["target_id"]]
        counts = np.asarray(owner["counts"], dtype=float)
        observed = counts / counts.sum()
        observations.append(
            {
                "case_id": case["case_id"],
                "target_id": case["target_id"],
                "counts": owner["counts"],
                "counts_source_reference": lineage[case["target_id"]]["raw"],
                "pollen_fraction": observed.tolist(),
            }
        )
        for method in METHODS:
            row = case["methods"][method]
            physical = _losses(np.asarray(row["pollen"], dtype=float), observed)
            direct = _losses(np.asarray(row["direct_pollen"], dtype=float), observed)
            valid = np.asarray(row["valid_mask"], dtype=bool)
            summaries.append(
                {
                    "case_id": case["case_id"],
                    "method": method,
                    "physical": ensemble_summary(physical, valid),
                    "direct_all_replicates": ensemble_summary(direct),
                    "direct_on_physical_defined": ensemble_summary(direct, valid),
                    "physical_minus_direct": ensemble_summary(physical - direct, valid),
                }
            )
            losses[method].append((physical, direct, valid))
    aggregate = {}
    for method, rows in losses.items():
        physical = np.mean([row[0] for row in rows], axis=0)
        direct = np.mean([row[1] for row in rows], axis=0)
        complete = np.logical_and.reduce([row[2] for row in rows])
        aggregate[method] = {
            "case_ids": [case["case_id"] for case in cases],
            "physical": ensemble_summary(physical, complete),
            "direct_on_physical_defined": ensemble_summary(direct, complete),
            "physical_minus_direct": ensemble_summary(physical - direct, complete),
        }
    return {"observed": observations, "cases": summaries, "aggregate": aggregate}
