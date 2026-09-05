"""Project scope, evidence-matrix, and intake-dossier projections."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from ...workflow.paths import ADNA_SOURCE_LIBRARY_DIR
from ..library.registries import build_project_registry, build_project_source_bundles
from ..library.specifications import _doi_slug
from .model import (
    SOURCE_INVENTORY_SCHEMA_VERSION,
    _count_by,
    _project_table_status,
    _source_root,
)


def build_tracked_project_scope_audit(output_root: Path) -> dict[str, object]:
    """Re-audit tracked animal projects by scope fit and retention reason."""
    rows: list[dict[str, object]] = []
    for row in build_project_registry(output_root):
        if row.inventory_disposition == "retained_rejected_reference":
            scope_fit_status = "out_of_scope_reference"
            scope_note = (
                row.rejection_reason or "Retained with an explicit rejection reason."
            )
        elif "comparator" in row.evidence_strength:
            scope_fit_status = "context_only_comparator"
            scope_note = "Retained as contextual comparison rather than a direct sample-owned intake path."
        else:
            scope_fit_status = "core_sample_intake_candidate"
            scope_note = "Retained as a direct sample-intake candidate for the governed animal evidence database."
        rows.append(
            {
                "project_accession": row.project_accession,
                "species_latin_name": row.species_latin_name,
                "source_family": row.source_family,
                "archive_status": row.archive_status,
                "evidence_strength": row.evidence_strength,
                "inventory_disposition": row.inventory_disposition,
                "scope_fit_status": scope_fit_status,
                "scope_note": scope_note,
            }
        )
    counts = _count_by(rows, "scope_fit_status")
    return {
        "schema_version": SOURCE_INVENTORY_SCHEMA_VERSION,
        "tracked_project_count": len(rows),
        "counts": counts,
        "rows": rows,
    }


def build_project_source_evidence_matrix(output_root: Path) -> dict[str, object]:
    """Publish one honest matrix across archive metadata, paper capture, supplements, and extracted tables."""
    source_root = _source_root(output_root)
    bundles = {
        row.project_accession: row for row in build_project_source_bundles(output_root)
    }
    rows: list[dict[str, object]] = []
    for row in build_project_registry(output_root):
        bundle = bundles[row.project_accession]
        sample_master_status, sample_master_count = _project_table_status(
            source_root / "projects" / row.project_accession / "sample_master.json"
        )
        sample_site_status, sample_site_count = _project_table_status(
            source_root / "projects" / row.project_accession / "sample_sites.json"
        )
        sample_chronology_status, sample_chronology_count = _project_table_status(
            source_root / "projects" / row.project_accession / "sample_chronology.json"
        )
        rows.append(
            {
                "project_accession": row.project_accession,
                "species_latin_name": row.species_latin_name,
                "source_family": row.source_family,
                "paper_doi": row.primary_paper_doi or "",
                "archive_metadata_status": "archived",
                "repository_article_capture_status": row.paper_download_status,
                "repository_article_readability_status": row.article_readability_status,
                "repository_supplement_capture_status": row.supplement_download_status,
                "repository_supplement_parse_status": row.supplement_parse_status,
                "local_reference_article_status": row.local_reference_article_status,
                "local_reference_supplement_status": row.local_reference_supplement_status,
                "sample_table_extraction_status": row.sample_table_extraction_status,
                "sample_master_row_count": sample_master_count,
                "sample_site_table_status": sample_site_status,
                "sample_site_row_count": sample_site_count,
                "sample_chronology_table_status": sample_chronology_status,
                "sample_chronology_row_count": sample_chronology_count,
                "evidence_acquisition_state": row.evidence_acquisition_state,
                "blockers": list(bundle.blockers),
            }
        )
    return {
        "schema_version": SOURCE_INVENTORY_SCHEMA_VERSION,
        "row_count": len(rows),
        "counts": {
            "repository_supplement_captured": sum(
                1
                for row in rows
                if row["repository_supplement_capture_status"] == "archived"
            ),
            "local_reference_supplement_staged": sum(
                1
                for row in rows
                if row["local_reference_supplement_status"] == "local_reference_staged"
            ),
            "sample_master_published": sum(
                1
                for row in rows
                if row["sample_table_extraction_status"]
                == "project_sample_master_published"
            ),
            "sample_site_published": sum(
                1 for row in rows if row["sample_site_table_status"] == "published"
            ),
            "sample_chronology_published": sum(
                1
                for row in rows
                if row["sample_chronology_table_status"] == "published"
            ),
        },
        "rows": rows,
    }


def build_cross_project_source_intake_dossier(output_root: Path) -> dict[str, object]:
    """Describe what each tracked paper or supplement is expected to contribute across the program."""
    matrix_rows = cast(
        list[dict[str, object]],
        build_project_source_evidence_matrix(output_root)["rows"],
    )
    matrix = {row["project_accession"]: row for row in matrix_rows}
    rows: list[dict[str, object]] = []
    for row in build_project_registry(output_root):
        evidence_row = matrix[row.project_accession]
        expected_contributions = []
        if row.sample_identifier_status != "missing_primary_paper_linkage":
            expected_contributions.append("sample_identifiers")
        if row.primary_paper_doi:
            expected_contributions.append("taxonomic_context")
        if (
            row.primary_paper_doi
            and evidence_row["sample_site_table_status"] != "published"
        ):
            expected_contributions.append("site_names")
            expected_contributions.append("coordinate_resolution_candidate")
        if (
            row.primary_paper_doi
            and evidence_row["sample_chronology_table_status"] != "published"
        ):
            expected_contributions.append("chronology")
        rows.append(
            {
                "project_accession": row.project_accession,
                "species_latin_name": row.species_latin_name,
                "paper_doi": row.primary_paper_doi or "",
                "inventory_disposition": row.inventory_disposition,
                "evidence_acquisition_state": row.evidence_acquisition_state,
                "expected_contributions": expected_contributions,
                "expected_sample_count_status": row.expected_sample_count_status,
                "sample_identifier_status": row.sample_identifier_status,
                "current_anchor_files": _current_anchor_files(
                    row.project_accession, row.primary_paper_doi or ""
                ),
            }
        )
    return {
        "schema_version": SOURCE_INVENTORY_SCHEMA_VERSION,
        "row_count": len(rows),
        "counts": {
            "projects_with_site_expectation": sum(
                1
                for row in rows
                if "site_names" in cast(list[str], row["expected_contributions"])
            ),
            "projects_with_chronology_expectation": sum(
                1
                for row in rows
                if "chronology" in cast(list[str], row["expected_contributions"])
            ),
            "projects_with_identifier_expectation": sum(
                1
                for row in rows
                if "sample_identifiers"
                in cast(list[str], row["expected_contributions"])
            ),
        },
        "rows": rows,
    }


def _current_anchor_files(project_accession: str, paper_doi: str) -> list[str]:
    anchors = [
        f"{ADNA_SOURCE_LIBRARY_DIR}/projects/{project_accession}/bundle_manifest.json",
        f"{ADNA_SOURCE_LIBRARY_DIR}/projects/{project_accession}/intake_dossier.json",
    ]
    if paper_doi:
        anchors.append(
            f"{ADNA_SOURCE_LIBRARY_DIR}/papers/{_doi_slug(paper_doi)}/supplementary_manifest.json"
        )
    return anchors
