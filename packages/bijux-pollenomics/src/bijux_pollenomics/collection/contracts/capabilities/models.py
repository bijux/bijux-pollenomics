from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceCapabilityProfile:
    source_key: str
    evidence_class: str
    allowed_role: str
    prohibited_claims: tuple[str, ...]
    support_by_dimension: dict[str, str]
    evidence_paths_by_dimension: dict[str, tuple[str, ...]]
    human_review_required: bool
    human_review_reason: str | None


@dataclass(frozen=True)
class _CapabilityAuditRow:
    source_key: str
    dimension: str
    support: str
    materialization: str
    evidence_paths: tuple[str, ...]
    present_evidence_paths: tuple[str, ...]
    missing_evidence_paths: tuple[str, ...]
    evidence_file_count: int
    required_evidence_count: int
    coverage_metrics: dict[str, int | None]
    human_review_required: bool
    reason_codes: tuple[str, ...]
