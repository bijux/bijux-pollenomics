"""Typed identities and JSON boundaries for quarantined workbook review."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import NoReturn

from ...quarantine import IntakeRefusal

SCHEMA = "quarantined-rootsi-cell-review.v1"
PARSER_VERSION = "2.0.2"
MEMBERS = (
    "workbooks.json",
    "sheets.jsonl",
    "cells.jsonl",
    "accounting.json",
    "capture-inventory.json",
)


def refuse(reason: str, detail: str) -> NoReturn:
    """Raise a source-specific refusal without implying scientific admission."""
    raise IntakeRefusal(f"rootsi_cells_{reason}", detail)


def object_value(value: object, field: str) -> dict[str, object]:
    """Require a JSON object with string keys."""
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        refuse("invalid_object", field)
    return dict(value)


def sequence(value: object, field: str) -> list[object]:
    """Require a JSON array."""
    if not isinstance(value, list):
        refuse("invalid_array", field)
    return list(value)


def integer(value: object, field: str, *, minimum: int = 0) -> int:
    """Require an exact nonboolean integer."""
    if type(value) is not int or value < minimum:
        refuse("invalid_integer", field)
    return value


def text(value: object, field: str, *, empty: bool = False) -> str:
    """Require source text without normalization."""
    if not isinstance(value, str) or (not empty and not value):
        refuse("invalid_text", field)
    return value


def digest(value: object, field: str) -> str:
    """Require a lowercase SHA256 identity."""
    result = text(value, field)
    if re.fullmatch(r"[a-f0-9]{64}", result) is None:
        refuse("invalid_digest", field)
    return result


def encoded(value: object) -> bytes:
    """Encode deterministic finite JSON with a terminal newline."""
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            refuse("duplicate_json_key", key)
        result[key] = value
    return result


def _constant(value: str) -> object:
    refuse("nonfinite_json", value)


def decoded(payload: bytes) -> object:
    """Read JSON without duplicate keys or nonfinite extensions."""
    try:
        return json.loads(payload, object_pairs_hook=_pairs, parse_constant=_constant)
    except (UnicodeError, ValueError) as exc:
        refuse("invalid_json", str(exc))


def byte_identity(payload: bytes) -> dict[str, object]:
    """Bind exact bytes."""
    return {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}


@dataclass(frozen=True)
class WorkbookInput:
    """A file bound to one exact retained archive-member claim."""

    archive_member: str
    path: Path
    sha256: str
    byte_count: int

    def as_dict(self) -> dict[str, object]:
        """Return portable identity, excluding machine-local path."""
        return {
            "archive_member": self.archive_member,
            "sha256": self.sha256,
            "bytes": self.byte_count,
        }


@dataclass(frozen=True)
class Capture:
    """Pinned retained inventory and selected workbook-file bindings."""

    inventory_path: Path
    inventory_sha256: str
    inventory_bytes: int
    archive_sha256: str
    scope: str
    available_workbooks: int
    workbooks: tuple[WorkbookInput, ...]

    def as_dict(self) -> dict[str, object]:
        """Expose honest retained-receipt custody and selected scope."""
        return {
            "inventory_sha256": self.inventory_sha256,
            "inventory_bytes": self.inventory_bytes,
            "archive_sha256": self.archive_sha256,
            "scope": self.scope,
            "available_workbooks": self.available_workbooks,
            "archive_membership_verification": "retained_receipt_bound_not_replayed",
            "selected_workbooks": [item.as_dict() for item in self.workbooks],
        }


@dataclass(frozen=True)
class ReviewBundle:
    """Pinned retained review identity; this is not observation admission."""

    directory: Path
    manifest_sha256: str
    _accounting_json: bytes

    @property
    def accounting(self) -> dict[str, object]:
        """Return an owned copy; mutation cannot alter this bundle identity."""
        return object_value(decoded(self._accounting_json), "accounting")
