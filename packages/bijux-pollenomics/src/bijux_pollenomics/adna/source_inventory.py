from __future__ import annotations

import json
from pathlib import Path

from ..core.files import write_json, write_text
from .paths import ADNA_SOURCE_LIBRARY_DIR
from .source_library import (
    _doi_slug,
    _reference_stash_records,
    _resolve_reference_stash_root,
    build_paper_registry,
    build_project_registry,
    build_project_source_bundles,
)
from .source_recovery import (
    build_manual_curation_worklist,
    build_missing_source_queue,
    build_paper_expected_sample_yield_review,
    build_project_expected_sample_yield_review,
    build_project_recovery_stage_review,
    build_source_recovery_progress,
    build_source_recovery_release_guard,
    build_species_project_deficit_ledger,
    render_manual_curation_worklist_markdown,
    render_missing_source_queue_markdown,
    render_paper_expected_sample_yield_review_markdown,
    render_project_expected_sample_yield_review_markdown,
    render_project_recovery_stage_review_markdown,
    render_source_recovery_progress_markdown,
    render_source_recovery_release_guard_markdown,
    render_species_project_deficit_ledger_markdown,
)

__all__ = [
    "build_cross_project_source_intake_dossier",
    "build_project_source_evidence_matrix",
    "build_reference_stash_doi_integrity_audit",
    "build_reference_stash_reconciliation",
    "build_supplement_acquisition_checklist",
    "build_supplement_file_family_audit",
    "build_supplement_recovery_audit",
    "build_source_blocker_review",
    "build_tracked_project_scope_audit",
    "materialize_source_inventory",
]

SOURCE_INVENTORY_SCHEMA_VERSION = "adna-source-inventory.v1"


def materialize_source_inventory(output_root: Path) -> None:
    """Write the richer source-inventory surfaces beside the core source-library registries."""
    output_root = Path(output_root)
    source_root = output_root / "adna" / "governance" / "source_library"
    source_root.mkdir(parents=True, exist_ok=True)

    payloads = {
        "tracked_project_scope_audit": (
            build_tracked_project_scope_audit(output_root),
            render_tracked_project_scope_audit_markdown,
        ),
        "project_source_evidence_matrix": (
            build_project_source_evidence_matrix(output_root),
            render_project_source_evidence_matrix_markdown,
        ),
        "reference_stash_reconciliation": (
            build_reference_stash_reconciliation(output_root),
            render_reference_stash_reconciliation_markdown,
        ),
        "reference_stash_doi_integrity_audit": (
            build_reference_stash_doi_integrity_audit(output_root),
            render_reference_stash_doi_integrity_markdown,
        ),
        "supplement_file_family_audit": (
            build_supplement_file_family_audit(output_root),
            render_supplement_file_family_audit_markdown,
        ),
        "supplement_acquisition_checklist": (
            build_supplement_acquisition_checklist(output_root),
            render_supplement_acquisition_checklist_markdown,
        ),
        "supplement_recovery_audit": (
            build_supplement_recovery_audit(output_root),
            render_supplement_recovery_audit_markdown,
        ),
        "source_blocker_review": (
            build_source_blocker_review(output_root),
            render_source_blocker_review_markdown,
        ),
        "cross_project_source_intake_dossier": (
            build_cross_project_source_intake_dossier(output_root),
            render_cross_project_source_intake_dossier_markdown,
        ),
        "project_recovery_stage_review": (
            build_project_recovery_stage_review(output_root),
            render_project_recovery_stage_review_markdown,
        ),
        "project_expected_sample_yield_review": (
            build_project_expected_sample_yield_review(output_root),
            render_project_expected_sample_yield_review_markdown,
        ),
        "paper_expected_sample_yield_review": (
            build_paper_expected_sample_yield_review(output_root),
            render_paper_expected_sample_yield_review_markdown,
        ),
        "species_project_deficit_ledger": (
            build_species_project_deficit_ledger(output_root),
            render_species_project_deficit_ledger_markdown,
        ),
        "manual_curation_worklist": (
            build_manual_curation_worklist(output_root),
            render_manual_curation_worklist_markdown,
        ),
        "source_recovery_progress": (
            build_source_recovery_progress(output_root),
            render_source_recovery_progress_markdown,
        ),
        "missing_source_queue": (
            build_missing_source_queue(output_root),
            render_missing_source_queue_markdown,
        ),
        "source_recovery_release_guard": (
            build_source_recovery_release_guard(output_root),
            render_source_recovery_release_guard_markdown,
        ),
    }
    for stem, (payload, renderer) in payloads.items():
        write_json(source_root / f"{stem}.json", payload)
        write_text(source_root / f"{stem}.md", renderer(payload))


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


def build_reference_stash_reconciliation(output_root: Path) -> dict[str, object]:
    """Compare tracked repo capture against the local reference stash without overstating repo completeness."""
    paper_rows = {row.paper_doi: row for row in build_paper_registry(output_root)}
    stash_records = _reference_stash_records(output_root)
    rows: list[dict[str, object]] = []
    all_slugs = sorted({_doi_slug(doi) for doi in paper_rows} | set(stash_records))
    for slug in all_slugs:
        paper_row = next(
            (row for doi, row in paper_rows.items() if _doi_slug(doi) == slug),
            None,
        )
        stash_record = stash_records.get(slug, {})
        rows.append(
            {
                "stash_slug": slug,
                "paper_doi": "" if paper_row is None else paper_row.paper_doi,
                "paper_registry_present": paper_row is not None,
                "repository_article_capture_status": (
                    "missing"
                    if paper_row is None
                    else paper_row.article_download_status
                ),
                "repository_supplement_capture_status": (
                    "missing"
                    if paper_row is None
                    else paper_row.supplementary_download_status
                ),
                "local_reference_article_status": (
                    "local_reference_staged"
                    if stash_record.get("article_formats")
                    else "missing"
                ),
                "local_reference_supplement_status": (
                    "local_reference_staged"
                    if stash_record.get("supplementary_assets")
                    else "missing"
                ),
                "repository_supplementary_count": (
                    0 if paper_row is None else int(paper_row.supplementary_count)
                ),
                "local_reference_supplementary_asset_count": len(
                    stash_record.get("supplementary_assets", ())
                ),
                "alignment_status": _reconciliation_alignment_status(
                    paper_row, stash_record
                ),
            }
        )
    return {
        "schema_version": SOURCE_INVENTORY_SCHEMA_VERSION,
        "reference_stash_visible": _resolve_reference_stash_root(output_root)
        is not None,
        "row_count": len(rows),
        "counts": _count_by(rows, "alignment_status"),
        "rows": rows,
    }


def build_reference_stash_doi_integrity_audit(output_root: Path) -> dict[str, object]:
    """Verify that every DOI visible in the local reference stash is represented in the tracked paper registry."""
    paper_rows = {row.paper_doi: row for row in build_paper_registry(output_root)}
    tracked_slugs = {_doi_slug(doi): doi for doi in paper_rows}
    stash_records = _reference_stash_records(output_root)
    rows = []
    for slug in sorted(set(tracked_slugs) | set(stash_records)):
        paper_doi = tracked_slugs.get(slug, "")
        rows.append(
            {
                "stash_slug": slug,
                "paper_doi": paper_doi,
                "represented_in_paper_registry": bool(paper_doi),
                "representation_status": (
                    "matched"
                    if slug in tracked_slugs and slug in stash_records
                    else (
                        "tracked_without_local_reference"
                        if slug in tracked_slugs
                        else "local_reference_not_tracked"
                    )
                ),
            }
        )
    missing_in_registry = [
        row["stash_slug"] for row in rows if not row["represented_in_paper_registry"]
    ]
    missing_in_stash = [
        row["paper_doi"]
        for row in rows
        if row["paper_doi"]
        and row["representation_status"] == "tracked_without_local_reference"
    ]
    return {
        "schema_version": SOURCE_INVENTORY_SCHEMA_VERSION,
        "reference_stash_visible": _resolve_reference_stash_root(output_root)
        is not None,
        "paper_registry_doi_count": len(paper_rows),
        "reference_stash_doi_count": len(stash_records),
        "all_stash_dois_tracked": len(missing_in_registry) == 0,
        "missing_in_paper_registry": missing_in_registry,
        "tracked_without_local_reference": missing_in_stash,
        "rows": rows,
    }


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


def build_source_blocker_review(output_root: Path) -> dict[str, object]:
    """Explain the real missing evidence stage for each blocked project."""
    matrix = {
        row["project_accession"]: row
        for row in build_project_source_evidence_matrix(output_root)["rows"]
    }
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


def build_cross_project_source_intake_dossier(output_root: Path) -> dict[str, object]:
    """Describe what each tracked paper or supplement is expected to contribute across the program."""
    matrix = {
        row["project_accession"]: row
        for row in build_project_source_evidence_matrix(output_root)["rows"]
    }
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
                    row.project_accession, row.primary_paper_doi
                ),
            }
        )
    return {
        "schema_version": SOURCE_INVENTORY_SCHEMA_VERSION,
        "row_count": len(rows),
        "counts": {
            "projects_with_site_expectation": sum(
                1 for row in rows if "site_names" in row["expected_contributions"]
            ),
            "projects_with_chronology_expectation": sum(
                1 for row in rows if "chronology" in row["expected_contributions"]
            ),
            "projects_with_identifier_expectation": sum(
                1
                for row in rows
                if "sample_identifiers" in row["expected_contributions"]
            ),
        },
        "rows": rows,
    }


def render_tracked_project_scope_audit_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Tracked project scope audit",
        "",
        f"- Tracked project count: `{payload['tracked_project_count']}`",
        f"- Core intake candidates: `{payload['counts'].get('core_sample_intake_candidate', 0)}`",
        f"- Comparator-only rows: `{payload['counts'].get('context_only_comparator', 0)}`",
        f"- Rejected references: `{payload['counts'].get('out_of_scope_reference', 0)}`",
        "",
        "| Project | Species | Scope fit | Source family | Note |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['project_accession']}` | `{row['species_latin_name']}` | "
            f"`{row['scope_fit_status']}` | `{row['source_family']}` | {row['scope_note']} |"
        )
    return "\n".join(lines) + "\n"


def render_project_source_evidence_matrix_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Project source evidence matrix",
        "",
        f"- Project rows: `{payload['row_count']}`",
        f"- Repository supplement-captured projects: `{payload['counts']['repository_supplement_captured']}`",
        f"- Local-reference supplement-staged projects: `{payload['counts']['local_reference_supplement_staged']}`",
        "",
        "| Project | Paper | Repo article | Repo supplement | Local supplement | Sample master | Site table | Chronology table | Acquisition state |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['project_accession']}` | `{row['paper_doi'] or 'none'}` | "
            f"`{row['repository_article_readability_status']}` | `{row['repository_supplement_parse_status']}` | "
            f"`{row['local_reference_supplement_status']}` | `{row['sample_table_extraction_status']}` | "
            f"`{row['sample_site_table_status']}` | `{row['sample_chronology_table_status']}` | "
            f"`{row['evidence_acquisition_state']}` |"
        )
    return "\n".join(lines) + "\n"


def render_reference_stash_reconciliation_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Reference stash reconciliation",
        "",
        f"- Reference stash visible: `{str(payload['reference_stash_visible']).lower()}`",
        f"- Row count: `{payload['row_count']}`",
        "",
        "| DOI slug | Paper registry | Repo supplement | Local supplement | Alignment |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['stash_slug']}` | `{str(row['paper_registry_present']).lower()}` | "
            f"`{row['repository_supplement_capture_status']}` | `{row['local_reference_supplement_status']}` | "
            f"`{row['alignment_status']}` |"
        )
    return "\n".join(lines) + "\n"


def render_reference_stash_doi_integrity_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Reference stash DOI integrity audit",
        "",
        f"- Reference stash visible: `{str(payload['reference_stash_visible']).lower()}`",
        f"- Paper registry DOI count: `{payload['paper_registry_doi_count']}`",
        f"- Reference stash DOI count: `{payload['reference_stash_doi_count']}`",
        f"- All stash DOIs tracked: `{str(payload['all_stash_dois_tracked']).lower()}`",
        "",
        "| DOI slug | Paper DOI | Representation status |",
        "| --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['stash_slug']}` | `{row['paper_doi'] or 'none'}` | "
            f"`{row['representation_status']}` |"
        )
    return "\n".join(lines) + "\n"


def render_supplement_file_family_audit_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Supplement file family audit",
        "",
        f"- Paper rows: `{payload['row_count']}`",
        "",
        "| Paper DOI | Verification | Repo capture | Parse status | Expected file families |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['paper_doi']}` | `{row['supplementary_verification_status']}` | "
            f"`{row['repository_supplement_capture_status']}` | `{row['supplement_parse_status']}` | "
            f"`{'; '.join(row['expected_supplementary_file_families'])}` |"
        )
    return "\n".join(lines) + "\n"


def render_supplement_acquisition_checklist_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Supplement acquisition checklist",
        "",
        f"- Paper rows: `{payload['row_count']}`",
        "",
        "| Paper DOI | Check status | Publisher page | DOI landing | Crossref | PMC or PubMed | HTML source |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['paper_doi']}` | `{row['acquisition_check_status']}` | "
            f"`{row['publisher_page_url']}` | `{row['doi_landing_url']}` | "
            f"`{row['crossref_url']}` | `{row['pmc_or_pubmed_url'] or '-'}` | "
            f"`{row['article_html_source_url'] or '-'}` |"
        )
    return "\n".join(lines) + "\n"


def render_supplement_recovery_audit_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Supplement recovery audit",
        "",
        f"- Paper rows: `{payload['row_count']}`",
        f"- Archived and parseable: `{payload['counts'].get('archived_and_parseable', 0)}`",
        f"- Confirmed absent: `{payload['counts'].get('confirmed_absent', 0)}`",
        f"- Local reference staged: `{payload['counts'].get('local_reference_staged_needs_repo_ingestion', 0)}`",
        f"- Not found yet: `{payload['counts'].get('not_found_yet', 0)}`",
        "",
        "| Paper DOI | Recovery status | Repo capture | Parse status | Local reference | Supplement count |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['paper_doi']}` | `{row['recovery_status']}` | "
            f"`{row['repository_supplement_capture_status']}` | `{row['supplement_parse_status']}` | "
            f"`{row['local_reference_supplement_status']}` | `{row['supplementary_count']}` |"
        )
    return "\n".join(lines) + "\n"


def render_source_blocker_review_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Source blocker review",
        "",
        f"- Blocked project rows: `{payload['row_count']}`",
        "",
        "| Project | Stage | Required evidence | Explanation |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['project_accession']}` | `{row['blocking_stage']}` | "
            f"`{'; '.join(row['required_evidence'])}` | {row['explanation']} |"
        )
    return "\n".join(lines) + "\n"


def render_cross_project_source_intake_dossier_markdown(
    payload: dict[str, object],
) -> str:
    lines = [
        "# Cross-project source intake dossier",
        "",
        f"- Project rows: `{payload['row_count']}`",
        "",
        "| Project | Paper | Contributions | Acquisition state |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['project_accession']}` | `{row['paper_doi'] or 'none'}` | "
            f"`{'; '.join(row['expected_contributions'])}` | `{row['evidence_acquisition_state']}` |"
        )
    return "\n".join(lines) + "\n"


def _source_root(output_root: Path) -> Path:
    return Path(output_root) / "adna" / "governance" / "source_library"


def _project_table_status(path: Path) -> tuple[str, int]:
    if not path.is_file():
        return ("not_published", 0)
    rows = json.loads(path.read_text(encoding="utf-8")).get("rows", [])
    if rows:
        return ("published", len(rows))
    return ("published_empty", 0)


def _count_by(rows: list[dict[str, object]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get(field, ""))
        counts[key] = counts.get(key, 0) + 1
    return counts


def _reconciliation_alignment_status(
    paper_row: object | None, stash_record: dict[str, object]
) -> str:
    repo_supplements = (
        0 if paper_row is None else int(getattr(paper_row, "supplementary_count", 0))
    )
    stash_supplements = len(stash_record.get("supplementary_assets", ()))
    if paper_row is not None and stash_supplements == repo_supplements:
        return "aligned"
    if paper_row is not None and stash_supplements > repo_supplements:
        return "local_reference_ahead_of_repo"
    if paper_row is not None:
        return "repo_ahead_of_local_reference"
    return "local_reference_not_tracked"


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
