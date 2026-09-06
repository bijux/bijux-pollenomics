"""Canonical scoped-acquisition serialization and time handling."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime

from .models import _SAFE_RUN_ID


def _validate_identity(value: str, field: str, *, path_segment: bool = False) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"SEAD acquisition requires a stable {field}")
    if path_segment and not _SAFE_RUN_ID.fullmatch(value):
        raise ValueError("SEAD acquisition run_id is not a safe path segment")


def _table_payload_bytes(table: str, rows: Iterable[Mapping[str, object]]) -> bytes:
    return _canonical_bytes(
        {
            "schema_version": "sead-table-payload.v1",
            "table": table,
            "rows": list(rows),
        }
    )


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _observed_schema(rows: Sequence[Mapping[str, object]]) -> dict[str, object]:
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


def _row_identity(row: Mapping[str, object], index: int, primary_key: str) -> str:
    value = row.get(primary_key)
    return f"{primary_key}:{value}" if value is not None else f"row:{index}"


def _current_utc() -> datetime:
    return datetime.now(UTC)


def _utc_text(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("SEAD acquisition timestamps must be timezone-aware")
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
