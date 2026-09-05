from __future__ import annotations

from bijux_pollenomics.analysis import (
    build_sweden_lake_evidence_richness_report as analysis_entry_point,
)
from bijux_pollenomics.analysis.fieldwork.evidence_richness import (
    build_sweden_lake_evidence_richness_report as domain_entry_point,
)
from bijux_pollenomics.analysis.fieldwork.evidence_richness import service
from bijux_pollenomics.analysis.fieldwork.evidence_richness.service.orchestration import (
    build_sweden_lake_evidence_richness_report as orchestration_entry_point,
)


def test_public_entry_points_reexport_the_owned_orchestrator() -> None:
    assert service.__all__ == ["build_sweden_lake_evidence_richness_report"]
    assert (
        service.build_sweden_lake_evidence_richness_report is orchestration_entry_point
    )
    assert domain_entry_point is orchestration_entry_point
    assert analysis_entry_point is orchestration_entry_point
