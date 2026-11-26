"""Capture and validate governed animal chronology source JSON rows."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import cast

_Row = dict[str, object]


def _read_object(
    path: Path,
    *,
    captured_inputs: dict[Path, bytes],
    held: Mapping[str, bytes] | None = None,
    source_root: Path | None = None,
) -> _Row:
    if held is None and (not path.is_file() or path.is_symlink()):
        raise ValueError(f"governed animal chronology input is unavailable: {path}")
    try:
        if held is None:
            content = path.read_bytes()
        else:
            if source_root is None:
                raise ValueError("animal chronology captured root differs")
            content = held[path.relative_to(source_root).as_posix()]
        value = json.loads(content.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError) as exc:
        raise ValueError(f"invalid governed animal chronology JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"governed animal chronology root must be an object: {path}")
    captured_inputs[path] = content
    return cast(_Row, value)


def _rows(payload: Mapping[str, object], label: str) -> list[_Row]:
    value = payload.get("rows")
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"{label} rows must be a list of objects")
    return cast(list[_Row], value)
