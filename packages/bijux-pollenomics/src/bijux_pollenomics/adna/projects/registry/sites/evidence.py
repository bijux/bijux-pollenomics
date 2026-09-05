"""Evidence classification and review policy for sample-site rows."""

from __future__ import annotations

from typing import Any, cast

from .records import ADNA_LOCALITY_RESOLUTION_STATUSES, AdnaProjectSampleSiteRow


def _artifact_kind_from_path(path: str) -> str:
    if "#Supplementary_Data_" in path:
        return "supplementary_spreadsheet_row"
    if path.endswith(".xlsx"):
        return "supplementary_spreadsheet_row"
    if path.endswith(".pdf"):
        return "supplementary_pdf_text"
    if path.endswith(".html"):
        return "article_or_archive_text"
    return "tracked_source_artifact"


def _project_level_locality_status(provenance_row: object | None) -> str:
    if provenance_row is None:
        return "unresolved"
    provenance = cast(Any, provenance_row)
    if provenance.mapping_posture == "refused_region_only":
        return "region_only"
    if provenance.coordinate_basis == "named_site_geocoding":
        return "named_place_inferred"
    return "project_level_site_only"


def _review_note_for(*, status: str, site_row: object | None) -> str:
    if status == "project_level_site_only":
        return "Current evidence names only a project-level locality context, not a sample-owned site row."
    if status == "named_place_inferred":
        return "Current evidence names a place that can be resolved, but the mapped point still depends on place-name inference."
    if status == "region_only":
        return "Current evidence stays at region or transect scale and must not masquerade as exact sample-site truth."
    if site_row is None:
        return (
            "No location evidence has been extracted yet for this recovered sample row."
        )
    return "Recovered sample row still lacks a defensible sample-owned site assignment."


def _counts_by_status(rows: tuple[AdnaProjectSampleSiteRow, ...]) -> dict[str, int]:
    counts = dict.fromkeys(ADNA_LOCALITY_RESOLUTION_STATUSES, 0)
    for row in rows:
        counts[row.locality_resolution_status] += 1
    return counts
