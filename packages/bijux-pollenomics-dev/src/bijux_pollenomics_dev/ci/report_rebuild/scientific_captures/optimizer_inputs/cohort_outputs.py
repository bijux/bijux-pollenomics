"""Independently validate saved homogeneous fifteen-fold fixed-start evidence."""

from __future__ import annotations

from typing import Any

from ...contracts import ReportRebuildError
from .cohort_predictions import validate_frozen, validate_scores
from .cohort_training import COUNTS, validate_pool
from .withheld_fold import _decode, _same_pin
from .withheld_pollen import _object, _require, validate_prediction_freeze

PRIOR_REVIEW = "c499552ead9141a34f8e70a0a6a3c3f1e6fad59841fe79c35e4348cbe9aa1d5f"
PRODUCT_ROLES = {"report", "training", "trials", "prediction_freeze", "outcome_access"}


def _validate(
    bodies: dict[str, bytes],
    pins: dict[str, dict[str, Any]],
    protocol: dict[str, Any],
    inputs: dict[str, bytes],
) -> dict[str, Any]:
    prior = protocol["prior_evidence"]
    _require(
        protocol["schema_version"] == "author-love-cohort-development-protocol.v1"
        and protocol["counts"] == COUNTS
        and len(prior) == 8,
        "finite scientific protocol differs",
    )
    _require(
        set(bodies) == set(pins) == PRODUCT_ROLES | set(prior),
        "finite saved evidence roles differ",
    )
    for role, raw in bodies.items():
        validate_prediction_freeze(raw, pins[role])
    for role, row in prior.items():
        _require(_same_pin(row, pins[role]), "prior immutable source identity differs")
    declared = {row["path"]: row for row in protocol["inputs"]}
    _require(
        len(declared) == len(protocol["inputs"]) == 37 and set(inputs) == set(declared),
        "exact37 original scientific inputs required",
    )
    for name, raw in inputs.items():
        validate_prediction_freeze(raw, declared[name])
    authority = _object(_decode(bodies["development_receipt"]))
    _require(
        authority["original_receipts"]["independent_review"]["sha256"] == PRIOR_REVIEW
        and authority["execution"]["native_exit"]
        == authority["execution"]["common_exit"]
        == authority["execution"]["outer_exit"]
        == 0
        and authority["independent_semantics"]["attempts"] == 832
        and authority["independent_semantics"]["new_attempts"] == 704
        and authority["independent_semantics"]["reused_attempts"] == 128
        and authority["independent_semantics"]["failures"] == [],
        "original independently admitted832 authority required",
    )
    for role in ("training", "trials"):
        _require(
            _same_pin(
                authority["products"][role]["original_reference"],
                prior["development_" + role],
            ),
            "832 source authority does not bind reused body",
        )
    previous = _object(_decode(bodies["development_training"]))
    first = _object(_decode(bodies["start_report"]))
    _require(
        _same_pin(previous["reused_report"], prior["start_report"])
        and _same_pin(previous["reused_trials"], prior["start_trials"]),
        "original128 reuse source identity differs",
    )
    report = _object(_decode(bodies["report"]))
    training = _object(_decode(bodies["training"]))
    _require(
        report["schema_version"] == "author-love-cohort-development.v1"
        and report["profile"]
        == training.get("profile", protocol["profile"])
        == protocol["profile"]
        and report["counts"] == COUNTS
        and report["scientific_acceptance"] == "not_evaluated"
        and _same_pin(report["training"], pins["training"]),
        "saved cohort scope or training content differs",
    )
    experiment = _object(_decode(inputs["experiment.json"]))
    _require(
        len(experiment["sites"]) == 15
        and len({row["record_id"] for row in experiment["sites"]}) == 15
        and len({row["site_id"] for row in experiment["sites"]}) == 15
        and all(not row["identity_keys"] for row in experiment["sites"]),
        "exact original fifteen single-site groups required",
    )
    for site in experiment["sites"]:
        for role in ("raw", "geometry"):
            row = site[role]
            _require(
                row["path"] in declared
                and declared[row["path"]]["sha256"] == row["sha256"],
                "source catalogue differs from authenticated original inputs",
            )
    events = [_object(_decode(line)) for line in bodies["trials"].splitlines()]
    result = validate_pool(training, events, previous, first, protocol, experiment)
    frozen = _object(_decode(bodies["prediction_freeze"]))
    access = [_object(_decode(line)) for line in bodies["outcome_access"].splitlines()]
    successful = validate_frozen(report, frozen, access, pins, result, experiment)
    # No scoring raw body is decoded until all45 slots and access records pass.
    scores = validate_scores(successful, report, experiment, inputs)
    return {
        "counts": COUNTS,
        "accepted": result["accepted"],
        "refused": result["refused"],
        "refused_rings": result["refused_rings"],
        "new_lifecycle_events": len(events),
        "reused_attempts": 832,
        "predicted_folds": len(successful),
        "refused_folds": len(report["failures"]),
        "failures": report["failures"],
        "prediction_freeze_sha256": pins["prediction_freeze"]["sha256"],
        "scores": scores,
        "scope": "Homogeneous retrospective prior-exposed fixed-start pollen development diagnostic. Every fold excludes its own target from training; source pollen is legitimately training in other folds. Original uniform scores remain separate; no global-unread, independent vegetation, uncertainty, global-optimum, R-parity or release admission.",
    }


def validate_saved_outputs(
    bodies: dict[str, bytes],
    pins: dict[str, dict[str, Any]],
    protocol: dict[str, Any],
    inputs: dict[str, bytes],
) -> dict[str, Any]:
    """Refuse malformed saved evidence without rerunning any numerical producer."""
    try:
        return _validate(bodies, pins, protocol, inputs)
    except (KeyError, TypeError, ValueError, OverflowError, StopIteration) as error:
        raise ReportRebuildError(
            "LOVE cohort malformed saved evidence: " + str(error)
        ) from error
