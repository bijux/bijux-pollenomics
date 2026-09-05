"""Explicit score weights and ranking policy for each candidate authority."""

from __future__ import annotations

from collections.abc import Sequence

from ..metrics import _weighted_average
from ..models import LakeEvidenceBandScore, LakeEvidenceCandidate
from ..scoring import _svar_aggregate_priority_key, _svar_band_priority_key
from .signals import _BandSignals

__all__: list[str] = []


def _pollen_total_score(
    candidate: LakeEvidenceCandidate, signals: _BandSignals
) -> float:
    return round(
        candidate.direct_pollen_signal * 0.2
        + signals.nearby_pollen * 0.1
        + signals.archaeology * 0.25
        + signals.human * 0.2
        + signals.animal * 0.15
        + signals.diversity * 0.1,
        4,
    )


def _svar_total_score(candidate: LakeEvidenceCandidate, signals: _BandSignals) -> float:
    direct_pollen_source_signal = min(1.0, candidate.direct_pollen_source_count / 2.0)
    direct_pollen_signal = _weighted_average(
        (candidate.direct_pollen_signal, 0.65),
        (direct_pollen_source_signal, 0.35),
    )
    return round(
        signals.human * 0.59
        + direct_pollen_signal * 0.14
        + signals.nearby_pollen * 0.07
        + signals.archaeology * 0.07
        + signals.animal * 0.04
        + signals.diversity * 0.02
        + candidate.lake_sampling_fit * 0.07,
        4,
    )


def _pollen_band_tiebreaker(
    candidate: LakeEvidenceCandidate,
    band_score: LakeEvidenceBandScore,
    aggregate_score: float,
) -> tuple[object, ...]:
    del band_score
    return (-aggregate_score, candidate.lake_label)


def _pollen_aggregate_tiebreaker(
    candidate: LakeEvidenceCandidate,
    band_scores: Sequence[LakeEvidenceBandScore],
) -> tuple[object, ...]:
    return (-band_scores[0].total_score, candidate.lake_label)


def _svar_band_tiebreaker(
    candidate: LakeEvidenceCandidate,
    band_score: LakeEvidenceBandScore,
    aggregate_score: float,
) -> tuple[object, ...]:
    del aggregate_score
    return _svar_band_priority_key(candidate, band_score)


def _svar_aggregate_tiebreaker(
    candidate: LakeEvidenceCandidate,
    band_scores: Sequence[LakeEvidenceBandScore],
) -> tuple[object, ...]:
    return _svar_aggregate_priority_key(candidate, band_scores)
