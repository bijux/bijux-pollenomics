"""Scientific progress measures grounded in evidence depth."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict, cast

from .core_counts import _build_source_assessment_counts as _build_core_counts

__all__ = [
    "build_repository_scientific_progress_audit",
    "render_repository_scientific_progress_audit_markdown",
]

_ScientificProgressPayload = TypedDict(
    "_ScientificProgressPayload",
    {
        "overall_progress_posture": str,
        "progress_measures": list[str],
        "anti_measures": list[str],
        "findings": list[str],
    },
)


def build_repository_scientific_progress_audit(
    *,
    data_root: Path,
    docs_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Describe progress using evidence depth instead of artifact count."""
    counts = _build_core_counts(data_root, docs_root, report_root)
    zero_collection_surfaces = counts["zero_collection_summary_surfaces"]
    return {
        "schema_version": "repository-scientific-progress-audit.v1",
        "overall_progress_posture": "data_recovery_required",
        "progress_measures": [
            "paper-by-paper supplement coverage",
            "sample-owned locality and chronology support depth",
            "mappable animal rows with traceable site and coordinate evidence",
            "non-aDNA source-family explanation breadth",
        ],
        "anti_measures": [
            "checked-in JSON file count",
            "country bundle count without sample-depth context",
            "atlas bundle existence without mapped evidence depth",
        ],
        "findings": [
            (
                f"all {counts['tracked_paper_count']} tracked papers now ship archived supplementary material, but sample-owned extraction still lags behind supplement recovery"
                if counts["papers_with_archived_supplements"]
                >= counts["tracked_paper_count"]
                else f"only {counts['papers_with_archived_supplements']} of {counts['tracked_paper_count']} tracked papers currently ship archived supplementary material"
            ),
            (
                f"the shipped animal atlas exposes {counts['published_atlas_point_count']} published animal point rows"
                if counts["animal_sample_database_review_available"]
                else "animal sample publication accounting is unavailable"
            ),
            (
                f"{counts['animal_unresolved_sample_count']} unresolved animal samples are a subset of {counts['animal_blocked_sample_count']} blocked samples among {counts['animal_tracked_sample_count']} tracked samples; {counts['animal_coordinate_refused_provenance_count']} of {counts['animal_coordinate_provenance_count']} coordinate-provenance rows are refused from mapping"
                if counts["animal_sample_database_review_available"]
                and counts["animal_map_readiness_available"]
                else "animal sample and coordinate-provenance deficits cannot be quantified until both accounting surfaces are available"
            ),
            (
                "collection_summary still reports zero counts for "
                + ", ".join(zero_collection_surfaces)
                if zero_collection_surfaces
                else "collection_summary keeps non-aDNA counts visible"
            ),
        ],
    }


def render_repository_scientific_progress_audit_markdown(
    payload: dict[str, object],
) -> str:
    audit = cast(_ScientificProgressPayload, payload)
    lines = [
        "# Repository scientific progress audit",
        "",
        f"- Overall progress posture: `{audit['overall_progress_posture']}`",
        "",
        "## Use These Measures",
        "",
    ]
    for row in audit["progress_measures"]:
        lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Do Not Use These As Progress",
            "",
        ]
    )
    for row in audit["anti_measures"]:
        lines.append(f"- {row}")
    lines.extend(
        [
            "",
            "## Current Findings",
            "",
        ]
    )
    for row in audit["findings"]:
        lines.append(f"- {row}")
    return "\n".join(lines) + "\n"
