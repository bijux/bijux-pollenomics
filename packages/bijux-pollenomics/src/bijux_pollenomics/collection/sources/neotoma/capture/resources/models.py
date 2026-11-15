"""Explicit resource identities, exposure roles and bounded retrieval populations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

RESOURCE_SCHEMA = "neotoma-resource-http-capture.v1"
DEVELOPMENT_ROLES = frozenset({"development_resource_discovery", "exposed_development"})
EXPOSURE_ROLES = DEVELOPMENT_ROLES | {
    "reserved_candidate_confirmation",
    "heldout_no_numerical_access",
}


@dataclass(frozen=True)
class NeotomaResourceSpec:
    dataset_id: int
    site_id: int
    collection_unit_id: int
    dataset_type: str
    database: str | None
    exposure_role: str
    metadata_sha256: str
    metadata_pointer: str
    versions: tuple[str, ...] = ("current", "doi_frozen")


@dataclass(frozen=True)
class NeotomaResourcePlan:
    resources: tuple[NeotomaResourceSpec, ...]
    roster_sha256: str
    policy_sources: tuple[str, ...] = (
        "https://www.neotomadb.org/data/data-use-and-embargo-policy",
        "https://epdweblog.org/epd_data_home/epd_policy/",
    )


@dataclass(frozen=True)
class NeotomaResourceLimits:
    max_requests: int = 1500
    max_attempts: int = 2
    max_response_bytes: int = 32 * 1024 * 1024
    max_total_bytes: int = 1024 * 1024 * 1024
    timeout_seconds: float = 90.0
    wall_seconds: float = 1800.0
    retry_delay_seconds: float = 1.0


DEFAULT_RESOURCE_LIMITS = NeotomaResourceLimits()


@dataclass(frozen=True)
class NeotomaRetainedSource:
    body_path: Path
    provenance_path: Path
    provenance_sha256: str
    body_sha256: str


@dataclass(frozen=True)
class NeotomaResourceCapture:
    manifest_sha256: str
    resources: tuple[dict[str, Any], ...]
    request_count: int
    response_bytes: int
    partitions: dict[str, int]
