"""Shared schema identity and row accounting for source-inventory evidence."""

from __future__ import annotations

import json
from pathlib import Path

SOURCE_INVENTORY_SCHEMA_VERSION = "adna-source-inventory.v1"


def _source_root(output_root: Path) -> Path:
    return Path(output_root) / "adna" / "governance" / "source_library"


def _project_table_status(path: Path) -> tuple[str, int]:
    if not path.is_file():
        return ("not_published", 0)
    rows = json.loads(path.read_text(encoding="utf-8")).get("rows", [])
    if rows:
        return ("published", len(rows))
    return ("published_empty", 0)


def _count_by(rows: list[dict[str, object]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get(field, ""))
        counts[key] = counts.get(key, 0) + 1
    return counts
