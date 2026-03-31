from __future__ import annotations

from collections.abc import Callable, Iterable
import time
from urllib.error import HTTPError, URLError

SEAD_LIMIT = 1000
SEAD_FILTER_BATCH_SIZE = 100
SEAD_POSTGREST_ROOT = "https://browser.sead.se/postgrest"
SEAD_REQUEST_RETRIES = 5
SEAD_REQUEST_TIMEOUT_SECONDS = 60.0


def fetch_sead_rows(
    table_name: str,
    *,
    fetch_json_fn: Callable[..., object],
    filters: tuple[tuple[str, str], ...] | None = None,
    order_by: tuple[str, ...] = (),
    select: str,
    request_retries: int = SEAD_REQUEST_RETRIES,
    request_timeout_seconds: float = SEAD_REQUEST_TIMEOUT_SECONDS,
) -> list[dict[str, object]]:
    """Fetch every row from one SEAD PostgREST table for a selected projection."""
    rows: list[dict[str, object]] = []
    start = 0
    params: list[tuple[str, str]] = [("select", select)]
    if filters:
        params.extend(filters)
    if order_by:
        params.append(("order", ",".join(order_by)))
    while True:
        chunk = fetch_sead_chunk(
            table_name,
            fetch_json_fn=fetch_json_fn,
            params=params,
            start=start,
            request_retries=request_retries,
            request_timeout_seconds=request_timeout_seconds,
        )
        if not isinstance(chunk, list) or not chunk:
            break
        rows.extend(item for item in chunk if isinstance(item, dict))
        if len(chunk) < SEAD_LIMIT:
            break
        start += SEAD_LIMIT
    return rows


def fetch_sead_rows_by_ids(
    table_name: str,
    *,
    fetch_json_fn: Callable[..., object],
    filter_field: str,
    ids: Iterable[int],
    order_by: tuple[str, ...] = (),
    select: str,
    request_retries: int = SEAD_REQUEST_RETRIES,
    request_timeout_seconds: float = SEAD_REQUEST_TIMEOUT_SECONDS,
) -> list[dict[str, object]]:
    """Fetch SEAD rows in manageable `in.(...)` batches."""
    unique_ids = sorted({int(value) for value in ids})
    rows: list[dict[str, object]] = []
    for start in range(0, len(unique_ids), SEAD_FILTER_BATCH_SIZE):
        batch = unique_ids[start:start + SEAD_FILTER_BATCH_SIZE]
        rows.extend(
            fetch_sead_rows(
                table_name,
                fetch_json_fn=fetch_json_fn,
                select=select,
                filters=((filter_field, build_sead_in_filter(batch)),),
                order_by=order_by,
                request_retries=request_retries,
                request_timeout_seconds=request_timeout_seconds,
            )
        )
    return rows


def fetch_sead_chunk(
    table_name: str,
    *,
    fetch_json_fn: Callable[..., object],
    params: list[tuple[str, str]],
    start: int,
    request_retries: int,
    request_timeout_seconds: float,
) -> object:
    """Fetch one ranged SEAD chunk with bounded retries for transient transport failures."""
    for attempt in range(request_retries):
        try:
            return fetch_json_fn(
                f"{SEAD_POSTGREST_ROOT}/{table_name}",
                params=params,
                headers={
                    "Range-Unit": "items",
                    "Range": f"{start}-{start + SEAD_LIMIT - 1}",
                },
                timeout=request_timeout_seconds,
            )
        except (TimeoutError, URLError, HTTPError) as exc:
            if not sead_retryable_error(exc) or attempt + 1 >= request_retries:
                raise
            time.sleep(float(attempt + 1))
    raise RuntimeError("SEAD request retries exhausted unexpectedly")


def sead_retryable_error(exc: Exception) -> bool:
    """Return whether one SEAD transport failure is worth retrying."""
    if isinstance(exc, HTTPError):
        return exc.code == 429 or 500 <= exc.code <= 599
    return isinstance(exc, (TimeoutError, URLError))


def build_sead_in_filter(values: list[int]) -> str:
    """Render a PostgREST `in.(...)` filter from integer identifiers."""
    return f"in.({','.join(str(value) for value in values)})"


__all__ = [
    "SEAD_FILTER_BATCH_SIZE",
    "SEAD_LIMIT",
    "SEAD_POSTGREST_ROOT",
    "build_sead_in_filter",
    "fetch_sead_rows",
    "fetch_sead_rows_by_ids",
]
