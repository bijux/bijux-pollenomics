"""Validate complete fixed-start LOVE attempts without opening scientific outcomes."""

from __future__ import annotations

import math
from typing import Any

from ...contracts import ReportRebuildError

ITEMS = ("author:CUTHILL2", "author:LONGBREACH")


STARTS = (
    "local-observed-half-uniform",
    "regional-cover-half-uniform",
    *(f"taxon-{index:02d}-half-uniform" for index in range(30)),
)


def _require(value: object, reason: str) -> None:
    if not value:
        raise ReportRebuildError("LOVE fixed-start " + reason)


def _object(value: object) -> dict[str, Any]:
    _require(type(value) is dict, "object required")
    assert isinstance(value, dict)
    return value


def _finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate_regional_handoffs(report: dict[str, Any]) -> dict[str, list[float]]:
    """Keep rounded source percentages distinct from normalized start directions."""
    handoffs = report.get("regional_handoffs")
    _require(
        type(handoffs) is list and len(handoffs) == 2,
        "two raw regional handoffs required",
    )
    assert isinstance(handoffs, list)
    directions: dict[str, list[float]] = {}
    taxa = None
    for item, value in zip(ITEMS, handoffs, strict=True):
        row = _object(value)
        _require(
            row.get("item_id") == item
            and type(row.get("native_percent_decimal_places")) is int
            and row["native_percent_decimal_places"] == 3,
            "regional precision or identity differs",
        )
        names = row.get("taxa")
        _require(
            type(names) is list
            and len(names) == 30
            and all(type(name) is str and name for name in names)
            and len(set(names)) == 30,
            "regional taxon axis differs",
        )
        taxa = names if taxa is None else taxa
        _require(names == taxa, "regional axes disagree")
        native, fraction, direction = (
            row.get(name)
            for name in (
                "native_cover_percent",
                "fractional_cover",
                "normalized_start_direction",
            )
        )
        _require(
            all(
                type(vector) is list
                and len(vector) == 30
                and all(_finite(x) and x >= 0 for x in vector)
                for vector in (native, fraction, direction)
            ),
            "finite regional vectors required",
        )
        assert (
            isinstance(native, list)
            and isinstance(fraction, list)
            and isinstance(direction, list)
        )
        _require(
            all(abs(x * 1000 - round(x * 1000)) <= 1e-8 for x in native),
            "native percent precision changed",
        )
        native_sum, fraction_sum = (
            row.get("native_cover_percent_sum"),
            row.get("fractional_cover_sum"),
        )
        _require(
            _finite(native_sum) and _finite(fraction_sum),
            "positive raw regional mass required",
        )
        assert isinstance(native_sum, (int, float)) and isinstance(
            fraction_sum, (int, float)
        )
        _require(
            native_sum > 0 and fraction_sum > 0, "positive raw regional mass required"
        )
        _require(
            math.isclose(sum(native), native_sum, rel_tol=1e-12, abs_tol=1e-12)
            and math.isclose(sum(fraction), fraction_sum, rel_tol=1e-12, abs_tol=1e-12),
            "raw regional mass was rewritten",
        )
        _require(
            all(
                abs(b - a / 100) <= 1e-15 for a, b in zip(native, fraction, strict=True)
            ),
            "percentage/fraction conversion differs",
        )
        _require(
            all(
                abs(b - a / fraction_sum) <= 1e-15
                for a, b in zip(fraction, direction, strict=True)
            )
            and abs(sum(direction) - 1) <= 1e-12,
            "regional start direction differs from raw mass",
        )
        directions[item] = direction
    return directions


def validate_lifecycle(
    report: dict[str, Any], ledger: list[dict[str, Any]], baseline: dict[str, Any]
) -> None:
    """Check the complete denominator and preserve every actual numerical refusal."""
    _require(
        report.get("schema_version") == "author-love-fixed-start-diagnostic.v1",
        "report schema differs",
    )
    for key in (
        "source_manifest_sha256",
        "experiment_sha256",
        "fold_id",
        "withheld_site",
        "regional_anchor",
    ):
        _require(
            report.get(key) == baseline.get(key), "baseline source identity differs"
        )
    protocol = _object(report.get("optimizer_contract"))
    for key, value in {
        "starts_per_ring": 32,
        "rings_per_item": 2,
        "total_new_attempts": 128,
        "maxiter_per_attempt": 300,
        "max_objective_evaluations_per_attempt": 16000,
        "ftol": 1e-8,
        "single_process": True,
        "numerical_threads": 1,
    }.items():
        _require(
            type(protocol.get(key)) is type(value) and protocol[key] == value,
            "optimizer protocol differs",
        )
    attempts, summaries = report.get("attempts"), report.get("ring_selections")
    _require(
        type(attempts) is list and len(attempts) == 128 and len(ledger) == 256,
        "128 attempts and256 lifecycle rows required",
    )
    _require(
        type(summaries) is list and len(summaries) == 4, "four ring summaries required"
    )
    assert isinstance(attempts, list) and isinstance(summaries, list)
    directions = validate_regional_handoffs(report)
    prior = {row["item_id"]: row for row in baseline["items"]}
    completed = 0
    common_fields = (
        "item_id",
        "request_sha256",
        "ring_index",
        "outer_m",
        "start_id",
        "start",
    )
    for group_index, (item, ring) in enumerate(
        (item, ring) for item in ITEMS for ring in range(2)
    ):
        group = attempts[32 * group_index : 32 * (group_index + 1)]
        successes = []
        reference = prior[item]["rings"][ring]
        for row, start_id in zip(group, STARTS, strict=True):
            row = _object(row)
            _require(
                row.get("item_id") == item
                and row.get("request_sha256") == prior[item]["request_sha256"]
                and type(row.get("ring_index")) is int
                and row["ring_index"] == ring
                and row.get("start_id") == start_id
                and row.get("outer_m") == reference["outer_m"],
                "ordered attempt identity differs",
            )
            start = row.get("start")
            _require(
                type(start) is list
                and len(start) == 30
                and all(_finite(x) and x > 0 for x in start)
                and abs(sum(start) - 1) <= 1e-12,
                "positive closed thirty-taxon start differs",
            )
            assert isinstance(start, list)
            if start_id == "regional-cover-half-uniform":
                _require(
                    all(
                        abs(x - (1 / 60 + 0.5 * value)) <= 1e-15
                        for x, value in zip(start, directions[item], strict=True)
                    ),
                    "regional start used changed background or mass",
                )
            if start_id.startswith("taxon-"):
                index = int(start_id.split("-")[1])
                _require(
                    all(
                        abs(x - (1 / 60 + (0.5 if i == index else 0))) <= 1e-15
                        for i, x in enumerate(start)
                    ),
                    "declared taxon-axis start differs",
                )
            _require(
                type(row.get("accepted")) is bool
                and _finite(row.get("elapsed_seconds"))
                and row["elapsed_seconds"] >= 0,
                "attempt acceptance or timing differs",
            )
            calls = _object(row.get("observed_calls"))
            _require(
                set(calls) == {"objective", "jacobian"}
                and all(type(x) is int and x >= 0 for x in calls.values())
                and calls["objective"] <= 16001,
                "objective accounting differs",
            )
            result = row.get("result")
            if result is not None:
                result = _object(result)
                _require(
                    "refusal" not in row
                    and type(result.get("success")) is bool
                    and type(result.get("nfev")) is int
                    and result["nfev"] >= 1
                    and type(result.get("certification_nfev")) is int
                    and result["certification_nfev"] == 1
                    and calls["objective"] == result["nfev"] + 1,
                    "host certification or search accounting differs",
                )
                cover = result.get("x")
                feasible = (
                    type(cover) is list
                    and len(cover) == 30
                    and all(_finite(x) and 0 <= x <= 1 for x in cover)
                    and abs(sum(cover) - 1) <= 1e-6
                )
                accepted = result["success"] and _finite(result.get("fun")) and feasible
                _require(
                    row["accepted"] is accepted,
                    "host refusal or feasibility was relabeled",
                )
                if accepted:
                    successes.append((result["fun"], start_id))
            else:
                _require(
                    row["accepted"] is False
                    and type(row.get("refusal_type")) is str
                    and bool(row["refusal_type"])
                    and type(row.get("refusal")) is str
                    and bool(row["refusal"]),
                    "numerical refusal was lost",
                )
            began, ended = ledger[2 * completed : 2 * completed + 2]
            _require(
                began
                == {
                    "event": "attempt_started",
                    **{key: row[key] for key in common_fields},
                }
                and ended == {"event": "attempt_completed", **row},
                "ledger lifecycle differs from report",
            )
            completed += 1
        summary = _object(summaries[group_index])
        selected = list(min(successes)) if successes else None
        _require(
            summary.get("item_id") == item
            and summary.get("ring_index") == ring
            and summary.get("attempted") == 32
            and summary.get("accepted") == len(successes)
            and summary.get("selected") == selected
            and summary.get("baseline_analytic") == reference["analytic"]
            and summary.get("baseline_reused_without_rerun") is True,
            "minimum accepted objective or original refusal differs",
        )
        delta = selected[0] - float(reference["analytic"]["fun"]) if selected else None
        _require(
            summary.get("selected_objective_delta_vs_refused_uniform") == delta,
            "baseline comparison differs",
        )
    _require(completed == 128, "incomplete attempt population")
