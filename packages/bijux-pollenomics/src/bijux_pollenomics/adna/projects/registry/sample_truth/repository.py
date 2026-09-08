"""Filesystem readers and stable grouping for animal sample truth."""

from __future__ import annotations

import json
from pathlib import Path
from re import Pattern


def readme_curated_sample_count(path: Path, pattern: Pattern[str]) -> int | None:
    if not path.is_file():
        return None
    match = pattern.search(path.read_text(encoding="utf-8"))
    if match is None:
        return None
    return int(match.group("count"))


def group_sample_rows_by_project(
    sample_rows: list[dict[str, object]],
) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in sample_rows:
        accession = str(row.get("project_accession", "")).strip()
        if accession:
            grouped.setdefault(accession, []).append(row)
    return grouped


def load_rows(species_root: Path, filename: str, field: str) -> list[dict[str, object]]:
    path = species_root / "normalized" / filename
    if not path.is_file():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get(field, [])
    return [row for row in rows if isinstance(row, dict)]
