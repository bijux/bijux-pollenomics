"""Retained batch-request and operation evidence for grouped-local products."""

from __future__ import annotations

import json

from .....lra.batches.models import LRABatchItem
from ....contracts import ValidationRefusal, canonical_json, manifest_sha256
from ...configuration import identity, object_list, object_mapping
from ...outputs import ExperimentProduct, read_member
from .evidence import digest

_ATTEMPT_FIELDS = {
    "schema_version",
    "event",
    "completion_receipt",
    "batch_sha256",
    "limits",
    "numerical_threads_per_worker",
    "input_root",
    "cache_root",
    "items",
    "resume_authority",
}
_RESULT_FIELDS = {
    "schema_version",
    "batch_sha256",
    "batch_status",
    "interruption_reason",
    "all_items_completed",
    "scientific_acceptance",
    "counts",
    "items",
}
_ITEM_FIELDS = {
    "schema_version",
    "index",
    "item_id",
    "request_sha256",
    "item_status",
    "scientific_acceptance",
}
_PRODUCT_FIELDS = {
    "directory",
    "manifest_sha256",
    "scientific_content_sha256",
}


def _contains_outcome_field(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            key.startswith("observed_")
            or "outcome" in key
            or _contains_outcome_field(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_outcome_field(item) for item in value)
    return False


def batch_evidence(
    product: ExperimentProduct,
    manifest: dict[str, object],
    operations_value: object,
    *,
    expected_records: tuple[str, ...],
) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]]]:
    """Authenticate exact request bodies and their terminal operation ledger."""
    operations = object_mapping(operations_value, "operations")
    files = object_mapping(manifest["files"], "files")
    receipt_name = "batch/receipt.json"
    summary_name = "batch/summary/receipt.json"
    if not operations:
        if {receipt_name, summary_name} & set(files):
            raise ValidationRefusal(
                "invalid_local_batch_evidence", "Attempt exists without a result"
            )
        return {}, {}
    if not {receipt_name, summary_name}.issubset(files):
        raise ValidationRefusal(
            "invalid_local_batch_evidence", "Batch request bytes are absent"
        )
    attempt = object_mapping(read_member(product, receipt_name), "batch_attempt")
    summary = object_mapping(read_member(product, summary_name), "batch_summary")
    limits = object_mapping(attempt.get("limits"), "batch_limits")
    if (
        summary != operations
        or set(attempt) != _ATTEMPT_FIELDS
        or set(operations) != _RESULT_FIELDS
        or set(limits) != {"max_workers", "max_items"}
        or attempt.get("schema_version") != "lra-batch-attempt.v1"
        or attempt.get("event") != "attempt_started"
        or attempt.get("completion_receipt") != "summary/receipt.json"
        or attempt.get("numerical_threads_per_worker") != 1
        or attempt.get("resume_authority")
        != "verified_cache_products_only_not_attempt_receipts"
        or operations.get("schema_version") != "lra-batch-result.v1"
        or operations.get("scientific_acceptance") != "not_evaluated"
    ):
        raise ValidationRefusal(
            "invalid_local_batch_evidence", "Batch posture or identity differs"
        )
    requests: dict[str, dict[str, object]] = {}
    attempt_order = []
    identity_rows = []
    for value in object_list(attempt["items"], "batch_items"):
        item = object_mapping(value, "batch_item")
        if set(item) != {"item_id", "request_sha256", "request"}:
            raise ValidationRefusal(
                "invalid_local_batch_evidence", "Closed request item required"
            )
        record = identity(item["item_id"])
        request = object_mapping(item["request"], "request")
        request_sha256 = digest(item["request_sha256"], "Invalid request digest")
        if (
            record in requests
            or record not in expected_records
            or LRABatchItem(record, request).request_sha256 != request_sha256
        ):
            raise ValidationRefusal(
                "invalid_local_batch_evidence", "Request item identity differs"
            )
        requests[record] = request
        attempt_order.append(record)
        identity_rows.append({"item_id": record, "request_sha256": request_sha256})
    if attempt_order != [key for key in expected_records if key in requests]:
        raise ValidationRefusal(
            "invalid_local_batch_evidence", "Request order differs from folds"
        )
    batch_sha256 = manifest_sha256(identity_rows)
    if (
        attempt.get("batch_sha256") != batch_sha256
        or operations.get("batch_sha256") != batch_sha256
    ):
        raise ValidationRefusal(
            "invalid_local_batch_evidence", "Batch digest differs from requests"
        )
    results: dict[str, dict[str, object]] = {}
    statuses = ("completed", "refused", "failed", "not_run", "unobserved")
    result_rows = object_list(operations["items"], "operation_items")
    for index, value in enumerate(result_rows):
        item = object_mapping(value, "operation_item")
        record = identity(item["item_id"])
        status = item.get("item_status")
        expected_fields = _ITEM_FIELDS | (
            {"product", "cache_key", "cache_hit"}
            if "product" in item
            else ({"error"} if "error" in item else set())
        )
        retained_product = (
            object_mapping(item["product"], "operation_product")
            if "product" in item
            else None
        )
        if (
            set(item) != expected_fields
            or _contains_outcome_field(item)
            or (
                retained_product is not None
                and set(retained_product) != _PRODUCT_FIELDS
            )
            or item.get("schema_version") != "lra-batch-item.v1"
            or item.get("index") != index
            or item.get("scientific_acceptance") != "not_evaluated"
            or record in results
            or record not in requests
            or status not in statuses
            or item.get("request_sha256")
            != LRABatchItem(record, requests[record]).request_sha256
        ):
            raise ValidationRefusal(
                "invalid_local_batch_evidence", "Operation item differs from request"
            )
        results[record] = item
    counts = object_mapping(operations["counts"], "counts")
    if (
        list(results) != attempt_order
        or set(counts) != set(statuses)
        or any(
            type(counts[status]) is not int
            or counts[status]
            != sum(row.get("item_status") == status for row in results.values())
            for status in statuses
        )
        or operations.get("all_items_completed")
        is not all(row.get("item_status") == "completed" for row in results.values())
        or operations.get("batch_status") not in {"finished", "interrupted"}
        or (operations.get("batch_status") == "interrupted")
        is not (operations.get("interruption_reason") is not None)
    ):
        raise ValidationRefusal(
            "invalid_local_batch_evidence", "Operation denominator differs"
        )
    return requests, results


def validate_failure_batch_evidence(
    failures_value: object,
    folds: dict[str, dict[str, object]],
    requests: dict[str, dict[str, object]],
    results: dict[str, dict[str, object]],
) -> None:
    """Bind scientific failure details to raw operation evidence when attempted."""
    for value in object_list(failures_value, "failures"):
        failure = object_mapping(value, "failure")
        fold_id = identity(failure["fold_id"])
        record = identity(
            object_list(folds[fold_id]["test_record_ids"], "test_record_ids")[0]
        )
        batch_item_id = failure.get("batch_item_id")
        if batch_item_id is None:
            if record in requests or record in results:
                raise ValidationRefusal(
                    "invalid_local_batch_evidence",
                    "An attempted failure lacks its batch item identity",
                )
            continue
        if identity(batch_item_id) != record or record not in requests:
            raise ValidationRefusal(
                "invalid_local_batch_evidence", "Failure batch ownership differs"
            )
        operation = results.get(record)
        detail_value = failure.get("detail")
        if operation is None or not isinstance(detail_value, str):
            raise ValidationRefusal(
                "invalid_local_batch_evidence", "Failure operation detail is absent"
            )
        try:
            detail = object_mapping(json.loads(detail_value), "failure_detail")
        except (TypeError, ValueError) as exc:
            raise ValidationRefusal(
                "invalid_local_batch_evidence", "Failure detail is not canonical JSON"
            ) from exc
        projection_error = detail.get("projection_error")
        fields = {
            "batch_item_status",
            "operational_error",
            "projection_interrupted",
        }
        if projection_error is not None:
            fields.add("projection_error")
        status = identity(failure["status"])
        raw_status = identity(operation["item_status"])
        if (
            set(detail) != fields
            or detail_value != canonical_json(detail)
            or detail.get("batch_item_status") != raw_status
            or detail.get("operational_error") != operation.get("error")
            or type(detail.get("projection_interrupted")) is not bool
            or (projection_error is not None)
            is not (status == "refused" and raw_status == "completed")
            or (
                detail.get("projection_interrupted") is True
                and not (status == "not_run" and raw_status == "completed")
            )
        ):
            raise ValidationRefusal(
                "invalid_local_batch_evidence",
                "Scientific failure differs from its raw batch terminal",
            )
        if projection_error is not None:
            error = object_mapping(projection_error, "projection_error")
            if (
                set(error) != {"reason_code", "detail"}
                or error.get("reason_code") != failure.get("reason_code")
                or not isinstance(error.get("detail"), str)
                or not error["detail"]
            ):
                raise ValidationRefusal(
                    "invalid_local_batch_evidence",
                    "Projection refusal detail differs from its scientific terminal",
                )
