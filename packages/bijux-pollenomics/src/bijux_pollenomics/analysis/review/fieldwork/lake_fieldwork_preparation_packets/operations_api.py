"""Compatibility operations routed through the package surface."""

from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from bijux_pollenomics.analysis.fieldwork.evidence_richness import (
    LakeEvidenceRichnessAssessment,
    LakeEvidenceRichnessReport,
)


def _surface() -> ModuleType:
    return importlib.import_module(__package__ or "")


def build_lake_fieldwork_preparation_payload(
    report: LakeEvidenceRichnessReport,
    *,
    top_n: int = 20,
) -> dict[str, Any]:
    """Build a refusal-prone Sweden lake fieldwork-preparation packet."""
    surface = _surface()
    return cast(
        dict[str, Any],
        surface.build_payload(
            report,
            top_n=top_n,
            select_rows=surface.fieldwork_rows,
            build_row=surface._build_fieldwork_preparation_row,
        ),
    )


def write_lake_fieldwork_preparation_json(
    path: Path,
    report: LakeEvidenceRichnessReport,
    *,
    top_n: int = 20,
) -> None:
    """Write one JSON payload for Sweden lake fieldwork preparation."""
    surface = _surface()
    surface.write_json(
        path,
        report,
        top_n=top_n,
        build_payload=surface.build_lake_fieldwork_preparation_payload,
        json_module=surface.json,
    )


def write_lake_fieldwork_preparation_csv(
    path: Path,
    report: LakeEvidenceRichnessReport,
    *,
    top_n: int = 20,
) -> None:
    """Write one CSV row per reviewed Sweden lake candidate."""
    surface = _surface()
    surface.write_csv(
        path,
        report,
        top_n=top_n,
        build_payload=surface.build_lake_fieldwork_preparation_payload,
        csv_module=surface.csv,
    )


def render_lake_fieldwork_preparation_markdown(
    payload: dict[str, Any],
) -> str:
    """Render the Sweden lake fieldwork-preparation packet as markdown."""
    return str(_surface().render_markdown(payload))


def render_lake_fieldwork_preparation_section(
    *,
    json_name: str,
    csv_name: str,
    markdown_name: str,
) -> str:
    """Render the README section that links the fieldwork-preparation outputs."""
    return str(
        _surface().render_section(
            json_name=json_name,
            csv_name=csv_name,
            markdown_name=markdown_name,
        )
    )


def _build_fieldwork_preparation_row(
    assessment: LakeEvidenceRichnessAssessment,
    *,
    fieldwork_rank: int,
) -> dict[str, object]:
    surface = _surface()
    return cast(
        dict[str, object],
        surface.build_candidate_row(
            assessment,
            fieldwork_rank=fieldwork_rank,
            band_score=surface.band_score,
            shortlist_score=surface.fieldwork_shortlist_score,
            human_posture=surface.human_context_posture,
            identity_posture=surface._identity_posture,
            top20_presence_count=surface._scenario_top20_presence_count,
            consistency_posture=surface._scenario_consistency_posture,
            sead_posture=surface._sead_context_posture,
            palaeopen_posture=surface._palaeopen_alignment_posture,
            preparation_posture=surface._preparation_posture,
            required_actions=surface._required_actions,
            maps_url=surface._google_maps_url,
            mean_value=surface.mean,
        ),
    )


def _identity_posture(ambiguity_flags: tuple[str, ...]) -> str:
    return str(_surface().identity_posture(ambiguity_flags))


def _sead_context_posture(sead_site_count: int) -> str:
    return str(_surface().sead_context_posture(sead_site_count))


def _palaeopen_alignment_posture(
    *,
    direct_pollen_source_count: int,
    evidence_family_count: int,
) -> str:
    return str(
        _surface().palaeopen_alignment_posture(
            direct_pollen_source_count=direct_pollen_source_count,
            evidence_family_count=evidence_family_count,
        )
    )


def _preparation_posture(
    *,
    ambiguity_flags: tuple[str, ...],
    sampling_posture: str,
    sampling_fit: float,
    human_context_posture: str,
    direct_pollen_source_count: int,
    evidence_family_count: int,
    sead_site_count: int,
    human_locality_count: int,
    scenario_consistency_posture: str,
) -> str:
    return str(
        _surface().preparation_posture(
            ambiguity_flags=ambiguity_flags,
            sampling_posture=sampling_posture,
            sampling_fit=sampling_fit,
            human_context_posture=human_context_posture,
            direct_pollen_source_count=direct_pollen_source_count,
            evidence_family_count=evidence_family_count,
            sead_site_count=sead_site_count,
            human_locality_count=human_locality_count,
            scenario_consistency_posture=scenario_consistency_posture,
        )
    )


def _required_actions(
    *,
    ambiguity_flags: tuple[str, ...],
    sampling_posture: str,
    human_context_posture: str,
    scenario_consistency_posture: str,
    sead_context_posture: str,
    palaeopen_alignment_posture: str,
    preparation_posture: str,
) -> list[str]:
    return cast(
        list[str],
        _surface().required_actions(
            ambiguity_flags=ambiguity_flags,
            sampling_posture=sampling_posture,
            human_context_posture=human_context_posture,
            scenario_consistency_posture=scenario_consistency_posture,
            sead_context_posture=sead_context_posture,
            palaeopen_alignment_posture=palaeopen_alignment_posture,
            preparation_posture=preparation_posture,
        ),
    )


def _scenario_top20_presence_count(
    *,
    aggregate_rank: int,
    scenario_ranks: dict[str, int],
) -> int:
    return int(
        _surface().scenario_top20_presence_count(
            aggregate_rank=aggregate_rank,
            scenario_ranks=scenario_ranks,
        )
    )


def _scenario_consistency_posture(top20_presence_count: int) -> str:
    return str(_surface().scenario_consistency_posture(top20_presence_count))


def _google_maps_url(latitude: float, longitude: float) -> str:
    return str(_surface().google_maps_url(latitude, longitude))
