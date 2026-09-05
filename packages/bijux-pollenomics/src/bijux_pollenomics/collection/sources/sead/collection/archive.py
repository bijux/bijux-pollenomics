from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from bijux_pollenomics.collection.sources.sead.acquisition.archive import (
    SEAD_LINKED_SOURCE_TABLES,
)

from .model import SEAD_ARCHIVE_SCHEMA_VERSION
from .validation import required_positive_int, validate_sead_rows


def canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def write_sead_site_archive(
    raw_dir: Path,
    *,
    bbox: tuple[float, float, float, float],
    rows: list[dict[str, object]],
    inventory_summary: dict[str, int | str],
) -> Path:
    """Atomically create a deterministic site archive or accept identical bytes."""
    validate_sead_rows("tbl_sites", rows)
    ordered_rows = sorted(
        rows,
        key=lambda row: required_positive_int(row, "site_id", "tbl_sites"),
    )
    row_bytes = canonical_json_bytes(ordered_rows)
    raw_path = Path(raw_dir) / "nordic_sites.json"
    payload = {
        "schema_version": SEAD_ARCHIVE_SCHEMA_VERSION,
        "source": "SEAD",
        "endpoint": "https://browser.sead.se/postgrest/tbl_sites",
        "source_snapshot_id": f"sha256:{hashlib.sha256(row_bytes).hexdigest()}",
        "row_count": len(rows),
        "bbox": list(bbox),
        "source_tables": list(SEAD_LINKED_SOURCE_TABLES),
        "inventory_summary": inventory_summary,
        "rows": ordered_rows,
    }
    content = canonical_json_bytes(payload)
    if raw_path.exists():
        if raw_path.is_symlink() or not raw_path.is_file():
            raise FileExistsError(f"Unsafe existing SEAD archive: {raw_path}")
        if raw_path.read_bytes() == content:
            return raw_path
        raise FileExistsError(f"Non-identical SEAD archive already exists: {raw_path}")
    staging_path = raw_path.with_name(f".{raw_path.name}.staging-{os.getpid()}")
    if staging_path.exists() or staging_path.is_symlink():
        raise FileExistsError(f"SEAD archive staging collision: {staging_path}")
    try:
        staging_path.write_bytes(content)
        os.replace(staging_path, raw_path)
    finally:
        if staging_path.exists():
            staging_path.unlink()
    return raw_path
