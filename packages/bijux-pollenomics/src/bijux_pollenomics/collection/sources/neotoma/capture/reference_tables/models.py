"""Two explicit reference-metadata tables with fixed prefix and transport caps."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..resources.models import NeotomaResourceLimits

REFERENCE_SCHEMA = "neotoma-reference-table-http-capture.v1"
REFERENCE_TABLES = ("variableunits", "geopoliticalunits")
METADATA_SCOPE = "current public reference prefixes only; no dictionary completeness, country assignment or numerical-resource admission"
POLICY_SOURCES = ("https://www.neotomadb.org/data/data-use-and-embargo-policy",)
DEFAULT_REFERENCE_LIMITS = NeotomaResourceLimits(
    max_requests=2,
    max_attempts=1,
    max_response_bytes=2 * 1024 * 1024 - 1,
    max_total_bytes=4 * 1024 * 1024 - 1,
    timeout_seconds=45,
    wall_seconds=120,
    retry_delay_seconds=0,
)


@dataclass(frozen=True)
class NeotomaReferenceTablePlan:
    tables: tuple[str, ...]


@dataclass(frozen=True)
class NeotomaReferenceTableCapture:
    manifest_sha256: str
    tables: tuple[dict[str, Any], ...]
    request_count: int
    response_bytes: int
    partitions: dict[str, int]


@dataclass(frozen=True)
class NeotomaReferenceTableBody:
    table: str
    body: bytes
    body_sha256: str
    receipt_sha256: str
