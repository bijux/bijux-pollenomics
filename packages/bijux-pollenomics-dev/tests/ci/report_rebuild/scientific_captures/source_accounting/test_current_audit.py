"""Strict owner acceptance and current/earlier summary correspondence controls."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from functools import partial
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_accounting.current_audit import (
    ORIGINAL_OWNER,
    REPORT,
    RETAINED_OWNER,
    original_ownership,
    ownership,
    same_metadata,
    summary_correspondence,
)


def refused(call: Callable[[], None]) -> None:
    try:
        call()
    except ReportRebuildError:
        return
    raise AssertionError("Malformed or broadened source-accounting proof must refuse")


def summaries() -> tuple[dict[str, Any], dict[str, Any]]:
    original = {
        **{str(i): {"counts": [1, 2], "unknown": None} for i in range(14)},
        "full_source_confirmation": False,
        "summary_sha256": "a" * 64,
        "full_audit_sha256": "26116f18017f5695c8782849e9ab827251d033cc56a8e1e76eabf38063c9ba90",
        "input_closure_sha256": "b" * 64,
    }
    current = deepcopy(original)
    current["summary_sha256"] = "c" * 64
    current["full_audit_sha256"] = (
        "3ec6ed5dc52d23c88fead8b33f812ca31f1206c8cb497780c78bc7ea04c8aa3b"
    )
    current["input_closure_sha256"] = "d" * 64
    return original, current


def test_exact_original_and_retained_owner_contracts() -> None:
    sibling: dict[str, Any] = {
        "owner_id": "other",
        "paths": ["docs/report/other/report.json"],
    }
    original_ownership([deepcopy(ORIGINAL_OWNER), sibling])
    ownership([deepcopy(RETAINED_OWNER), sibling])


def test_owner_mutations_refused() -> None:
    for selector, baseline in [
        (original_ownership, ORIGINAL_OWNER),
        (ownership, RETAINED_OWNER),
    ]:
        for key, value in [
            ("verification", "narrowed mechanical rule"),
            ("paths", []),
            ("producer_paths", ["unknown.py"]),
            ("producer_inputs", ["unknown.json"]),
            ("permission_claimed", True),
        ]:
            changed = deepcopy(baseline)
            changed[key] = value
            refused(partial(selector, [changed]))
        refused(partial(selector, [deepcopy(baseline), deepcopy(baseline)]))
        refused(
            partial(
                selector,
                [deepcopy(baseline), {"owner_id": "overlap", "paths": [REPORT]}],
            )
        )
    refused(lambda: ownership([deepcopy(ORIGINAL_OWNER)]))
    refused(lambda: original_ownership([deepcopy(RETAINED_OWNER)]))


def test_exact_summary_provenance_succession() -> None:
    original, current = summaries()
    summary_correspondence(original, current)
    reordered = {key: current[key] for key in reversed(current)}
    summary_correspondence(original, reordered)


def test_scientific_summary_changes_refused() -> None:
    original, current = summaries()
    for mutation in (
        "null_zero",
        "list_order",
        "bool_count",
        "extra",
        "full_confirmation",
        "old_digest",
        "no_provenance_change",
    ):
        changed = deepcopy(current)
        if mutation == "null_zero":
            changed["0"]["unknown"] = 0
        elif mutation == "list_order":
            changed["0"]["counts"] = [2, 1]
        elif mutation == "bool_count":
            changed["0"]["counts"] = [True, 2]
        elif mutation == "extra":
            changed["invented"] = 0
        elif mutation == "full_confirmation":
            changed["full_source_confirmation"] = True
        elif mutation == "old_digest":
            changed["full_audit_sha256"] = "0" * 64
        else:
            changed["summary_sha256"] = original["summary_sha256"]
        refused(partial(summary_correspondence, original, changed))


def test_exact_metadata_values_and_refusals() -> None:
    same_metadata({"a": [1, 2], "b": None}, {"b": None, "a": [1, 2]})
    refused(lambda: same_metadata({"a": 1}, {"a": True}))
    refused(lambda: same_metadata([1, 2], [2, 1]))
    refused(lambda: same_metadata(0.0, -0.0))
    refused(lambda: same_metadata(float("nan"), float("nan")))
