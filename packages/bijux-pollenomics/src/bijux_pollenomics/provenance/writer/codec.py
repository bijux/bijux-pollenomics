"""Canonical JSON encoding and typed field access."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import cast

from ..release_evidence import ReleaseEvidenceError


def _load_json(payload: bytes) -> Mapping[str, object]:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ReleaseEvidenceError(f"duplicate JSON field: {key}")
            result[key] = value
        return result

    value = json.loads(payload, object_pairs_hook=reject_duplicates)
    return _mapping(value, "JSON document")


def _canonical_bytes(value: Mapping[str, object]) -> bytes:
    try:
        return (
            json.dumps(
                dict(value),
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
    except (TypeError, ValueError) as error:
        raise ReleaseEvidenceError("release evidence is not canonical JSON") from error


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ReleaseEvidenceError(f"{field} must be an object with string keys")
    return cast(Mapping[str, object], value)


def _mapping_field(record: Mapping[str, object], field: str) -> Mapping[str, object]:
    return _mapping(record[field], field)


def _list_field(record: Mapping[str, object], field: str) -> list[object]:
    value = record[field]
    if not isinstance(value, list):
        raise ReleaseEvidenceError(f"{field} must be a list")
    return value


def _string_value(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ReleaseEvidenceError(f"{field} must be a string")
    return value


def _string_field(record: Mapping[str, object], field: str) -> str:
    return _string_value(record[field], field)


def _bool_field(record: Mapping[str, object], field: str) -> bool:
    value = record[field]
    if type(value) is not bool:
        raise ReleaseEvidenceError(f"{field} must be a boolean")
    return value


def _optional_string_field(record: Mapping[str, object], field: str) -> str | None:
    value = record[field]
    if value is not None and not isinstance(value, str):
        raise ReleaseEvidenceError(f"{field} must be a string or null")
    return value


def _int_field(record: Mapping[str, object], field: str) -> int:
    value = record[field]
    if type(value) is not int:
        raise ReleaseEvidenceError(f"{field} must be an integer")
    return value


def _optional_int_field(record: Mapping[str, object], field: str) -> int | None:
    value = record[field]
    if value is not None and type(value) is not int:
        raise ReleaseEvidenceError(f"{field} must be an integer or null")
    return value
