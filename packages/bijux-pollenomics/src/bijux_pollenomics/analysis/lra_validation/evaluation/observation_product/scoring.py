"""Evaluate only a fully parent-bound observed six-cell product."""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from typing import Any, Literal, cast

from ...contracts import canonical_json, manifest_sha256
from ..contracts import EvaluationResult, digest, refuse
from ..scoring import _evaluate_authenticated_final
from .join import (
    ObservedSixCellEvaluationProduct,
    reopen_observed_six_cell_product,
)

OBSERVED_SIX_CELL_RESULT_PROFILE = "pollenomics-observed-six-cell-evaluation-result.v1"
ResultStatus = Literal["passed", "failed", "ineligible"]
_RESULT_FACTORY_TOKEN = object()


@dataclass(frozen=True)
class ProtocolEvaluation:
    """One protocol result retained under its exact policy and scope parents."""

    protocol_id: str
    result: EvaluationResult


def _key(value: object) -> tuple[str, str, str, str, str]:
    row = cast(Any, value).row
    return row.fold_id, row.record_id, row.experiment, row.target, row.model_id


def _retain_source_terminals(
    generic: EvaluationResult, attachments: tuple[object, ...]
) -> EvaluationResult:
    """Refine only unavailable-source labels; generic scoring arithmetic stays exact."""
    try:
        payload = json.loads(generic.canonical_result_json)
    except (json.JSONDecodeError, TypeError) as exc:
        refuse(f"Malformed generic protocol result: {exc}")
    statuses = payload.get("row_statuses") if isinstance(payload, dict) else None
    if not isinstance(statuses, list) or any(
        not isinstance(value, dict) for value in statuses
    ):
        refuse("Generic protocol result lacks its exact row-status ledger")
    by_key: dict[tuple[str, str, str, str, str], dict[str, object]] = {}
    for raw in cast(list[dict[str, object]], statuses):
        raw_key = raw.get("key")
        if (
            not isinstance(raw_key, list)
            or len(raw_key) != 5
            or any(not isinstance(value, str) for value in raw_key)
        ):
            refuse("Generic protocol result has a malformed row-status key")
        key = cast(tuple[str, str, str, str, str], tuple(raw_key))
        if key in by_key:
            refuse("Generic protocol result duplicates a row-status key")
        by_key[key] = raw
    expected = {_key(value) for value in attachments}
    if set(by_key) != expected or len(expected) != len(attachments):
        refuse("Generic protocol result and joined row denominator differ")
    for value in attachments:
        attachment = cast(Any, value)
        if attachment.observation_status not in {"missing", "refused"}:
            continue
        if attachment.row.status == "prediction_failed":
            if by_key[_key(attachment)].get("status") != "prediction_failed":
                refuse("Prediction failure lost precedence over source status")
            continue
        if by_key[_key(attachment)].get("status") != "missing_observation":
            refuse("Unavailable source differs from generic missing-observation status")
        by_key[_key(attachment)]["status"] = f"{attachment.observation_status}_source"
    canonical = canonical_json(payload)
    return EvaluationResult(canonical, manifest_sha256(payload), generic.status)


def _evaluate_product(
    product: ObservedSixCellEvaluationProduct,
) -> tuple[dict[str, object], tuple[ProtocolEvaluation, ...]]:
    reopened = reopen_observed_six_cell_product(
        product.canonical_product_json,
        product.product_sha256,
        prediction_product=product.prediction_product,
        authenticated_observations=product.observation_product,
    )
    access_started = reopened.observation_product.completion_receipt.start_receipt.access_started_at_utc
    protocol_results: list[ProtocolEvaluation] = []
    for protocol in reopened.prediction_product.protocols:
        attachments = tuple(
            value
            for value in reopened.attachments
            if value.protocol_id == protocol.protocol_id
        )
        if not attachments:
            refuse("Observed release result omitted a bound protocol")
        access_bound_policy = replace(
            protocol.policy, first_test_access_at=access_started
        )
        generic = _evaluate_authenticated_final(
            access_bound_policy,
            scope=protocol.scope,
            rows=tuple(value.row for value in attachments),
        )
        protocol_results.append(
            ProtocolEvaluation(
                protocol.protocol_id,
                _retain_source_terminals(
                    generic, cast(tuple[object, ...], attachments)
                ),
            )
        )
    statuses = [value.result.status for value in protocol_results]
    status: ResultStatus = (
        "ineligible"
        if "ineligible" in statuses
        else "failed"
        if "failed" in statuses
        else "passed"
    )
    observations = reopened.observation_product
    completion = observations.completion_receipt
    start = completion.start_receipt
    payload: dict[str, object] = {
        "schema_version": OBSERVED_SIX_CELL_RESULT_PROFILE,
        "status": status,
        "observed_six_cell_product_sha256": reopened.product_sha256,
        "prediction_product_sha256": reopened.prediction_product.product_sha256,
        "authenticated_observation_product_sha256": observations.product_sha256,
        "source_completion_receipt_sha256": completion.receipt_sha256,
        "access_start_receipt_sha256": start.receipt_sha256,
        "access_plan_sha256": start.plan.plan_sha256,
        "release_admission_sha256": reopened.prediction_product.release_admission_sha256,
        "scope_sha256": reopened.prediction_product.scope_sha256,
        "protocol_results": [
            {
                "protocol_id": value.protocol_id,
                "policy_sha256": next(
                    protocol.policy.policy_sha256
                    for protocol in reopened.prediction_product.protocols
                    if protocol.protocol_id == value.protocol_id
                ),
                "result_sha256": value.result.result_sha256,
                "canonical_result_json": value.result.canonical_result_json,
                "status": value.result.status,
            }
            for value in protocol_results
        ],
        "review_authenticity_verified": False,
        "scientific_approval_granted": False,
        "empirical_evaluation_performed": True,
    }
    return payload, tuple(protocol_results)


@dataclass(frozen=True, init=False)
class ObservedSixCellEvaluationResult:
    """Canonical two-protocol result; it does not authenticate scientific review."""

    canonical_result_json: str
    result_sha256: str
    status: ResultStatus
    observed_product: ObservedSixCellEvaluationProduct
    protocol_results: tuple[ProtocolEvaluation, ...]

    def __init__(
        self,
        canonical_result_json: str,
        result_sha256: str,
        observed_product: ObservedSixCellEvaluationProduct,
        *,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _RESULT_FACTORY_TOKEN:
            refuse("Observed six-cell results require the governed scorer")
        expected, protocol_results = _evaluate_product(observed_product)
        try:
            loaded = json.loads(canonical_result_json)
        except (json.JSONDecodeError, TypeError) as exc:
            refuse(f"Malformed observed six-cell result: {exc}")
        if (
            not isinstance(loaded, dict)
            or canonical_json(loaded) != canonical_result_json
            or manifest_sha256(loaded) != digest(result_sha256)
            or canonical_json(loaded) != canonical_json(expected)
        ):
            refuse("Observed six-cell result bytes or parents differ")
        object.__setattr__(self, "canonical_result_json", canonical_result_json)
        object.__setattr__(self, "result_sha256", result_sha256)
        object.__setattr__(self, "status", cast(ResultStatus, loaded["status"]))
        object.__setattr__(self, "observed_product", observed_product)
        object.__setattr__(self, "protocol_results", protocol_results)


def evaluate_observed_six_cell_product(
    product: ObservedSixCellEvaluationProduct,
) -> ObservedSixCellEvaluationResult:
    """Score a typed joined product; reject raw rows before inspecting them."""
    if type(product) is not ObservedSixCellEvaluationProduct:
        refuse("Release scoring requires an exact observed six-cell product")
    payload, _ = _evaluate_product(product)
    canonical = canonical_json(payload)
    return ObservedSixCellEvaluationResult(
        canonical,
        manifest_sha256(payload),
        product,
        _factory_token=_RESULT_FACTORY_TOKEN,
    )


def reopen_observed_six_cell_evaluation_result(
    canonical_result_json: str,
    result_sha256: str,
    *,
    observed_product: ObservedSixCellEvaluationProduct,
) -> ObservedSixCellEvaluationResult:
    """Replay a persisted result against its exact joined parent."""
    if type(observed_product) is not ObservedSixCellEvaluationProduct:
        refuse("Result reopening requires an exact observed six-cell product")
    return ObservedSixCellEvaluationResult(
        canonical_result_json,
        result_sha256,
        observed_product,
        _factory_token=_RESULT_FACTORY_TOKEN,
    )
