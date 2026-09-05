"""Scalar and sequence validation primitives for classification audits."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast

from .constants import SHA256_PATTERN
from .models import ClassificationAuditRefusalError


def mapping_sequence(
    value: object, *, field_name: str
) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        refuse("invalid_accounting_schema", f"{field_name} must be an array")
    value = cast(Sequence[object], value)
    if not all(isinstance(row, Mapping) for row in value):
        refuse("invalid_accounting_schema", f"{field_name} rows must be objects")
    return tuple(row for row in value if isinstance(row, Mapping))


def sequence_values(value: object, *, field_name: str) -> tuple[object, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        refuse("invalid_classification_record", f"{field_name} must be an array")
    return tuple(cast(Sequence[object], value))


def required_text(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        refuse("invalid_accounting_schema", f"{field_name} must be non-empty")
    return cast(str, value).strip()


def required_digest(value: object, *, field_name: str) -> str:
    text = required_text(value, field_name=field_name)
    if SHA256_PATTERN.fullmatch(text) is None:
        refuse(
            "invalid_contract_digest",
            f"{field_name} must be a prefixed SHA-256 digest",
        )
    return text


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def refuse(reason_code: str, detail: str) -> None:
    raise ClassificationAuditRefusalError(reason_code, detail)
