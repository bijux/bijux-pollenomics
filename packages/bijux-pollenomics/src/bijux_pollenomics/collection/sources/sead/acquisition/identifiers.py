"""Exact SEAD source keys, independent of chronology and measurement parsing."""

from __future__ import annotations


def required_sead_identifier(value: object) -> int:
    """Read a positive native integer or ASCII decimal string without rounding."""
    if isinstance(value, str) and value.isascii() and value.isdecimal():
        value = int(value)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"Invalid SEAD source identifier: {value!r}")
    return value


def optional_sead_identifier(value: object) -> int | None:
    """Preserve a missing key while refusing non-null invalid source identities."""
    return None if value is None else required_sead_identifier(value)
