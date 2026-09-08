"""Scoped query-receipt and join-row fixture construction."""

from __future__ import annotations

from collections.abc import Mapping

from bijux_pollenomics.collection.sources.sead.acquisition.client import (
    SEAD_LIMIT,
    SEAD_POSTGREST_ROOT,
    build_sead_in_filter,
)
from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    ACQUISITION_RECEIPT_SCHEMA_VERSION,
    TABLE_PAYLOAD_SCHEMA_VERSION,
    reconcile_sead_join,
)
from bijux_pollenomics.collection.sources.sead.acquisition.scoped import (
    SEAD_SCOPED_TABLE_PLANS,
)

from .models import (
    _BUILD_ID,
    _JOIN_TABLES,
    _PARENT_RUN_ID,
    _RUN_ID,
    _SCOPE_ID,
    _SITE_PROJECTION,
    _TABLE_PRIMARY_KEYS,
)
from .serialization import (
    _canonical_bytes,
    _digest,
    _fixture_positive_int,
    _observed_schema,
)


def _query_receipt(
    table: str,
    *,
    rows: list[dict[str, object]],
    spatial_scope: Mapping[str, object],
    parameters: list[list[str]] | None = None,
    max_pages: int = 10_000,
) -> dict[str, object]:
    row_count = len(rows)
    plans = {plan.table: plan for plan in SEAD_SCOPED_TABLE_PLANS}
    if table == "tbl_sites":
        projection = _SITE_PROJECTION
        order_by = ["site_id"]
        default_parameters = [
            ["select", projection],
            ["latitude_dd", "gte.54.0"],
            ["latitude_dd", "lte.72.0"],
            ["longitude_dd", "gte.4.0"],
            ["longitude_dd", "lte.35.0"],
            ["order", "site_id"],
        ]
    else:
        plan = plans[table]
        projection = plan.projection
        order_by = [plan.filter_field, plan.primary_key]
        raw_filter_ids = spatial_scope.get("filter_ids")
        filter_ids = (
            [_fixture_positive_int(value) for value in raw_filter_ids]
            if isinstance(raw_filter_ids, list)
            else []
        )
        default_parameters = [
            ["select", projection],
            [plan.filter_field, build_sead_in_filter(filter_ids)],
            ["order", ",".join(order_by)],
        ]
    schema = _observed_schema(rows)
    payload = {
        "schema_version": TABLE_PAYLOAD_SCHEMA_VERSION,
        "table": table,
        "rows": rows,
    }
    receipt: dict[str, object] = {
        "schema_version": ACQUISITION_RECEIPT_SCHEMA_VERSION,
        "source": "SEAD",
        "route": "postgrest",
        "table": table,
        "endpoint": f"{SEAD_POSTGREST_ROOT}/{table}",
        "parameters": parameters if parameters is not None else default_parameters,
        "order_by": order_by,
        "country_scope": ["SE", "DK", "NO", "FI"],
        "spatial_scope": dict(spatial_scope),
        "parent_run_id": _PARENT_RUN_ID,
        "build_id": _BUILD_ID,
        "started_at": "2026-09-04T00:00:00Z",
        "completed_at": "2026-09-04T00:00:01Z",
        "row_count": row_count,
        "canonical_schema": schema,
        "canonical_schema_sha256": _digest(_canonical_bytes(schema)),
        "content_sha256": _digest(_canonical_bytes(payload)),
        "tool_version": "sead-postgrest-acquisition.v1",
        "status": "complete",
        "failure_reason": None,
        "failures": [],
        "pagination": {
            "complete": True,
            "max_pages": max_pages,
            "page_size": SEAD_LIMIT,
            "pages": [
                {
                    "page": 1,
                    "range": f"0-{SEAD_LIMIT - 1}",
                    "row_count": row_count,
                }
            ],
        },
        "result": {"attempt_count": 1, "failure_count": 0, "retry_count": 0},
    }
    receipt["receipt_id"] = "sead-receipt:" + _digest(_canonical_bytes(receipt))
    return receipt


def _join_row(
    edge: str,
    parent_table: str,
    child_table: str,
    rows_by_table: Mapping[str, list[dict[str, object]]],
) -> dict[str, object]:
    parent_key = _TABLE_PRIMARY_KEYS[parent_table]
    child_key = _TABLE_PRIMARY_KEYS[child_table]
    child_foreign_key = parent_key
    reference_required = edge in set(list(_JOIN_TABLES)[:12])
    parent_rows = rows_by_table[parent_table]
    all_child_rows = rows_by_table[child_table]
    referenced_child_rows = [
        row
        for row in all_child_rows
        if reference_required or row.get(child_foreign_key) is not None
    ]
    result = reconcile_sead_join(
        edge=edge,
        parent_rows=parent_rows,
        child_rows=referenced_child_rows,
        parent_key=parent_key,
        child_key=child_key,
        child_foreign_key=child_foreign_key,
    )
    parent_ids = {str(row[parent_key]) for row in parent_rows}
    child_counts: dict[str, int] = {}
    for row in referenced_child_rows:
        foreign_key = row.get(child_foreign_key)
        if foreign_key is not None:
            key = str(foreign_key)
            child_counts[key] = child_counts.get(key, 0) + 1
    matched_ids = sorted(parent_ids & set(child_counts))
    zero_ids = sorted(parent_ids - set(child_counts))
    result.update(
        {
            "scope_id": _SCOPE_ID,
            "run_id": _RUN_ID,
            "parent_run_id": _PARENT_RUN_ID,
            "build_id": _BUILD_ID,
            "reference_required": reference_required,
            "total_child_row_count": len(all_child_rows),
            "referenced_child_row_count": len(referenced_child_rows),
            "null_reference_child_count": 0,
            "null_reference_child_ids": [],
            "matched_parent_count": len(matched_ids),
            "matched_parent_ids": matched_ids,
            "zero_child_parent_count": len(zero_ids),
            "zero_child_parent_ids": zero_ids,
            "one_child_parent_count": sum(
                child_counts.get(key, 0) == 1 for key in parent_ids
            ),
            "many_child_parent_count": sum(
                child_counts.get(key, 0) > 1 for key in parent_ids
            ),
        }
    )
    return result
