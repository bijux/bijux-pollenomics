"""Auditable, fail-closed acquisition primitives for SEAD PostgREST tables."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import time
from typing import Any
from urllib.error import HTTPError, URLError

from bijux_pollenomics.collection.sources.sead.acquisition.client import (
    SEAD_POSTGREST_ROOT,
    sead_retryable_error,
)

ACQUISITION_RECEIPT_SCHEMA_VERSION = "sead-acquisition-receipt.v1"
TABLE_PAYLOAD_SCHEMA_VERSION = "sead-table-payload.v1"
ACQUISITION_MANIFEST_SCHEMA_VERSION = "sead-acquisition-manifest.v1"
ACQUISITION_TOOL_VERSION = "sead-postgrest-acquisition.v1"
NORDIC_COUNTRY_CODES = ("SE", "DK", "NO", "FI", "UNASSIGNED")

_SAFE_TABLE_NAME = re.compile(r"tbl_[a-z0-9_]+\Z")


@dataclass(frozen=True)
class SeadTableAcquisition:
    """One table payload and the receipt that proves how it was obtained."""

    table: str
    rows: tuple[dict[str, object], ...]
    receipt: dict[str, object]


class SeadAcquisitionError(RuntimeError):
    """A failed or partial table acquisition carrying its auditable result."""

    def __init__(self, message: str, result: SeadTableAcquisition) -> None:
        super().__init__(message)
        self.result = result


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
    _validate_request(
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
    started_at = _utc_text(now())
    endpoint = f"{SEAD_POSTGREST_ROOT}/{table}"
    params = [("select", select), *filters, ("order", ",".join(order_by))]
    rows: list[dict[str, object]] = []
    pages: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    attempt_count = 0

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
                    return _raise_acquisition_error(
                        table=table,
                        rows=rows,
                        endpoint=endpoint,
                        params=params,
                        order_by=order_by,
                        country_scope=country_scope,
                        spatial_scope=spatial_scope,
                        parent_run_id=parent_run_id,
                        build_id=build_id,
                        page_size=page_size,
                        max_pages=max_pages,
                        started_at=started_at,
                        completed_at=_utc_text(now()),
                        pages=pages,
                        failures=failures,
                        attempt_count=attempt_count,
                        reason="terminal_request_failure",
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
            return _raise_acquisition_error(
                table=table,
                rows=rows,
                endpoint=endpoint,
                params=params,
                order_by=order_by,
                country_scope=country_scope,
                spatial_scope=spatial_scope,
                parent_run_id=parent_run_id,
                build_id=build_id,
                page_size=page_size,
                max_pages=max_pages,
                started_at=started_at,
                completed_at=_utc_text(now()),
                pages=pages,
                failures=failures,
                attempt_count=attempt_count,
                reason="invalid_page_payload",
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
            return _raise_acquisition_error(
                table=table,
                rows=rows,
                endpoint=endpoint,
                params=params,
                order_by=order_by,
                country_scope=country_scope,
                spatial_scope=spatial_scope,
                parent_run_id=parent_run_id,
                build_id=build_id,
                page_size=page_size,
                max_pages=max_pages,
                started_at=started_at,
                completed_at=_utc_text(now()),
                pages=pages,
                failures=failures,
                attempt_count=attempt_count,
                reason="page_size_contract_violation",
            )
        rows.extend(page_rows)
        pages.append(
            {"page": page_number, "range": range_text, "row_count": len(page_rows)}
        )
        if len(page_rows) < page_size:
            return _build_result(
                table=table,
                rows=rows,
                endpoint=endpoint,
                params=params,
                order_by=order_by,
                country_scope=country_scope,
                spatial_scope=spatial_scope,
                parent_run_id=parent_run_id,
                build_id=build_id,
                page_size=page_size,
                max_pages=max_pages,
                started_at=started_at,
                completed_at=_utc_text(now()),
                pages=pages,
                failures=failures,
                attempt_count=attempt_count,
                status="complete",
                failure_reason=None,
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
    return _raise_acquisition_error(
        table=table,
        rows=rows,
        endpoint=endpoint,
        params=params,
        order_by=order_by,
        country_scope=country_scope,
        spatial_scope=spatial_scope,
        parent_run_id=parent_run_id,
        build_id=build_id,
        page_size=page_size,
        max_pages=max_pages,
        started_at=started_at,
        completed_at=_utc_text(now()),
        pages=pages,
        failures=failures,
        attempt_count=attempt_count,
        reason="page_limit_exceeded",
    )


def reconcile_sead_countries(
    rows: Iterable[Mapping[str, object]],
    *,
    country_by_site_id: Mapping[str, str],
) -> dict[str, object]:
    """Account for every site in the four-country scope or as unassigned."""
    counts: Counter[str] = Counter(dict.fromkeys(NORDIC_COUNTRY_CODES, 0))
    row_count = 0
    duplicate_site_ids: list[str] = []
    seen: set[str] = set()
    for row in rows:
        row_count += 1
        site_id = str(row.get("site_id", "")).strip()
        if not site_id or site_id in seen:
            duplicate_site_ids.append(site_id)
        seen.add(site_id)
        code = country_by_site_id.get(site_id, "UNASSIGNED").strip().upper()
        counts[code if code in NORDIC_COUNTRY_CODES else "UNASSIGNED"] += 1
    assigned_count = sum(counts[code] for code in NORDIC_COUNTRY_CODES[:-1])
    return {
        "schema_version": "sead-country-reconciliation.v1",
        "row_count": row_count,
        "counts": {code: counts[code] for code in NORDIC_COUNTRY_CODES},
        "assigned_count": assigned_count,
        "unassigned_count": counts["UNASSIGNED"],
        "duplicate_site_ids": sorted(duplicate_site_ids),
        "reconciles": assigned_count + counts["UNASSIGNED"] == row_count
        and not duplicate_site_ids,
    }


def reconcile_sead_join(
    *,
    edge: str,
    parent_rows: Iterable[Mapping[str, object]],
    child_rows: Iterable[Mapping[str, object]],
    parent_key: str,
    child_key: str,
    child_foreign_key: str,
) -> dict[str, object]:
    """Build a loss ledger for one declared parent-to-child relation edge."""
    parent_values = [row.get(parent_key) for row in parent_rows]
    null_parent_keys = [
        f"row:{index}" for index, value in enumerate(parent_values) if value is None
    ]
    parent_ids = {str(value) for value in parent_values if value is not None}
    duplicate_parent_ids = sorted(
        str(value)
        for value, count in Counter(
            str(value) for value in parent_values if value is not None
        ).items()
        if count > 1
    )
    null_child_ids: list[str] = []
    orphan_child_ids: list[str] = []
    child_key_values: list[object] = []
    child_count = 0
    matched_count = 0
    for index, row in enumerate(child_rows):
        child_count += 1
        child_key_values.append(row.get(child_key))
        foreign_key = row.get(child_foreign_key)
        child_identity = _child_identity(row, index)
        if foreign_key is None:
            null_child_ids.append(child_identity)
        elif str(foreign_key) not in parent_ids:
            orphan_child_ids.append(child_identity)
        else:
            matched_count += 1
    null_child_keys = [
        f"row:{index}" for index, value in enumerate(child_key_values) if value is None
    ]
    duplicate_child_ids = sorted(
        value
        for value, count in Counter(
            str(value) for value in child_key_values if value is not None
        ).items()
        if count > 1
    )
    unexplained_loss_count = (
        len(null_parent_keys)
        + len(duplicate_parent_ids)
        + len(null_child_keys)
        + len(duplicate_child_ids)
        + len(null_child_ids)
        + len(orphan_child_ids)
    )
    return {
        "schema_version": "sead-join-reconciliation.v1",
        "edge": edge,
        "parent_key": parent_key,
        "child_key": child_key,
        "child_foreign_key": child_foreign_key,
        "parent_row_count": len(parent_values),
        "unique_parent_count": len(parent_ids),
        "null_parent_keys": null_parent_keys,
        "child_row_count": child_count,
        "matched_child_count": matched_count,
        "duplicate_parent_ids": duplicate_parent_ids,
        "null_child_keys": null_child_keys,
        "duplicate_child_ids": duplicate_child_ids,
        "null_foreign_key_child_ids": sorted(null_child_ids),
        "orphan_child_ids": sorted(orphan_child_ids),
        "unexplained_loss_count": unexplained_loss_count,
        "status": "complete" if unexplained_loss_count == 0 else "failed",
    }


def assert_sead_join_complete(reconciliation: Mapping[str, object]) -> None:
    """Fail closed when a join reconciliation contains unexplained loss."""
    if reconciliation.get("status") != "complete":
        raise ValueError(
            f"SEAD join reconciliation failed: {reconciliation.get('edge', 'unknown')}"
        )


def materialize_sead_acquisition(
    output_root: Path,
    *,
    acquisitions: Sequence[SeadTableAcquisition],
    required_tables: Sequence[str],
    country_reconciliation: Mapping[str, object],
    join_reconciliations: Sequence[Mapping[str, object]],
) -> Path:
    """Atomically persist payloads, receipts, reconciliations, and a digest manifest."""
    root = _safe_output_root(output_root)
    for item in acquisitions:
        _validate_table_name(item.table)
    for table in required_tables:
        _validate_table_name(table)
    by_table = {item.table: item for item in acquisitions}
    if len(by_table) != len(acquisitions):
        raise ValueError("Duplicate SEAD table acquisition")
    missing = sorted(set(required_tables) - set(by_table))
    incomplete = sorted(
        table
        for table in required_tables
        if table in by_table and by_table[table].receipt.get("status") != "complete"
    )
    failed_joins = sorted(
        str(item.get("edge", "unknown"))
        for item in join_reconciliations
        if item.get("status") != "complete"
    )
    country_status = (
        "complete" if country_reconciliation.get("reconciles") is True else "failed"
    )
    status = (
        "complete"
        if not missing
        and not incomplete
        and not failed_joins
        and country_status == "complete"
        else "failed"
    )

    files: dict[str, bytes] = {}
    for table, acquisition in sorted(by_table.items()):
        payload = _payload_bytes(table, acquisition.rows)
        if acquisition.receipt.get("table") != table:
            raise ValueError(f"SEAD receipt table mismatch: {table}")
        if acquisition.receipt.get("row_count") != len(acquisition.rows):
            raise ValueError(f"SEAD receipt row count mismatch: {table}")
        if (
            acquisition.receipt.get("content_sha256")
            != hashlib.sha256(payload).hexdigest()
        ):
            raise ValueError(f"SEAD receipt content checksum mismatch: {table}")
        files[f"payloads/{table}.json"] = payload
        files[f"receipts/{table}.json"] = _canonical_bytes(acquisition.receipt)
    files["reconciliation/countries.json"] = _canonical_bytes(country_reconciliation)
    files["reconciliation/joins.json"] = _canonical_bytes(
        {
            "schema_version": "sead-join-reconciliations.v1",
            "edges": list(join_reconciliations),
        }
    )
    manifest = {
        "schema_version": ACQUISITION_MANIFEST_SCHEMA_VERSION,
        "status": status,
        "required_tables": sorted(set(required_tables)),
        "missing_required_tables": missing,
        "incomplete_required_tables": incomplete,
        "failed_join_edges": failed_joins,
        "country_reconciliation_status": country_status,
        "files": [
            {
                "path": path,
                "sha256": hashlib.sha256(content).hexdigest(),
                "byte_count": len(content),
            }
            for path, content in sorted(files.items())
        ],
    }
    files["manifest.json"] = _canonical_bytes(manifest)
    _publish_directory(root, files)
    return root / "manifest.json"


def _build_result(
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
    payload = _payload_bytes(table, rows)
    schema = _observed_schema(rows)
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
        "canonical_schema_sha256": hashlib.sha256(_canonical_bytes(schema)).hexdigest(),
        "content_sha256": hashlib.sha256(payload).hexdigest(),
        "tool_version": ACQUISITION_TOOL_VERSION,
        "parent_run_id": parent_run_id,
        "build_id": build_id,
        "status": status,
        "failure_reason": failure_reason,
    }
    receipt["receipt_id"] = (
        "sead-receipt:" + hashlib.sha256(_canonical_bytes(receipt)).hexdigest()
    )
    return SeadTableAcquisition(table=table, rows=tuple(rows), receipt=receipt)


def _raise_acquisition_error(**kwargs: Any) -> SeadTableAcquisition:
    status = "partial" if kwargs["rows"] else "failed"
    result = _build_result(status=status, failure_reason=kwargs.pop("reason"), **kwargs)
    raise SeadAcquisitionError(
        f"SEAD table acquisition {status}: {result.table}", result
    )


def _observed_schema(rows: Iterable[Mapping[str, object]]) -> dict[str, object]:
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
                    {_json_type(row[field]) for row in materialized if field in row}
                ),
            }
            for field in fields
        ],
    }


def _json_type(value: object) -> str:
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


def _payload_bytes(table: str, rows: Iterable[Mapping[str, object]]) -> bytes:
    return _canonical_bytes(
        {
            "schema_version": TABLE_PAYLOAD_SCHEMA_VERSION,
            "table": table,
            "rows": list(rows),
        }
    )


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode()


def _utc_text(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Acquisition timestamps must be timezone-aware")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _child_identity(row: Mapping[str, object], index: int) -> str:
    for key in sorted(row):
        if key.endswith("_id") and row.get(key) is not None:
            return f"{key}:{row[key]}"
    return f"row:{index}"


def _validate_request(
    *,
    table: str,
    select: str,
    order_by: Sequence[str],
    country_scope: Sequence[str],
    parent_run_id: str,
    build_id: str,
    page_size: int,
    max_pages: int,
    request_retries: int,
    request_timeout_seconds: float,
) -> None:
    _validate_table_name(table)
    if not select.strip() or not order_by:
        raise ValueError("SEAD acquisition requires an explicit projection and order")
    if list(country_scope) != list(NORDIC_COUNTRY_CODES[:-1]):
        raise ValueError("SEAD country scope must be exactly SE, DK, NO, FI")
    if not parent_run_id.strip() or not build_id.strip():
        raise ValueError("SEAD acquisition requires parent run and build IDs")
    if page_size < 1 or max_pages < 1 or request_retries < 1:
        raise ValueError("SEAD pagination and retry bounds must be positive")
    if request_timeout_seconds <= 0:
        raise ValueError("SEAD request timeout must be positive")


def _validate_table_name(table: str) -> None:
    if not _SAFE_TABLE_NAME.fullmatch(table):
        raise ValueError(f"Unsafe SEAD table name: {table}")


def _safe_output_root(output_root: Path) -> Path:
    root = Path(output_root)
    if not root.is_absolute() or root == Path(root.anchor):
        raise ValueError("SEAD acquisition output root must be a safe absolute path")
    if ".." in root.parts or root.is_symlink():
        raise ValueError("Unsafe SEAD acquisition output root")
    for ancestor in root.parents:
        if ancestor.exists() and ancestor.is_symlink():
            raise ValueError("SEAD acquisition output cannot traverse a symlink")
    root.parent.mkdir(parents=True, exist_ok=True)
    if root.parent.is_symlink():
        raise ValueError("SEAD acquisition output parent cannot be a symlink")
    return root


def _publish_directory(root: Path, files: Mapping[str, bytes]) -> None:
    if root.exists():
        if not root.is_dir() or root.is_symlink():
            raise FileExistsError(f"Unsafe existing SEAD acquisition output: {root}")
        existing = {
            str(path.relative_to(root)): path.read_bytes()
            for path in root.rglob("*")
            if path.is_file()
        }
        if existing == dict(files):
            return
        raise FileExistsError(f"Non-identical SEAD acquisition output exists: {root}")
    staging = root.with_name(f".{root.name}.staging-{os.getpid()}")
    if staging.exists() or staging.is_symlink():
        raise FileExistsError(f"SEAD acquisition staging collision: {staging}")
    staging.mkdir()
    try:
        for relative_path, content in files.items():
            destination = staging / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        os.replace(staging, root)
    except Exception:
        if staging.exists():
            for path in sorted(staging.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    path.rmdir()
            staging.rmdir()
        raise


__all__ = [
    "NORDIC_COUNTRY_CODES",
    "SeadAcquisitionError",
    "SeadTableAcquisition",
    "acquire_sead_table",
    "assert_sead_join_complete",
    "materialize_sead_acquisition",
    "reconcile_sead_countries",
    "reconcile_sead_join",
]
