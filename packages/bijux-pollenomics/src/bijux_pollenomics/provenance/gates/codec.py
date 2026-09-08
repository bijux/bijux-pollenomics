"""Canonical recorded-gate JSON encoding and identities."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json

from ..release_evidence import ReleaseEvidenceError


def _canonical_bytes(value: Mapping[str, object]) -> bytes:
    try:
        return (
            json.dumps(
                dict(value),
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
    except (TypeError, ValueError) as error:
        raise ReleaseEvidenceError("gate evidence is not canonical JSON") from error


def _digest_json(value: object) -> str:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ReleaseEvidenceError("gate evidence is not canonical JSON") from error
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"
