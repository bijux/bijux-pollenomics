"""Preserved paired LOVE method differences keep denominators and refusals exact."""

from __future__ import annotations

import copy
from functools import cache
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.author_method_comparison import (
    OWNER,
    PREFIX,
    PRODUCTS,
    validate_products,
    validated_author_method_comparison,
)

REPOSITORY = Path(__file__).absolute().parents[5]


@cache
def saved_products() -> tuple[dict[str, bytes], dict[str, Any]]:
    bodies = {
        role: (REPOSITORY / PREFIX / name).read_bytes()
        for role, name in PRODUCTS.items()
    }
    return bodies, json.loads(bodies["report"])


def test_current_comparison_support_and_products() -> None:
    tracked = {}
    for name in PRODUCTS.values():
        path = PREFIX + name
        raw = (REPOSITORY / path).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        tracked[path] = InventoryEntry(
            path.removeprefix("docs/report/"), "file", len(raw), digest, digest
        )
    owner: dict[str, object] = {
        "owner_id": OWNER,
        "role": "retained_source",
        "paths": sorted(tracked),
        "producer_paths": [],
        "producer_inputs": [],
    }
    accepted, result = validated_author_method_comparison(REPOSITORY, tracked, [owner])
    assert len(accepted) == 3
    assert result["saved_source_support_and_arithmetic_verified"] is True
    assert result["models_or_rescoring_executed"] is False


def test_current_saved_projections() -> None:
    bodies, report = saved_products()
    result = validate_products(bodies, report)
    counts = result["counts"]
    assert isinstance(counts, dict)
    assert counts["matched_folds"] == 14
    assert counts["paired_baseline_rows"] == 42
    assert result["unmatched_cohort_scores"] == 3


def _changed_saved_result_refused(change: str) -> None:
    bodies, report = saved_products()
    changed = copy.deepcopy(report)
    damaged = dict(bodies)
    if change == "denominator":
        changed["counts"]["matched_folds"] = 15
    elif change == "delta":
        changed["paired_scores"][0]["metrics"]["total_variation"]["delta"] += 1
    elif change == "unpaired_score":
        changed["unmatched_cohort_scores"][0]["original_score"] = 0
    elif change == "refusal_reason":
        next(
            row
            for row in changed["fold_dispositions"]
            if row["original_status"] == "refused"
        )["original_reason"] = None
    elif change == "missing_pair":
        changed["paired_scores"].pop()
    else:
        damaged["paired_scores"] += b"invented,unmatched,row\n"
    if change != "csv":
        damaged["report"] = (
            json.dumps(changed, indent=2, sort_keys=True, allow_nan=False) + "\n"
        ).encode()
    with pytest.raises(ReportRebuildError):
        validate_products(damaged, report)


def test_changed_denominator_refused() -> None:
    _changed_saved_result_refused("denominator")


def test_changed_delta_refused() -> None:
    _changed_saved_result_refused("delta")


def test_changed_unpaired_score_refused() -> None:
    _changed_saved_result_refused("unpaired_score")


def test_changed_refusal_reason_refused() -> None:
    _changed_saved_result_refused("refusal_reason")


def test_changed_missing_pair_refused() -> None:
    _changed_saved_result_refused("missing_pair")


def test_changed_csv_refused() -> None:
    _changed_saved_result_refused("csv")
