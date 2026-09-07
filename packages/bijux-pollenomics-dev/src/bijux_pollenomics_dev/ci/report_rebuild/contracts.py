"""Strict contracts shared by partitioned report rebuild stages."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import stat
from typing import cast

JsonObject = dict[str, object]


class ReportRebuildError(RuntimeError):
    """Raised when partitioned report evidence is incomplete or inconsistent."""


@dataclass(frozen=True)
class RebuildBinding:
    """Content identity shared by every job in one rebuild DAG."""

    policy_sha256: str
    repository: JsonObject
    inputs_sha256: str

    def as_json(self) -> JsonObject:
        """Return the stable serialized binding."""
        return {
            "policy_sha256": self.policy_sha256,
            "repository": self.repository,
            "inputs_sha256": self.inputs_sha256,
        }


def sha256_bytes(payload: bytes) -> str:
    """Return a lowercase SHA-256 digest."""
    return hashlib.sha256(payload).hexdigest()


def canonical_json_sha256(value: object) -> str:
    """Digest one JSON value using a stable encoding."""
    return sha256_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    )


def require_mapping(value: object, label: str) -> JsonObject:
    """Return a string-keyed object or reject the value."""
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ReportRebuildError(f"{label} must be an object")
    return cast(JsonObject, value)


def require_string(value: object, label: str) -> str:
    """Return a non-empty string or reject the value."""
    if not isinstance(value, str) or not value:
        raise ReportRebuildError(f"{label} must be a non-empty string")
    return value


def require_string_sequence(value: object, label: str) -> tuple[str, ...]:
    """Return a unique non-empty string sequence or reject it."""
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ReportRebuildError(f"{label} must be a non-empty string list")
    items = cast(list[str], value)
    if not items or len(items) != len(set(items)):
        raise ReportRebuildError(f"{label} must be non-empty and unique")
    return tuple(items)


def load_json(path: Path, label: str) -> JsonObject:
    """Load one strict JSON object."""
    try:
        if not stat.S_ISREG(path.lstat().st_mode) or path.is_symlink():
            raise ReportRebuildError(f"{label} must be a regular file: {path}")
        return require_mapping(json.loads(path.read_text(encoding="utf-8")), label)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReportRebuildError(f"cannot load {label}: {path}") from error


def atomic_write_json(path: Path, value: Mapping[str, object]) -> None:
    """Write stable JSON without exposing a partial manifest."""
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.with_name(f".{path.name}.writing")
    if staging.exists() or staging.is_symlink():
        raise ReportRebuildError(f"manifest staging path already exists: {staging}")
    staging.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    staging.replace(path)


def parse_binding(value: object, label: str) -> RebuildBinding:
    """Parse an exact rebuild binding object."""
    record = require_mapping(value, label)
    if set(record) != {"inputs_sha256", "policy_sha256", "repository"}:
        raise ReportRebuildError(f"{label} fields are not exact")
    repository = require_mapping(record["repository"], f"{label}.repository")
    return RebuildBinding(
        policy_sha256=require_string(record["policy_sha256"], f"{label}.policy_sha256"),
        repository=repository,
        inputs_sha256=require_string(record["inputs_sha256"], f"{label}.inputs_sha256"),
    )


def require_exact_binding(
    observed: RebuildBinding, expected: RebuildBinding, label: str
) -> None:
    """Reject evidence from another policy, input tree, or repository identity."""
    if observed != expected:
        raise ReportRebuildError(f"{label} rebuild binding does not match the plan")


def inventory_payload_sha256(entries: Sequence[Mapping[str, object]]) -> str:
    """Digest an ordered inventory payload."""
    return canonical_json_sha256(list(entries))
