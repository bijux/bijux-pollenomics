"""Four literal country names with fixed metadata-only routes and transport caps."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..resources.models import NeotomaResourceLimits

COUNTRY_SCHEMA = "neotoma-country-authority-http-capture.v1"
COUNTRY_NAMES = ("Denmark", "Finland", "Norway", "Sweden")
METADATA_SCOPE = "current exact-name rank1 country records only; no territorial hierarchy, dictionary completeness, country assignment or numerical-resource admission"
POLICY_SOURCES = ("https://www.neotomadb.org/data/data-use-and-embargo-policy",)
DEFAULT_COUNTRY_LIMITS = NeotomaResourceLimits(
    max_requests=4,
    max_attempts=1,
    max_response_bytes=2 * 1024 * 1024 - 1,
    max_total_bytes=8 * 1024 * 1024 - 1,
    timeout_seconds=45,
    wall_seconds=120,
    retry_delay_seconds=0,
)


@dataclass(frozen=True)
class NeotomaCountryAuthorityPlan:
    countries: tuple[str, ...]


@dataclass(frozen=True)
class NeotomaCountryAuthorityCapture:
    manifest_sha256: str
    countries: tuple[dict[str, Any], ...]
    request_count: int
    response_bytes: int
    partitions: dict[str, int]


@dataclass(frozen=True)
class NeotomaCountryAuthorityBody:
    country: str
    body: bytes
    body_sha256: str
    receipt_sha256: str
