"""Acquisition manifest and table-payload validation."""

from __future__ import annotations
from collections.abc import Mapping, Sequence
import hashlib
from pathlib import Path, PurePosixPath
from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    TABLE_PAYLOAD_SCHEMA_VERSION,
)
from bijux_pollenomics.collection.sources.sead.acquisition.scoped import (
    SCOPED_RECEIPT_SCHEMA_VERSION,
)

from ..codec import (
    _canonical_bytes,
    _expect_equal,
    _non_negative_int,
    _observed_schema,
    _positive_int,
    _read_regular_file,
    _required_text,
    _safe_relative_path,
    _sha256,
)
from .contracts import _declared_table_contract
from ..models import _AdmissionProfile


def _validate_manifest_files(
    root: Path,
    manifest: Mapping[str, object],
    manifest_bytes: bytes,
    *,
    tables: Sequence[str],
    allowed_extra_paths: set[str],
) -> dict[str, bytes]:
    records = manifest.get("files")
    if not isinstance(records, list):
        raise TypeError("SEAD manifest files must be a list")
    expected_paths = {
        *(f"payloads/{table}.json" for table in tables),
        *(f"receipts/{table}.json" for table in tables),
        "reconciliation/countries.json",
        "reconciliation/joins.json",
    }
    files: dict[str, bytes] = {"manifest.json": manifest_bytes}
    for item in records:
        if not isinstance(item, Mapping):
            raise TypeError("SEAD manifest file record must be an object")
        relative_path = _safe_relative_path(item.get("path"))
        if relative_path in files:
            raise ValueError(f"Duplicate SEAD manifest path: {relative_path}")
        content = _read_regular_file(root.joinpath(*PurePosixPath(relative_path).parts))
        _expect_equal(
            len(content),
            _non_negative_int(item.get("byte_count"), f"{relative_path} byte_count"),
            f"{relative_path} byte_count",
        )
        _expect_equal(
            hashlib.sha256(content).hexdigest(),
            _sha256(item.get("sha256"), relative_path),
            f"{relative_path} SHA-256",
        )
        files[relative_path] = content
    if set(files) - {"manifest.json"} != expected_paths:
        raise ValueError("SEAD manifest does not cover the exact acquisition file set")
    actual_paths: set[str] = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Symlinks are forbidden in SEAD acquisition: {path}")
        if path.is_file():
            actual_paths.add(path.relative_to(root).as_posix())
    if actual_paths != set(files) | allowed_extra_paths:
        raise ValueError("SEAD acquisition contains missing or unmanifested files")
    return files


def _validate_table_payload(
    table: str,
    payload: Mapping[str, object],
    payload_bytes: bytes,
    receipt: Mapping[str, object],
    *,
    profile: _AdmissionProfile,
) -> list[Mapping[str, object]]:
    _expect_equal(
        payload.get("schema_version"),
        TABLE_PAYLOAD_SCHEMA_VERSION,
        f"{table} payload schema_version",
    )
    _expect_equal(payload.get("table"), table, f"{table} payload table")
    rows = payload.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise ValueError(f"SEAD payload rows must be objects: {table}")
    typed_rows = [row for row in rows if isinstance(row, Mapping)]
    _expect_equal(payload_bytes, _canonical_bytes(payload), f"{table} canonical bytes")
    _expect_equal(
        receipt.get("schema_version"),
        SCOPED_RECEIPT_SCHEMA_VERSION,
        f"{table} receipt schema_version",
    )
    _expect_equal(receipt.get("source"), "SEAD", f"{table} receipt source")
    _expect_equal(receipt.get("status"), "complete", f"{table} receipt status")
    _expect_equal(receipt.get("table"), table, f"{table} receipt table")
    _expect_equal(
        _non_negative_int(receipt.get("row_count"), f"{table} receipt row_count"),
        len(typed_rows),
        f"{table} receipt row_count",
    )
    _expect_equal(
        receipt.get("content_sha256"),
        hashlib.sha256(payload_bytes).hexdigest(),
        f"{table} receipt content_sha256",
    )
    observed_schema = _observed_schema(typed_rows)
    _expect_equal(
        receipt.get("canonical_schema"),
        observed_schema,
        f"{table} canonical schema",
    )
    _expect_equal(
        receipt.get("canonical_schema_sha256"),
        hashlib.sha256(_canonical_bytes(observed_schema)).hexdigest(),
        f"{table} canonical schema SHA-256",
    )
    receipt_without_id = dict(receipt)
    receipt_id = receipt_without_id.pop("receipt_id", None)
    _expect_equal(
        receipt_id,
        "sead-scoped-receipt:"
        + hashlib.sha256(_canonical_bytes(receipt_without_id)).hexdigest(),
        f"{table} receipt_id",
    )
    expected_primary_key, expected_projection, _ = _declared_table_contract(
        table, plans=profile.table_plans
    )
    primary_key = _required_text(receipt.get("primary_key"), f"{table} primary_key")
    projection = _required_text(receipt.get("projection"), f"{table} projection")
    _expect_equal(primary_key, expected_primary_key, f"{table} declared primary_key")
    _expect_equal(projection, expected_projection, f"{table} declared projection")
    projected_fields = set(projection.split(","))
    identifiers: list[int] = []
    for index, row in enumerate(typed_rows):
        missing = sorted(projected_fields - set(row))
        if missing:
            raise ValueError(f"SEAD {table} row {index} misses fields: {missing}")
        extra = sorted(set(row) - projected_fields)
        if extra:
            raise ValueError(f"SEAD {table} row {index} has undeclared fields: {extra}")
        identifiers.append(
            _positive_int(row.get(primary_key), f"{table}.{primary_key}")
        )
    if len(identifiers) != len(set(identifiers)):
        raise ValueError(f"SEAD {table} contains duplicate primary keys")
    if identifiers != sorted(identifiers):
        raise ValueError(f"SEAD {table} rows are not ordered by primary key")
    return typed_rows
