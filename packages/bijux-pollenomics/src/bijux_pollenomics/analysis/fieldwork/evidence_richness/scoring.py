"""Distance-band evidence metrics and scoring."""

from __future__ import annotations

from collections.abc import Sequence

from bijux_pollenomics.core import (
    haversine_km,
)
from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from .models import (
    LakeEvidenceBandScore,
    LakeEvidenceCandidate,
    _SVAR_AGGREGATE_RADIUS_WEIGHTS,
    _DensityCell,
    _PointEvidence,
)
from .temporal import (
    _context_point_has_numeric_interval,
    _context_point_overlaps_any_human,
)

__all__ = []


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
