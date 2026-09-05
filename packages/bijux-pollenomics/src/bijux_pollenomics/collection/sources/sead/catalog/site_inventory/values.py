"""Strict parsing for SEAD catalog scalar fields."""

from __future__ import annotations

import math

from bijux_pollenomics.core.text import clean_optional_text

def parse_optional_int(value: object) -> int | None:
    """Parse one optional integer-like SEAD field."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return int(round(value))
    text = clean_optional_text(value)
    if not text:
        return None
    try:
        return int(round(float(text)))
    except (OverflowError, ValueError):
        return None



def parse_required_int(value: object) -> int:
    """Parse one required SEAD integer-like field or fall back to zero."""
    return parse_optional_int(value) or 0



__all__ = ["parse_optional_int", "parse_required_int"]
