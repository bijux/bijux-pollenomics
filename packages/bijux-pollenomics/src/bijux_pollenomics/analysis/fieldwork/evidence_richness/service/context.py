"""Source loading and authority context for evidence-richness reports."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.collection.sources.raa import assess_raa_density_authority

from ..inputs import (
    _load_sweden_context_points,
    _load_sweden_density_cells,
    _load_sweden_neotoma_position_notes,
    _load_sweden_pollen_points,
)
from ..methodology import _build_context_temporal_coverage_summary
from ..models import _DensityCell, _PointEvidence
from ..temporal import _extract_animal_points, _extract_human_points

__all__: list[str] = []


@dataclass(frozen=True)
class _ReportContext:
    pollen_points: tuple[ContextPointRecord, ...]
    neotoma_position_notes: dict[str, str]
    human_points: tuple[_PointEvidence, ...]
    animal_points: tuple[_PointEvidence, ...]
    sead_points: tuple[ContextPointRecord, ...]
    raa_cells: tuple[_DensityCell, ...]
    raa_authority: dict[str, object]
    source_temporal_coverage: dict[str, object]


def _load_report_context(
    *,
    context_root: Path,
    human_localities: Iterable[object],
    animal_localities: Iterable[dict[str, object]],
) -> _ReportContext:
    pollen_points = _load_sweden_pollen_points(context_root)
    sead_points = _load_sweden_context_points(
        context_root / "sead" / "normalized" / "nordic_environmental_sites.geojson",
        country="Sweden",
    )
    source_temporal_coverage = _build_context_temporal_coverage_summary(
        pollen_points,
        context_root=context_root,
        sead_points=sead_points,
    )
    raa_authority = assess_raa_density_authority(context_root)
    raa_cells = (
        _load_sweden_density_cells(
            context_root / "raa" / "normalized" / "sweden_archaeology_density.geojson"
        )
        if raa_authority.admitted
        else ()
    )
    return _ReportContext(
        pollen_points=pollen_points,
        neotoma_position_notes=_load_sweden_neotoma_position_notes(context_root),
        human_points=_extract_human_points(human_localities),
        animal_points=_extract_animal_points(animal_localities),
        sead_points=sead_points,
        raa_cells=raa_cells,
        raa_authority={
            "admitted": raa_authority.admitted,
            "reason_codes": list(raa_authority.reason_codes),
            "archived_feature_count": raa_authority.archived_feature_count,
            "heritage_site_count": raa_authority.heritage_site_count,
            "density_site_count": raa_authority.density_site_count,
            "density_feature_count": raa_authority.density_feature_count,
            "reviewer_id": raa_authority.reviewer_id,
        },
        source_temporal_coverage=source_temporal_coverage,
    )
