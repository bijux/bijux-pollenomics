from __future__ import annotations


def pick_value(left: str, right: str) -> str:
    """Keep the first non-empty value when merging duplicate sample rows."""
    return left if left else right


__all__ = ["pick_value"]
