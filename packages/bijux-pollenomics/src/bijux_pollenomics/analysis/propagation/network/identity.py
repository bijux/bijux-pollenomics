"""Deterministic propagation identifiers and digests."""

from __future__ import annotations

import hashlib


def _stable_id(prefix: str, *values: str) -> str:
    return f"{prefix}:{_stable_digest(*values)[:24]}"


def _stable_digest(*values: str) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()
