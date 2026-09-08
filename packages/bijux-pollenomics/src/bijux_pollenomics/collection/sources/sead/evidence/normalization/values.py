"""Primitive value parsing for SEAD evidence normalization."""

from __future__ import annotations

from ......core.text import clean_optional_text


def parse_optional_float(value: object) -> float | None:
    """Parse one optional numeric field as float."""
    if isinstance(value, (int, float)):
        return float(value)
    text = clean_optional_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_int_or_default(value: object, *, default: int = 0) -> int:
    """Parse one optional numeric field as integer with fallback."""
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = clean_optional_text(value)
    if not text:
        return default
    try:
        return int(text)
    except ValueError:
        return default
