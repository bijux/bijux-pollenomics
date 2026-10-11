"""Checked heterogeneous payload views for fieldwork assertions."""

from __future__ import annotations


def require_mapping(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    assert all(isinstance(key, str) for key in value)
    return value


def require_rows(value: object) -> list[dict[str, object]]:
    assert isinstance(value, list)
    return [require_mapping(row) for row in value]


def require_string(value: object) -> str:
    assert isinstance(value, str)
    return value
