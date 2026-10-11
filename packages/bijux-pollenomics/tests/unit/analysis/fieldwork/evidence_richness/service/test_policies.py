from __future__ import annotations

from types import SimpleNamespace
from typing import cast

from bijux_pollenomics.analysis.fieldwork.evidence_richness.models import (
    LakeEvidenceCandidate,
)
from bijux_pollenomics.analysis.fieldwork.evidence_richness.service.policies import (
    _pollen_total_score,
    _svar_total_score,
)
from bijux_pollenomics.analysis.fieldwork.evidence_richness.service.signals import (
    _BandSignals,
    _build_band_score,
)


def test_candidate_authorities_retain_distinct_score_weights() -> None:
    candidate = cast(
        LakeEvidenceCandidate,
        SimpleNamespace(
            direct_pollen_signal=0.9,
            direct_pollen_source_count=3,
            lake_sampling_fit=0.8,
        ),
    )
    signals = _BandSignals(
        nearby_pollen=0.4,
        human=0.5,
        animal=0.6,
        archaeology=0.7,
        diversity=0.8,
    )

    assert _pollen_total_score(candidate, signals) == 0.665
    assert _svar_total_score(candidate, signals) == 0.5989


def test_refused_raa_is_missing_but_admitted_zero_is_observed() -> None:
    candidate = cast(LakeEvidenceCandidate, SimpleNamespace())
    raw = {
        "nearby_pollen_lake_count": 0,
        "time_aware_pollen_site_count": 0,
        "human_overlap_pollen_site_count": 0,
        "human_adna_locality_count": 0,
        "human_adna_sample_count": 0,
        "domesticated_animal_locality_count": 0,
        "domesticated_animal_sample_count": 0,
        "sead_site_count": 1,
        "time_aware_sead_site_count": 1,
        "human_overlap_sead_site_count": 1,
        "raa_density_site_count": 0,
        "evidence_family_count": 1,
    }
    maxima = {key: max(value, 1) for key, value in raw.items()}
    refused = _build_band_score(
        candidate=candidate,
        radius_km=10,
        raw=raw,
        maxima=maxima,
        raa_density_admitted=False,
        total_score_policy=lambda _candidate, signals: signals.archaeology,
    )
    admitted_zero = _build_band_score(
        candidate=candidate,
        radius_km=10,
        raw=raw,
        maxima=maxima,
        raa_density_admitted=True,
        total_score_policy=lambda _candidate, signals: signals.archaeology,
    )
    assert refused.archaeology_signal == refused.total_score == 1.0
    assert admitted_zero.archaeology_signal == admitted_zero.total_score == 0.8
    assert refused.raa_density_site_count is None
    assert admitted_zero.raa_density_site_count == 0
    assert refused.as_dict()["raa_density_site_count"] is None
    assert admitted_zero.as_dict()["raa_density_site_count"] == 0
