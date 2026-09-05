"""Markdown renderers for source-inventory evidence surfaces."""

from __future__ import annotations

from typing import Any, cast


def _payload_counts(payload: dict[str, object]) -> dict[str, int]:
    return cast(dict[str, int], payload["counts"])


def _payload_rows(payload: dict[str, object]) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], payload["rows"])


def render_tracked_project_scope_audit_markdown(payload: dict[str, object]) -> str:
    lines = [
        "# Tracked project scope audit",
        "",
        f"- Tracked project count: `{payload['tracked_project_count']}`",
        f"- Core intake candidates: `{_payload_counts(payload).get('core_sample_intake_candidate', 0)}`",
        f"- Comparator-only rows: `{_payload_counts(payload).get('context_only_comparator', 0)}`",
        f"- Rejected references: `{_payload_counts(payload).get('out_of_scope_reference', 0)}`",
        "",
        "| Project | Species | Scope fit | Source family | Note |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in _payload_rows(payload):
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
        f"- Repository supplement-captured projects: `{_payload_counts(payload)['repository_supplement_captured']}`",
        f"- Local-reference supplement-staged projects: `{_payload_counts(payload)['local_reference_supplement_staged']}`",
        "",
        "| Project | Paper | Repo article | Repo supplement | Local supplement | Sample master | Site table | Chronology table | Acquisition state |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in _payload_rows(payload):
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
    for row in _payload_rows(payload):
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
    for row in _payload_rows(payload):
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
    for row in _payload_rows(payload):
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
    for row in _payload_rows(payload):
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
        f"- Archived and parseable: `{_payload_counts(payload).get('archived_and_parseable', 0)}`",
        f"- Confirmed absent: `{_payload_counts(payload).get('confirmed_absent', 0)}`",
        f"- Local reference staged: `{_payload_counts(payload).get('local_reference_staged_needs_repo_ingestion', 0)}`",
        f"- Not found yet: `{_payload_counts(payload).get('not_found_yet', 0)}`",
        "",
        "| Paper DOI | Recovery status | Repo capture | Parse status | Local reference | Supplement count |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for row in _payload_rows(payload):
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
    for row in _payload_rows(payload):
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
    for row in _payload_rows(payload):
        lines.append(
            f"| `{row['project_accession']}` | `{row['paper_doi'] or 'none'}` | "
            f"`{'; '.join(row['expected_contributions'])}` | `{row['evidence_acquisition_state']}` |"
        )
    return "\n".join(lines) + "\n"
