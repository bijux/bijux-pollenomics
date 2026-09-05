"""Text normalization shared by Homo sapiens metadata boundaries."""

from __future__ import annotations


def clean_text(value: str | None) -> str:
    """Collapse source whitespace without inventing missing values."""
    return " ".join((value or "").split()).strip()
