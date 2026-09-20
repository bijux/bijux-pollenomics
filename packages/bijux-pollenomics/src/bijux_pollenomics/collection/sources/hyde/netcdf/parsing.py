"""Strict bounded parsing primitives for retained HYDE declarations."""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any, cast

from ...quarantine import IntakeRefusal
from ..local.contracts import checked_path, digest, sha256


def read_pinned(path: Path, expected: str, limit: int, role: str) -> bytes:
    """Read one compact input after path, size and digest validation."""
    digest(expected)
    source = checked_path(path)
    if source.is_symlink() or not source.is_file():
        raise IntakeRefusal("hyde_netcdf_input_invalid", role)
    try:
        with source.open("rb") as handle:
            content = handle.read(limit + 1)
    except OSError as exc:
        raise IntakeRefusal("hyde_netcdf_input_unreadable", role) from exc
    if len(content) > limit:
        raise IntakeRefusal("hyde_netcdf_input_limit", role)
    if sha256(content) != expected:
        raise IntakeRefusal("hyde_netcdf_digest_mismatch", role)
    return content


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise IntakeRefusal("hyde_netcdf_json_duplicate_key", key)
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> object:
    raise ValueError(value)


def json_value(content: bytes, role: str) -> object:
    try:
        return json.loads(
            content.decode("utf-8"),
            object_pairs_hook=_unique,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeDecodeError, TypeError, ValueError) as exc:
        if isinstance(exc, IntakeRefusal):
            raise
        raise IntakeRefusal("hyde_netcdf_json_invalid", role) from exc


def json_lines(content: bytes, role: str) -> list[object]:
    try:
        lines = content.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise IntakeRefusal("hyde_netcdf_json_invalid", role) from exc
    if not lines:
        raise IntakeRefusal("hyde_netcdf_json_invalid", role)
    return [json_value((line + "\n").encode(), role) for line in lines]


def obj(value: object, fields: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise IntakeRefusal("hyde_netcdf_schema_invalid", label)
    if any(not isinstance(key, str) for key in value):
        raise IntakeRefusal("hyde_netcdf_schema_invalid", label)
    return dict(value)


def string_object(value: object, label: str) -> dict[str, str]:
    if not isinstance(value, Mapping) or not value:
        raise IntakeRefusal("hyde_netcdf_schema_invalid", label)
    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise IntakeRefusal("hyde_netcdf_schema_invalid", label)
        result[key] = text(item, f"{label}.{key}")
    return result


def array(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise IntakeRefusal("hyde_netcdf_schema_invalid", label)
    return list(value)


def text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise IntakeRefusal("hyde_netcdf_text_invalid", label)
    return value


def integer(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise IntakeRefusal("hyde_netcdf_integer_invalid", label)
    return value


def boolean(value: object, label: str) -> bool:
    if type(value) is not bool:
        raise IntakeRefusal("hyde_netcdf_boolean_invalid", label)
    return value


def number(value: object, label: str) -> float:
    if type(value) not in {int, float}:
        raise IntakeRefusal("hyde_netcdf_number_invalid", label)
    result = float(cast(float, value))
    if result != result or result in {float("inf"), float("-inf")}:
        raise IntakeRefusal("hyde_netcdf_number_invalid", label)
    return result
