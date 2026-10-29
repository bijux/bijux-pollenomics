"""Reuse all certified nominal attempts and fit only exact new transport requests."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def previous(
    common: dict[str, Any],
    repository: Path,
    protocol: dict[str, Any],
    libraries: dict[str, dict[str, Any]],
) -> tuple[dict[tuple[str, int], list[dict[str, Any]]], dict[str, Any]]:
    refs = {
        name: common["checked"](repository, row)
        for name, row in protocol["prior_evidence"].items()
    }
    math = libraries["math"]
    pool = libraries["pool"]
    prior = common["decode"](refs["development_training"])
    reused = pool["prior_attempts"](
        math,
        prior,
        refs["development_trials"],
        common["decode"](refs["start_report"]),
        refs["start_trials"],
    )
    cohort = common["decode"](refs["cohort_training"])
    events = [common["decode"](line) for line in refs["cohort_trials"].splitlines()]
    attempts = cohort["new_attempts"]
    if (
        len(attempts) != 896
        or len(events) != 1792
        or len(cohort["numerical_requests"]) != 27
    ):
        raise ValueError("Exact admitted prior896/1728 lifecycle required")
    for index, row in enumerate(attempts):
        start, finish = events[2 * index : 2 * index + 2]
        if (
            start.pop("event") != "attempt_started"
            or finish.pop("event") != "attempt_completed"
            or finish != row
        ):
            raise ValueError("Prior cohort lifecycle changed")
        if any(
            start[k] != row[k]
            for k in (
                "item_id",
                "request_sha256",
                "ring_index",
                "outer_m",
                "start_id",
                "start",
                "execution",
            )
        ) or row["accepted"] != math["_accepted"](row):
            raise ValueError("Prior convergence/request identity changed")
        reused.setdefault((row["request_sha256"], row["ring_index"]), []).append(row)
    if len(reused) != 54 or any(len(rows) != 32 for rows in reused.values()):
        raise ValueError("Prior54 ring/1728 attempt population differs")
    authority = common["decode"](refs["cohort_receipt"])
    if any(
        authority["execution"][name] != 0
        for name in ("common_exit", "outer_exit", "native_exit")
    ):
        raise ValueError("Prior actual cohort did not pass")
    return reused, {"training": list(cohort["numerical_requests"].values())}


def fit(
    common: dict[str, Any],
    libraries: dict[str, dict[str, Any]],
    numeric: dict[str, Any],
    prepared: Path,
    output: Path,
    method: str,
    reused: dict[tuple[str, int], list[dict[str, Any]]],
    previous_training: dict[str, Any],
) -> dict[str, Any]:
    if method != "gpm neutral":
        reused = {}
    overlap = {key[0] for key in reused} & set(numeric)
    if len(overlap) != (27 if method == "gpm neutral" else 0):
        raise ValueError("Exact nominal27 request identity reuse required")
    records = {}
    attempts = []
    with (output / "trials.jsonl").open("x") as ledger:

        def emit(row: dict[str, Any]) -> None:
            ledger.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            ledger.flush()
            os.fsync(ledger.fileno())

        for checksum, item in sorted(numeric.items()):
            record, new = libraries["pool"]["fit_request"](
                libraries["original"],
                libraries["starts"],
                libraries["math"],
                item,
                prepared,
                reused,
                previous_training,
                emit,
            )
            records[checksum] = record
            attempts.extend(new)
    budget = 768 if method == "gpm neutral" else 2496
    if len(attempts) != budget:
        raise ValueError("Complete finite per-shard start population required")
    return {
        "method": method,
        "numerical_requests": records,
        "new_attempts": attempts,
        "request_refusals": [],
        "planned_new_start_slots": budget,
        "actual_new_attempts": len(attempts),
        "reused_attempts": 1728 if method == "gpm neutral" else 0,
        "raw_regional_handoff": "Each transport recomputes source3decimal-percent REVEALS; raw/100 handoff unchanged. Normalize regional direction only inside existing start generator.",
    }
