"""Canonical JSON, SHA-256, strict text, and refusal primitives."""

from __future__ import annotations
import hashlib
import json
from typing import NoReturn

from .models import PropagationOutputRefusalError


def _canonical_json_bytes(payload: object) -> bytes:
    try:
        rendered = json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
    except (TypeError, ValueError) as error:
        raise PropagationOutputRefusalError(
            "invalid_output_serialization",
            "propagation output must be finite canonical JSON",
        ) from error
    return f"{rendered}\n".encode()


def _validate_sha256(value: object, *, field_name: str) -> None:
    if not _is_sha256_digest(value):
        _refuse("invalid_build_identity", f"{field_name} must be a SHA-256 digest")


def _is_sha256_digest(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _required_text(value: object, *, field_name: str) -> str:
    if type(value) is not str or not value.strip():
        _refuse("invalid_build_identity", f"{field_name} must be non-empty")
    return value.strip()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _refuse(reason_code: str, detail: str) -> NoReturn:
    raise PropagationOutputRefusalError(reason_code, detail)
