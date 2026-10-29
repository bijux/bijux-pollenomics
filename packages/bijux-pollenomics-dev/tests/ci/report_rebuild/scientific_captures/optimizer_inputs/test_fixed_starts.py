"""Keep artificial fixed-start lifecycle checks independent of scientific fitting."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.optimizer_inputs.fixed_starts import (
    ITEMS,
    STARTS,
    validate_lifecycle,
)


def _documents() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    baseline: dict[str, Any] = {
        "source_manifest_sha256": "a" * 64,
        "experiment_sha256": "b" * 64,
        "fold_id": "artificial-training-fold",
        "withheld_site": "artificial-unopened-site",
        "regional_anchor": "artificial-training-anchor",
        "items": [
            {
                "item_id": item,
                "request_sha256": "c" * 64,
                "rings": [
                    {"outer_m": outer, "analytic": {"fun": 2.0, "success": False}}
                    for outer in (100.0, 200.0)
                ],
            }
            for item in ITEMS
        ],
    }
    report: dict[str, Any] = {
        key: value for key, value in baseline.items() if key != "items"
    }
    report.update(
        schema_version="author-love-fixed-start-diagnostic.v1",
        optimizer_contract={
            "starts_per_ring": 32,
            "rings_per_item": 2,
            "total_new_attempts": 128,
            "maxiter_per_attempt": 300,
            "max_objective_evaluations_per_attempt": 16000,
            "ftol": 1e-8,
            "single_process": True,
            "numerical_threads": 1,
        },
        attempts=[],
        ring_selections=[],
        regional_handoffs=[],
    )
    ledger = []
    for item_index, item in enumerate(ITEMS):
        native = [1.0] * 29 + [70.999 if item_index == 0 else 71.001]
        fraction = [x / 100 for x in native]
        direction = [x / sum(fraction) for x in fraction]
        report["regional_handoffs"].append(
            {
                "item_id": item,
                "taxa": [f"taxon-{i}" for i in range(30)],
                "native_percent_decimal_places": 3,
                "native_cover_percent": native,
                "native_cover_percent_sum": sum(native),
                "fractional_cover": fraction,
                "fractional_cover_sum": sum(fraction),
                "normalized_start_direction": direction,
            }
        )
        for ring, outer in enumerate((100.0, 200.0)):
            successful = []
            for index, start_id in enumerate(STARTS):
                start = (
                    [1 / 30] * 30
                    if index < 2
                    else [
                        1 / 60 + (0.5 if axis == index - 2 else 0) for axis in range(30)
                    ]
                )
                if index == 1:
                    start = [1 / 60 + 0.5 * x for x in direction]
                row: dict[str, Any] = {
                    "item_id": item,
                    "request_sha256": "c" * 64,
                    "ring_index": ring,
                    "outer_m": outer,
                    "start_id": start_id,
                    "start": start,
                }
                began = {"event": "attempt_started", **deepcopy(row)}
                row.update(
                    accepted=False,
                    elapsed_seconds=0.001,
                    observed_calls={"objective": 3, "jacobian": 2},
                )
                if index == 0:
                    row.update(refusal_type="ValueError", refusal="artificial refusal")
                else:
                    accepted = index in {3, 4}
                    row["accepted"] = accepted
                    row["result"] = {
                        "x": [1 / 30] * 30,
                        "fun": 0.1 if accepted else 0.2,
                        "success": accepted,
                        "nfev": 2,
                        "certification_nfev": 1,
                    }
                    if accepted:
                        successful.append((0.1, start_id))
                report["attempts"].append(row)
                ledger.extend([began, {"event": "attempt_completed", **deepcopy(row)}])
            report["ring_selections"].append(
                {
                    "item_id": item,
                    "ring_index": ring,
                    "attempted": 32,
                    "accepted": 2,
                    "selected": list(min(successful)),
                    "baseline_analytic": {"fun": 2.0, "success": False},
                    "selected_objective_delta_vs_refused_uniform": 0.1 - 2.0,
                    "baseline_reused_without_rerun": True,
                }
            )
    return report, ledger, baseline


def test_complete_lifecycle_retains_successes_ties_and_refusals() -> None:
    report, ledger, baseline = _documents()
    validate_lifecycle(report, ledger, baseline)
    assert report["attempts"][0]["refusal"] == "artificial refusal"
    assert report["attempts"][1]["accepted"] is False
    assert report["ring_selections"][0]["selected"] == [
        0.1,
        "taxon-01-half-uniform",
    ]


@pytest.mark.parametrize(
    "change",
    [
        "missing_attempt",
        "missing_lifecycle",
        "wrong_request",
        "changed_start",
        "lost_refusal",
        "relabeled_refusal",
        "evaluation_mismatch",
        "lost_certification",
        "infeasible_success",
        "wrong_selected_tie",
        "old_baseline_changed",
        "ledger_rewritten",
        "raw_mass_rewritten",
        "direction_rewritten",
        "source_unit_conversion_changed",
    ],
)
def test_changed_scientific_accounting_is_refused(change: str) -> None:
    report, ledger, baseline = _documents()
    attempt = report["attempts"]
    if change == "missing_attempt":
        attempt.pop()
    elif change == "missing_lifecycle":
        ledger.pop()
    elif change == "wrong_request":
        attempt[0]["request_sha256"] = "d" * 64
    elif change == "changed_start":
        attempt[2]["start"][0] = 0.25
    elif change == "lost_refusal":
        attempt[0].pop("refusal")
    elif change == "relabeled_refusal":
        attempt[1]["accepted"] = True
    elif change == "evaluation_mismatch":
        attempt[1]["observed_calls"]["objective"] = 4
    elif change == "lost_certification":
        attempt[1]["result"]["certification_nfev"] = 0
    elif change == "infeasible_success":
        attempt[3]["result"]["x"][0] = 2.0
    elif change == "wrong_selected_tie":
        report["ring_selections"][0]["selected"][1] = "taxon-02-half-uniform"
    elif change == "old_baseline_changed":
        report["ring_selections"][0]["baseline_analytic"]["success"] = True
    elif change == "raw_mass_rewritten":
        report["regional_handoffs"][0]["fractional_cover_sum"] = 1.0
    elif change == "direction_rewritten":
        report["regional_handoffs"][0]["normalized_start_direction"][0] = 0.1
    elif change == "source_unit_conversion_changed":
        report["regional_handoffs"][0]["fractional_cover"][0] = 1.0
    else:
        ledger[0]["start_id"] = "rewritten"
    with pytest.raises(ReportRebuildError):
        validate_lifecycle(report, ledger, baseline)
