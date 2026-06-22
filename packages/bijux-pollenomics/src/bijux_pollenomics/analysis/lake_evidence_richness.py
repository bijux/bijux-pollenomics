from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import json
from pathlib import Path
import re
import unicodedata

from ..core import haversine_km, temporal_semantics_has_numeric_interval
from ..data_downloader.models import ContextPointRecord
from ..data_downloader.spatial.representative_points import (
    geometry_to_representative_point,
)

__all__ = [
    "DEFAULT_LAKE_EVIDENCE_RADII_KM",
    "LakeEvidenceBandScore",
    "LakeEvidenceCandidate",
    "LakeEvidenceRichnessAssessment",
    "LakeEvidenceRichnessReport",
    "LakeEvidenceSourceAnchor",
    "build_sweden_lake_evidence_richness_report",
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


@dataclass(frozen=True)
class LakeEvidenceSourceAnchor:
    """One source-backed coordinate that supports a lake candidate."""

    source_record: str
    source_name: str
    source_layer_key: str
    latitude: float
    longitude: float
    source_url: str

    def as_dict(self) -> dict[str, object]:
        return {
            "source_record": self.source_record,
            "source_name": self.source_name,
            "source_layer_key": self.source_layer_key,
            "latitude": round(self.latitude, 6),
            "longitude": round(self.longitude, 6),
            "source_url": self.source_url,
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


@dataclass(frozen=True)
class _LakeSourcePoint:
    point: ContextPointRecord
    name_key: str
    cleaned_name: str
    source_record: str
    position_note: str | None


def build_sweden_lake_evidence_richness_report(
    *,
    context_root: Path,
    human_localities: Iterable[object],
    animal_localities: Iterable[dict[str, object]],
    radii_km: Sequence[int] = DEFAULT_LAKE_EVIDENCE_RADII_KM,
) -> LakeEvidenceRichnessReport:
    """Rank Sweden lake candidates by surrounding pollen, archaeology, and aDNA richness."""
    normalized_radii = tuple(
        sorted({int(radius) for radius in radii_km if int(radius) > 0})
    )
    pollen_points = _load_sweden_pollen_points(Path(context_root))
    neotoma_position_notes = _load_sweden_neotoma_position_notes(Path(context_root))
    human_points = _extract_human_points(human_localities)
    animal_points = _extract_animal_points(animal_localities)
    sead_points = _load_sweden_context_points(
        Path(context_root)
        / "sead"
        / "normalized"
        / "nordic_environmental_sites.geojson",
        country="Sweden",
    )
    source_temporal_coverage = _build_context_temporal_coverage_summary(
        pollen_points,
        context_root=Path(context_root),
        sead_points=sead_points,
    )
    raa_cells = _load_sweden_density_cells(
        Path(context_root) / "raa" / "normalized" / "sweden_archaeology_density.geojson"
    )
    svar_lake_path = (
        Path(context_root) / "svar" / "normalized" / "sweden_lake_registry.geojson"
    )
    if svar_lake_path.exists():
        return _build_svar_lake_report(
            radii_km=normalized_radii,
            svar_lake_path=svar_lake_path,
            pollen_points=pollen_points,
            neotoma_position_notes=neotoma_position_notes,
            human_points=human_points,
            animal_points=animal_points,
            sead_points=sead_points,
            raa_cells=raa_cells,
            source_temporal_coverage=source_temporal_coverage,
        )
    candidates = _derive_lake_candidates(
        pollen_points,
        neotoma_position_notes=neotoma_position_notes,
    )
    if not candidates:
        return _build_empty_report(
            normalized_radii,
            candidate_source="pollen_candidate_points",
            source_temporal_coverage=source_temporal_coverage,
        )

    raw_scores: dict[str, dict[int, dict[str, int]]] = {
        candidate.lake_token: {
            radius: _build_raw_band_metrics(
                candidate,
                candidates,
                human_points,
                animal_points,
                sead_points,
                raa_cells,
                radius_km=radius,
            )
            for radius in normalized_radii
        }
        for candidate in candidates
    }
    maxima_by_radius = {
        radius: _build_band_maxima(raw_scores, radius_km=radius)
        for radius in normalized_radii
    }
    candidate_rows: list[dict[str, object]] = []
    for candidate in candidates:
        band_scores: list[LakeEvidenceBandScore] = []
        for radius in normalized_radii:
            raw = raw_scores[candidate.lake_token][radius]
            maxima = maxima_by_radius[radius]
            nearby_pollen_signal = _normalized_ratio(
                raw["nearby_pollen_lake_count"],
                maxima["nearby_pollen_lake_count"],
            )
            if raw["nearby_pollen_lake_count"] > 0:
                nearby_pollen_signal = _weighted_average(
                    (nearby_pollen_signal, 0.6),
                    (
                        _normalized_ratio(
                            raw["time_aware_pollen_site_count"],
                            max(
                                raw["nearby_pollen_lake_count"],
                                maxima["time_aware_pollen_site_count"],
                            ),
                        ),
                        0.2,
                    ),
                    (
                        _normalized_ratio(
                            raw["human_overlap_pollen_site_count"],
                            max(
                                raw["nearby_pollen_lake_count"],
                                maxima["human_overlap_pollen_site_count"],
                            ),
                        ),
                        0.2,
                    ),
                )
            human_signal = _weighted_average(
                (
                    _normalized_ratio(
                        raw["human_adna_locality_count"],
                        maxima["human_adna_locality_count"],
                    ),
                    0.45,
                ),
                (
                    _normalized_ratio(
                        raw["human_adna_sample_count"],
                        maxima["human_adna_sample_count"],
                    ),
                    0.55,
                ),
            )
            animal_signal = _weighted_average(
                (
                    _normalized_ratio(
                        raw["domesticated_animal_locality_count"],
                        maxima["domesticated_animal_locality_count"],
                    ),
                    0.5,
                ),
                (
                    _normalized_ratio(
                        raw["domesticated_animal_sample_count"],
                        maxima["domesticated_animal_sample_count"],
                    ),
                    0.5,
                ),
            )
            archaeology_signal = _weighted_average(
                (
                    _normalized_ratio(
                        raw["sead_site_count"], maxima["sead_site_count"]
                    ),
                    0.4,
                ),
                (
                    _normalized_ratio(
                        raw["time_aware_sead_site_count"],
                        max(
                            raw["sead_site_count"],
                            maxima["time_aware_sead_site_count"],
                        ),
                    ),
                    0.2,
                ),
                (
                    _normalized_ratio(
                        raw["human_overlap_sead_site_count"],
                        max(
                            raw["sead_site_count"],
                            maxima["human_overlap_sead_site_count"],
                        ),
                    ),
                    0.2,
                ),
                (
                    _normalized_ratio(
                        raw["raa_density_site_count"],
                        maxima["raa_density_site_count"],
                    ),
                    0.2,
                ),
            )
            diversity_signal = round(raw["evidence_family_count"] / 5.0, 4)
            total_score = round(
                candidate.direct_pollen_signal * 0.2
                + nearby_pollen_signal * 0.1
                + archaeology_signal * 0.25
                + human_signal * 0.2
                + animal_signal * 0.15
                + diversity_signal * 0.1,
                4,
            )
            band_scores.append(
                LakeEvidenceBandScore(
                    radius_km=radius,
                    band_rank=0,
                    total_score=total_score,
                    nearby_pollen_lake_count=raw["nearby_pollen_lake_count"],
                    time_aware_pollen_site_count=raw["time_aware_pollen_site_count"],
                    human_overlap_pollen_site_count=raw[
                        "human_overlap_pollen_site_count"
                    ],
                    human_adna_locality_count=raw["human_adna_locality_count"],
                    human_adna_sample_count=raw["human_adna_sample_count"],
                    domesticated_animal_locality_count=raw[
                        "domesticated_animal_locality_count"
                    ],
                    domesticated_animal_sample_count=raw[
                        "domesticated_animal_sample_count"
                    ],
                    sead_site_count=raw["sead_site_count"],
                    time_aware_sead_site_count=raw["time_aware_sead_site_count"],
                    human_overlap_sead_site_count=raw[
                        "human_overlap_sead_site_count"
                    ],
                    raa_density_site_count=raw["raa_density_site_count"],
                    evidence_family_count=raw["evidence_family_count"],
                    nearby_pollen_signal=nearby_pollen_signal,
                    human_signal=human_signal,
                    animal_signal=animal_signal,
                    archaeology_signal=archaeology_signal,
                    diversity_signal=diversity_signal,
                )
            )
        aggregate_score = round(
            sum(
                score.total_score * _AGGREGATE_RADIUS_WEIGHTS.get(score.radius_km, 0.0)
                for score in band_scores
            ),
            4,
        )
        candidate_rows.append(
            {
                "candidate": candidate,
                "aggregate_score": aggregate_score,
                "band_scores": tuple(band_scores),
            }
        )

    for radius in normalized_radii:
        ordered = sorted(
            candidate_rows,
            key=lambda row: (
                -_band_score_for_radius(
                    row["band_scores"],  # type: ignore[arg-type]
                    radius_km=radius,
                ).total_score,
                -row["aggregate_score"],  # type: ignore[arg-type]
                row["candidate"].lake_label,  # type: ignore[index]
            ),
        )
        for rank, row in enumerate(ordered, start=1):
            updated_scores = []
            for score in row["band_scores"]:  # type: ignore[assignment]
                if score.radius_km == radius:
                    updated_scores.append(
                        LakeEvidenceBandScore(
                            radius_km=score.radius_km,
                            band_rank=rank,
                            total_score=score.total_score,
                            nearby_pollen_lake_count=score.nearby_pollen_lake_count,
                            time_aware_pollen_site_count=score.time_aware_pollen_site_count,
                            human_overlap_pollen_site_count=score.human_overlap_pollen_site_count,
                            human_adna_locality_count=score.human_adna_locality_count,
                            human_adna_sample_count=score.human_adna_sample_count,
                            domesticated_animal_locality_count=score.domesticated_animal_locality_count,
                            domesticated_animal_sample_count=score.domesticated_animal_sample_count,
                            sead_site_count=score.sead_site_count,
                            time_aware_sead_site_count=score.time_aware_sead_site_count,
                            human_overlap_sead_site_count=score.human_overlap_sead_site_count,
                            raa_density_site_count=score.raa_density_site_count,
                            evidence_family_count=score.evidence_family_count,
                            nearby_pollen_signal=score.nearby_pollen_signal,
                            human_signal=score.human_signal,
                            animal_signal=score.animal_signal,
                            archaeology_signal=score.archaeology_signal,
                            diversity_signal=score.diversity_signal,
                        )
                    )
                else:
                    updated_scores.append(score)
            row["band_scores"] = tuple(updated_scores)

    ordered_candidates = sorted(
        candidate_rows,
        key=lambda row: (
            -row["aggregate_score"],  # type: ignore[arg-type]
            -_band_score_for_radius(
                row["band_scores"],  # type: ignore[arg-type]
                radius_km=normalized_radii[0],
            ).total_score,
            row["candidate"].lake_label,  # type: ignore[index]
        ),
    )
    assessments = tuple(
        LakeEvidenceRichnessAssessment(
            candidate=row["candidate"],  # type: ignore[arg-type]
            aggregate_rank=rank,
            aggregate_score=row["aggregate_score"],  # type: ignore[arg-type]
            band_scores=row["band_scores"],  # type: ignore[arg-type]
        )
        for rank, row in enumerate(ordered_candidates, start=1)
    )
    return LakeEvidenceRichnessReport(
        schema_version="sweden-lake-evidence-richness.v2",
        country="Sweden",
        radii_km=normalized_radii,
        candidate_count=len(assessments),
        methodology=_build_methodology(
            normalized_radii,
            source_temporal_coverage=source_temporal_coverage,
        ),
        assessments=assessments,
    )


def _build_svar_lake_report(
    *,
    radii_km: tuple[int, ...],
    svar_lake_path: Path,
    pollen_points: Sequence[ContextPointRecord],
    neotoma_position_notes: dict[str, str],
    human_points: Sequence[_PointEvidence],
    animal_points: Sequence[_PointEvidence],
    sead_points: Sequence[ContextPointRecord],
    raa_cells: Sequence[_DensityCell],
    source_temporal_coverage: dict[str, object] | None = None,
) -> LakeEvidenceRichnessReport:
    svar_lakes = _load_sweden_svar_lakes(svar_lake_path)
    if not svar_lakes or not human_points:
        return _build_empty_report(
            radii_km,
            candidate_source="svar_lake_registry",
            source_temporal_coverage=source_temporal_coverage,
        )
    candidates = _derive_svar_lake_candidates(
        svar_lakes,
        pollen_points=pollen_points,
        neotoma_position_notes=neotoma_position_notes,
        human_points=human_points,
    )
    if not candidates:
        return _build_empty_report(
            radii_km,
            candidate_source="svar_lake_registry",
            source_temporal_coverage=source_temporal_coverage,
        )

    raw_scores: dict[str, dict[int, dict[str, int]]] = {
        candidate.lake_token: {
            radius: _build_raw_band_metrics(
                candidate,
                candidates,
                human_points,
                animal_points,
                sead_points,
                raa_cells,
                radius_km=radius,
                pollen_points=pollen_points,
            )
            for radius in radii_km
        }
        for candidate in candidates
    }
    maxima_by_radius = {
        radius: _build_band_maxima(raw_scores, radius_km=radius) for radius in radii_km
    }
    candidate_rows: list[dict[str, object]] = []
    for candidate in candidates:
        band_scores: list[LakeEvidenceBandScore] = []
        for radius in radii_km:
            raw = raw_scores[candidate.lake_token][radius]
            maxima = maxima_by_radius[radius]
            nearby_pollen_signal = _normalized_ratio(
                raw["nearby_pollen_lake_count"],
                maxima["nearby_pollen_lake_count"],
            )
            if raw["nearby_pollen_lake_count"] > 0:
                nearby_pollen_signal = _weighted_average(
                    (nearby_pollen_signal, 0.6),
                    (
                        _normalized_ratio(
                            raw["time_aware_pollen_site_count"],
                            max(
                                raw["nearby_pollen_lake_count"],
                                maxima["time_aware_pollen_site_count"],
                            ),
                        ),
                        0.2,
                    ),
                    (
                        _normalized_ratio(
                            raw["human_overlap_pollen_site_count"],
                            max(
                                raw["nearby_pollen_lake_count"],
                                maxima["human_overlap_pollen_site_count"],
                            ),
                        ),
                        0.2,
                    ),
                )
            human_signal = _weighted_average(
                (
                    _normalized_ratio(
                        raw["human_adna_locality_count"],
                        maxima["human_adna_locality_count"],
                    ),
                    0.45,
                ),
                (
                    _normalized_ratio(
                        raw["human_adna_sample_count"],
                        maxima["human_adna_sample_count"],
                    ),
                    0.55,
                ),
            )
            animal_signal = _weighted_average(
                (
                    _normalized_ratio(
                        raw["domesticated_animal_locality_count"],
                        maxima["domesticated_animal_locality_count"],
                    ),
                    0.5,
                ),
                (
                    _normalized_ratio(
                        raw["domesticated_animal_sample_count"],
                        maxima["domesticated_animal_sample_count"],
                    ),
                    0.5,
                ),
            )
            archaeology_signal = _weighted_average(
                (
                    _normalized_ratio(
                        raw["sead_site_count"], maxima["sead_site_count"]
                    ),
                    0.4,
                ),
                (
                    _normalized_ratio(
                        raw["time_aware_sead_site_count"],
                        max(
                            raw["sead_site_count"],
                            maxima["time_aware_sead_site_count"],
                        ),
                    ),
                    0.2,
                ),
                (
                    _normalized_ratio(
                        raw["human_overlap_sead_site_count"],
                        max(
                            raw["sead_site_count"],
                            maxima["human_overlap_sead_site_count"],
                        ),
                    ),
                    0.2,
                ),
                (
                    _normalized_ratio(
                        raw["raa_density_site_count"],
                        maxima["raa_density_site_count"],
                    ),
                    0.2,
                ),
            )
            diversity_signal = round(raw["evidence_family_count"] / 5.0, 4)
            direct_pollen_source_signal = min(
                1.0,
                candidate.direct_pollen_source_count / 2.0,
            )
            direct_pollen_signal = _weighted_average(
                (candidate.direct_pollen_signal, 0.65),
                (direct_pollen_source_signal, 0.35),
            )
            total_score = round(
                human_signal * 0.59
                + direct_pollen_signal * 0.14
                + nearby_pollen_signal * 0.07
                + archaeology_signal * 0.07
                + animal_signal * 0.04
                + diversity_signal * 0.02
                + candidate.lake_sampling_fit * 0.07,
                4,
            )
            band_scores.append(
                LakeEvidenceBandScore(
                    radius_km=radius,
                    band_rank=0,
                    total_score=total_score,
                    nearby_pollen_lake_count=raw["nearby_pollen_lake_count"],
                    time_aware_pollen_site_count=raw["time_aware_pollen_site_count"],
                    human_overlap_pollen_site_count=raw[
                        "human_overlap_pollen_site_count"
                    ],
                    human_adna_locality_count=raw["human_adna_locality_count"],
                    human_adna_sample_count=raw["human_adna_sample_count"],
                    domesticated_animal_locality_count=raw[
                        "domesticated_animal_locality_count"
                    ],
                    domesticated_animal_sample_count=raw[
                        "domesticated_animal_sample_count"
                    ],
                    sead_site_count=raw["sead_site_count"],
                    time_aware_sead_site_count=raw["time_aware_sead_site_count"],
                    human_overlap_sead_site_count=raw[
                        "human_overlap_sead_site_count"
                    ],
                    raa_density_site_count=raw["raa_density_site_count"],
                    evidence_family_count=raw["evidence_family_count"],
                    nearby_pollen_signal=nearby_pollen_signal,
                    human_signal=human_signal,
                    animal_signal=animal_signal,
                    archaeology_signal=archaeology_signal,
                    diversity_signal=diversity_signal,
                )
            )
        aggregate_score = round(
            sum(
                score.total_score
                * _SVAR_AGGREGATE_RADIUS_WEIGHTS.get(score.radius_km, 0.0)
                for score in band_scores
            ),
            4,
        )
        candidate_rows.append(
            {
                "candidate": candidate,
                "aggregate_score": aggregate_score,
                "band_scores": tuple(band_scores),
            }
        )

    for radius in radii_km:
        ordered = sorted(
            candidate_rows,
            key=lambda row: (
                -_band_score_for_radius(
                    row["band_scores"],  # type: ignore[arg-type]
                    radius_km=radius,
                ).total_score,
                *_svar_band_priority_key(
                    row["candidate"],  # type: ignore[arg-type]
                    _band_score_for_radius(
                        row["band_scores"],  # type: ignore[arg-type]
                        radius_km=radius,
                    ),
                ),
            ),
        )
        for rank, row in enumerate(ordered, start=1):
            updated_scores = []
            for score in row["band_scores"]:  # type: ignore[assignment]
                if score.radius_km == radius:
                    updated_scores.append(
                        LakeEvidenceBandScore(
                            radius_km=score.radius_km,
                            band_rank=rank,
                            total_score=score.total_score,
                            nearby_pollen_lake_count=score.nearby_pollen_lake_count,
                            time_aware_pollen_site_count=score.time_aware_pollen_site_count,
                            human_overlap_pollen_site_count=score.human_overlap_pollen_site_count,
                            human_adna_locality_count=score.human_adna_locality_count,
                            human_adna_sample_count=score.human_adna_sample_count,
                            domesticated_animal_locality_count=score.domesticated_animal_locality_count,
                            domesticated_animal_sample_count=score.domesticated_animal_sample_count,
                            sead_site_count=score.sead_site_count,
                            time_aware_sead_site_count=score.time_aware_sead_site_count,
                            human_overlap_sead_site_count=score.human_overlap_sead_site_count,
                            raa_density_site_count=score.raa_density_site_count,
                            evidence_family_count=score.evidence_family_count,
                            nearby_pollen_signal=score.nearby_pollen_signal,
                            human_signal=score.human_signal,
                            animal_signal=score.animal_signal,
                            archaeology_signal=score.archaeology_signal,
                            diversity_signal=score.diversity_signal,
                        )
                    )
                else:
                    updated_scores.append(score)
            row["band_scores"] = tuple(updated_scores)

    ordered_candidates = sorted(
        candidate_rows,
        key=lambda row: (
            -row["aggregate_score"],  # type: ignore[arg-type]
            *_svar_aggregate_priority_key(
                row["candidate"],  # type: ignore[arg-type]
                row["band_scores"],  # type: ignore[arg-type]
            ),
        ),
    )
    assessments = tuple(
        LakeEvidenceRichnessAssessment(
            candidate=row["candidate"],  # type: ignore[arg-type]
            aggregate_rank=rank,
            aggregate_score=row["aggregate_score"],  # type: ignore[arg-type]
            band_scores=row["band_scores"],  # type: ignore[arg-type]
        )
        for rank, row in enumerate(ordered_candidates, start=1)
    )
    return LakeEvidenceRichnessReport(
        schema_version="sweden-lake-evidence-richness.v2",
        country="Sweden",
        radii_km=radii_km,
        candidate_count=len(assessments),
        methodology=_build_methodology(
            radii_km,
            candidate_source="svar_lake_registry",
            source_temporal_coverage=source_temporal_coverage,
        ),
        assessments=assessments,
    )


def _extract_human_points(localities: Iterable[object]) -> tuple[_PointEvidence, ...]:
    rows: list[_PointEvidence] = []
    for locality in localities:
        latitude = getattr(locality, "latitude", None)
        longitude = getattr(locality, "longitude", None)
        if not isinstance(latitude, (int, float)) or not isinstance(
            longitude, (int, float)
        ):
            continue
        sample_count = getattr(locality, "sample_count", 0)
        rows.append(
            _PointEvidence(
                latitude=float(latitude),
                longitude=float(longitude),
                sample_count=int(sample_count) if isinstance(sample_count, int) else 0,
                time_start_bp=_optional_int(getattr(locality, "time_start_bp", None)),
                time_end_bp=_optional_int(getattr(locality, "time_end_bp", None)),
                time_mean_bp=_optional_int(getattr(locality, "time_mean_bp", None)),
            )
        )
    return tuple(rows)


def _extract_animal_points(
    animal_localities: Iterable[dict[str, object]],
) -> tuple[_PointEvidence, ...]:
    rows: list[_PointEvidence] = []
    for locality in animal_localities:
        latitude = locality.get("latitude")
        longitude = locality.get("longitude")
        if not isinstance(latitude, (int, float)) or not isinstance(
            longitude, (int, float)
        ):
            continue
        sample_count = locality.get("sample_count", 0)
        rows.append(
            _PointEvidence(
                latitude=float(latitude),
                longitude=float(longitude),
                sample_count=int(sample_count) if isinstance(sample_count, int) else 0,
                time_start_bp=_optional_int(locality.get("time_start_bp")),
                time_end_bp=_optional_int(locality.get("time_end_bp")),
                time_mean_bp=_optional_int(locality.get("time_mean_bp")),
            )
        )
    return tuple(rows)


def _load_sweden_pollen_points(context_root: Path) -> tuple[ContextPointRecord, ...]:
    paths = (
        context_root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
        context_root
        / "landclim"
        / "normalized"
        / "nordic_pollen_site_sequences.geojson",
    )
    records: list[ContextPointRecord] = []
    for path in paths:
        records.extend(_load_sweden_context_points(path, country="Sweden"))
    return tuple(records)


def _load_sweden_context_points(
    path: Path,
    *,
    country: str,
) -> tuple[ContextPointRecord, ...]:
    if not path.exists():
        return ()
    payload = json.loads(path.read_text(encoding="utf-8"))
    features = payload.get("features", [])
    records: list[ContextPointRecord] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        if not isinstance(properties, dict) or not isinstance(geometry, dict):
            continue
        if str(properties.get("country", "")).strip() != country:
            continue
        coordinates = geometry.get("coordinates", [])
        if (
            geometry.get("type") != "Point"
            or not isinstance(coordinates, list)
            or len(coordinates) < 2
        ):
            continue
        longitude, latitude = coordinates[0], coordinates[1]
        if not isinstance(latitude, (int, float)) or not isinstance(
            longitude, (int, float)
        ):
            continue
        popup_rows = tuple(
            (
                str(item.get("label", "")),
                str(item.get("value", "")),
            )
            for item in properties.get("popup_rows", [])
            if isinstance(item, dict)
        )
        records.append(
            ContextPointRecord(
                source=str(properties.get("source", "")),
                layer_key=str(properties.get("layer_key", "")),
                layer_label=str(properties.get("layer_label", "")),
                category=str(properties.get("category", "")),
                country=str(properties.get("country", "")),
                record_id=str(properties.get("record_id", "")),
                name=str(properties.get("name", "")),
                latitude=float(latitude),
                longitude=float(longitude),
                geometry_type=str(properties.get("geometry_type", "Point")),
                subtitle=str(properties.get("subtitle", "")),
                description=str(properties.get("description", "")),
                source_url=str(properties.get("source_url", "")),
                record_count=int(properties.get("record_count", 1) or 1),
                popup_rows=popup_rows,
                time_start_bp=_optional_int(properties.get("time_start_bp")),
                time_end_bp=_optional_int(properties.get("time_end_bp")),
                time_mean_bp=_optional_int(properties.get("time_mean_bp")),
                time_label=str(properties.get("time_label", "")),
                temporal_semantics=properties.get("temporal_semantics")
                if isinstance(properties.get("temporal_semantics"), dict)
                else None,
            )
        )
    return tuple(records)


def _load_sweden_density_cells(path: Path) -> tuple[_DensityCell, ...]:
    if not path.exists():
        return ()
    payload = json.loads(path.read_text(encoding="utf-8"))
    cells: list[_DensityCell] = []
    for feature in payload.get("features", []):
        if not isinstance(feature, dict):
            continue
        geometry = feature.get("geometry", {})
        properties = feature.get("properties", {})
        if not isinstance(geometry, dict) or not isinstance(properties, dict):
            continue
        if geometry.get("type") != "Polygon":
            continue
        rings = geometry.get("coordinates", [])
        if not isinstance(rings, list) or not rings:
            continue
        ring = rings[0]
        if not isinstance(ring, list) or not ring:
            continue
        latitudes = [
            float(coordinate[1])
            for coordinate in ring
            if isinstance(coordinate, list)
            and len(coordinate) >= 2
            and isinstance(coordinate[0], (int, float))
            and isinstance(coordinate[1], (int, float))
        ]
        longitudes = [
            float(coordinate[0])
            for coordinate in ring
            if isinstance(coordinate, list)
            and len(coordinate) >= 2
            and isinstance(coordinate[0], (int, float))
            and isinstance(coordinate[1], (int, float))
        ]
        if not latitudes or not longitudes:
            continue
        cells.append(
            _DensityCell(
                min_latitude=min(latitudes),
                max_latitude=max(latitudes),
                min_longitude=min(longitudes),
                max_longitude=max(longitudes),
                count=int(properties.get("count", 0) or 0),
            )
        )
    return tuple(cells)


def _load_sweden_svar_lakes(path: Path) -> tuple[_SvarLakeRecord, ...]:
    if not path.exists():
        return ()
    payload = json.loads(path.read_text(encoding="utf-8"))
    features = payload.get("features", [])
    lakes: list[_SvarLakeRecord] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        if not isinstance(properties, dict) or not isinstance(geometry, dict):
            continue
        country = str(properties.get("country", "")).strip()
        if country not in {"SE", "Sweden"}:
            continue
        representative_point = geometry_to_representative_point(geometry)
        if representative_point is None:
            continue
        longitude, latitude, _geometry_type = representative_point
        lake_name = next(
            (
                value.strip()
                for value in (
                    str(properties.get("name", "")),
                    str(properties.get("register_name", "")),
                    str(properties.get("water_name", "")),
                    str(properties.get("fallback_name", "")),
                )
                if value.strip()
            ),
            "",
        )
        if not lake_name:
            continue
        cleaned_name = _clean_lake_name_display(lake_name)
        name_key = _lake_name_key(cleaned_name)
        if not name_key:
            continue
        area_km2 = properties.get("area_km2")
        lakes.append(
            _SvarLakeRecord(
                lake_name=cleaned_name,
                lake_label=cleaned_name,
                lake_token=_build_lake_token(
                    cleaned_name,
                    latitude=float(latitude),
                    longitude=float(longitude),
                ),
                name_key=name_key,
                latitude=round(float(latitude), 6),
                longitude=round(float(longitude), 6),
                source_url=str(properties.get("source_url", "")).strip(),
                lake_registry_id=str(properties.get("sjoid", "")).strip(),
                lake_registry_uuid=str(properties.get("sj_uuid", "")).strip(),
                lake_water_identity=str(properties.get("sj_vatten_id", "")).strip(),
                lake_name_status=str(properties.get("lake_name_status", "")).strip(),
                lake_area_km2=float(area_km2)
                if isinstance(area_km2, (int, float))
                else None,
            )
        )
    return tuple(
        sorted(lakes, key=lambda lake: (lake.lake_name, lake.latitude, lake.longitude))
    )


def _load_sweden_neotoma_position_notes(context_root: Path) -> dict[str, str]:
    path = context_root / "neotoma" / "raw" / "neotoma_pollen_sites.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        return {}
    notes: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        site_id = str(row.get("siteid", "")).strip()
        note = _normalize_note_text(str(row.get("notes", "")))
        if site_id and note and _note_signals_position_uncertainty(note):
            notes[site_id] = note
    return notes


def _derive_lake_candidates(
    pollen_points: Iterable[ContextPointRecord],
    *,
    neotoma_position_notes: dict[str, str],
) -> tuple[LakeEvidenceCandidate, ...]:
    lake_points: list[_LakeSourcePoint] = []
    for point in pollen_points:
        basin_posture = _resolve_basin_posture(point.name, point.description)
        if basin_posture != "lake_basin":
            continue
        name_key = _lake_name_key(point.name)
        if not name_key:
            continue
        position_note = (
            neotoma_position_notes.get(point.record_id)
            if point.layer_key == "neotoma-pollen"
            else None
        )
        lake_points.append(
            _LakeSourcePoint(
                point=point,
                name_key=name_key,
                cleaned_name=_clean_lake_name_display(point.name),
                source_record=f"{point.layer_key}:{point.record_id}",
                position_note=position_note,
            )
        )

    components = _build_lake_components(lake_points)
    provisional_candidates: list[dict[str, object]] = []
    for component in components:
        points = tuple(component)
        canonical_name = _choose_canonical_lake_name(points)
        representative_source_point = _choose_representative_source_point(points)
        representative_latitude = round(representative_source_point.point.latitude, 6)
        representative_longitude = round(representative_source_point.point.longitude, 6)
        pollen_sources = tuple(
            sorted({source_point.point.layer_key for source_point in points})
        )
        supporting_names = tuple(
            sorted({source_point.cleaned_name for source_point in points})
        )
        supporting_source_records = tuple(
            sorted({source_point.source_record for source_point in points})
        )
        supporting_source_points = tuple(
            sorted(
                (
                    LakeEvidenceSourceAnchor(
                        source_record=source_point.source_record,
                        source_name=source_point.cleaned_name,
                        source_layer_key=source_point.point.layer_key,
                        latitude=source_point.point.latitude,
                        longitude=source_point.point.longitude,
                        source_url=source_point.point.source_url,
                    )
                    for source_point in points
                ),
                key=lambda source_point: (
                    source_point.source_name,
                    source_point.source_layer_key,
                    source_point.source_record,
                ),
            )
        )
        coordinate_spread_km = round(_max_pair_distance(points), 4)
        ambiguity_flags = list(_base_ambiguity_flags(points, coordinate_spread_km))
        position_notes = tuple(
            sorted(
                {
                    source_point.position_note
                    for source_point in points
                    if source_point.position_note
                }
            )
        )
        direct_pollen_signal = round(
            _weighted_average(
                (
                    min(1.0, len(pollen_sources) / 2.0),
                    0.35,
                ),
                (
                    min(1.0, len(points) / 4.0),
                    0.25,
                ),
                (
                    _time_aware_ratio(
                        tuple(source_point.point for source_point in points)
                    ),
                    0.2,
                ),
                (
                    1.0,
                    0.2,
                ),
            ),
            4,
        )
        provisional_candidates.append(
            {
                "lake_name": canonical_name,
                "name_key": _lake_name_key(canonical_name),
                "lake_token": _build_lake_token(
                    canonical_name,
                    latitude=representative_latitude,
                    longitude=representative_longitude,
                ),
                "latitude": representative_latitude,
                "longitude": representative_longitude,
                "basin_posture": "lake_basin",
                "direct_pollen_source_count": len(pollen_sources),
                "direct_pollen_record_count": len(points),
                "time_aware_direct_pollen_records": sum(
                    1
                    for source_point in points
                    if source_point.point.time_start_bp is not None
                    and source_point.point.time_end_bp is not None
                ),
                "pollen_sources": pollen_sources,
                "supporting_pollen_names": supporting_names,
                "supporting_source_records": supporting_source_records,
                "supporting_source_points": supporting_source_points,
                "representative_source_record": representative_source_point.source_record,
                "representative_source_layer_key": representative_source_point.point.layer_key,
                "representative_source_name": representative_source_point.cleaned_name,
                "representative_source_url": representative_source_point.point.source_url,
                "coordinate_resolution_method": _coordinate_resolution_method(points),
                "coordinate_spread_km": coordinate_spread_km,
                "ambiguity_flags": ambiguity_flags,
                "position_notes": position_notes,
                "direct_pollen_signal": direct_pollen_signal,
            }
        )

    duplicate_name_counts = Counter(
        candidate["name_key"]
        for candidate in provisional_candidates
        if candidate["name_key"]
    )
    candidates: list[LakeEvidenceCandidate] = []
    for candidate in provisional_candidates:
        ambiguity_flags = list(candidate["ambiguity_flags"])
        duplicate_name_count = duplicate_name_counts[candidate["name_key"]]
        if duplicate_name_count > 1 and "duplicate_sweden_name" not in ambiguity_flags:
            ambiguity_flags.append("duplicate_sweden_name")
        ambiguity_flags = sorted(set(ambiguity_flags))
        lake_name = str(candidate["lake_name"])
        latitude = float(candidate["latitude"])
        longitude = float(candidate["longitude"])
        candidates.append(
            LakeEvidenceCandidate(
                lake_name=lake_name,
                lake_label=_build_lake_label(
                    lake_name,
                    latitude=latitude,
                    longitude=longitude,
                    duplicate_name_count=duplicate_name_count,
                    ambiguity_flags=tuple(ambiguity_flags),
                ),
                lake_token=str(candidate["lake_token"]),
                name_key=str(candidate["name_key"]),
                latitude=latitude,
                longitude=longitude,
                basin_posture=str(candidate["basin_posture"]),
                direct_pollen_source_count=int(candidate["direct_pollen_source_count"]),
                direct_pollen_record_count=int(candidate["direct_pollen_record_count"]),
                time_aware_direct_pollen_records=int(
                    candidate["time_aware_direct_pollen_records"]
                ),
                pollen_sources=tuple(candidate["pollen_sources"]),  # type: ignore[arg-type]
                supporting_pollen_names=tuple(
                    candidate["supporting_pollen_names"]  # type: ignore[arg-type]
                ),
                supporting_source_records=tuple(
                    candidate["supporting_source_records"]  # type: ignore[arg-type]
                ),
                supporting_source_points=tuple(
                    candidate["supporting_source_points"]  # type: ignore[arg-type]
                ),
                representative_source_record=str(
                    candidate["representative_source_record"]
                ),
                representative_source_layer_key=str(
                    candidate["representative_source_layer_key"]
                ),
                representative_source_name=str(candidate["representative_source_name"]),
                representative_source_url=str(candidate["representative_source_url"]),
                coordinate_resolution_method=str(
                    candidate["coordinate_resolution_method"]
                ),
                duplicate_name_count=duplicate_name_count,
                coordinate_spread_km=float(candidate["coordinate_spread_km"]),
                ambiguity_flags=tuple(ambiguity_flags),
                ambiguity_note=_build_ambiguity_note(
                    duplicate_name_count=duplicate_name_count,
                    coordinate_spread_km=float(candidate["coordinate_spread_km"]),
                    ambiguity_flags=tuple(ambiguity_flags),
                    position_notes=tuple(candidate["position_notes"]),  # type: ignore[arg-type]
                ),
                direct_pollen_signal=float(candidate["direct_pollen_signal"]),
            )
        )
    return tuple(sorted(candidates, key=lambda candidate: candidate.lake_label))


def _derive_svar_lake_candidates(
    svar_lakes: Sequence[_SvarLakeRecord],
    *,
    pollen_points: Sequence[ContextPointRecord],
    neotoma_position_notes: dict[str, str],
    human_points: Sequence[_PointEvidence],
) -> tuple[LakeEvidenceCandidate, ...]:
    del neotoma_position_notes
    lake_basin_pollen_points = tuple(
        point
        for point in pollen_points
        if _resolve_basin_posture(point.name, point.description) == "lake_basin"
    )
    provisional_candidates: list[dict[str, object]] = []
    for lake in svar_lakes:
        if lake.lake_name_status in {"fallback_waterwebb_label", "unnamed"}:
            continue
        lake_sampling_posture, lake_sampling_notes = _classify_sampling_lake(
            lake.lake_name,
            lake_area_km2=lake.lake_area_km2,
        )
        if lake_sampling_posture in {
            "engineered_waterbody_excluded",
            "wetland_context_excluded",
        }:
            continue
        nearest_human_distance = min(
            (
                haversine_km(
                    latitude_a=lake.latitude,
                    longitude_a=lake.longitude,
                    latitude_b=point.latitude,
                    longitude_b=point.longitude,
                )
                for point in human_points
            ),
            default=None,
        )
        if nearest_human_distance is None or nearest_human_distance > 50:
            continue
        direct_pollen_points = tuple(
            point
            for point in lake_basin_pollen_points
            if _is_direct_lake_pollen_match(lake, point)
        )
        pollen_sources = tuple(
            sorted({point.layer_key for point in direct_pollen_points})
        )
        supporting_pollen_names = tuple(
            sorted(
                {_clean_lake_name_display(point.name) for point in direct_pollen_points}
            )
        )
        supporting_source_records = tuple(
            sorted(
                {
                    f"svar-lakes:{lake.lake_registry_id or lake.lake_registry_uuid or lake.lake_token}",
                    *(
                        f"{point.layer_key}:{point.record_id}"
                        for point in direct_pollen_points
                    ),
                }
            )
        )
        supporting_source_points = tuple(
            [
                LakeEvidenceSourceAnchor(
                    source_record=(
                        f"svar-lakes:{lake.lake_registry_id or lake.lake_registry_uuid or lake.lake_token}"
                    ),
                    source_name=lake.lake_name,
                    source_layer_key="svar-lakes",
                    latitude=lake.latitude,
                    longitude=lake.longitude,
                    source_url=lake.source_url,
                ),
                *sorted(
                    (
                        LakeEvidenceSourceAnchor(
                            source_record=f"{point.layer_key}:{point.record_id}",
                            source_name=_clean_lake_name_display(point.name),
                            source_layer_key=point.layer_key,
                            latitude=point.latitude,
                            longitude=point.longitude,
                            source_url=point.source_url,
                        )
                        for point in direct_pollen_points
                    ),
                    key=lambda source_point: (
                        source_point.source_name,
                        source_point.source_layer_key,
                        source_point.source_record,
                    ),
                ),
            ]
        )
        ambiguity_flags: list[str] = []
        if lake.lake_name_status and lake.lake_name_status not in {
            "official_register_name",
            "water_surface_name",
        }:
            ambiguity_flags.append("non_official_registry_name")
        lake_sampling_fit = _lake_sampling_fit(
            lake_area_km2=lake.lake_area_km2,
            lake_sampling_posture=lake_sampling_posture,
        )
        nearby_human_points = tuple(
            point
            for point in human_points
            if haversine_km(
                latitude_a=lake.latitude,
                longitude_a=lake.longitude,
                latitude_b=point.latitude,
                longitude_b=point.longitude,
            )
            <= 50
        )
        direct_pollen_signal = round(
            _weighted_average(
                (min(1.0, len(pollen_sources) / 2.0), 0.3),
                (min(1.0, len(direct_pollen_points) / 4.0), 0.25),
                (_time_aware_ratio(direct_pollen_points), 0.15),
                (
                    _human_context_overlap_ratio(
                        direct_pollen_points,
                        nearby_human_points,
                    ),
                    0.2,
                ),
                (1.0 if direct_pollen_points else 0.0, 0.1),
            ),
            4,
        )
        provisional_candidates.append(
            {
                "lake_name": lake.lake_name,
                "name_key": lake.name_key,
                "lake_token": (
                    f"sweden_lake_registry:{lake.lake_registry_id}"
                    if lake.lake_registry_id
                    else lake.lake_token
                ),
                "latitude": lake.latitude,
                "longitude": lake.longitude,
                "basin_posture": "lake_basin",
                "direct_pollen_source_count": len(pollen_sources),
                "direct_pollen_record_count": len(direct_pollen_points),
                "time_aware_direct_pollen_records": sum(
                    1
                    for point in direct_pollen_points
                    if point.time_start_bp is not None and point.time_end_bp is not None
                ),
                "pollen_sources": pollen_sources,
                "supporting_pollen_names": supporting_pollen_names,
                "supporting_source_records": supporting_source_records,
                "supporting_source_points": supporting_source_points,
                "representative_source_record": (
                    f"svar-lakes:{lake.lake_registry_id or lake.lake_registry_uuid or lake.lake_token}"
                ),
                "representative_source_layer_key": "svar-lakes",
                "representative_source_name": lake.lake_name,
                "representative_source_url": lake.source_url,
                "coordinate_resolution_method": "svar_polygon_representative_point",
                "coordinate_spread_km": 0.0,
                "ambiguity_flags": ambiguity_flags,
                "position_notes": (),
                "direct_pollen_signal": direct_pollen_signal,
                "lake_registry_id": lake.lake_registry_id,
                "lake_registry_uuid": lake.lake_registry_uuid,
                "lake_water_identity": lake.lake_water_identity,
                "lake_name_status": lake.lake_name_status,
                "lake_area_km2": lake.lake_area_km2,
                "lake_sampling_posture": lake_sampling_posture,
                "lake_sampling_fit": lake_sampling_fit,
                "lake_sampling_notes": lake_sampling_notes,
            }
        )

    duplicate_name_counts = Counter(
        candidate["name_key"]
        for candidate in provisional_candidates
        if candidate["name_key"]
    )
    candidates: list[LakeEvidenceCandidate] = []
    for candidate in provisional_candidates:
        ambiguity_flags = list(candidate["ambiguity_flags"])
        duplicate_name_count = duplicate_name_counts[str(candidate["name_key"])]
        if duplicate_name_count > 1 and "duplicate_sweden_name" not in ambiguity_flags:
            ambiguity_flags.append("duplicate_sweden_name")
        ambiguity_flags = sorted(set(ambiguity_flags))
        lake_name = str(candidate["lake_name"])
        latitude = float(candidate["latitude"])
        longitude = float(candidate["longitude"])
        candidates.append(
            LakeEvidenceCandidate(
                lake_name=lake_name,
                lake_label=_build_lake_label(
                    lake_name,
                    latitude=latitude,
                    longitude=longitude,
                    duplicate_name_count=duplicate_name_count,
                    ambiguity_flags=tuple(ambiguity_flags),
                ),
                lake_token=str(candidate["lake_token"]),
                name_key=str(candidate["name_key"]),
                latitude=latitude,
                longitude=longitude,
                basin_posture=str(candidate["basin_posture"]),
                direct_pollen_source_count=int(candidate["direct_pollen_source_count"]),
                direct_pollen_record_count=int(candidate["direct_pollen_record_count"]),
                time_aware_direct_pollen_records=int(
                    candidate["time_aware_direct_pollen_records"]
                ),
                pollen_sources=tuple(candidate["pollen_sources"]),  # type: ignore[arg-type]
                supporting_pollen_names=tuple(
                    candidate["supporting_pollen_names"]  # type: ignore[arg-type]
                ),
                supporting_source_records=tuple(
                    candidate["supporting_source_records"]  # type: ignore[arg-type]
                ),
                supporting_source_points=tuple(
                    candidate["supporting_source_points"]  # type: ignore[arg-type]
                ),
                representative_source_record=str(
                    candidate["representative_source_record"]
                ),
                representative_source_layer_key=str(
                    candidate["representative_source_layer_key"]
                ),
                representative_source_name=str(candidate["representative_source_name"]),
                representative_source_url=str(candidate["representative_source_url"]),
                coordinate_resolution_method=str(
                    candidate["coordinate_resolution_method"]
                ),
                duplicate_name_count=duplicate_name_count,
                coordinate_spread_km=float(candidate["coordinate_spread_km"]),
                ambiguity_flags=tuple(ambiguity_flags),
                ambiguity_note=_build_ambiguity_note(
                    duplicate_name_count=duplicate_name_count,
                    coordinate_spread_km=float(candidate["coordinate_spread_km"]),
                    ambiguity_flags=tuple(ambiguity_flags),
                    position_notes=tuple(candidate["position_notes"]),  # type: ignore[arg-type]
                    lake_name_status=str(candidate["lake_name_status"]),
                ),
                direct_pollen_signal=float(candidate["direct_pollen_signal"]),
                lake_registry_id=str(candidate["lake_registry_id"]),
                lake_registry_uuid=str(candidate["lake_registry_uuid"]),
                lake_water_identity=str(candidate["lake_water_identity"]),
                lake_name_status=str(candidate["lake_name_status"]),
                lake_area_km2=float(candidate["lake_area_km2"])
                if isinstance(candidate["lake_area_km2"], (int, float))
                else None,
                lake_sampling_posture=str(candidate["lake_sampling_posture"]),
                lake_sampling_fit=float(candidate["lake_sampling_fit"]),
                lake_sampling_notes=tuple(
                    candidate["lake_sampling_notes"]  # type: ignore[arg-type]
                ),
            )
        )
    return tuple(sorted(candidates, key=lambda candidate: candidate.lake_label))


def _build_lake_components(
    lake_points: Sequence[_LakeSourcePoint],
) -> tuple[tuple[_LakeSourcePoint, ...], ...]:
    components: list[tuple[_LakeSourcePoint, ...]] = []
    visited: set[int] = set()
    adjacency = {
        index: {
            other_index
            for other_index in range(len(lake_points))
            if other_index != index
            and _lake_points_match(lake_points[index], lake_points[other_index])
        }
        for index in range(len(lake_points))
    }
    for index in range(len(lake_points)):
        if index in visited:
            continue
        stack = [index]
        component_indexes: list[int] = []
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            component_indexes.append(current)
            stack.extend(adjacency[current] - visited)
        components.append(
            tuple(
                sorted(
                    (lake_points[item] for item in component_indexes),
                    key=lambda source_point: (
                        source_point.cleaned_name,
                        source_point.point.layer_key,
                        source_point.point.record_id,
                    ),
                )
            )
        )
    return tuple(components)


def _lake_points_match(left: _LakeSourcePoint, right: _LakeSourcePoint) -> bool:
    if left.name_key != right.name_key:
        return False
    return (
        haversine_km(
            latitude_a=left.point.latitude,
            longitude_a=left.point.longitude,
            latitude_b=right.point.latitude,
            longitude_b=right.point.longitude,
        )
        <= _LAKE_MATCH_DISTANCE_KM
    )


def _choose_canonical_lake_name(points: Sequence[_LakeSourcePoint]) -> str:
    cleaned_counts = Counter(source_point.cleaned_name for source_point in points)
    best = max(
        points,
        key=lambda source_point: (
            _name_has_non_ascii(source_point.cleaned_name),
            cleaned_counts[source_point.cleaned_name],
            _lake_name_source_priority(source_point.point.layer_key),
            len(source_point.cleaned_name),
            source_point.cleaned_name,
        ),
    )
    return best.cleaned_name


def _choose_representative_source_point(
    points: Sequence[_LakeSourcePoint],
) -> _LakeSourcePoint:
    coordinate_counts = Counter(
        (
            round(source_point.point.latitude, 6),
            round(source_point.point.longitude, 6),
        )
        for source_point in points
    )
    return min(
        points,
        key=lambda source_point: (
            -coordinate_counts[
                (
                    round(source_point.point.latitude, 6),
                    round(source_point.point.longitude, 6),
                )
            ],
            _total_distance_to_component(source_point, points),
            -_lake_name_source_priority(source_point.point.layer_key),
            -_name_has_non_ascii(source_point.cleaned_name),
            source_point.cleaned_name,
            source_point.source_record,
        ),
    )


def _total_distance_to_component(
    anchor: _LakeSourcePoint,
    points: Sequence[_LakeSourcePoint],
) -> float:
    return round(
        sum(
            haversine_km(
                latitude_a=anchor.point.latitude,
                longitude_a=anchor.point.longitude,
                latitude_b=other.point.latitude,
                longitude_b=other.point.longitude,
            )
            for other in points
        ),
        6,
    )


def _coordinate_resolution_method(points: Sequence[_LakeSourcePoint]) -> str:
    unique_coordinates = {
        (
            round(source_point.point.latitude, 6),
            round(source_point.point.longitude, 6),
        )
        for source_point in points
    }
    if len(unique_coordinates) == 1:
        return "shared_source_coordinate"
    return "source_coordinate_medoid"


def _base_ambiguity_flags(
    points: Sequence[_LakeSourcePoint], coordinate_spread_km: float
) -> tuple[str, ...]:
    flags: set[str] = set()
    if len({source_point.cleaned_name for source_point in points}) > 1:
        flags.add("source_name_variants")
    if coordinate_spread_km >= _COORDINATE_SPREAD_FLAG_KM:
        flags.add("source_coordinate_spread")
    if any(source_point.position_note for source_point in points):
        flags.add("source_position_note")
    return tuple(sorted(flags))


def _build_lake_label(
    lake_name: str,
    *,
    latitude: float,
    longitude: float,
    duplicate_name_count: int,
    ambiguity_flags: tuple[str, ...],
) -> str:
    if duplicate_name_count > 1 or ambiguity_flags:
        return f"{lake_name} ({latitude:.6f}, {longitude:.6f})"
    return lake_name


def _build_ambiguity_note(
    *,
    duplicate_name_count: int,
    coordinate_spread_km: float,
    ambiguity_flags: tuple[str, ...],
    position_notes: tuple[str, ...],
    lake_name_status: str = "",
) -> str:
    parts: list[str] = []
    if "duplicate_sweden_name" in ambiguity_flags:
        parts.append(
            f"{duplicate_name_count} Sweden candidates share this cleaned lake name."
        )
    if "source_coordinate_spread" in ambiguity_flags:
        parts.append(
            f"Source coordinates span {coordinate_spread_km:.2f} km inside this candidate."
        )
    if "source_name_variants" in ambiguity_flags:
        parts.append(
            "Source records use more than one lake name form for this candidate."
        )
    if "non_official_registry_name" in ambiguity_flags and lake_name_status:
        parts.append(
            "Lake naming falls back to a non-register registry label "
            f"({lake_name_status})."
        )
    if "source_position_note" in ambiguity_flags and position_notes:
        parts.append(position_notes[0])
    return " ".join(parts)


def _classify_sampling_lake(
    lake_name: str,
    *,
    lake_area_km2: float | None,
) -> tuple[str, tuple[str, ...]]:
    normalized_name = _normalize_text(lake_name)
    has_lake_term = any(term in normalized_name for term in _LAKE_NAME_TERMS)
    has_wetland_term = any(term in normalized_name for term in _WETLAND_TERMS)
    has_engineered_term = any(term in normalized_name for term in _ENGINEERED_WATER_TERMS)
    notes: list[str] = []
    if has_wetland_term and not has_lake_term:
        notes.append("registry name points to a wetland-style basin rather than a lake")
        return ("wetland_context_excluded", tuple(notes))
    if has_engineered_term and not has_lake_term:
        notes.append(
            "registry name points to an engineered water body rather than a natural lake"
        )
        return ("engineered_waterbody_excluded", tuple(notes))
    if lake_area_km2 is not None and lake_area_km2 < 0.05:
        notes.append(
            "very small mapped water surface; treat as a micro-basin until field validation confirms suitability"
        )
        return ("small_lake_review", tuple(notes))
    if lake_area_km2 is not None and lake_area_km2 < 0.15:
        notes.append(
            "small mapped water surface; prefer checking basin depth and access before field planning"
        )
        return ("compact_lake_candidate", tuple(notes))
    return ("sampling_lake_candidate", tuple(notes))


def _lake_sampling_fit(
    *,
    lake_area_km2: float | None,
    lake_sampling_posture: str,
) -> float:
    if lake_sampling_posture in {
        "engineered_waterbody_excluded",
        "wetland_context_excluded",
    }:
        return 0.0
    if lake_area_km2 is None:
        area_score = 0.7
    elif lake_area_km2 < 0.03:
        area_score = 0.15
    elif lake_area_km2 < 0.05:
        area_score = 0.3
    elif lake_area_km2 < 0.15:
        area_score = 0.55
    elif lake_area_km2 < 0.5:
        area_score = 0.78
    elif lake_area_km2 < 20:
        area_score = 1.0
    else:
        area_score = 0.9
    posture_score = {
        "small_lake_review": 0.45,
        "compact_lake_candidate": 0.75,
        "sampling_lake_candidate": 1.0,
    }.get(lake_sampling_posture, 0.6)
    return round(_weighted_average((area_score, 0.6), (posture_score, 0.4)), 4)


def _build_raw_band_metrics(
    candidate: LakeEvidenceCandidate,
    candidates: Sequence[LakeEvidenceCandidate],
    human_points: Sequence[_PointEvidence],
    animal_points: Sequence[_PointEvidence],
    sead_points: Sequence[ContextPointRecord],
    raa_cells: Sequence[_DensityCell],
    *,
    radius_km: int,
    pollen_points: Sequence[ContextPointRecord] | None = None,
) -> dict[str, int]:
    nearby_human_points = tuple(
        point
        for point in human_points
        if haversine_km(
            latitude_a=candidate.latitude,
            longitude_a=candidate.longitude,
            latitude_b=point.latitude,
            longitude_b=point.longitude,
        )
        <= radius_km
    )
    if pollen_points is None:
        nearby_pollen_lake_count = sum(
            1
            for other in candidates
            if other.lake_token != candidate.lake_token
            and _distance_between_candidates(candidate, other) <= radius_km
        )
        time_aware_pollen_site_count = 0
        human_overlap_pollen_site_count = 0
    else:
        nearby_pollen_points = tuple(
            point
            for point in pollen_points
            if haversine_km(
                latitude_a=candidate.latitude,
                longitude_a=candidate.longitude,
                latitude_b=point.latitude,
                longitude_b=point.longitude,
            )
            <= radius_km
        )
        nearby_pollen_lake_count = len(nearby_pollen_points)
        time_aware_pollen_site_count = sum(
            1
            for point in nearby_pollen_points
            if _context_point_has_numeric_interval(point)
        )
        human_overlap_pollen_site_count = sum(
            1
            for point in nearby_pollen_points
            if _context_point_overlaps_any_human(point, nearby_human_points)
        )
    human_locality_count = 0
    human_sample_count = 0
    for point in nearby_human_points:
        human_locality_count += 1
        human_sample_count += point.sample_count
    animal_locality_count = 0
    animal_sample_count = 0
    for point in animal_points:
        if (
            haversine_km(
                latitude_a=candidate.latitude,
                longitude_a=candidate.longitude,
                latitude_b=point.latitude,
                longitude_b=point.longitude,
            )
            <= radius_km
        ):
            animal_locality_count += 1
            animal_sample_count += point.sample_count
    nearby_sead_points = tuple(
        point
        for point in sead_points
        if haversine_km(
            latitude_a=candidate.latitude,
            longitude_a=candidate.longitude,
            latitude_b=point.latitude,
            longitude_b=point.longitude,
        )
        <= radius_km
    )
    sead_site_count = len(nearby_sead_points)
    time_aware_sead_site_count = sum(
        1 for point in nearby_sead_points if _context_point_has_numeric_interval(point)
    )
    human_overlap_sead_site_count = sum(
        1
        for point in nearby_sead_points
        if _context_point_overlaps_any_human(point, nearby_human_points)
    )
    raa_density_site_count = sum(
        cell.count
        for cell in raa_cells
        if _distance_to_density_cell(candidate, cell) <= radius_km
    )
    evidence_family_count = (1 if candidate.direct_pollen_signal > 0 else 0) + sum(
        1
        for has_evidence in (
            nearby_pollen_lake_count > 0,
            human_locality_count > 0,
            animal_locality_count > 0,
            sead_site_count > 0 or raa_density_site_count > 0,
        )
        if has_evidence
    )
    return {
        "nearby_pollen_lake_count": nearby_pollen_lake_count,
        "time_aware_pollen_site_count": time_aware_pollen_site_count,
        "human_overlap_pollen_site_count": human_overlap_pollen_site_count,
        "human_adna_locality_count": human_locality_count,
        "human_adna_sample_count": human_sample_count,
        "domesticated_animal_locality_count": animal_locality_count,
        "domesticated_animal_sample_count": animal_sample_count,
        "sead_site_count": sead_site_count,
        "time_aware_sead_site_count": time_aware_sead_site_count,
        "human_overlap_sead_site_count": human_overlap_sead_site_count,
        "raa_density_site_count": raa_density_site_count,
        "evidence_family_count": evidence_family_count,
    }


def _build_band_maxima(
    raw_scores: dict[str, dict[int, dict[str, int]]],
    *,
    radius_km: int,
) -> dict[str, int]:
    keys = (
        "nearby_pollen_lake_count",
        "time_aware_pollen_site_count",
        "human_overlap_pollen_site_count",
        "human_adna_locality_count",
        "human_adna_sample_count",
        "domesticated_animal_locality_count",
        "domesticated_animal_sample_count",
        "sead_site_count",
        "time_aware_sead_site_count",
        "human_overlap_sead_site_count",
        "raa_density_site_count",
    )
    return {
        key: max(raw_scores[lake_token][radius_km][key] for lake_token in raw_scores)
        for key in keys
    }


def _resolve_basin_posture(name: str, description: str) -> str:
    normalized_name = _normalize_text(name)
    normalized_description = _normalize_text(description)
    if any(
        term in normalized_name or term in normalized_description
        for term in _LAKE_NAME_TERMS
    ):
        return "lake_basin"
    if any(
        term in normalized_name or term in normalized_description
        for term in _WETLAND_TERMS
    ):
        return "wetland_basin"
    return "ambiguous_basin"


def _build_lake_token(name: str, *, latitude: float, longitude: float) -> str:
    return (
        f"sweden_lake:{_lake_name_key(name)}:{round(latitude, 6)}:{round(longitude, 6)}"
    )


def _lake_name_key(value: str) -> str:
    tokens = _tokenize_lake_name(value)
    while tokens and (tokens[0] in _GENERIC_LAKE_TOKENS or len(tokens[0]) == 1):
        tokens = tokens[1:]
    return "".join(tokens)


def _tokenize_lake_name(value: str) -> list[str]:
    normalized = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    return [token for token in re.findall(r"[a-z0-9]+", normalized.casefold()) if token]


def _clean_lake_name_display(value: str) -> str:
    cleaned = re.sub(r"^\s*lake\s+", "", value, flags=re.IGNORECASE)
    cleaned = re.sub(r"^\s*[A-Za-zÅÄÖåäö]\.\s+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -")
    return cleaned or value.strip()


def _lake_name_source_priority(layer_key: str) -> int:
    priorities = {
        "landclim-sites": 3,
        "neotoma-pollen": 2,
    }
    return priorities.get(layer_key, 0)


def _name_has_non_ascii(value: str) -> int:
    return 1 if any(ord(character) > 127 for character in value) else 0


def _max_pair_distance(points: Sequence[_LakeSourcePoint]) -> float:
    maximum = 0.0
    for left_index, left in enumerate(points):
        for right in points[left_index + 1 :]:
            maximum = max(
                maximum,
                haversine_km(
                    latitude_a=left.point.latitude,
                    longitude_a=left.point.longitude,
                    latitude_b=right.point.latitude,
                    longitude_b=right.point.longitude,
                ),
            )
    return maximum


def _normalize_text(value: str) -> str:
    normalized = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    return re.sub(r"[^a-z0-9]+", "", normalized.casefold())


def _normalize_note_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\r", " ").replace("\n", " ")).strip()


def _note_signals_position_uncertainty(note: str) -> bool:
    return any(pattern.search(note) for pattern in _POSITION_NOTE_PATTERNS)


def _time_aware_ratio(points: Sequence[ContextPointRecord]) -> float:
    if not points:
        return 0.0
    time_aware = sum(
        1
        for point in points
        if _context_point_has_numeric_interval(point)
    )
    return round(time_aware / len(points), 4)


def _context_point_has_numeric_interval(point: ContextPointRecord) -> bool:
    if temporal_semantics_has_numeric_interval(point.temporal_semantics):
        return True
    return point.time_start_bp is not None and point.time_end_bp is not None


def _human_context_overlap_ratio(
    points: Sequence[ContextPointRecord],
    human_points: Sequence[_PointEvidence],
) -> float:
    if not points:
        return 0.0
    overlaps = sum(
        1 for point in points if _context_point_overlaps_any_human(point, human_points)
    )
    return round(overlaps / len(points), 4)


def _context_point_overlaps_any_human(
    point: ContextPointRecord,
    human_points: Sequence[_PointEvidence],
) -> bool:
    if not _context_point_has_numeric_interval(point):
        return False
    if point.time_start_bp is None or point.time_end_bp is None:
        return False
    return any(
        _intervals_overlap(
            point.time_start_bp,
            point.time_end_bp,
            human_point.time_start_bp,
            human_point.time_end_bp,
        )
        for human_point in human_points
        if human_point.time_start_bp is not None and human_point.time_end_bp is not None
    )


def _intervals_overlap(
    start_a: int | None,
    end_a: int | None,
    start_b: int | None,
    end_b: int | None,
) -> bool:
    if (
        start_a is None
        or end_a is None
        or start_b is None
        or end_b is None
    ):
        return False
    left_start, left_end = sorted((start_a, end_a))
    right_start, right_end = sorted((start_b, end_b))
    return not (left_end < right_start or left_start > right_end)


def _distance_between_candidates(
    left: LakeEvidenceCandidate, right: LakeEvidenceCandidate
) -> float:
    return haversine_km(
        latitude_a=left.latitude,
        longitude_a=left.longitude,
        latitude_b=right.latitude,
        longitude_b=right.longitude,
    )


def _distance_to_density_cell(
    candidate: LakeEvidenceCandidate, cell: _DensityCell
) -> float:
    nearest_latitude = min(
        max(candidate.latitude, cell.min_latitude),
        cell.max_latitude,
    )
    nearest_longitude = min(
        max(candidate.longitude, cell.min_longitude),
        cell.max_longitude,
    )
    return haversine_km(
        latitude_a=candidate.latitude,
        longitude_a=candidate.longitude,
        latitude_b=nearest_latitude,
        longitude_b=nearest_longitude,
    )


def _normalized_ratio(value: int, maximum: int) -> float:
    if maximum <= 0:
        return 0.0
    return round(value / maximum, 4)


def _weighted_average(*pairs: tuple[float, float]) -> float:
    numerator = sum(value * weight for value, weight in pairs)
    denominator = sum(weight for _, weight in pairs)
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def _weighted_band_metric(
    band_scores: Sequence[LakeEvidenceBandScore],
    metric_name: str,
) -> float:
    return round(
        sum(
            float(getattr(score, metric_name))
            * _SVAR_AGGREGATE_RADIUS_WEIGHTS.get(score.radius_km, 0.0)
            for score in band_scores
        ),
        4,
    )


def _sampling_priority_rank(sampling_posture: str) -> int:
    return {
        "sampling_lake_candidate": 0,
        "compact_lake_candidate": 1,
        "small_lake_review": 2,
        "sampling_not_scored": 3,
    }.get(sampling_posture, 4)


def _svar_band_priority_key(
    candidate: LakeEvidenceCandidate,
    band_score: LakeEvidenceBandScore,
) -> tuple[object, ...]:
    return (
        -band_score.human_adna_locality_count,
        -band_score.human_adna_sample_count,
        -candidate.direct_pollen_source_count,
        -candidate.time_aware_direct_pollen_records,
        -band_score.evidence_family_count,
        -band_score.sead_site_count,
        -band_score.raa_density_site_count,
        _sampling_priority_rank(
            candidate.lake_sampling_posture or "sampling_not_scored"
        ),
        -candidate.lake_sampling_fit,
        candidate.lake_label,
    )


def _svar_aggregate_priority_key(
    candidate: LakeEvidenceCandidate,
    band_scores: Sequence[LakeEvidenceBandScore],
) -> tuple[object, ...]:
    return (
        -_weighted_band_metric(band_scores, "human_adna_locality_count"),
        -_weighted_band_metric(band_scores, "human_adna_sample_count"),
        -candidate.direct_pollen_source_count,
        -candidate.time_aware_direct_pollen_records,
        -_weighted_band_metric(band_scores, "evidence_family_count"),
        -_weighted_band_metric(band_scores, "nearby_pollen_lake_count"),
        -_weighted_band_metric(band_scores, "sead_site_count"),
        -_weighted_band_metric(band_scores, "raa_density_site_count"),
        _sampling_priority_rank(
            candidate.lake_sampling_posture or "sampling_not_scored"
        ),
        -candidate.lake_sampling_fit,
        candidate.lake_label,
    )


def _band_score_for_radius(
    band_scores: Sequence[LakeEvidenceBandScore],
    *,
    radius_km: int,
) -> LakeEvidenceBandScore:
    for score in band_scores:
        if score.radius_km == radius_km:
            return score
    raise ValueError(f"Missing band score for radius {radius_km}")


def _optional_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    return None


def _is_direct_lake_pollen_match(
    lake: _SvarLakeRecord,
    point: ContextPointRecord,
) -> bool:
    distance_km = haversine_km(
        latitude_a=lake.latitude,
        longitude_a=lake.longitude,
        latitude_b=point.latitude,
        longitude_b=point.longitude,
    )
    point_name_key = _lake_name_key(point.name)
    if point_name_key and point_name_key == lake.name_key and distance_km <= 10:
        return True
    return distance_km <= _LAKE_MATCH_DISTANCE_KM


def _build_empty_report(
    radii_km: tuple[int, ...],
    *,
    candidate_source: str = "pollen_candidate_points",
    source_temporal_coverage: dict[str, object] | None = None,
) -> LakeEvidenceRichnessReport:
    return LakeEvidenceRichnessReport(
        schema_version="sweden-lake-evidence-richness.v2",
        country="Sweden",
        radii_km=radii_km,
        methodology=_build_methodology(
            radii_km,
            candidate_source=candidate_source,
            source_temporal_coverage=source_temporal_coverage,
        ),
        candidate_count=0,
        assessments=(),
    )


def _build_methodology(
    radii_km: tuple[int, ...],
    *,
    candidate_source: str = "pollen_candidate_points",
    source_temporal_coverage: dict[str, object] | None = None,
) -> dict[str, object]:
    if candidate_source == "svar_lake_registry":
        payload = {
            "candidate_derivation": (
                "Candidates come from the Sweden lake registry published through "
                "SMHI SVAR. Each candidate uses a representative point derived "
                "from the official lake polygon instead of a pollen-point centroid. "
                "Only lakes with at least one human aDNA locality within 50 km "
                "remain in the ranked set. Registry names that clearly describe "
                "engineered water bodies or wetlands instead of sampling lakes are "
                "kept out of the shortlist."
            ),
            "distance_bands": list(radii_km),
            "aggregate_radius_weights": {
                str(radius): _SVAR_AGGREGATE_RADIUS_WEIGHTS.get(radius, 0.0)
                for radius in radii_km
            },
            "score_components": {
                "human_adna_signal": 0.59,
                "direct_pollen_signal": 0.14,
                "nearby_pollen_signal": 0.07,
                "lake_sampling_fit": 0.07,
                "archaeology_signal": 0.07,
                "domesticated_animal_signal": 0.04,
                "evidence_diversity_signal": 0.02,
            },
            "ranking_decision_rule": (
                "Aggregate and band ranks sort first by human aDNA locality and "
                "sample coverage, then by direct pollen support, then by broader "
                "pollen and archaeology context, with sampling fit and blended score "
                "used as later tie-breakers."
            ),
            "temporal_alignment_rule": (
                "Neotoma pollen and SEAD archaeology remain lake-anchored context "
                "layers, but their stronger chronology contribution comes only from "
                "records with numeric BP intervals that overlap nearby human locality "
                "windows."
            ),
            "identity_diagnostics": {
                "coordinate_spread_flag_km": _COORDINATE_SPREAD_FLAG_KM,
                "name_match_distance_km": _LAKE_MATCH_DISTANCE_KM,
                "coordinate_resolution_methods": [
                    "svar_polygon_representative_point",
                ],
                "ambiguity_flags": [
                    "duplicate_sweden_name",
                    "non_official_registry_name",
                ],
            },
            "pollen_note": (
                "Direct pollen signal reflects lake-basin pollen records placed on "
                "or very near the official lake. Nearby pollen signal then adds "
                "broader pollen context within the active distance band, with extra "
                "credit when those pollen records carry comparable chronology that "
                "overlaps nearby human localities."
            ),
            "sampling_note": (
                "Lake suitability remains separate from evidence density. Very small "
                "basins stay visible but score lower, while registry names that "
                "clearly point to wetlands, pits, ponds, or engineered water bodies "
                "do not enter the ranked shortlist."
            ),
            "archaeology_note": (
                "SEAD contributes site-level point counts and gains stronger weight "
                "when those site spans are numerically comparable and overlap nearby "
                "human locality windows. RAÄ contributes coarse density cells, so the "
                "archaeology term still measures surrounding evidence richness rather "
                "than exact site-to-lake proximity."
            ),
            "animal_note": (
                "Domesticated animal aDNA remains a secondary contextual signal. "
                "Human aDNA is the decisive ranking term, direct pollen is the "
                "next tie-break, and archaeology resolves ties among similarly "
                "sampled lakes."
            ),
        }
        if source_temporal_coverage:
            payload["source_temporal_coverage"] = source_temporal_coverage
        return payload
    payload = {
        "candidate_derivation": (
            "Candidates come from Sweden-scoped Neotoma and LandClim pollen "
            "points whose names or site descriptions identify lake-like basins. "
            "Points merge only when their cleaned lake names match and their "
            "coordinates stay within 2 km, so nearby but differently named lakes "
            "remain distinct. Each candidate keeps one source-backed "
            "representative coordinate chosen from the supporting points instead "
            "of a synthetic arithmetic centroid. Duplicate names, coordinate "
            "spread, and source position notes remain explicit as ambiguity "
            "diagnostics."
        ),
        "distance_bands": list(radii_km),
        "aggregate_radius_weights": {
            str(radius): _AGGREGATE_RADIUS_WEIGHTS.get(radius, 0.0)
            for radius in radii_km
        },
        "score_components": {
            "direct_pollen_signal": 0.2,
            "nearby_pollen_signal": 0.1,
            "archaeology_signal": 0.25,
            "human_adna_signal": 0.2,
            "domesticated_animal_signal": 0.15,
            "evidence_diversity_signal": 0.1,
        },
        "identity_diagnostics": {
            "coordinate_spread_flag_km": _COORDINATE_SPREAD_FLAG_KM,
            "name_match_distance_km": _LAKE_MATCH_DISTANCE_KM,
            "coordinate_resolution_methods": [
                "shared_source_coordinate",
                "source_coordinate_medoid",
            ],
            "ambiguity_flags": [
                "duplicate_sweden_name",
                "source_coordinate_spread",
                "source_name_variants",
                "source_position_note",
            ],
        },
        "archaeology_note": (
            "SEAD contributes site-level point counts. RAÄ contributes coarse "
            "1-degree density cells, so the RAÄ term captures archaeology "
            "richness around the lake rather than precise site-by-site distance."
        ),
        "animal_note": (
            "Domesticated animal aDNA remains sparse in the current Sweden bundle. "
            "The ranking keeps that sparsity visible instead of inflating it."
        ),
    }
    if source_temporal_coverage:
        payload["source_temporal_coverage"] = source_temporal_coverage
    return payload


def _build_context_temporal_coverage_summary(
    pollen_points: Sequence[ContextPointRecord],
    *,
    context_root: Path,
    sead_points: Sequence[ContextPointRecord],
) -> dict[str, object]:
    neotoma_summary = _temporal_coverage_summary(
        point
        for point in pollen_points
        if point.layer_key == "neotoma-pollen" or point.source == "Neotoma"
    )
    landclim_summary = _temporal_coverage_summary(
        point
        for point in pollen_points
        if point.layer_key == "landclim-sites" or point.source == "LandClim"
    )
    sead_summary = _temporal_coverage_summary(sead_points)
    _merge_source_temporal_review(
        neotoma_summary,
        _load_review_payload(context_root / "neotoma" / "review" / "temporal_review.json"),
        source_family="neotoma",
    )
    _merge_source_temporal_review(
        sead_summary,
        _load_review_payload(context_root / "sead" / "review" / "temporal_review.json"),
        source_family="sead",
    )
    if not landclim_summary.get("capture_posture"):
        landclim_summary["capture_posture"] = "spatial_inventory_only"
    return {
        "neotoma_pollen": neotoma_summary,
        "landclim_pollen": landclim_summary,
        "sead_archaeology": sead_summary,
    }


def _temporal_coverage_summary(
    points: Iterable[ContextPointRecord],
) -> dict[str, object]:
    materialized_points = tuple(points)
    total_records = len(materialized_points)
    numeric_interval_records = sum(
        1
        for point in materialized_points
        if temporal_semantics_has_numeric_interval(point.temporal_semantics)
    )
    return {
        "record_count": total_records,
        "numeric_interval_record_count": numeric_interval_records,
        "numeric_interval_share": round(
            numeric_interval_records / total_records, 4
        )
        if total_records
        else 0.0,
    }


def _merge_source_temporal_review(
    summary: dict[str, object],
    payload: dict[str, object],
    *,
    source_family: str,
) -> None:
    if source_family == "neotoma":
        coverage_summary = payload.get("coverage_summary", {})
        if not isinstance(coverage_summary, dict):
            return
        capture_posture = str(
            coverage_summary.get("chronology_capture_posture", "")
        ).strip()
        if capture_posture:
            summary["capture_posture"] = capture_posture
        summary["bp_age_range_record_count"] = int(
            coverage_summary.get("site_count_with_bp_age_ranges", 0) or 0
        )
        summary["chronology_row_record_count"] = int(
            coverage_summary.get("site_count_with_chronologies", 0) or 0
        )
        return
    if source_family == "sead":
        inventory_summary = payload.get("inventory_summary", {})
        if not isinstance(inventory_summary, dict):
            return
        capture_posture = str(inventory_summary.get("temporal_capture_posture", "")).strip()
        if capture_posture:
            summary["capture_posture"] = capture_posture
        summary["site_inventory_only_record_count"] = int(
            inventory_summary.get("site_inventory_only_row_count", 0) or 0
        )


def _load_review_payload(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}
