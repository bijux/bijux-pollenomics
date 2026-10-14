"""Describe native-versus-stored JSON changes without treating them as harmless."""

from __future__ import annotations

from fractions import Fraction
import json
from typing import Any


def canonical(value: object) -> bytes:
    """Retain JSON scalar types, including booleans versus integer identifiers."""
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode()


def same(value: object, native: object, label: str) -> None:
    if canonical(value) != canonical(native):
        raise ValueError("Native annotation differs: " + label)


def json_type(value: object) -> str:
    if value is None:
        return "null"
    if type(value) is bool:
        return "boolean"
    if type(value) is int:
        return "integer"
    if type(value) is float:
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


def compare_field(field: str, raw: object, stored: dict[str, Any]) -> dict[str, Any]:
    present = field in stored
    category = "omitted"
    if present:
        value = stored[field]
        if canonical(raw) == canonical(value):
            category = "exact"
        elif raw is None and value == "" and type(value) is str:
            category = "null_to_empty_string"
        elif raw is None and type(value) is bool:
            category = "null_to_boolean"
        elif raw is None:
            category = "null_to_other_value"
        elif type(raw) is bool or type(value) is bool:
            category = (
                "boolean_value_changed"
                if type(raw) is bool and type(value) is bool
                else "boolean_type_changed"
            )
        elif isinstance(raw, (int, float)) and isinstance(value, (int, float)):
            category = (
                "numeric_representation_changed_equal_value"
                if Fraction(raw) == Fraction(value)
                else "numeric_value_changed"
            )
        elif isinstance(raw, str) and isinstance(value, str):
            category = (
                "text_whitespace_changed"
                if raw.strip() == value
                else "text_value_changed"
            )
        else:
            category = "json_type_or_value_changed"
    return {
        "field": field,
        "category": category,
        "raw_type": json_type(raw),
        "stored_present": present,
        "stored_type": json_type(stored[field]) if present else None,
        "native_unknown_flag": raw is None and field.endswith("is_uncertain"),
        "scientific_equivalence_approved": False,
    }
