"""Canonical identity and input indexing for source-native nodes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
from math import isfinite
from typing import TypeGuard


def canonical(value: object) -> str:
    """Serialize a JSON-like value for deterministic comparison and hashing."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest(value: object) -> str:
    """Return a deterministic SHA-256 digest for a JSON-like value."""
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def optional_text(value: object) -> str | None:
    """Return a stripped non-empty string or ``None``."""
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def finite_number(value: object) -> TypeGuard[float | int]:
    """Return whether a value is a finite real number, excluding booleans."""
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and isfinite(float(value))
    )


def unique_index(
    rows: Sequence[Mapping[str, object]], key_name: str
) -> tuple[dict[str, Mapping[str, object]], set[str]]:
    """Index rows and identify keys carrying conflicting representations."""
    result: dict[str, Mapping[str, object]] = {}
    conflicts: set[str] = set()
    for row in rows:
        key = optional_text(row.get(key_name))
        if key is None:
            continue
        existing = result.get(key)
        if existing is None:
            result[key] = row
        elif canonical(existing) != canonical(row):
            conflicts.add(key)
    return result, conflicts


def observation_index(
    rows: Sequence[Mapping[str, object]],
) -> tuple[dict[str, Mapping[str, object]], set[str], int]:
    """Index observations while refusing every duplicated source identity."""
    result: dict[str, Mapping[str, object]] = {}
    duplicates: set[str] = set()
    duplicate_row_count = 0
    for row in rows:
        observation_id = optional_text(row.get("observation_id"))
        if observation_id is None:
            raise ValueError("source observation requires observation_id")
        if observation_id in result:
            duplicates.add(observation_id)
            duplicate_row_count += 1
        else:
            result[observation_id] = row
    return result, duplicates, duplicate_row_count


__all__ = [
    "canonical",
    "digest",
    "finite_number",
    "observation_index",
    "optional_text",
    "unique_index",
]
