"""Pollen-derived candidate report construction."""

from __future__ import annotations

from ..candidates import _derive_lake_candidates
from ..methodology import _build_empty_report, _build_methodology
from ..models import LakeEvidenceRichnessReport, _AGGREGATE_RADIUS_WEIGHTS
from ..temporal import _attach_temporal_context
from .context import _ReportContext
from .policies import (
    _pollen_aggregate_tiebreaker,
    _pollen_band_tiebreaker,
    _pollen_total_score,
)
from .ranking import _build_candidate_score_rows, _rank_candidate_score_rows

__all__: list[str] = []


def _build_pollen_candidate_report(
    *, radii_km: tuple[int, ...], context: _ReportContext
) -> LakeEvidenceRichnessReport:
    candidates = _derive_lake_candidates(
        context.pollen_points,
        neotoma_position_notes=context.neotoma_position_notes,
    )
    candidates = _attach_temporal_context(
        candidates,
        pollen_points=context.pollen_points,
        human_points=context.human_points,
        animal_points=context.animal_points,
        sead_points=context.sead_points,
    )
    if not candidates:
        return _build_empty_report(
            radii_km,
            candidate_source="pollen_candidate_points",
            source_temporal_coverage=context.source_temporal_coverage,
            raa_authority=context.raa_authority,
        )
    rows = _build_candidate_score_rows(
        candidates=candidates,
        radii_km=radii_km,
        human_points=context.human_points,
        animal_points=context.animal_points,
        sead_points=context.sead_points,
        raa_cells=context.raa_cells,
        aggregate_radius_weights=_AGGREGATE_RADIUS_WEIGHTS,
        total_score_policy=_pollen_total_score,
    )
    assessments = _rank_candidate_score_rows(
        rows,
        radii_km=radii_km,
        band_tiebreaker=_pollen_band_tiebreaker,
        aggregate_tiebreaker=_pollen_aggregate_tiebreaker,
    )
    return LakeEvidenceRichnessReport(
        schema_version="sweden-lake-evidence-richness.v2",
        country="Sweden",
        radii_km=radii_km,
        candidate_count=len(assessments),
        methodology=_build_methodology(
            radii_km,
            source_temporal_coverage=context.source_temporal_coverage,
            candidates=candidates,
            raa_authority=context.raa_authority,
        ),
        assessments=assessments,
    )
