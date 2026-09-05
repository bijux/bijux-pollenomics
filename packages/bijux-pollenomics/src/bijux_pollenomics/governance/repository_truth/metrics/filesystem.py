"""Filesystem and serialization primitives for repository evidence metrics."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import cast

__all__: list[str] = []


def _count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for file_path in path.iterdir() if file_path.is_file())


def _count_tree_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for file_path in path.rglob("*") if file_path.is_file())


def _count_suffix_files(path: Path, suffix: str) -> int:
    if not path.exists():
        return 0
    return sum(1 for file_path in path.rglob(f"*{suffix}") if file_path.is_file())


def _count_geojson_features(path: Path) -> int:
    if not path.exists():
        return 0
    payload = _load_json(path)
    return len(list(cast(Iterable[object], payload.get("features", []))))


def _format_metric_map(metrics: dict[str, object]) -> str:
    return ", ".join(f"`{key}` {value}" for key, value in metrics.items())


def _load_json(path: Path) -> dict[str, object]:
    return cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))


def _load_json_or_default(path: Path, default: dict[str, object]) -> dict[str, object]:
    if not path.exists():
        return default
    return _load_json(path)
