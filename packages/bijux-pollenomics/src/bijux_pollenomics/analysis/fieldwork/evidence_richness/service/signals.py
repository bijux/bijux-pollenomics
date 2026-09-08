"""Shared evidence-band signal construction."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..metrics import _normalized_ratio, _weighted_average
from ..models import LakeEvidenceBandScore, LakeEvidenceCandidate

__all__: list[str] = []


@dataclass(frozen=True)
class _BandSignals:
    nearby_pollen: float
    human: float
    animal: float
    archaeology: float
    diversity: float


_TotalScorePolicy = Callable[[LakeEvidenceCandidate, _BandSignals], float]


def _build_band_score(
    *,
    candidate: LakeEvidenceCandidate,
    radius_km: int,
    raw: dict[str, int],
    maxima: dict[str, int],
    total_score_policy: _TotalScorePolicy,
) -> LakeEvidenceBandScore:
    nearby_pollen = _normalized_ratio(
        raw["nearby_pollen_lake_count"], maxima["nearby_pollen_lake_count"]
    )
    if raw["nearby_pollen_lake_count"] > 0:
        nearby_pollen = _weighted_average(
            (nearby_pollen, 0.6),
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
    human = _weighted_average(
        (
            _normalized_ratio(
                raw["human_adna_locality_count"],
                maxima["human_adna_locality_count"],
            ),
            0.45,
        ),
        (
            _normalized_ratio(
                raw["human_adna_sample_count"], maxima["human_adna_sample_count"]
            ),
            0.55,
        ),
    )
    animal = _weighted_average(
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
    archaeology = _weighted_average(
        (_normalized_ratio(raw["sead_site_count"], maxima["sead_site_count"]), 0.4),
        (
            _normalized_ratio(
                raw["time_aware_sead_site_count"],
                max(raw["sead_site_count"], maxima["time_aware_sead_site_count"]),
            ),
            0.2,
        ),
        (
            _normalized_ratio(
                raw["human_overlap_sead_site_count"],
                max(raw["sead_site_count"], maxima["human_overlap_sead_site_count"]),
            ),
            0.2,
        ),
        (
            _normalized_ratio(
                raw["raa_density_site_count"], maxima["raa_density_site_count"]
            ),
            0.2,
        ),
    )
    signals = _BandSignals(
        nearby_pollen=nearby_pollen,
        human=human,
        animal=animal,
        archaeology=archaeology,
        diversity=round(raw["evidence_family_count"] / 5.0, 4),
    )
    return LakeEvidenceBandScore(
        radius_km=radius_km,
        band_rank=0,
        total_score=total_score_policy(candidate, signals),
        nearby_pollen_lake_count=raw["nearby_pollen_lake_count"],
        time_aware_pollen_site_count=raw["time_aware_pollen_site_count"],
        human_overlap_pollen_site_count=raw["human_overlap_pollen_site_count"],
        human_adna_locality_count=raw["human_adna_locality_count"],
        human_adna_sample_count=raw["human_adna_sample_count"],
        domesticated_animal_locality_count=raw["domesticated_animal_locality_count"],
        domesticated_animal_sample_count=raw["domesticated_animal_sample_count"],
        sead_site_count=raw["sead_site_count"],
        time_aware_sead_site_count=raw["time_aware_sead_site_count"],
        human_overlap_sead_site_count=raw["human_overlap_sead_site_count"],
        raa_density_site_count=raw["raa_density_site_count"],
        evidence_family_count=raw["evidence_family_count"],
        nearby_pollen_signal=signals.nearby_pollen,
        human_signal=signals.human,
        animal_signal=signals.animal,
        archaeology_signal=signals.archaeology,
        diversity_signal=signals.diversity,
    )
