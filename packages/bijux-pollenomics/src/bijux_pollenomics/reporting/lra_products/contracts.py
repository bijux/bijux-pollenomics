"""Presentation identities and strict input encoding; no scientific admission."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Any


class LRAPresentationRefusal(ValueError):
    """A presentation input or output cannot satisfy its declared contract."""

    def __init__(self, reason_code: str, detail: str) -> None:
        self.reason_code = reason_code
        super().__init__(f"{reason_code}: {detail}")


@dataclass(frozen=True)
class LRAPresentation:
    """An exploratory report identity, without publication or scientific approval."""

    directory: Path
    manifest_sha256: str
    product_manifest_sha256: str
    geometry_sha256: str
    mapped_site_count: int
    refused_site_count: int


def canonical(value: object) -> bytes:
    """Encode finite deterministic JSON with an intentional terminal newline."""
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def require_digest(value: str) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise LRAPresentationRefusal("invalid_expected_digest", "Expected SHA-256 hex")


def json_object(value: bytes) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = item
        return result

    result = json.loads(value, object_pairs_hook=unique)
    if not isinstance(result, dict):
        raise ValueError("Expected JSON object")
    canonical(result)
    return result


def regular_bytes(path: Path) -> bytes:
    """Read only regular files, refusing visible symlink ancestors and endpoints."""
    path = path.absolute()
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError("Symbolic links are not presentation inputs")
    descriptor = os.open(
        path, os.O_RDONLY | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0)
    )
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("Presentation input is not a regular file")
        return stream.read()


def bound_bytes(path: Path, expected: str) -> bytes:
    require_digest(expected)
    value = regular_bytes(path)
    if digest(value) != expected:
        raise LRAPresentationRefusal("changed_presentation_input", path.name)
    return value


__all__ = ["LRAPresentation", "LRAPresentationRefusal"]
