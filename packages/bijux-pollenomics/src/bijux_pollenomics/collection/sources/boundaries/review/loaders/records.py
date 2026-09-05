"""Source-record validation and lineage helpers for boundary review."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from ..models import JsonObject
from ..serialization import _file_sha256, _optional_text, _required_number


def _point_feature(
    feature: Mapping[str, object], source: str
) -> tuple[Mapping[str, object], float, float]:
    properties = feature.get("properties")
    geometry = feature.get("geometry")
    if not isinstance(properties, Mapping) or not isinstance(geometry, Mapping):
        raise TypeError(f"{source} point feature is incomplete")
    if geometry.get("type") != "Point":
        raise ValueError(
            f"{source} governed point surface contains a non-point feature"
        )
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, Sequence) or isinstance(coordinates, str):
        raise TypeError(f"{source} point coordinates are invalid")
    if len(coordinates) < 2:
        raise ValueError(f"{source} point coordinates are incomplete")
    return (
        properties,
        _required_number(coordinates[0], f"{source} longitude"),
        _required_number(coordinates[1], f"{source} latitude"),
    )


def _popup_value(properties: Mapping[str, object], label: str) -> str | None:
    rows = properties.get("popup_rows")
    if not isinstance(rows, list):
        return None
    for row in rows:
        if isinstance(row, Mapping) and row.get("label") == label:
            return _optional_text(row.get("value"))
    return None


def _artifact_records(root: Path, paths: Iterable[Path]) -> list[JsonObject]:
    records: list[JsonObject] = []
    for path in paths:
        absolute = root / path
        if not absolute.is_file():
            raise ValueError(f"Governed source artifact is missing: {path}")
        records.append(
            {
                "path": path.as_posix(),
                "sha256": _file_sha256(absolute),
                "bytes": absolute.stat().st_size,
            }
        )
    return records


def _lineage(path: Path, locator: str, role: str) -> JsonObject:
    return {"role": role, "path": path.as_posix(), "locator": locator}


def _safe_relative_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Source lineage path must be repository-relative: {value}")
    return path
