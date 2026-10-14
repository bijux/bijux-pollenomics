"""Lossless JSON source metadata for chronology contracts."""

from __future__ import annotations

from collections.abc import Mapping
from math import isfinite


def _source_metadata_copy(
    metadata: Mapping[str, object] | None,
    *,
    reserved: Mapping[str, object],
) -> dict[str, object]:
    """Retain explicit JSON source assertions without overriding computed semantics."""
    if metadata is None:
        return {}
    result: dict[str, object] = {}
    for key, item in metadata.items():
        if not isinstance(key, str) or key in reserved:
            raise ValueError("Source metadata must use noncanonical string keys")
        result[key] = _json_metadata_copy(item, seen=set())
    return result


def _json_metadata_copy(value: object, *, seen: set[int]) -> object:
    """Copy JSON metadata exactly; reject nonfinite values and non-JSON objects."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("Source metadata numbers must be finite")
        return value
    if isinstance(value, (dict, list)):
        identity = id(value)
        if identity in seen:
            raise ValueError("Source metadata must not contain cycles")
        seen.add(identity)
        try:
            if isinstance(value, list):
                return [_json_metadata_copy(item, seen=seen) for item in value]
            result: dict[str, object] = {}
            for key, item in value.items():
                if not isinstance(key, str):
                    raise ValueError("Source metadata object keys must be strings")
                result[key] = _json_metadata_copy(item, seen=seen)
            return result
        finally:
            seen.remove(identity)
    raise ValueError("Source metadata must contain only JSON values")
