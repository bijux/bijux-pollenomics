"""Fit only the two declared new PPE request populations."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


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
    if method not in ("ppe-minus-source-sd", "ppe-plus-source-sd") or reused:
        raise ValueError(
            "Only exact new PPE requests without nominal attempt relabelling may fit"
        )
    overlap = {key[0] for key in reused} & set(numeric)
    if len(overlap) != 0:
        raise ValueError("No PPE request may reuse nominal optimizer attempts")
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
    budget = 2496
    if len(attempts) != budget:
        raise ValueError("Complete finite per-shard start population required")
    return {
        "method": method,
        "numerical_requests": records,
        "new_attempts": attempts,
        "request_refusals": [],
        "planned_new_start_slots": budget,
        "actual_new_attempts": len(attempts),
        "reused_attempts": 0,
        "raw_regional_handoff": "Each declared PPE vector recomputes source3decimal-percent REVEALS; raw/100 handoff unchanged. Normalize regional direction only inside existing start generator.",
    }
