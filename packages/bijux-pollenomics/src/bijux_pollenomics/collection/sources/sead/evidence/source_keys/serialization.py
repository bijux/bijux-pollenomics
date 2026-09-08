"""Canonical serialization for SEAD source-key identities."""

from __future__ import annotations

import hashlib
import json


def canonical_bytes(value: object) -> bytes:
    """Serialize one source-key value with the repository JSON convention."""
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def canonical_sha256(value: object) -> str:
    """Digest one canonically serialized source-key value."""
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


__all__ = ["canonical_bytes", "canonical_sha256"]
