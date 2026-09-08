from __future__ import annotations

from bijux_pollenomics.analysis.fieldwork.evidence_richness import candidates
from bijux_pollenomics.analysis.fieldwork.evidence_richness.candidates.matching import (
    _build_lake_components,
)
from bijux_pollenomics.analysis.fieldwork.evidence_richness.candidates.naming import (
    _lake_name_key,
)
from bijux_pollenomics.analysis.fieldwork.evidence_richness.candidates.pollen import (
    _derive_lake_candidates,
)
from bijux_pollenomics.analysis.fieldwork.evidence_richness.candidates.registry import (
    _derive_svar_lake_candidates,
)
from bijux_pollenomics.analysis.fieldwork.evidence_richness.candidates.sampling import (
    _classify_sampling_lake,
)
from bijux_pollenomics.analysis.fieldwork.evidence_richness.candidates.uncertainty import (
    _build_ambiguity_note,
)


def test_compatibility_facade_reexports_owned_candidate_operations() -> None:
    assert candidates.__all__ == []
    assert candidates._derive_lake_candidates is _derive_lake_candidates
    assert candidates._derive_svar_lake_candidates is _derive_svar_lake_candidates
    assert candidates._build_lake_components is _build_lake_components
    assert candidates._lake_name_key is _lake_name_key
    assert candidates._classify_sampling_lake is _classify_sampling_lake
    assert candidates._build_ambiguity_note is _build_ambiguity_note
