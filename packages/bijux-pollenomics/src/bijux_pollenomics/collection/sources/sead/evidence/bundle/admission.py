from __future__ import annotations

from collections.abc import Mapping
import hashlib
from pathlib import Path
from typing import cast

from bijux_pollenomics.collection.sources.sead.acquisition.archive import (
    SEAD_FULL_EVIDENCE_SOURCE_TABLES,
)

from .serialization import (
    _decode_object,
    _positive_int,
    _read_object,
    _reject_symlink_ancestors,
    _required_text,
    _verify_record,
)


def _load_full_admission(
    acquisition_root: Path,
    *,
    validated_admission: Mapping[str, object],
) -> tuple[Path, dict[str, list[dict[str, object]]], dict[str, str]]:
    root = Path(acquisition_root)
    if not root.is_absolute() or root == Path(root.anchor):
        raise ValueError("SEAD evidence acquisition must be a safe absolute path")
    _reject_symlink_ancestors(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("SEAD evidence acquisition must be a regular directory")
    admission = _read_object(root / "admission.json")
    if admission != validated_admission:
        raise ValueError("SEAD evidence admission changed after independent validation")
    scope = admission.get("declared_scope")
    if not isinstance(scope, Mapping):
        raise TypeError("SEAD evidence admission declared_scope is missing")
    if scope.get("scope_key") != "full_evidence_relations":
        raise ValueError("SEAD evidence requires a full-evidence admission")
    expected_tables = sorted(SEAD_FULL_EVIDENCE_SOURCE_TABLES)
    if scope.get("tables") != expected_tables or scope.get("table_count") != 61:
        raise ValueError("SEAD evidence admission must bind the exact 61 tables")
    if scope.get("join_count") != 86:
        raise ValueError("SEAD evidence admission must bind the exact 86 joins")
    copied = admission.get("copied_files")
    if not isinstance(copied, list):
        raise TypeError("SEAD evidence admission copied_files is missing")
    records: dict[str, Mapping[str, object]] = {}
    for item in copied:
        if not isinstance(item, Mapping):
            raise TypeError("SEAD copied-file record must be an object")
        name = _required_text(item, "path")
        if name in records:
            raise ValueError(f"Duplicate SEAD copied-file path: {name}")
        records[name] = item
    tables: dict[str, list[dict[str, object]]] = {}
    digests: dict[str, str] = {}
    for table in SEAD_FULL_EVIDENCE_SOURCE_TABLES:
        name = f"payloads/{table}.json"
        record = records.get(name)
        if record is None:
            raise ValueError(f"SEAD full-evidence payload is missing: {table}")
        content = (root / name).read_bytes()
        _verify_record(content, record, name)
        payload = _decode_object(content, name)
        if payload.get("table") != table:
            raise ValueError(f"SEAD evidence table identity changed: {table}")
        rows = payload.get("rows")
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise TypeError(f"SEAD evidence rows are invalid: {table}")
        tables[table] = cast(list[dict[str, object]], rows)
        digests[table] = hashlib.sha256(content).hexdigest()
    return root, tables, digests


def _country_by_site(root: Path) -> dict[int, str]:
    document = _read_object(root / "country-decisions.json")
    rows = document.get("decisions")
    if not isinstance(rows, list):
        raise TypeError("SEAD country decisions are missing")
    result: dict[int, str] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise TypeError("SEAD country decision must be an object")
        code = row.get("governed_country_code")
        if code in {"SE", "DK", "NO", "FI"}:
            result[_positive_int(row.get("site_id"), "country site")] = cast(str, code)
    return result
