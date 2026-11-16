"""Bounded SEAD queries with exact source keys and explicit EOF evidence."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
import re
import time
from urllib.error import HTTPError, URLError

from .identifiers import required_sead_identifier

SEAD_LIMIT = 1000
SEAD_MAX_PAGES = 1000
SEAD_FILTER_BATCH_SIZE = 100
SEAD_POSTGREST_ROOT = "https://browser.sead.se/postgrest"
SEAD_REQUEST_RETRIES = 5
SEAD_REQUEST_TIMEOUT_SECONDS = 60.0
SEAD_MAX_RETRY_AFTER_SECONDS = 60.0


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
    for _ in range(SEAD_MAX_PAGES):
        try:
            chunk = fetch_sead_chunk(
                table_name,
                fetch_json_fn=fetch_json_fn,
                params=params,
                start=start,
                request_retries=request_retries,
                request_timeout_seconds=request_timeout_seconds,
            )
        except HTTPError as error:
            if error.code == 416 and _range_exhausted_at(error, start):
                return rows
            raise
        if not isinstance(chunk, list) or any(
            not isinstance(row, Mapping) for row in chunk
        ):
            raise ValueError(
                f"SEAD page must be an array of JSON objects: {table_name}"
            )
        if len(chunk) > SEAD_LIMIT:
            raise ValueError(f"SEAD page exceeds requested size: {table_name}")
        if not chunk:
            return rows
        rows.extend(dict(row) for row in chunk)
        start += len(chunk)
    raise ValueError(f"SEAD pagination exceeded {SEAD_MAX_PAGES} pages: {table_name}")


def _range_exhausted_at(error: HTTPError, start: int) -> bool:
    """Accept a range refusal only when one header proves the exact next offset."""
    headers: object = error.headers
    get_all = getattr(headers, "get_all", None)
    if callable(get_all):
        declarations = get_all("Content-Range", [])
    elif isinstance(headers, Mapping):
        declarations = [
            value for key, value in headers.items() if key.casefold() == "content-range"
        ]
    else:
        return False
    if len(declarations) != 1 or not isinstance(declarations[0], str):
        return False
    match = re.fullmatch(r"\*/(0|[1-9][0-9]*)", declarations[0])
    return match is not None and match[1] == str(start)


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
    identifier = r"[A-Za-z_][A-Za-z0-9_]*"
    if re.fullmatch(identifier, filter_field) is None or (
        select != "*"
        and re.fullmatch(rf"{identifier}(?:,{identifier})*", select) is None
    ):
        raise ValueError("SEAD filtered projection requires literal source fields")
    added_owner = select != "*" and filter_field not in select.split(",")
    verified_select = f"{select},{filter_field}" if added_owner else select
    unique_ids = sorted({required_sead_identifier(value) for value in ids})
    rows: list[dict[str, object]] = []
    for start in range(0, len(unique_ids), SEAD_FILTER_BATCH_SIZE):
        batch = unique_ids[start : start + SEAD_FILTER_BATCH_SIZE]

        def selected_page(
            url: str, *, allowed: frozenset[int] = frozenset(batch), **kwargs: object
        ) -> object:
            payload = fetch_json_fn(url, **kwargs)
            if isinstance(payload, list):
                for row in payload:
                    if isinstance(row, Mapping):
                        owner = required_sead_identifier(row.get(filter_field))
                        if owner not in allowed:
                            raise ValueError(
                                f"SEAD source ignored identity filter for {table_name}: "
                                f"{filter_field}={owner}"
                            )
                if added_owner:
                    return [
                        {
                            key: value
                            for key, value in row.items()
                            if key != filter_field
                        }
                        if isinstance(row, Mapping)
                        else row
                        for row in payload
                    ]
            return payload

        selected_rows = fetch_sead_rows(
            table_name,
            fetch_json_fn=selected_page,
            select=verified_select,
            filters=((filter_field, build_sead_in_filter(batch)),),
            order_by=order_by,
            request_retries=request_retries,
            request_timeout_seconds=request_timeout_seconds,
        )
        rows.extend(selected_rows)
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
            delay = sead_retry_delay(exc, attempt + 1)
            if delay is None:
                raise
            time.sleep(delay)
    raise RuntimeError("SEAD request retries exhausted unexpectedly")


def sead_retryable_error(exc: Exception) -> bool:
    """Return whether one SEAD transport failure is worth retrying."""
    if isinstance(exc, HTTPError):
        return exc.code == 429 or 500 <= exc.code <= 599
    return isinstance(exc, (TimeoutError, URLError))


def sead_retry_delay(exc: Exception, attempt: int) -> float | None:
    """Honor server retry timing or refuse a wait beyond the bounded client policy."""
    if isinstance(exc, HTTPError) and exc.code in {429, 503}:
        value = exc.headers.get("Retry-After") if exc.headers is not None else None
        if value is not None:
            if value.isdecimal():
                delay = float(value)
            else:
                try:
                    retry_at = parsedate_to_datetime(value)
                except (TypeError, ValueError, IndexError):
                    retry_at = None
                delay = (
                    max(0.0, (retry_at - datetime.now(UTC)).total_seconds())
                    if retry_at is not None and retry_at.tzinfo is not None
                    else float(attempt)
                )
            return delay if delay <= SEAD_MAX_RETRY_AFTER_SECONDS else None
    return float(attempt)


def build_sead_in_filter(values: list[int]) -> str:
    """Render a PostgREST `in.(...)` filter from integer identifiers."""
    return f"in.({','.join(str(required_sead_identifier(value)) for value in values)})"


__all__ = [
    "SEAD_FILTER_BATCH_SIZE",
    "SEAD_LIMIT",
    "SEAD_POSTGREST_ROOT",
    "build_sead_in_filter",
    "fetch_sead_rows",
    "fetch_sead_rows_by_ids",
]
