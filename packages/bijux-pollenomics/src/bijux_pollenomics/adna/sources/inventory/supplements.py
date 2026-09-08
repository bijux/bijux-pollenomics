"""Supplement acquisition, file-family, and recovery evidence."""

from __future__ import annotations

from pathlib import Path

from ..library.registries import build_paper_registry
from .model import SOURCE_INVENTORY_SCHEMA_VERSION, _count_by


def build_supplement_file_family_audit(output_root: Path) -> dict[str, object]:
    """Record the expected supplementary file families for each tracked paper."""
    rows: list[dict[str, object]] = []
    for row in build_paper_registry(output_root):
        rows.append(
            {
                "paper_doi": row.paper_doi,
                "project_accessions": list(row.project_accessions),
                "supplementary_verification_status": row.supplementary_verification_status,
                "repository_supplement_capture_status": row.supplementary_download_status,
                "supplement_parse_status": row.supplement_parse_status,
                "expected_supplementary_file_families": list(
                    row.expected_supplementary_file_families
                ),
                "expected_supplementary_artifacts": list(
                    row.expected_supplementary_artifacts
                ),
            }
        )
    return {
        "schema_version": SOURCE_INVENTORY_SCHEMA_VERSION,
        "row_count": len(rows),
        "rows": rows,
    }


def build_supplement_acquisition_checklist(output_root: Path) -> dict[str, object]:
    """Publish one paper-by-paper checklist for supplement verification and ingestion."""
    rows: list[dict[str, object]] = []
    for row in build_paper_registry(output_root):
        article_source_url = row.article_source_url
        rows.append(
            {
                "paper_doi": row.paper_doi,
                "project_accessions": list(row.project_accessions),
                "article_source_url": article_source_url,
                "publisher_page_url": article_source_url,
                "doi_landing_url": row.canonical_url,
                "crossref_url": f"https://api.crossref.org/works/{row.paper_doi}",
                "article_html_source_url": article_source_url
                if row.article_readability_status
                in {"readable_html", "blocked_landing_page_only"}
                else "",
                "pmc_or_pubmed_url": article_source_url
                if "pmc.ncbi.nlm.nih.gov" in article_source_url
                or "pubmed.ncbi.nlm.nih.gov" in article_source_url
                else "",
                "supplementary_verification_status": row.supplementary_verification_status,
                "repository_supplement_capture_status": row.supplementary_download_status,
                "supplement_parse_status": row.supplement_parse_status,
                "expected_supplementary_file_families": list(
                    row.expected_supplementary_file_families
                ),
                "local_reference_supplement_status": row.local_reference_supplement_status,
                "acquisition_check_status": (
                    "repo_archived"
                    if row.supplementary_download_status == "archived"
                    else (
                        "local_reference_ready_for_ingestion"
                        if row.local_reference_supplement_status
                        == "local_reference_staged"
                        else "still_missing_or_unverified"
                    )
                ),
            }
        )
    return {
        "schema_version": SOURCE_INVENTORY_SCHEMA_VERSION,
        "row_count": len(rows),
        "counts": _count_by(rows, "acquisition_check_status"),
        "rows": rows,
    }


def build_supplement_recovery_audit(output_root: Path) -> dict[str, object]:
    """Summarize whether each tracked paper has archived supplements, confirmed absence, or a remaining gap."""
    rows: list[dict[str, object]] = []
    for row in build_paper_registry(output_root):
        recovery_status = _supplement_recovery_status(row)
        rows.append(
            {
                "paper_doi": row.paper_doi,
                "project_accessions": list(row.project_accessions),
                "supplementary_verification_status": row.supplementary_verification_status,
                "repository_supplement_capture_status": row.supplementary_download_status,
                "supplement_parse_status": row.supplement_parse_status,
                "local_reference_supplement_status": row.local_reference_supplement_status,
                "supplementary_count": row.supplementary_count,
                "recovery_status": recovery_status,
            }
        )
    return {
        "schema_version": SOURCE_INVENTORY_SCHEMA_VERSION,
        "row_count": len(rows),
        "counts": _count_by(rows, "recovery_status"),
        "rows": rows,
    }


def _supplement_recovery_status(paper_row: object) -> str:
    verification_status = str(
        getattr(paper_row, "supplementary_verification_status", "")
    )
    repository_capture_status = str(
        getattr(paper_row, "supplementary_download_status", "")
    )
    local_reference_status = str(
        getattr(paper_row, "local_reference_supplement_status", "")
    )
    if repository_capture_status == "archived":
        return "archived_and_parseable"
    if verification_status == "supplement_confirmed_absent":
        return "confirmed_absent"
    if local_reference_status == "local_reference_staged":
        return "local_reference_staged_needs_repo_ingestion"
    return "not_found_yet"
