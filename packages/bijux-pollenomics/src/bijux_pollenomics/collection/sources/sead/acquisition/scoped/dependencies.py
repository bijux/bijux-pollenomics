"""Dependency-scoped table acquisition and aggregation."""

from __future__ import annotations
from collections.abc import Callable, Iterable, Mapping, Sequence
from datetime import datetime
import hashlib
from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    SeadTableAcquisition,
    acquire_sead_table,
)
from bijux_pollenomics.collection.sources.sead.acquisition.client import (
    build_sead_in_filter,
)

from .codec import _canonical_bytes, _observed_schema, _table_payload_bytes, _utc_text
from .models import (
    NORDIC_TARGET_COUNTRIES,
    SCOPED_RECEIPT_SCHEMA_VERSION,
    SeadScopedTablePlan,
)
from .validation import _required_source_id, _validated_rows


def _acquire_dependency_scoped_table(
    plan: SeadScopedTablePlan,
    *,
    requested_ids: tuple[int, ...],
    fetch_json_fn: Callable[..., object],
    scope: Mapping[str, object],
    run_id: str,
    parent_run_id: str,
    build_id: str,
    clock: Callable[[], datetime],
    sleep_fn: Callable[[float], None],
    id_batch_size: int,
    page_size: int,
    max_pages: int,
    request_retries: int,
    request_timeout_seconds: float,
    orchestrator_version: str,
) -> SeadTableAcquisition:
    query_acquisitions: list[SeadTableAcquisition] = []
    rows: list[dict[str, object]] = []
    for start in range(0, len(requested_ids), id_batch_size):
        batch = requested_ids[start : start + id_batch_size]
        acquisition = acquire_sead_table(
            plan.table,
            fetch_json_fn=fetch_json_fn,
            select=plan.projection,
            filters=((plan.filter_field, build_sead_in_filter(list(batch))),),
            order_by=(plan.filter_field, plan.primary_key),
            country_scope=NORDIC_TARGET_COUNTRIES,
            spatial_scope={
                **scope,
                "kind": "dependency_identity_filter",
                "filter_field": plan.filter_field,
                "filter_ids": list(batch),
            },
            parent_run_id=parent_run_id,
            build_id=build_id,
            page_size=page_size,
            max_pages=max_pages,
            request_retries=request_retries,
            request_timeout_seconds=request_timeout_seconds,
            clock=clock,
            sleep_fn=sleep_fn,
        )
        allowed = set(batch)
        for row in acquisition.rows:
            observed = _required_source_id(row, plan.filter_field)
            if observed not in allowed:
                raise ValueError(
                    f"SEAD source ignored dependency filter for {plan.table}: "
                    f"{plan.filter_field}={observed}"
                )
        query_acquisitions.append(acquisition)
        rows.extend(dict(row) for row in acquisition.rows)
    validated = _validated_rows(plan.table, rows, plan.primary_key, plan.projection)
    return _aggregate_table_acquisition(
        table=plan.table,
        rows=validated,
        primary_key=plan.primary_key,
        projection=plan.projection,
        filter_field=plan.filter_field,
        requested_ids=requested_ids,
        query_acquisitions=tuple(query_acquisitions),
        scope=scope,
        run_id=run_id,
        parent_run_id=parent_run_id,
        build_id=build_id,
        completion_basis=(
            "all_dependency_batches_complete"
            if requested_ids
            else "empty_dependency_identity_set"
        ),
        extra_receipt_fields={},
        orchestrator_version=orchestrator_version,
        clock=clock,
    )


def _aggregate_table_acquisition(
    *,
    table: str,
    rows: Iterable[Mapping[str, object]],
    primary_key: str,
    projection: str,
    filter_field: str,
    requested_ids: Sequence[int],
    query_acquisitions: Sequence[SeadTableAcquisition],
    scope: Mapping[str, object],
    run_id: str,
    parent_run_id: str,
    build_id: str,
    completion_basis: str,
    extra_receipt_fields: Mapping[str, object],
    orchestrator_version: str,
    clock: Callable[[], datetime],
) -> SeadTableAcquisition:
    if any(item.receipt.get("status") != "complete" for item in query_acquisitions):
        raise ValueError(f"Cannot aggregate incomplete SEAD queries for {table}")
    materialized_rows = tuple(dict(row) for row in rows)
    payload = _table_payload_bytes(table, materialized_rows)
    schema = _observed_schema(materialized_rows)
    if query_acquisitions:
        started_at = str(query_acquisitions[0].receipt["started_at"])
        completed_at = str(query_acquisitions[-1].receipt["completed_at"])
    else:
        started_at = _utc_text(clock())
        completed_at = _utc_text(clock())
    receipt: dict[str, object] = {
        "schema_version": SCOPED_RECEIPT_SCHEMA_VERSION,
        "source": "SEAD",
        "route": "postgrest_dependency_scoped",
        "table": table,
        "primary_key": primary_key,
        "projection": projection,
        "filter_field": filter_field,
        "requested_identity_count": len(requested_ids),
        "requested_identities": list(requested_ids),
        "query_count": len(query_acquisitions),
        "query_receipts": [dict(item.receipt) for item in query_acquisitions],
        "completion_basis": completion_basis,
        "country_scope": list(NORDIC_TARGET_COUNTRIES),
        "spatial_scope": dict(scope),
        "scope_id": scope["scope_id"],
        "run_id": run_id,
        "parent_run_id": parent_run_id,
        "build_id": build_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "row_count": len(materialized_rows),
        "canonical_schema": schema,
        "canonical_schema_sha256": hashlib.sha256(_canonical_bytes(schema)).hexdigest(),
        "content_sha256": hashlib.sha256(payload).hexdigest(),
        "tool_version": orchestrator_version,
        "status": "complete",
        "failure_reason": None,
        **dict(extra_receipt_fields),
    }
    receipt["receipt_id"] = (
        "sead-scoped-receipt:" + hashlib.sha256(_canonical_bytes(receipt)).hexdigest()
    )
    return SeadTableAcquisition(table=table, rows=materialized_rows, receipt=receipt)
