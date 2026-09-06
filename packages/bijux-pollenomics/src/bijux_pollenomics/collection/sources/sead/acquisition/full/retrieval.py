from __future__ import annotations

import time
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from typing import TypedDict
from urllib.error import HTTPError, URLError

from bijux_pollenomics.collection.sources.sead.acquisition.client import (
    SEAD_POSTGREST_ROOT,
    sead_retryable_error,
)

from .model import SeadTableAcquisition
from .serialization import build_result, raise_acquisition_error, utc_text
from .validation import validate_request


class _ResultArguments(TypedDict):
    table: str
    rows: list[dict[str, object]]
    endpoint: str
    params: Sequence[tuple[str, str]]
    order_by: Sequence[str]
    country_scope: Sequence[str]
    spatial_scope: Mapping[str, object]
    parent_run_id: str
    build_id: str
    page_size: int
    max_pages: int
    started_at: str
    completed_at: str
    pages: list[dict[str, object]]
    failures: list[dict[str, object]]
    attempt_count: int


def acquire_sead_table(
    table: str,
    *,
    fetch_json_fn: Callable[..., object],
    select: str,
    filters: Sequence[tuple[str, str]] = (),
    order_by: Sequence[str],
    country_scope: Sequence[str],
    spatial_scope: Mapping[str, object],
    parent_run_id: str,
    build_id: str,
    page_size: int = 1000,
    max_pages: int = 10_000,
    request_retries: int = 5,
    request_timeout_seconds: float = 60.0,
    clock: Callable[[], datetime] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> SeadTableAcquisition:
    """Fetch one ordered table completely or raise with a partial/failed receipt."""
    validate_request(
        table=table,
        select=select,
        order_by=order_by,
        country_scope=country_scope,
        parent_run_id=parent_run_id,
        build_id=build_id,
        page_size=page_size,
        max_pages=max_pages,
        request_retries=request_retries,
        request_timeout_seconds=request_timeout_seconds,
    )
    now = clock or (lambda: datetime.now(UTC))
    started_at = utc_text(now())
    endpoint = f"{SEAD_POSTGREST_ROOT}/{table}"
    params = [("select", select), *filters, ("order", ",".join(order_by))]
    rows: list[dict[str, object]] = []
    pages: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    attempt_count = 0

    def result_arguments() -> _ResultArguments:
        return {
            "table": table,
            "rows": rows,
            "endpoint": endpoint,
            "params": params,
            "order_by": order_by,
            "country_scope": country_scope,
            "spatial_scope": spatial_scope,
            "parent_run_id": parent_run_id,
            "build_id": build_id,
            "page_size": page_size,
            "max_pages": max_pages,
            "started_at": started_at,
            "completed_at": utc_text(now()),
            "pages": pages,
            "failures": failures,
            "attempt_count": attempt_count,
        }

    for page_number in range(1, max_pages + 1):
        start = (page_number - 1) * page_size
        range_text = f"{start}-{start + page_size - 1}"
        payload: object | None = None
        for attempt in range(1, request_retries + 1):
            attempt_count += 1
            try:
                payload = fetch_json_fn(
                    endpoint,
                    params=list(params),
                    headers={"Range-Unit": "items", "Range": range_text},
                    timeout=request_timeout_seconds,
                )
                break
            except (TimeoutError, URLError, HTTPError) as exc:
                retryable = sead_retryable_error(exc)
                failures.append(
                    {
                        "page": page_number,
                        "range": range_text,
                        "attempt": attempt,
                        "error_type": type(exc).__name__,
                        "message": str(exc),
                        "retryable": retryable,
                    }
                )
                if not retryable or attempt == request_retries:
                    return raise_acquisition_error(
                        **result_arguments(), reason="terminal_request_failure"
                    )
                sleep_fn(float(attempt))
        if not isinstance(payload, list) or any(
            not isinstance(row, Mapping) for row in payload
        ):
            failures.append(
                {
                    "page": page_number,
                    "range": range_text,
                    "attempt": 1,
                    "error_type": "InvalidPayload",
                    "message": "PostgREST page must be a list of JSON objects",
                    "retryable": False,
                }
            )
            return raise_acquisition_error(
                **result_arguments(), reason="invalid_page_payload"
            )
        page_rows = [dict(row) for row in payload]
        if len(page_rows) > page_size:
            failures.append(
                {
                    "page": page_number,
                    "range": range_text,
                    "attempt": 1,
                    "error_type": "PageOverflow",
                    "message": f"received {len(page_rows)} rows for page size {page_size}",
                    "retryable": False,
                }
            )
            return raise_acquisition_error(
                **result_arguments(), reason="page_size_contract_violation"
            )
        rows.extend(page_rows)
        pages.append(
            {"page": page_number, "range": range_text, "row_count": len(page_rows)}
        )
        if len(page_rows) < page_size:
            return build_result(
                **result_arguments(), status="complete", failure_reason=None
            )

    failures.append(
        {
            "page": max_pages,
            "range": pages[-1]["range"],
            "attempt": 1,
            "error_type": "PageLimitExceeded",
            "message": f"completion was not proven within {max_pages} pages",
            "retryable": False,
        }
    )
    return raise_acquisition_error(**result_arguments(), reason="page_limit_exceeded")
