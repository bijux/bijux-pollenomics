"""Explicit whole-unit speleothem requests with frozen role and metadata authority."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

UNIT_SCHEMA = "neotoma-unit-resource-http-capture.v1"


@dataclass(frozen=True)
class NeotomaUnitResourcePlan:
    collection_unit_ids: tuple[int, ...]
    roster_sha256: str
    metadata_capture_manifest_sha256s: tuple[str, ...]


@dataclass(frozen=True)
class NeotomaUnitResourceCapture:
    manifest_sha256: str
    units: tuple[dict[str, Any], ...]
    request_count: int
    response_bytes: int
    partitions: dict[str, int]


@dataclass(frozen=True)
class NeotomaUnitBody:
    unit_key: str
    body: bytes
    body_sha256: str
    receipt_sha256: str
    scope: dict[str, Any]
