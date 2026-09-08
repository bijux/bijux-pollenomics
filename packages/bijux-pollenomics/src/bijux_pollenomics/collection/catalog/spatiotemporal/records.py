"""Safe readers and scalar coercions for posture evidence."""

from __future__ import annotations

import json
from pathlib import Path

__all__ = []


def _load_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _geojson_features(payload: dict[str, object]) -> list[dict[str, object]]:
    features = payload.get("features")
    if not isinstance(features, list):
        return []
    return [feature for feature in features if isinstance(feature, dict)]


def _feature_has_numeric_interval(feature: dict[str, object]) -> bool:
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        return False
    start = properties.get("time_start_bp")
    end = properties.get("time_end_bp")
    return isinstance(start, (int, float)) or isinstance(end, (int, float))


def _dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip()
    if not text:
        return 0
    try:
        return int(text)
    except ValueError:
        return 0
