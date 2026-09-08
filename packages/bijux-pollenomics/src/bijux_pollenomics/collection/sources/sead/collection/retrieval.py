from __future__ import annotations

from collections.abc import Callable, Iterable

from bijux_pollenomics.collection.sources.sead.acquisition import (
    client as sead_api_client,
)
from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    acquire_sead_table,
)

from .validation import strict_input_identifier, validate_sead_rows


def retrieve_rows(
    table_name: str,
    *,
    fetch_json_fn: Callable[..., object],
    primary_key: str,
    select: str,
    filters: tuple[tuple[str, str], ...] | None,
    order_by: tuple[str, ...],
    max_pages: int,
    sleep_fn: Callable[[float], None],
) -> list[dict[str, object]]:
    result = acquire_sead_table(
        table_name,
        fetch_json_fn=fetch_json_fn,
        select=select,
        filters=filters or (),
        order_by=order_by or (primary_key,),
        country_scope=("SE", "DK", "NO", "FI"),
        spatial_scope={
            "kind": "query_filters",
            "filters": [list(item) for item in filters or ()],
        },
        parent_run_id="sead-production-collection",
        build_id="bijux-pollenomics-runtime",
        page_size=sead_api_client.SEAD_LIMIT,
        max_pages=max_pages,
        request_retries=sead_api_client.SEAD_REQUEST_RETRIES,
        request_timeout_seconds=sead_api_client.SEAD_REQUEST_TIMEOUT_SECONDS,
        sleep_fn=sleep_fn,
    )
    rows = [dict(row) for row in result.rows]
    validate_sead_rows(table_name, rows)
    return rows


def retrieve_rows_by_ids(
    table_name: str,
    *,
    select: str,
    filter_field: str,
    ids: Iterable[int],
    order_by: tuple[str, ...],
    fetch_rows: Callable[..., list[dict[str, object]]],
    build_filter: Callable[[list[int]], str],
) -> list[dict[str, object]]:
    unique_ids = sorted({strict_input_identifier(value) for value in ids})
    rows: list[dict[str, object]] = []
    for start in range(0, len(unique_ids), sead_api_client.SEAD_FILTER_BATCH_SIZE):
        batch = unique_ids[start : start + sead_api_client.SEAD_FILTER_BATCH_SIZE]
        rows.extend(
            fetch_rows(
                table_name,
                select=select,
                filters=((filter_field, build_filter(batch)),),
                order_by=order_by,
            )
        )
    validate_sead_rows(table_name, rows)
    return rows
