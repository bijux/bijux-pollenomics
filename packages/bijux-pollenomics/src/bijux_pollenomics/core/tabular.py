"""Serialization helpers for record-oriented tabular outputs."""

from __future__ import annotations

import csv
import io
from collections.abc import Mapping, Sequence


def render_csv_rows(rows: Sequence[Mapping[str, object]]) -> str:
    """Render homogeneous record rows as deterministic CSV text."""
    if not rows:
        return ""
    fieldnames = tuple(rows[0].keys())
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _csv_value(value) for key, value in row.items()})
    return buffer.getvalue()


def _csv_value(value: object) -> object:
    if isinstance(value, (list, tuple)):
        return ";".join(str(item) for item in value)
    if isinstance(value, bool):
        return str(value).lower()
    return value
