from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from .model import (
    ACQUISITION_RECEIPT_SCHEMA_VERSION,
    ACQUISITION_TOOL_VERSION,
    TABLE_PAYLOAD_SCHEMA_VERSION,
    SeadAcquisitionError,
    SeadTableAcquisition,
)


def build_result(
    *,
    table: str,
    rows: list[dict[str, object]],
    endpoint: str,
    params: Sequence[tuple[str, str]],
    order_by: Sequence[str],
    country_scope: Sequence[str],
    spatial_scope: Mapping[str, object],
    parent_run_id: str,
    build_id: str,
    page_size: int,
    max_pages: int,
    started_at: str,
    completed_at: str,
    pages: list[dict[str, object]],
    failures: list[dict[str, object]],
    attempt_count: int,
    status: str,
    failure_reason: str | None,
) -> SeadTableAcquisition:
    payload = payload_bytes(table, rows)
    schema = observed_schema(rows)
    receipt: dict[str, object] = {
        "schema_version": ACQUISITION_RECEIPT_SCHEMA_VERSION,
        "source": "SEAD",
        "route": "postgrest",
        "endpoint": endpoint,
        "table": table,
        "parameters": [[key, value] for key, value in params],
        "order_by": list(order_by),
        "country_scope": list(country_scope),
        "spatial_scope": dict(spatial_scope),
        "started_at": started_at,
        "completed_at": completed_at,
        "pagination": {
            "page_size": page_size,
            "max_pages": max_pages,
            "pages": pages,
            "complete": status == "complete",
        },
        "result": {
            "attempt_count": attempt_count,
            "retry_count": max(
                0,
                attempt_count
                - len(
                    {
                        page_number
                        for item in (*pages, *failures)
                        if isinstance((page_number := item.get("page")), int)
                    }
                ),
            ),
            "failure_count": len(failures),
        },
        "failures": failures,
        "row_count": len(rows),
        "source_schema_version": None,
        "source_schema_version_status": "not_reported_by_endpoint",
        "canonical_schema": schema,
        "canonical_schema_sha256": hashlib.sha256(canonical_bytes(schema)).hexdigest(),
        "content_sha256": hashlib.sha256(payload).hexdigest(),
        "tool_version": ACQUISITION_TOOL_VERSION,
        "parent_run_id": parent_run_id,
        "build_id": build_id,
        "status": status,
        "failure_reason": failure_reason,
    }
    receipt["receipt_id"] = (
        "sead-receipt:" + hashlib.sha256(canonical_bytes(receipt)).hexdigest()
    )
    return SeadTableAcquisition(table=table, rows=tuple(rows), receipt=receipt)


def raise_acquisition_error(**kwargs: Any) -> SeadTableAcquisition:
    status = "partial" if kwargs["rows"] else "failed"
    result = build_result(status=status, failure_reason=kwargs.pop("reason"), **kwargs)
    raise SeadAcquisitionError(
        f"SEAD table acquisition {status}: {result.table}", result
    )


def observed_schema(rows: Iterable[Mapping[str, object]]) -> dict[str, object]:
    materialized = list(rows)
    fields = sorted({key for row in materialized for key in row})
    return {
        "row_count": len(materialized),
        "fields": [
            {
                "name": field,
                "presence_count": sum(field in row for row in materialized),
                "null_count": sum(
                    row.get(field) is None for row in materialized if field in row
                ),
                "json_types": sorted(
                    {json_type(row[field]) for row in materialized if field in row}
                ),
            }
            for field in fields
        ],
    }


def json_type(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


def payload_bytes(table: str, rows: Iterable[Mapping[str, object]]) -> bytes:
    return canonical_bytes(
        {
            "schema_version": TABLE_PAYLOAD_SCHEMA_VERSION,
            "table": table,
            "rows": list(rows),
        }
    )


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode()


def utc_text(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Acquisition timestamps must be timezone-aware")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
