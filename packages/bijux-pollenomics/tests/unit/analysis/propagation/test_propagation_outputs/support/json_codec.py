"""Canonical JSON helpers for propagation output tests."""

from __future__ import annotations

import json
from pathlib import Path


def canonical_json_bytes(value: object) -> bytes:
    """Serialize a fixture using the product's canonical JSON shape."""
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode()


def read_json(path: Path) -> dict[str, object]:
    """Read and narrow a JSON object fixture."""
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value
