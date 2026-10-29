"""Validate complete source-bound BECKHAM training and prediction/scoring handoffs."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from ...contracts import ReportRebuildError
from .fixed_starts import STARTS, validate_lifecycle
from .withheld_pollen import (
    TARGET,
    _close,
    _composition,
    _number,
    _object,
    _require,
    validate_pollen_scores,
    validate_prediction_freeze,
)


def _decode(raw: bytes) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            _require(key not in value, "duplicate JSON key")
            value[key] = item
        return value

    def nonfinite(_value: str) -> None:
        raise ReportRebuildError("BECKHAM fixed-start nonfinite JSON token")

    return json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)


def _canonical_sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def _same_pin(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Physical paths may move after publication; content identities remain exact."""
    return (
        left.get("sha256") == right.get("sha256")
        and type(left.get("bytes")) is int
        and left.get("bytes") == right.get("bytes")
    )


def _attempts(
    rows: list[dict[str, Any]],
    events: list[dict[str, Any]],
    expected_items: list[str],
) -> None:
    expected = [
        (item, ring, start)
        for item in expected_items
        for ring in range(2)
        for start in STARTS
    ]
    _require(
        len(rows) == len(expected) and len(events) == len(rows) * 2,
        "new attempt denominator differs",
    )
    for index, (row, key) in enumerate(zip(rows, expected, strict=True)):
        _require(
            (row.get("item_id"), row.get("ring_index"), row.get("start_id")) == key,
            "new attempt ordering or population differs",
        )
        begin = {
            name: row[name]
            for name in (
                "item_id",
                "request_sha256",
                "ring_index",
                "outer_m",
                "start_id",
                "start",
                "execution",
            )
        }
        _require(
            row.get("execution") == "new"
            and events[2 * index] == {"event": "attempt_started", **begin}
            and events[2 * index + 1] == {"event": "attempt_completed", **row},
            "new lifecycle row differs",
        )
        start = row.get("start")
        _require(
            type(start) is list
            and len(start) == 30
            and all(_number(x) and x > 0 for x in start)
            and abs(math.fsum(start) - 1) <= 1e-12,
            "positive closed thirty-taxon start required",
        )
        assert isinstance(start, list)
        if key[2].startswith("taxon-"):
            axis = int(key[2].split("-")[1])
            _require(
                all(
                    x == 0.5 / 30 + (0.5 if j == axis else 0)
                    for j, x in enumerate(start)
                ),
                "fixed taxon-axis start differs",
            )
        calls = _object(row.get("observed_calls"))
        _require(
            set(calls) == {"objective", "jacobian"}
            and all(type(x) is int and x >= 0 for x in calls.values())
            and calls["objective"] <= 16001
            and calls["jacobian"] <= 300,
            "objective or gradient call budget differs",
        )
        result = row.get("result")
        if result is None:
            _require(
                row.get("accepted") is False
                and row.get("refusal_type") in {"ValueError", "ValidationError"}
                and type(row.get("refusal")) is str
                and row["refusal"],
                "numerical refusal lost",
            )
            continue
        result = _object(result)
        x = result.get("x")
        _require(
            type(x) is list
            and len(x) == 30
            and all(_number(v) or v in ("NaN", "Infinity", "-Infinity") for v in x)
            and (
                _number(result.get("fun"))
                or result.get("fun") in ("NaN", "Infinity", "-Infinity")
            ),
            "explicit solver values required",
        )
        assert isinstance(x, list)
        accepted = (
            result.get("success") is True
            and _number(result.get("fun"))
            and all(_number(v) for v in x)
            and all(0 <= v <= 1 for v in x)
            and abs(math.fsum(x) - 1) <= 1e-6
        )
        _require(
            type(row.get("accepted")) is bool
            and row["accepted"] is accepted
            and type(result.get("success")) is bool,
            "host feasibility or convergence was overridden",
        )
        _require(
            type(result.get("nit")) is int
            and 0 <= result["nit"] <= 300
            and type(result.get("nfev")) is int
            and 1 <= result["nfev"] <= 16000
            and result.get("certification_nfev") == 1
            and calls["objective"] == result["nfev"] + 1,
            "solver or final certification budget differs",
        )


def _training(
    training: dict[str, Any], prior: dict[str, Any], protocol: dict[str, Any]
) -> dict[str, Any]:
    items = protocol["local_predictors"]
    rows = training["training"]
    _require(
        len(items) == len(set(items)) == 13
        and len(rows) == 13
        and [row["item_id"] for row in rows] == items,
        "exact thirteen predictor population required",
    )
    attempts = prior["attempts"] + training["new_attempts"]
    regional = None
    accepted_total = 0
    failures = []
    for row in rows:
        _require(len(row["selections"]) == 2, "two selected rings required")
        regional = row["regional_cover"] if regional is None else regional
        _require(
            row["regional_cover"]
            == regional
            == prior["regional_handoffs"][0]["fractional_cover"],
            "common raw regional handoff differs",
        )
        for ring, chosen in enumerate(row["selections"]):
            candidates = [
                attempt
                for attempt in attempts
                if attempt["item_id"] == row["item_id"]
                and attempt["ring_index"] == ring
            ]
            _require(
                len(candidates) == 32
                and all(
                    attempt["request_sha256"] == row["request_sha256"]
                    for attempt in candidates
                ),
                "training request or ring population differs",
            )
            declared = {attempt["start_id"]: attempt["start"] for attempt in candidates}
            _require(
                set(declared) == set(STARTS)
                and all(
                    _close(value, 0.5 / 30 + 0.5 * raw / math.fsum(regional))
                    for value, raw in zip(
                        declared["regional-cover-half-uniform"], regional, strict=True
                    )
                ),
                "regional fixed-start direction differs",
            )
            valid = [attempt for attempt in candidates if attempt["accepted"]]
            if not valid:
                _require(chosen is None, "a refused ring cannot supply prediction")
                failures.append(
                    {
                        "item_id": row["item_id"],
                        "ring_index": ring,
                        "reason": "all_declared_starts_refused",
                    }
                )
                continue
            _require(chosen is not None, "an accepted ring selection is missing")
            selected = min(
                valid,
                key=lambda attempt: (attempt["result"]["fun"], attempt["start_id"]),
            )
            _require(
                chosen["item_id"] == row["item_id"]
                and chosen["request_sha256"] == row["request_sha256"]
                and chosen["ring_index"] == ring
                and chosen["attempted"] == 32
                and chosen["accepted"] == len(valid)
                and chosen["refused"] == 32 - len(valid),
                "selected ring accounting differs",
            )
            _require(
                chosen["selected_start_id"] == selected["start_id"]
                and chosen["selected_objective"] == selected["result"]["fun"]
                and chosen["selected_attempt_sha256"] == _canonical_sha(selected),
                "selected attempt is not the certified minimum",
            )
            execution = (
                "reused"
                if row["item_id"] in ("author:CUTHILL2", "author:LONGBREACH")
                else "new"
            )
            _require(
                chosen["execution"] == execution, "reused attempt relabeled as new"
            )
            x = selected["result"]["x"]
            _require(
                chosen["raw_x"] == x and _close(chosen["raw_sum"], math.fsum(x)),
                "raw optimizer vector was rewritten",
            )
            composition = _composition(chosen["composition"])
            axis = prior["regional_handoffs"][0]["taxa"]
            _require(
                set(composition) == set(axis)
                and all(
                    _close(composition[taxon], raw / chosen["raw_sum"])
                    for taxon, raw in zip(axis, x, strict=True)
                )
                and _close(chosen["composition_sum"], math.fsum(composition.values())),
                "declared model composition transform differs",
            )
            accepted_total += len(valid)
    _require(
        type(regional) is list
        and len(regional) == 30
        and all(_number(x) and x >= 0 for x in regional),
        "raw regional vector differs",
    )
    _require(training["failures"] == failures, "whole-fold numerical refusals differ")
    return {
        "attempts": 832,
        "new_attempts": 704,
        "reused_attempts": 128,
        "accepted": accepted_total,
        "refused": 832 - accepted_total,
        "training_predictors": 13,
        "rings": 26,
        "failures": failures,
    }


def _validate_saved_outputs(
    bodies: dict[str, bytes], pins: dict[str, dict[str, Any]], protocol: dict[str, Any]
) -> dict[str, Any]:
    """Authenticate saved results; decode the target only after prediction admission."""
    base_roles = {
        "report",
        "training",
        "trials",
        "prior_report",
        "prior_trials",
        "baseline",
    }
    success_roles = {"prediction_freeze", "outcome_access", "outcome"}
    _require(
        set(bodies) == set(pins)
        and set(bodies) in (base_roles, base_roles | success_roles),
        "finite saved-output roles differ",
    )
    for role in bodies:
        validate_prediction_freeze(bodies[role], pins[role])
    report = _object(_decode(bodies["report"]))
    training = _object(_decode(bodies["training"]))
    prior = _object(_decode(bodies["prior_report"]))
    baseline = _object(_decode(bodies["baseline"]))
    prior_events = [
        _object(_decode(line)) for line in bodies["prior_trials"].splitlines()
    ]
    validate_lifecycle(prior, prior_events, baseline)
    _require(
        _same_pin(protocol["prior_evidence"]["report"], pins["prior_report"])
        and _same_pin(protocol["prior_evidence"]["trials"], pins["prior_trials"])
        and prior["fold_id"] == protocol["fold_id"]
        and prior["regional_anchor"] == protocol["regional_anchor"]
        and prior["withheld_site"] == TARGET,
        "original source or fold reuse binding differs",
    )
    events = [_object(_decode(line)) for line in bodies["trials"].splitlines()]
    items = protocol["local_predictors"]
    _attempts(
        training["new_attempts"],
        events,
        [
            item
            for item in items
            if item not in ("author:CUTHILL2", "author:LONGBREACH")
        ],
    )
    _require(
        report.get("schema_version") == "author-love-development-fold.v1"
        and report.get("scientific_acceptance") == "not_evaluated",
        "scientific scope differs",
    )
    for value in (report, training):
        _require(
            value.get("reused_attempts") == 128 and value.get("total_attempts") == 832,
            "whole fold must retain all attempts",
        )
        _require(
            value["fold"]["fold_id"] == protocol["fold_id"]
            and value["fold"]["train_record_ids"] == protocol["training_records"]
            and value["fold"]["test_record_ids"] == [TARGET],
            "original grouped fold differs",
        )
    _require(
        report.get("training_predictors") == 13
        and report.get("new_attempts") == training.get("new_attempt_count") == 704
        and _same_pin(report["training"], pins["training"]),
        "new or reused accounting differs",
    )
    for role, key in (
        ("prior_report", "reused_report"),
        ("prior_trials", "reused_trials"),
    ):
        _require(
            _same_pin(training[key], pins[role]), "original reused source bytes differ"
        )
    result = _training(training, prior, protocol)
    _require(
        report["failures"] == result["failures"], "reported training refusals differ"
    )
    if result["failures"]:
        _require(
            set(bodies) == base_roles
            and report["predictions"] == []
            and report["scores"] == []
            and report["target_opened_for_scoring"] is False
            and "prediction_freeze" not in report,
            "refused fold must not access target or supply prediction",
        )
        return {
            **result,
            "new_lifecycle_events": len(events),
            "reused_lifecycle_events": len(prior_events),
            "status": "training_reconstruction_refused",
        }
    _require(
        set(bodies) == base_roles | success_roles,
        "complete prediction/scoring evidence required",
    )
    freeze = _object(_decode(bodies["prediction_freeze"]))
    access = _object(_decode(bodies["outcome_access"]))
    _require(
        freeze["fold"] == report["fold"]
        and _same_pin(freeze["training"], pins["training"])
        and freeze["predictions"] == report["predictions"]
        and _same_pin(report["prediction_freeze"], pins["prediction_freeze"]),
        "scoring did not use exact frozen prediction",
    )
    for prediction in report["predictions"]:
        manifest = _object(prediction["prediction_manifest"])
        _require(
            prediction["prediction_manifest_sha256"] == _canonical_sha(manifest)
            and manifest["fold"] == report["fold"]
            and manifest["pollen_fraction"] == prediction["pollen_fraction"]
            and manifest["vegetation_fraction"] == prediction["vegetation_fraction"]
            and manifest["spatial_method"] == prediction["baseline"],
            "prediction content or manifest differs",
        )
        _require(
            manifest["experiment"] == "all_target_pollen_withheld"
            and manifest["uncertainty_status"]
            == "deterministic_point_prediction_no_predictive_intervals"
            and manifest["scientific_acceptance"] == "not_evaluated_by_prediction"
            and not (
                set(manifest["allowed_input_closure"])
                & {TARGET, *report["fold"]["test_group_ids"]}
            ),
            "prediction contains withheld ancestry or excess scientific claim",
        )
    _require(
        access.get("record_id") == TARGET
        and _same_pin(access["prediction_freeze"], pins["prediction_freeze"])
        and access.get("ordering")
        == "exclusive_prediction_freeze_reopened_before_target_decode"
        and access["outcome"]["sha256"] == pins["outcome"]["sha256"],
        "saved outcome access order or source differs",
    )
    _require(
        _same_pin(protocol["outcome"], pins["outcome"]),
        "original target source pin differs",
    )
    # Opening the saved target is deliberately below all prediction/freeze checks.
    outcome = _object(_decode(bodies["outcome"]))
    sample = _object(outcome["sample"])
    taxa, counts = outcome["taxa"], sample["counts"]
    _require(
        outcome.get("data_kind") == "source_observations"
        and sample.get("site_id") == "BECKHAM"
        and len(taxa) == len(set(taxa)) == len(counts) == 30,
        "source target or taxon denominator differs",
    )
    _require(
        report.get("target_opened_for_scoring") is True
        and all(row["bin_id"] == sample["bin_id"] for row in report["predictions"]),
        "target scoring phase or bin differs",
    )
    metrics = validate_pollen_scores(
        report["predictions"], report["scores"], dict(zip(taxa, counts, strict=True))
    )
    _require(
        report.get("observed_total_count") == metrics["observed_total_count"],
        "reported target denominator differs",
    )
    return {
        **result,
        **metrics,
        "new_lifecycle_events": len(events),
        "reused_lifecycle_events": len(prior_events),
        "prediction_freeze_sha256": pins["prediction_freeze"]["sha256"],
        "scope": "Retrospective descriptive pollen development diagnostic; no full acceptance, untouched cohort, vegetation truth, uncertainty or historical parity admission.",
    }


def validate_saved_outputs(
    bodies: dict[str, bytes], pins: dict[str, dict[str, Any]], protocol: dict[str, Any]
) -> dict[str, Any]:
    """Refuse malformed saved evidence at the scientific capture boundary."""
    try:
        return _validate_saved_outputs(bodies, pins, protocol)
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        raise ReportRebuildError(
            "BECKHAM fixed-start malformed saved evidence: " + str(error)
        ) from error
