"""Strict scalar and collection readers for chronology publication contracts."""

from __future__ import annotations

from collections.abc import Mapping


def mapping(value: object, label: str) -> Mapping[str, object]:
    """Return a string-keyed mapping or refuse malformed contract input."""
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"animal chronology {label} is invalid")
    return value


def mapping_rows(value: object, label: str) -> list[dict[str, object]]:
    """Return copied mapping rows or refuse malformed contract input."""
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"animal chronology {label} are invalid")
    return [dict(mapping(item, label)) for item in value]


def nonnegative_integer(value: object, label: str) -> int:
    """Return a nonnegative integer while refusing booleans."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"animal chronology {label} is invalid")
    return value


def nonblank_text(value: object, label: str) -> str:
    """Return nonblank text or refuse malformed contract input."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"animal chronology {label} is invalid")
    return value
