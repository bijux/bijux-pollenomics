"""Finite current context queries, with no dated-basin or method admission."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..resources.models import NeotomaResourceLimits

CONTEXT_SCHEMA = "neotoma-site-context-http-capture.v1"
RESOURCE_KINDS = ("depositional_environment", "lake_candidates")
SUPPORTED_RESOURCE_KINDS = (
    "depositional_environment",
    "dataset_depositional_environment",
    "lake_candidates",
)
SOURCE_SCOPE = "current source context only; no dated basin geometry, absence certification or scientific admission"
SNAPSHOT_CONSISTENCY = (
    "individually timed current queries; no transaction or historical coevality claim"
)
POLICY_SOURCES = ("https://www.neotomadb.org/data/data-use-and-embargo-policy",)
MAX_BYTES = 512 * 1024 * 1024
MAX_FILES = 20_000
MAX_METADATA_BYTES = 16 * 1024 * 1024
DEFAULT_CONTEXT_LIMITS = NeotomaResourceLimits(
    max_requests=8,
    max_attempts=1,
    max_response_bytes=2 * 1024 * 1024,
    max_total_bytes=8 * 1024 * 1024,
    timeout_seconds=45,
    wall_seconds=120,
    retry_delay_seconds=0,
)


@dataclass(frozen=True)
class NeotomaContextResourcePlan:
    site_ids: tuple[int, ...]
    context_manifest_sha256: str
    native_archive_manifest_sha256: str
    resource_kinds: tuple[str, ...] = RESOURCE_KINDS
    lake_buffer_m: int = 1000
    lake_precision: float = 0.0001
    lake_projection: int = 4326


@dataclass(frozen=True)
class NeotomaContextResourceCapture:
    manifest_sha256: str
    resources: tuple[dict[str, Any], ...]
    request_count: int
    response_bytes: int
    partitions: dict[str, int]
