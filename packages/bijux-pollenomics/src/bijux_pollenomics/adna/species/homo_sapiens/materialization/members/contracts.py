"""Versioned source-evidence ownership contracts; no scientific admission."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
import json
import re
from typing import cast

SCHEMA_VERSION = "aadr-metadata-evidence-members.v1"
MEMBER_FILES = (
    "source_files.json",
    "source_rows.ndjson",
    "members.ndjson",
    "coordinate_claims.ndjson",
    "chronology_claims.ndjson",
    "unkeyed_rows.ndjson",
)


def canonical_bytes(value: object) -> bytes:
    """Encode deterministic finite JSON, preserving exact Unicode/token text."""
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode()


def object_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(k, str) for k in value):
        raise ValueError("AADR member object required")
    return cast(dict[str, object], value)


def object_rows(value: object) -> tuple[dict[str, object], ...]:
    if not isinstance(value, list):
        raise ValueError("AADR member object array required")
    return tuple(object_mapping(item) for item in value)


def text(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("AADR member text required")
    return value


def strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(v, str) for v in value):
        raise ValueError("AADR member text array required")
    return tuple(value)


def boundary() -> dict[str, object]:
    return {
        "scientifically_admitted": False,
        "canonical_chronology_admitted": False,
        "country_membership_asserted": False,
        "taxon_scope_status": "not_asserted_by_source",
        "genotype_processing_performed": False,
    }


def validate_boundary(value: object) -> None:
    if canonical_bytes(value) != canonical_bytes(boundary()):
        raise ValueError("AADR evidence member cannot grant scientific admission")


def validate_digest(value: str) -> None:
    if re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError("AADR member digest must be lowercase SHA256")


def member_key(release_sha256: str, genetic_id: str) -> str:
    validate_digest(release_sha256)
    if not genetic_id or genetic_id != genetic_id.strip():
        raise ValueError("AADR member requires its reconciled Genetic ID")
    return (
        "aadr-member:"
        + sha256(
            canonical_bytes([SCHEMA_VERSION, release_sha256, genetic_id])
        ).hexdigest()
    )


def claim_key(kind: str, owner_kind: str, owner: str, row_keys: tuple[str, ...]) -> str:
    if kind not in {"coordinate", "chronology"} or owner_kind not in {
        "member",
        "unkeyed_row",
    }:
        raise ValueError("AADR unsupported evidence owner or claim")
    if not row_keys or len(set(row_keys)) != len(row_keys):
        raise ValueError("AADR claim row keys must be unique and nonempty")
    return (
        f"aadr-{kind}-claim:"
        + sha256(
            canonical_bytes([SCHEMA_VERSION, owner_kind, owner, sorted(row_keys)])
        ).hexdigest()
    )


def descriptor(payloads: Mapping[str, tuple[int, str, int]]) -> dict[str, object]:
    return {
        name: {"byte_count": size, "sha256": digest, "record_count": count}
        for name, (size, digest, count) in payloads.items()
    }
