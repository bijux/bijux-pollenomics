"""Runtime narrowing helpers for record-oriented payloads."""

from __future__ import annotations

from collections.abc import Mapping


def require_record_rows(
    payload: Mapping[str, object],
    key: str,
) -> tuple[dict[str, object], ...]:
    """Return object rows from a dynamic payload or reject its malformed boundary."""
    raw_rows = payload.get(key)
    if not isinstance(raw_rows, list):
        raise ValueError(f"Expected {key!r} to be a list")
    rows: list[dict[str, object]] = []
    for raw_row in raw_rows:
        if not isinstance(raw_row, dict):
            raise ValueError(f"Expected every {key!r} entry to be an object")
        rows.append(dict(raw_row))
    return tuple(rows)
