"""Strict admission of source and publication cardinalities."""

from __future__ import annotations

from collections.abc import Mapping


def require_nonnegative_count(value: object, *, field: str) -> int:
    """Return one declared count without coercing nulls, booleans, or text."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a nonnegative integer")
    return value


def resolve_declared_count(
    payload: Mapping[str, object],
    key: str,
    *,
    field: str,
    absent_default: int,
) -> int:
    """Resolve an optional legacy field while refusing malformed declarations."""
    fallback = require_nonnegative_count(absent_default, field=f"{field} fallback")
    if key not in payload:
        return fallback
    return require_nonnegative_count(payload[key], field=field)


__all__ = ["require_nonnegative_count", "resolve_declared_count"]
