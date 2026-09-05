"""Evidence-stage blocker classification for tracked source projects."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from ..library.registries import build_project_registry
from .model import SOURCE_INVENTORY_SCHEMA_VERSION, _count_by
from .project_evidence import build_project_source_evidence_matrix


def build_source_blocker_review(output_root: Path) -> dict[str, object]:
    """Explain the real missing evidence stage for each blocked project."""
    matrix_rows = cast(
        list[dict[str, object]],
        build_project_source_evidence_matrix(output_root)["rows"],
    )
    matrix = {row["project_accession"]: row for row in matrix_rows}
    rows: list[dict[str, object]] = []
    for row in build_project_registry(output_root):
        matrix_row = matrix[row.project_accession]
        stage = _blocking_stage(matrix_row)
        if stage == "ready_for_downstream_work":
            continue
        rows.append(
            {
                "project_accession": row.project_accession,
                "species_latin_name": row.species_latin_name,
                "paper_doi": row.primary_paper_doi or "",
                "blocking_stage": stage,
                "evidence_acquisition_state": row.evidence_acquisition_state,
                "required_evidence": _required_evidence(stage),
                "explanation": _blocking_explanation(stage, matrix_row),
            }
        )
    return {
        "schema_version": SOURCE_INVENTORY_SCHEMA_VERSION,
        "row_count": len(rows),
        "counts": _count_by(rows, "blocking_stage"),
        "rows": rows,
    }


def _blocking_stage(matrix_row: dict[str, object]) -> str:
    state = str(matrix_row["evidence_acquisition_state"])
    if state == "scope_rejected":
        return "scope_filter"
    if state in {
        "missing_capture",
        "paper_capture_partial",
        "paper_linkage_not_curated",
    }:
        return "paper_capture"
    if state in {
        "local_supplement_staged_needs_repo_ingestion",
        "repository_supplement_captured_needs_extraction",
    }:
        return "supplement_ingestion_or_parsing"
    if (
        matrix_row["sample_table_extraction_status"]
        != "project_sample_master_published"
    ):
        return "sample_identity_extraction"
    if matrix_row["sample_site_table_status"] != "published":
        return "site_extraction"
    if matrix_row["sample_chronology_table_status"] != "published":
        return "chronology_extraction"
    return "ready_for_downstream_work"


def _required_evidence(stage: str) -> list[str]:
    return {
        "scope_filter": ["explicit_rejection_reason"],
        "paper_capture": ["archived_article_surface", "stable_doi_linkage"],
        "supplement_ingestion_or_parsing": [
            "repo_supplement_copy",
            "structured_table_inventory",
        ],
        "sample_identity_extraction": ["project_sample_master"],
        "site_extraction": ["project_sample_sites"],
        "chronology_extraction": ["project_sample_chronology"],
    }.get(stage, [])


def _blocking_explanation(stage: str, matrix_row: dict[str, object]) -> str:
    if stage == "paper_capture":
        return "The tracked project still lacks a reliable readable paper surface inside the repository."
    if stage == "supplement_ingestion_or_parsing":
        return "Supplementary evidence exists or is expected, but the repository still needs a governed copy or a structured table inventory."
    if stage == "sample_identity_extraction":
        return "Sample identities are not yet published as a governed project sample master."
    if stage == "site_extraction":
        return "Sample identities exist, but exact locality extraction is not yet published."
    if stage == "chronology_extraction":
        return "Locality evidence exists, but the project chronology table is still missing."
    return "The project is retained only as an explicit out-of-scope or comparator reference."
