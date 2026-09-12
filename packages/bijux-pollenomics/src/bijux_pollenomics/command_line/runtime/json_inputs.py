"""Strict JSON object inputs shared by reconstruction command handlers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject ambiguous duplicate fields without silently keeping the last value."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_object(path: Path) -> dict[str, Any]:
    """Read a finite JSON object with no value or field coercion."""
    payload = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs
    )
    if not isinstance(payload, dict):
        raise TypeError("Request must be a JSON object")
    json.dumps(payload, allow_nan=False)
    return payload
