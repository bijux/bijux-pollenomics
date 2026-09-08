"""Authority selection and orchestration for Sweden lake reports."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path

from ..methodology import _build_empty_report
from ..models import DEFAULT_LAKE_EVIDENCE_RADII_KM, LakeEvidenceRichnessReport
from .context import _load_report_context
from .pollen_report import _build_pollen_candidate_report
from .svar_report import _build_svar_lake_report

__all__: list[str] = []


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
    root = Path(context_root)
    context = _load_report_context(
        context_root=root,
        human_localities=human_localities,
        animal_localities=animal_localities,
    )
    svar_candidate_path = (
        root / "svar" / "review" / "sweden_lake_candidate_registry.geojson"
    )
    svar_registry_path = root / "svar" / "normalized" / "sweden_lake_registry.geojson"
    if svar_candidate_path.exists() and not svar_registry_path.exists():
        return _build_empty_report(
            normalized_radii,
            candidate_source="svar_registry_authority_unavailable",
            source_temporal_coverage=context.source_temporal_coverage,
            raa_authority=context.raa_authority,
        )
    if svar_registry_path.exists():
        return _build_svar_lake_report(
            radii_km=normalized_radii,
            svar_lake_path=svar_registry_path,
            context=context,
        )
    return _build_pollen_candidate_report(radii_km=normalized_radii, context=context)
