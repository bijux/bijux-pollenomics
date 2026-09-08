"""SVAR-authoritative candidate report construction."""

from __future__ import annotations

from pathlib import Path

from ..candidates import _derive_svar_lake_candidates
from ..inputs import _load_sweden_svar_lakes
from ..methodology import _build_empty_report, _build_methodology
from ..models import _SVAR_AGGREGATE_RADIUS_WEIGHTS, LakeEvidenceRichnessReport
from ..temporal import _attach_temporal_context
from .context import _ReportContext
from .policies import (
    _svar_aggregate_tiebreaker,
    _svar_band_tiebreaker,
    _svar_total_score,
)
from .ranking import _build_candidate_score_rows, _rank_candidate_score_rows

__all__: list[str] = []


def _build_svar_lake_report(
    *,
    radii_km: tuple[int, ...],
    svar_lake_path: Path,
    context: _ReportContext,
) -> LakeEvidenceRichnessReport:
    svar_lakes = _load_sweden_svar_lakes(svar_lake_path)
    if not svar_lakes or not context.human_points:
        return _build_empty_report(
            radii_km,
            candidate_source="svar_lake_registry",
            source_temporal_coverage=context.source_temporal_coverage,
        )
    candidates = _derive_svar_lake_candidates(
        svar_lakes,
        pollen_points=context.pollen_points,
        neotoma_position_notes=context.neotoma_position_notes,
        human_points=context.human_points,
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
            candidate_source="svar_lake_registry",
            source_temporal_coverage=context.source_temporal_coverage,
        )
    rows = _build_candidate_score_rows(
        candidates=candidates,
        radii_km=radii_km,
        human_points=context.human_points,
        animal_points=context.animal_points,
        sead_points=context.sead_points,
        raa_cells=context.raa_cells,
        aggregate_radius_weights=_SVAR_AGGREGATE_RADIUS_WEIGHTS,
        total_score_policy=_svar_total_score,
        pollen_points=context.pollen_points,
    )
    assessments = _rank_candidate_score_rows(
        rows,
        radii_km=radii_km,
        band_tiebreaker=_svar_band_tiebreaker,
        aggregate_tiebreaker=_svar_aggregate_tiebreaker,
    )
    return LakeEvidenceRichnessReport(
        schema_version="sweden-lake-evidence-richness.v2",
        country="Sweden",
        radii_km=radii_km,
        candidate_count=len(assessments),
        methodology=_build_methodology(
            radii_km,
            candidate_source="svar_lake_registry",
            source_temporal_coverage=context.source_temporal_coverage,
            candidates=candidates,
            raa_authority=context.raa_authority,
        ),
        assessments=assessments,
    )
