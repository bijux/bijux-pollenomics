"""Checked row views of public collection-contract payloads in tests."""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def require_mapping(value: object) -> Mapping[str, object]:
    assert isinstance(value, dict)
    assert all(isinstance(key, str) for key in value)
    return value


def require_strings(value: object) -> Sequence[str]:
    assert isinstance(value, (list, tuple))
    assert all(isinstance(item, str) for item in value)
    return value


def require_rows(value: object) -> list[Mapping[str, object]]:
    assert isinstance(value, list)
    rows: list[Mapping[str, object]] = []
    for row in value:
        rows.append(require_mapping(row))
    return rows
