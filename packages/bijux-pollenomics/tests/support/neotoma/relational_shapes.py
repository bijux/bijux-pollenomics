"""Runtime shape checks for Neotoma fixture rows and snapshot tables."""

from __future__ import annotations

from collections.abc import Iterable, Mapping


def mapping(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    assert all(isinstance(key, str) for key in value)
    return value


def rows(value: object) -> list[dict[str, object]]:
    assert isinstance(value, list)
    return [mapping(row) for row in value]


def nested(value: object, *fields: str) -> dict[str, object]:
    selected = mapping(value)
    for field in fields:
        selected = mapping(selected[field])
    return selected


def tables(
    payload: Mapping[str, object], names: Iterable[str]
) -> dict[str, list[dict[str, object]]]:
    return {name: rows(payload[name]) for name in names}


__all__ = ["mapping", "nested", "rows", "tables"]
