"""Shared distance-band scoring and deterministic candidate ranking."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import replace
from typing import TypedDict

from bijux_pollenomics.collection.contracts.models import ContextPointRecord

from ..models import (
    LakeEvidenceBandScore,
    LakeEvidenceCandidate,
    LakeEvidenceRichnessAssessment,
    _DensityCell,
    _PointEvidence,
)
from ..scoring import (
    _band_score_for_radius,
    _build_band_maxima,
    _build_raw_band_metrics,
)
from .signals import _TotalScorePolicy, _build_band_score

__all__: list[str] = []


class _CandidateScoreRow(TypedDict):
    candidate: LakeEvidenceCandidate
    aggregate_score: float
    band_scores: tuple[LakeEvidenceBandScore, ...]


_BandTiebreaker = Callable[
    [LakeEvidenceCandidate, LakeEvidenceBandScore, float], tuple[object, ...]
]
_AggregateTiebreaker = Callable[
    [LakeEvidenceCandidate, Sequence[LakeEvidenceBandScore]], tuple[object, ...]
]


def _build_candidate_score_rows(
    *,
    candidates: Sequence[LakeEvidenceCandidate],
    radii_km: tuple[int, ...],
    human_points: Sequence[_PointEvidence],
    animal_points: Sequence[_PointEvidence],
    sead_points: Sequence[ContextPointRecord],
    raa_cells: Sequence[_DensityCell],
    aggregate_radius_weights: dict[int, float],
    total_score_policy: _TotalScorePolicy,
    pollen_points: Sequence[ContextPointRecord] | None = None,
) -> list[_CandidateScoreRow]:
    raw_scores = {
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
    rows: list[_CandidateScoreRow] = []
    for candidate in candidates:
        band_scores = tuple(
            _build_band_score(
                candidate=candidate,
                radius_km=radius,
                raw=raw_scores[candidate.lake_token][radius],
                maxima=maxima_by_radius[radius],
                total_score_policy=total_score_policy,
            )
            for radius in radii_km
        )
        rows.append(
            {
                "candidate": candidate,
                "aggregate_score": round(
                    sum(
                        score.total_score
                        * aggregate_radius_weights.get(score.radius_km, 0.0)
                        for score in band_scores
                    ),
                    4,
                ),
                "band_scores": band_scores,
            }
        )
    return rows


def _rank_candidate_score_rows(
    rows: list[_CandidateScoreRow],
    *,
    radii_km: tuple[int, ...],
    band_tiebreaker: _BandTiebreaker,
    aggregate_tiebreaker: _AggregateTiebreaker,
) -> tuple[LakeEvidenceRichnessAssessment, ...]:
    for radius in radii_km:
        ordered = sorted(
            rows,
            key=lambda row: (
                -_band_score_for_radius(
                    row["band_scores"], radius_km=radius
                ).total_score,
                *band_tiebreaker(
                    row["candidate"],
                    _band_score_for_radius(row["band_scores"], radius_km=radius),
                    row["aggregate_score"],
                ),
            ),
        )
        for rank, row in enumerate(ordered, start=1):
            row["band_scores"] = tuple(
                replace(score, band_rank=rank) if score.radius_km == radius else score
                for score in row["band_scores"]
            )
    ordered_rows = sorted(
        rows,
        key=lambda row: (
            -row["aggregate_score"],
            *aggregate_tiebreaker(row["candidate"], row["band_scores"]),
        ),
    )
    return tuple(
        LakeEvidenceRichnessAssessment(
            candidate=row["candidate"],
            aggregate_rank=rank,
            aggregate_score=row["aggregate_score"],
            band_scores=row["band_scores"],
        )
        for rank, row in enumerate(ordered_rows, start=1)
    )
