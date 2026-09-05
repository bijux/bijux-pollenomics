from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path, PurePosixPath
from typing import Any, cast


def write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError(f"Neotoma review output cannot use symlinks: {path}")
    candidate = path.parent / f".{path.name}.candidate"
    if candidate.exists() or candidate.is_symlink():
        raise FileExistsError(f"Neotoma review candidate path exists: {candidate}")
    try:
        with candidate.open("xb") as stream:
            stream.write(content)
        candidate.replace(path)
    finally:
        if candidate.exists():
            candidate.unlink()


def read_regular_file(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Neotoma review input is not a regular file: {path}")
    return path.read_bytes()


def json_object(
    content: bytes, label: str, *, json_module: Any = json
) -> dict[str, object]:
    try:
        payload = json_module.loads(content)
    except (UnicodeDecodeError, json_module.JSONDecodeError) as error:
        raise ValueError(f"Invalid JSON for {label}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"JSON must be an object for {label}")
    return payload


def mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"Expected object for {label}")
    return value


def required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Expected non-empty text for {label}")
    return value


def non_negative_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"Expected non-negative integer for {label}")
    return value


def safe_filename(value: str) -> str:
    candidate = PurePosixPath(value)
    if len(candidate.parts) != 1 or value in {"", ".", ".."}:
        raise ValueError(f"Unsafe Neotoma raw filename: {value!r}")
    return value


def safe_public_path(value: str) -> str:
    candidate = PurePosixPath(value)
    if not value or candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"Unsafe Neotoma public path: {value!r}")
    return candidate.as_posix()


def canonical_json(payload: object, *, json_module: Any = json) -> bytes:
    return cast(
        bytes,
        (
            json_module.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        ).encode("utf-8"),
    )
