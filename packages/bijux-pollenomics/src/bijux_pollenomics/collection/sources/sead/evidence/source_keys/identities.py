"""Canonical identity primitives for SEAD source-key evidence."""

from __future__ import annotations

from uuid import UUID


def canonical_site_uuid(value: object) -> str:
    """Require the lowercase hyphenated canonical UUID representation."""
    if not isinstance(value, str):
        raise ValueError("SEAD site UUID must be canonical text")
    try:
        parsed = UUID(value)
    except (AttributeError, ValueError) as exc:
        raise ValueError("SEAD site UUID must be canonical text") from exc
    if str(parsed) != value:
        raise ValueError("SEAD site UUID must be lowercase canonical text")
    return value


__all__ = ["canonical_site_uuid"]
