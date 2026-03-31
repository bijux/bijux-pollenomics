from __future__ import annotations

from collections.abc import Callable, Iterable

SEAD_LIMIT = 1000
SEAD_FILTER_BATCH_SIZE = 100
SEAD_POSTGREST_ROOT = "https://browser.sead.se/postgrest"


def fetch_sead_rows(
    table_name: str,
    *,
    fetch_json_fn: Callable[..., object],
    filters: tuple[tuple[str, str], ...] | None = None,
    order_by: tuple[str, ...] = (),
    select: str,
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
        chunk = fetch_json_fn(
            f"{SEAD_POSTGREST_ROOT}/{table_name}",
            params=params,
            headers={
                "Range-Unit": "items",
                "Range": f"{start}-{start + SEAD_LIMIT - 1}",
            },
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
            )
        )
    return rows


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
