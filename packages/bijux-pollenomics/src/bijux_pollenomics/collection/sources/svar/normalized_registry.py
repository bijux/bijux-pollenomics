"""Minimal shape check for the governing normalized SVAR registry."""

from __future__ import annotations

import json
from pathlib import Path


def normalized_registry_is_readable(path: Path) -> bool:
    """Recognize a registry document before interpreting its feature count."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return (
        isinstance(payload, dict)
        and payload.get("type") == "FeatureCollection"
        and isinstance(payload.get("features"), list)
        and all(
            isinstance(feature, dict)
            and feature.get("type") == "Feature"
            and isinstance(feature.get("geometry"), dict)
            and isinstance(feature.get("properties"), dict)
            for feature in payload["features"]
        )
    )
