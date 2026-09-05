from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceFamilyLayerContract:
    layer_key: str
    repository_path: str
    required: bool
    purpose: str
    example_artifacts: tuple[str, ...]


@dataclass(frozen=True)
class SourceFamilyContract:
    source_key: str
    display_name: str
    domain_group: str
    evidence_role: str
    primary_question: str
    raw_layer: SourceFamilyLayerContract
    normalized_layer: SourceFamilyLayerContract
    reviewed_layer: SourceFamilyLayerContract
    published_layer: SourceFamilyLayerContract
    coverage_metric_keys: tuple[str, ...]


@dataclass(frozen=True)
class SourceFamilyStateRow:
    source_key: str
    display_name: str
    domain_group: str
    evidence_role: str
    primary_question: str
    raw_status: str
    normalized_status: str
    reviewed_status: str
    published_status: str
    provenance_depth: str
    publication_posture: str
    authority_status: str
    authority_reasons: tuple[str, ...]
    coverage_metrics: dict[str, int | None]
    blocking_reasons: tuple[str, ...]


@dataclass(frozen=True)
class _SourceAuthorityState:
    status: str
    reason_codes: tuple[str, ...]
    governed_metrics: dict[str, int | None] | None = None
