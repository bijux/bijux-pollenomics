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
