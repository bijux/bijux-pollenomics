from __future__ import annotations

import importlib
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType
from typing import cast


def _surface() -> ModuleType:
    return importlib.import_module(__package__ or "")


def _write_atomic(path: Path, content: bytes) -> None:
    _surface().write_atomic(path, content)


def _read_regular_file(path: Path) -> bytes:
    return cast(bytes, _surface().read_regular_file(path))


def _json_object(content: bytes, label: str) -> dict[str, object]:
    surface = _surface()
    return cast(
        dict[str, object],
        surface.json_object(content, label, json_module=surface.json),
    )


def _mapping(value: object, label: str) -> Mapping[str, object]:
    return cast(Mapping[str, object], _surface().mapping(value, label))


def _required_text(value: object, label: str) -> str:
    return str(_surface().required_text(value, label))


def _non_negative_integer(value: object, label: str) -> int:
    return int(_surface().non_negative_integer(value, label))


def _safe_filename(value: str) -> str:
    return str(_surface().safe_filename(value))


def _safe_public_path(value: str) -> str:
    return str(_surface().safe_public_path(value))


def _canonical_json(payload: object) -> bytes:
    surface = _surface()
    return cast(bytes, surface.canonical_json(payload, json_module=surface.json))
