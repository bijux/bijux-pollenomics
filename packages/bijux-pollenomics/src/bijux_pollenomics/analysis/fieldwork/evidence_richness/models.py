"""Evidence-richness domain records and stable public values."""

from __future__ import annotations

import re
from dataclasses import dataclass

from bijux_pollenomics.collection.contracts.models import ContextPointRecord

__all__ = [
    "DEFAULT_LAKE_EVIDENCE_RADII_KM",
    "LakeEvidenceBandScore",
    "LakeEvidenceCandidate",
    "LakeEvidenceRichnessAssessment",
    "LakeEvidenceRichnessReport",
    "LakeEvidenceSourceAnchor",
]


DEFAULT_LAKE_EVIDENCE_RADII_KM = (10, 20, 30, 40, 50)
_AGGREGATE_RADIUS_WEIGHTS = {10: 0.30, 20: 0.25, 30: 0.20, 40: 0.15, 50: 0.10}
_SVAR_AGGREGATE_RADIUS_WEIGHTS = {10: 0.35, 20: 0.27, 30: 0.18, 40: 0.12, 50: 0.08}
_LAKE_NAME_TERMS = ("lake", "sjo", "sjon", "tjarn", "trask", "gol")
_WETLAND_TERMS = ("mosse", "mossen", "bog", "fen", "peat", "myr", "karr", "karret")
_ENGINEERED_WATER_TERMS = (
    "damm",
    "dammen",
    "dammar",
    "dammarna",
    "magasin",
    "magasinering",
    "brott",
    "brottet",
    "kalkbrott",
    "renings",
)
_POSITION_NOTE_PATTERNS = (
    re.compile(r"another lake also called", re.IGNORECASE),
    re.compile(r"position is not clear", re.IGNORECASE),
    re.compile(r"could also be the likely site", re.IGNORECASE),
    re.compile(r"another possibility", re.IGNORECASE),
    re.compile(r"assume that the site is", re.IGNORECASE),
)
_GENERIC_LAKE_TOKENS = {"lake"}
_LAKE_MATCH_DISTANCE_KM = 2.0
_COORDINATE_SPREAD_FLAG_KM = 0.75
_TEMPORAL_NAVIGATION_INTERVALS = {
    "recent_historical": (0, 1000),
    "late_holocene": (1001, 3000),
    "mid_holocene": (3001, 6000),
}


@dataclass(frozen=True)
class LakeEvidenceSourceAnchor:
    """One source-backed coordinate that supports a lake candidate."""

    source_record: str
    source_name: str
    source_layer_key: str
    latitude: float
    longitude: float
    source_url: str
    time_start_bp: int | None = None
    time_end_bp: int | None = None
    time_mean_bp: int | None = None
    time_label: str = ""
    temporal_semantics: dict[str, object] | None = None
    evidence_role: str = "direct_lake_evidence"
    record_count: int = 1
    sample_count: int = 0
    context_radius_km: int | None = None
    representative_source_records: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "source_record": self.source_record,
            "source_name": self.source_name,
            "source_layer_key": self.source_layer_key,
            "latitude": round(self.latitude, 6),
            "longitude": round(self.longitude, 6),
            "source_url": self.source_url,
            "time_start_bp": self.time_start_bp,
            "time_end_bp": self.time_end_bp,
            "time_mean_bp": self.time_mean_bp,
            "time_label": self.time_label,
            "temporal_semantics": self.temporal_semantics or {},
            "evidence_role": self.evidence_role,
            "record_count": self.record_count,
            "sample_count": self.sample_count,
            "context_radius_km": self.context_radius_km,
            "representative_source_records": list(self.representative_source_records),
        }


@dataclass(frozen=True)
class LakeEvidenceCandidate:
    """One Sweden lake candidate ranked against pollen, archaeology, and aDNA context."""

    lake_name: str
    lake_label: str
    lake_token: str
    name_key: str
    latitude: float
    longitude: float
    basin_posture: str
    direct_pollen_source_count: int
    direct_pollen_record_count: int
    time_aware_direct_pollen_records: int
    pollen_sources: tuple[str, ...]
    supporting_pollen_names: tuple[str, ...]
    supporting_source_records: tuple[str, ...]
    supporting_source_points: tuple[LakeEvidenceSourceAnchor, ...]
    representative_source_record: str
    representative_source_layer_key: str
    representative_source_name: str
    representative_source_url: str
    coordinate_resolution_method: str
    duplicate_name_count: int
    coordinate_spread_km: float
    ambiguity_flags: tuple[str, ...]
    ambiguity_note: str
    direct_pollen_signal: float
    lake_registry_id: str = ""
    lake_registry_uuid: str = ""
    lake_water_identity: str = ""
    lake_name_status: str = ""
    lake_area_km2: float | None = None
    lake_sampling_posture: str = ""
    lake_sampling_fit: float = 0.0
    lake_sampling_notes: tuple[str, ...] = ()
    lake_sampling_readiness_posture: str = "evidence_unavailable"
    lake_sampling_missing_inputs: tuple[str, ...] = ()
    temporal_context_points: tuple[LakeEvidenceSourceAnchor, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "lake_name": self.lake_name,
            "lake_label": self.lake_label,
            "lake_token": self.lake_token,
            "name_key": self.name_key,
            "latitude": round(self.latitude, 6),
            "longitude": round(self.longitude, 6),
            "basin_posture": self.basin_posture,
            "direct_pollen_source_count": self.direct_pollen_source_count,
            "direct_pollen_record_count": self.direct_pollen_record_count,
            "time_aware_direct_pollen_records": self.time_aware_direct_pollen_records,
            "pollen_sources": list(self.pollen_sources),
            "supporting_pollen_names": list(self.supporting_pollen_names),
            "supporting_source_records": list(self.supporting_source_records),
            "supporting_source_points": [
                source_point.as_dict() for source_point in self.supporting_source_points
            ],
            "representative_source_record": self.representative_source_record,
            "representative_source_layer_key": self.representative_source_layer_key,
            "representative_source_name": self.representative_source_name,
            "representative_source_url": self.representative_source_url,
            "coordinate_resolution_method": self.coordinate_resolution_method,
            "duplicate_name_count": self.duplicate_name_count,
            "coordinate_spread_km": self.coordinate_spread_km,
            "ambiguity_flags": list(self.ambiguity_flags),
            "ambiguity_note": self.ambiguity_note,
            "direct_pollen_signal": self.direct_pollen_signal,
            "lake_registry_id": self.lake_registry_id,
            "lake_registry_uuid": self.lake_registry_uuid,
            "lake_water_identity": self.lake_water_identity,
            "lake_name_status": self.lake_name_status,
            "lake_area_km2": self.lake_area_km2,
            "lake_sampling_posture": self.lake_sampling_posture,
            "lake_sampling_fit": self.lake_sampling_fit,
            "lake_sampling_notes": list(self.lake_sampling_notes),
            "lake_sampling_readiness_posture": self.lake_sampling_readiness_posture,
            "lake_sampling_missing_inputs": list(self.lake_sampling_missing_inputs),
            "temporal_context_points": [
                source_point.as_dict() for source_point in self.temporal_context_points
            ],
        }


@dataclass(frozen=True)
class LakeEvidenceBandScore:
    """One distance-band evidence view around a lake candidate."""

    radius_km: int
    band_rank: int
    total_score: float
    nearby_pollen_lake_count: int
    time_aware_pollen_site_count: int
    human_overlap_pollen_site_count: int
    human_adna_locality_count: int
    human_adna_sample_count: int
    domesticated_animal_locality_count: int
    domesticated_animal_sample_count: int
    sead_site_count: int
    time_aware_sead_site_count: int
    human_overlap_sead_site_count: int
    raa_density_site_count: int
    evidence_family_count: int
    nearby_pollen_signal: float
    human_signal: float
    animal_signal: float
    archaeology_signal: float
    diversity_signal: float

    def as_dict(self) -> dict[str, object]:
        return {
            "radius_km": self.radius_km,
            "band_rank": self.band_rank,
            "total_score": self.total_score,
            "nearby_pollen_lake_count": self.nearby_pollen_lake_count,
            "time_aware_pollen_site_count": self.time_aware_pollen_site_count,
            "human_overlap_pollen_site_count": self.human_overlap_pollen_site_count,
            "human_adna_locality_count": self.human_adna_locality_count,
            "human_adna_sample_count": self.human_adna_sample_count,
            "domesticated_animal_locality_count": self.domesticated_animal_locality_count,
            "domesticated_animal_sample_count": self.domesticated_animal_sample_count,
            "sead_site_count": self.sead_site_count,
            "time_aware_sead_site_count": self.time_aware_sead_site_count,
            "human_overlap_sead_site_count": self.human_overlap_sead_site_count,
            "raa_density_site_count": self.raa_density_site_count,
            "evidence_family_count": self.evidence_family_count,
            "signals": {
                "nearby_pollen": self.nearby_pollen_signal,
                "human_adna": self.human_signal,
                "domesticated_animal_adna": self.animal_signal,
                "archaeology": self.archaeology_signal,
                "evidence_diversity": self.diversity_signal,
            },
        }


@dataclass(frozen=True)
class LakeEvidenceRichnessAssessment:
    """Full multi-band evidence assessment for one Sweden lake candidate."""

    candidate: LakeEvidenceCandidate
    aggregate_rank: int
    aggregate_score: float
    band_scores: tuple[LakeEvidenceBandScore, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate": self.candidate.as_dict(),
            "aggregate_rank": self.aggregate_rank,
            "aggregate_score": self.aggregate_score,
            "band_scores": [score.as_dict() for score in self.band_scores],
        }


@dataclass(frozen=True)
class LakeEvidenceRichnessReport:
    """Machine-readable Sweden lake evidence richness ranking."""

    schema_version: str
    country: str
    radii_km: tuple[int, ...]
    methodology: dict[str, object]
    candidate_count: int
    assessments: tuple[LakeEvidenceRichnessAssessment, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "country": self.country,
            "radii_km": list(self.radii_km),
            "candidate_count": self.candidate_count,
            "methodology": self.methodology,
            "assessments": [assessment.as_dict() for assessment in self.assessments],
        }


@dataclass(frozen=True)
class _PointEvidence:
    latitude: float
    longitude: float
    sample_count: int = 1
    time_start_bp: int | None = None
    time_end_bp: int | None = None
    time_mean_bp: int | None = None
    source_record: str = ""
    source_name: str = ""
    source_layer_key: str = ""
    source_url: str = ""
    time_label: str = ""
    temporal_semantics: dict[str, object] | None = None


@dataclass(frozen=True)
class _DensityCell:
    min_latitude: float
    max_latitude: float
    min_longitude: float
    max_longitude: float
    count: int


@dataclass(frozen=True)
class _SvarLakeRecord:
    lake_name: str
    lake_label: str
    lake_token: str
    name_key: str
    latitude: float
    longitude: float
    source_url: str
    lake_registry_id: str
    lake_registry_uuid: str
    lake_water_identity: str
    lake_name_status: str
    lake_area_km2: float | None
    lake_sampling_readiness_posture: str
    lake_sampling_missing_inputs: tuple[str, ...]


@dataclass(frozen=True)
class _LakeSourcePoint:
    point: ContextPointRecord
    name_key: str
    cleaned_name: str
    source_record: str
    position_note: str | None
