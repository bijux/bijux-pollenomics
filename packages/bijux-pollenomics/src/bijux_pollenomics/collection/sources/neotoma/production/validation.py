from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any


def validated_input_directory(path: Path, label: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        raise ValueError(f"{label} path must be absolute")
    if candidate.is_symlink() or not candidate.is_dir():
        raise ValueError(f"{label} must be a non-symlink directory: {candidate}")
    return candidate.resolve(strict=True)


def validated_output_target(
    output_root: Path,
    approved_parent: Path,
    *,
    validate_directory: Any = validated_input_directory,
) -> Path:
    output = Path(output_root)
    parent = Path(approved_parent)
    if not output.is_absolute() or not parent.is_absolute():
        raise ValueError("Output and approved output parent must be absolute")
    resolved_parent = validate_directory(parent, "approved output parent")
    if output.exists() and output.is_symlink():
        raise ValueError("Neotoma production output must not be a symlink")
    resolved_output_parent = output.parent.resolve(strict=True)
    resolved_output = (resolved_output_parent / output.name).resolve(strict=False)
    if resolved_output == resolved_parent or not resolved_output.is_relative_to(
        resolved_parent
    ):
        raise ValueError("Neotoma production output is outside its approved parent")
    return resolved_output


def read_regular_file(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Required input is not a regular file: {path}")
    return path.read_bytes()


def json_object(
    content: bytes, path: Path, *, json_module: Any = json
) -> dict[str, object]:
    try:
        payload = json_module.loads(content)
    except (UnicodeDecodeError, json_module.JSONDecodeError) as error:
        raise ValueError(f"Invalid JSON input: {path}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"JSON input must be an object: {path}")
    return payload


def mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return value


def positive_integer(
    value: object,
    label: str,
    *,
    parse_integer: Callable[[object, str], int] = integer,
) -> int:
    result = parse_integer(value, label)
    if result < 1:
        raise ValueError(f"{label} must be positive")
    return result


def non_negative_integer(
    value: object,
    label: str,
    *,
    parse_integer: Callable[[object, str], int] = integer,
) -> int:
    result = parse_integer(value, label)
    if result < 0:
        raise ValueError(f"{label} must be non-negative")
    return result


def integer_list(
    value: object,
    label: str,
    *,
    parse_integer: Callable[[object, str], int] = integer,
) -> list[int]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return [parse_integer(item, label) for item in value]


def expect_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label} mismatch: expected {expected!r}, got {actual!r}")


def canonical_digest(
    payload: object, *, json_module: Any = json, hashlib_module: Any = hashlib
) -> str:
    content = json_module.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return str(hashlib_module.sha256(content).hexdigest())
