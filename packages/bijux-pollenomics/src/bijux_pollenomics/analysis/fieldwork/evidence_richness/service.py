"""Lake evidence-richness report orchestration."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import TypedDict

from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.collection.sources.raa import assess_raa_density_authority
from .candidates import (
    _derive_lake_candidates,
    _derive_svar_lake_candidates,
)
from .inputs import (
    _load_sweden_context_points,
    _load_sweden_density_cells,
    _load_sweden_neotoma_position_notes,
    _load_sweden_pollen_points,
    _load_sweden_svar_lakes,
)
from .methodology import (
    _build_context_temporal_coverage_summary,
    _build_empty_report,
    _build_methodology,
)
from .models import (
    DEFAULT_LAKE_EVIDENCE_RADII_KM,
    LakeEvidenceBandScore,
    LakeEvidenceCandidate,
    LakeEvidenceRichnessAssessment,
    LakeEvidenceRichnessReport,
    _AGGREGATE_RADIUS_WEIGHTS,
    _SVAR_AGGREGATE_RADIUS_WEIGHTS,
    _DensityCell,
    _PointEvidence,
)
from .metrics import (
    _normalized_ratio,
    _weighted_average,
)
from .scoring import (
    _band_score_for_radius,
    _build_band_maxima,
    _build_raw_band_metrics,
    _svar_aggregate_priority_key,
    _svar_band_priority_key,
)
from .temporal import (
    _attach_temporal_context,
    _extract_animal_points,
    _extract_human_points,
)

__all__ = [
    "build_sweden_lake_evidence_richness_report",
]


class _CandidateScoreRow(TypedDict):
    candidate: LakeEvidenceCandidate
    aggregate_score: float
    band_scores: tuple[LakeEvidenceBandScore, ...]


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
    raa_authority = assess_raa_density_authority(context_root)
    raa_cells = (
        _load_sweden_density_cells(
            Path(context_root)
            / "raa"
            / "normalized"
            / "sweden_archaeology_density.geojson"
        )
        if raa_authority.admitted
        else ()
    )
    raa_authority_summary: dict[str, object] = {
        "admitted": raa_authority.admitted,
        "reason_codes": list(raa_authority.reason_codes),
        "archived_feature_count": raa_authority.archived_feature_count,
        "heritage_site_count": raa_authority.heritage_site_count,
        "density_site_count": raa_authority.density_site_count,
        "density_feature_count": raa_authority.density_feature_count,
        "reviewer_id": raa_authority.reviewer_id,
    }
    svar_candidate_path = (
        Path(context_root)
        / "svar"
        / "review"
        / "sweden_lake_candidate_registry.geojson"
    )
    svar_registry_path = (
        Path(context_root) / "svar" / "normalized" / "sweden_lake_registry.geojson"
    )
    if svar_candidate_path.exists() and not svar_registry_path.exists():
        return _build_empty_report(
            normalized_radii,
            candidate_source="svar_registry_authority_unavailable",
            source_temporal_coverage=source_temporal_coverage,
            raa_authority=raa_authority_summary,
        )
    if svar_registry_path.exists():
        return _build_svar_lake_report(
            radii_km=normalized_radii,
            svar_lake_path=svar_registry_path,
            pollen_points=pollen_points,
            neotoma_position_notes=neotoma_position_notes,
            human_points=human_points,
            animal_points=animal_points,
            sead_points=sead_points,
            raa_cells=raa_cells,
            raa_authority=raa_authority_summary,
            source_temporal_coverage=source_temporal_coverage,
        )
    candidates = _derive_lake_candidates(
        pollen_points,
        neotoma_position_notes=neotoma_position_notes,
    )
    candidates = _attach_temporal_context(
        candidates,
        pollen_points=pollen_points,
        human_points=human_points,
        animal_points=animal_points,
        sead_points=sead_points,
    )
    if not candidates:
        return _build_empty_report(
            normalized_radii,
            candidate_source="pollen_candidate_points",
            source_temporal_coverage=source_temporal_coverage,
            raa_authority=raa_authority_summary,
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
    candidate_rows: list[_CandidateScoreRow] = []
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
                    human_overlap_sead_site_count=raw["human_overlap_sead_site_count"],
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
                    row["band_scores"],
                    radius_km=radius,
                ).total_score,
                -row["aggregate_score"],
                row["candidate"].lake_label,
            ),
        )
        for rank, row in enumerate(ordered, start=1):
            updated_scores = []
            for score in row["band_scores"]:
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
            -row["aggregate_score"],
            -_band_score_for_radius(
                row["band_scores"],
                radius_km=normalized_radii[0],
            ).total_score,
            row["candidate"].lake_label,
        ),
    )
    assessments = tuple(
        LakeEvidenceRichnessAssessment(
            candidate=row["candidate"],
            aggregate_rank=rank,
            aggregate_score=row["aggregate_score"],
            band_scores=row["band_scores"],
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
            candidates=candidates,
            raa_authority=raa_authority_summary,
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
    raa_authority: dict[str, object],
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
    candidates = _attach_temporal_context(
        candidates,
        pollen_points=pollen_points,
        human_points=human_points,
        animal_points=animal_points,
        sead_points=sead_points,
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
    candidate_rows: list[_CandidateScoreRow] = []
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
                    human_overlap_sead_site_count=raw["human_overlap_sead_site_count"],
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
                    row["band_scores"],
                    radius_km=radius,
                ).total_score,
                *_svar_band_priority_key(
                    row["candidate"],
                    _band_score_for_radius(
                        row["band_scores"],
                        radius_km=radius,
                    ),
                ),
            ),
        )
        for rank, row in enumerate(ordered, start=1):
            updated_scores = []
            for score in row["band_scores"]:
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
            -row["aggregate_score"],
            *_svar_aggregate_priority_key(
                row["candidate"],
                row["band_scores"],
            ),
        ),
    )
    assessments = tuple(
        LakeEvidenceRichnessAssessment(
            candidate=row["candidate"],
            aggregate_rank=rank,
            aggregate_score=row["aggregate_score"],
            band_scores=row["band_scores"],
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
            candidates=candidates,
            raa_authority=raa_authority,
        ),
        assessments=assessments,
    )
