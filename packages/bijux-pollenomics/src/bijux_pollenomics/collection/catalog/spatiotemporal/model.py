"""Source spatiotemporal posture records."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = []


@dataclass(frozen=True)
class SourceSpatiotemporalPostureRecord:
    source_key: str
    display_name: str
    governing_surface_path: str
    review_surface_paths: tuple[str, ...]
    spatial_representation: str
    temporal_support_posture: str
    temporal_support_note: str
    temporal_scope: str
    distance_scoring_posture: str
    distance_scoring_note: str
    availability_status: str
    refusal_reasons: tuple[str, ...]
    record_count: int | None
    numeric_interval_record_count: int
    detail_metrics: dict[str, int | None]
    caveats: tuple[str, ...]
    capability_contract_path: str = "data/source_family_contracts.json"
    capability_materialization_audit_path: str = (
        "data/source_family_evidence_stage_matrix.json"
    )
    capability_and_materialization_are_independent: bool = True
