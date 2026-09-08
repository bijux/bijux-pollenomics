"""Boundary-review value objects and shared type contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias

JsonObject: TypeAlias = dict[str, object]
SourceScope: TypeAlias = Literal[
    "four_country_expected",
    "global_with_four_country_filter",
]


@dataclass(frozen=True)
class PointEvidence:
    """One source-owned WGS84 point awaiting a governed country decision."""

    source_family: str
    source_scope: SourceScope
    source_record_id: str
    longitude: float
    latitude: float
    raw_country: str | None
    published_country: str | None
    lineage: tuple[JsonObject, ...]
    prior_decision: JsonObject | None = None


@dataclass(frozen=True)
class BoundaryAuthority:
    """Validated local identity and geometry for one pinned boundary snapshot."""

    boundaries: dict[str, dict[str, object]]
    normalized_collection: JsonObject
    source_manifest: JsonObject
    manifest_sha256: str
    normalized_artifact_sha256: str
    artifact_digest: str


@dataclass(frozen=True)
class BoundaryCountryReviewReport:
    """Paths and denominators produced by one country-review materialization."""

    output_root: Path
    boundary_review_path: Path
    country_decision_paths: tuple[Path, ...]
    review_queue_path: Path
    manifest_path: Path
    point_count: int
    point_review_count: int
