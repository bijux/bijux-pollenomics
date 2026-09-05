"""Fixture mutation, schema observation, and canonical serialization."""

from __future__ import annotations
from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from bijux_pollenomics.collection.sources.sead.acquisition.full import (
    ACQUISITION_MANIFEST_SCHEMA_VERSION,
)
from bijux_pollenomics.collection.sources.sead.acquisition.archive import (
    SEAD_LINKED_SOURCE_TABLES,
)


def _refresh_scoped_receipt(receipt: dict[str, object]) -> None:
    receipt.pop("receipt_id", None)
    receipt["receipt_id"] = "sead-scoped-receipt:" + _digest(_canonical_bytes(receipt))


def _first_query_receipt(receipt: Mapping[str, object]) -> dict[str, object]:
    queries = receipt.get("query_receipts")
    if not isinstance(queries, list) or not queries or not isinstance(queries[0], dict):
        raise ValueError("fixture query receipts must contain an object")
    return queries[0]


def _refresh_query_receipt(receipt: dict[str, object]) -> None:
    receipt.pop("receipt_id", None)
    receipt["receipt_id"] = "sead-receipt:" + _digest(_canonical_bytes(receipt))


def _refresh_manifest(snapshot: Path) -> None:
    files = []
    for relative_path in sorted(
        [
            *(f"payloads/{table}.json" for table in SEAD_LINKED_SOURCE_TABLES),
            *(f"receipts/{table}.json" for table in SEAD_LINKED_SOURCE_TABLES),
            "reconciliation/countries.json",
            "reconciliation/joins.json",
        ]
    ):
        content = (snapshot / relative_path).read_bytes()
        files.append(
            {
                "path": relative_path,
                "sha256": _digest(content),
                "byte_count": len(content),
            }
        )
    _write_json(
        snapshot / "manifest.json",
        {
            "schema_version": ACQUISITION_MANIFEST_SCHEMA_VERSION,
            "status": "complete",
            "required_tables": sorted(SEAD_LINKED_SOURCE_TABLES),
            "missing_required_tables": [],
            "incomplete_required_tables": [],
            "failed_join_edges": [],
            "country_reconciliation_status": "complete",
            "files": files,
        },
    )


def _observed_schema(rows: list[dict[str, object]]) -> dict[str, object]:
    fields = sorted({field for row in rows for field in row})
    return {
        "row_count": len(rows),
        "fields": [
            {
                "name": field,
                "presence_count": sum(field in row for row in rows),
                "null_count": sum(
                    row.get(field) is None for row in rows if field in row
                ),
                "json_types": sorted(
                    {_json_type(row[field]) for row in rows if field in row}
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


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_bytes(value))


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"Fixture JSON must be an object: {path}")
    return value


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _fixture_positive_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("fixture source identity must be a positive integer")
    return value
