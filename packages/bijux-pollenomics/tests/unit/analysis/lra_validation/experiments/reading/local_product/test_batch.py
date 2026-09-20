"""Scientific failures remain bound to their raw batch operation evidence."""

from __future__ import annotations

import pytest

from bijux_pollenomics.analysis.lra_validation import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.contracts import canonical_json
from bijux_pollenomics.analysis.lra_validation.experiments.reading.local_product.batch import (
    validate_failure_batch_evidence,
)


@pytest.mark.parametrize(
    "status,raw_status,projection_interrupted,projection_error",
    [
        ("refused", "failed", False, None),
        (
            "refused",
            "completed",
            False,
            {"reason_code": "projection_refused", "detail": "invalid projection"},
        ),
        ("not_run", "completed", True, None),
        ("not_run", "completed", False, None),
    ],
)
def test_attempted_failure_binds_raw_operation_terminal(
    status: str,
    raw_status: str,
    projection_interrupted: bool,
    projection_error: dict[str, str] | None,
) -> None:
    record = "p1"
    fold = "fold:p1"
    operation: dict[str, object] = {
        "item_status": raw_status,
        "error": {"reason_code": "raw_failed"} if raw_status == "failed" else None,
    }
    detail: dict[str, object] = {
        "batch_item_status": raw_status,
        "operational_error": operation["error"],
        "projection_interrupted": projection_interrupted,
    }
    if projection_error is not None:
        detail["projection_error"] = projection_error
    failure = {
        "fold_id": fold,
        "record_ids": [record],
        "status": status,
        "reason_code": (
            projection_error["reason_code"]
            if projection_error is not None
            else "experiment_interrupted"
            if status == "not_run"
            else "local_reconstruction_incomplete"
        ),
        "detail": canonical_json(detail),
        "batch_item_id": record,
    }
    validate_failure_batch_evidence(
        [failure],
        {fold: {"test_record_ids": [record]}},
        {record: {}},
        {record: operation},
    )


@pytest.mark.parametrize("mutation", ["owner", "raw_status", "detail", "projection"])
def test_attempted_failure_batch_contradictions_refuse(mutation: str) -> None:
    record = "p1"
    fold = "fold:p1"
    detail = {
        "batch_item_status": "failed",
        "operational_error": {"reason_code": "raw_failed"},
        "projection_interrupted": False,
    }
    failure = {
        "fold_id": fold,
        "record_ids": [record],
        "status": "refused",
        "reason_code": "local_reconstruction_incomplete",
        "detail": canonical_json(detail),
        "batch_item_id": "other" if mutation == "owner" else record,
    }
    operation: dict[str, object] = {
        "item_status": "refused" if mutation == "raw_status" else "failed",
        "error": {"reason_code": "raw_failed"},
    }
    if mutation == "detail":
        failure["detail"] = "not-json"
    elif mutation == "projection":
        detail["projection_interrupted"] = True
        failure["detail"] = canonical_json(detail)
    with pytest.raises(ValidationRefusal):
        validate_failure_batch_evidence(
            [failure],
            {fold: {"test_record_ids": [record]}},
            {record: {}},
            {record: operation},
        )
