from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from .models import _Target as Target


def load_features(path: Path, *, json_module: Any) -> list[dict[str, object]]:
    payload = json_module.loads(path.read_text(encoding="utf-8"))
    return [
        feature for feature in payload.get("features", []) if isinstance(feature, dict)
    ]


def target_landclim_features(
    target: Target,
    features: list[dict[str, object]],
    *,
    dataset_id: str,
    contains: Callable[..., bool],
) -> list[dict[str, object]]:
    selected = []
    for feature in features:
        properties: Any = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        if properties.get("dataset_id") != dataset_id:
            continue
        if contains(geometry, longitude=target.longitude, latitude=target.latitude):
            selected.append(feature)
    selected.sort(key=lambda feature: int(feature["properties"]["time_start_bp"]))  # type: ignore[index]
    return selected
