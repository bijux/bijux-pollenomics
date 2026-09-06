"""Human-readable aDNA source-library rendering."""

from __future__ import annotations

from pathlib import Path
from .models import (
    AdnaPaperRegistryRow,
    AdnaProjectRegistryRow,
    AdnaSourceBundleManifest,
)


def _render_curation_note(bundle: AdnaSourceBundleManifest) -> str:
    requirement = (
        "Paper and supplementary materials are required to recover sample and site detail."
        if bundle.paper_required and bundle.supplement_required
        else (
            "Paper-level evidence is required; locally curated supplementary "
            "evidence is also available."
            if bundle.paper_required
            and bundle.supplement_download_status in {"archived", "partial"}
            else "Paper-level evidence is required, and no supplementary artifact "
            "is currently curated."
            if bundle.paper_required
            else "Archive metadata is sufficient for the current curation posture."
        )
    )
    blockers = (
        "\n".join(f"- `{item}`" for item in bundle.blockers)
        if bundle.blockers
        else "- none"
    )
    return (
        f"# {bundle.project_accession}\n\n"
        f"- Species: `{bundle.species_latin_name}`\n"
        f"- Archive status: `{bundle.archive_status}`\n"
        f"- Evidence strength: `{bundle.evidence_strength}`\n"
        f"- Project URL: {bundle.project_url}\n"
        f"- Paper DOI: `{bundle.paper_doi or 'none'}`\n"
        f"- Paper download status: `{bundle.paper_download_status}`\n"
        f"- Supplement download status: `{bundle.supplement_download_status}`\n\n"
        f"{requirement}\n\n"
        "## Local artifacts\n\n"
        + ("\n".join(f"- `{path}`" for path in bundle.local_artifact_paths) or "- none")
        + "\n\n## Blockers\n\n"
        + blockers
        + "\n"
    )


def _render_source_storage_audit(audit: dict[str, object]) -> str:
    raw_rows = audit.get("rows", [])
    rows = raw_rows if isinstance(raw_rows, list) else []
    lines = [
        "# Source storage audit",
        "",
        f"- Archived artifacts: `{audit['archived_artifact_count']}`",
        f"- Archived HTML artifacts: `{audit['archived_html_artifact_count']}`",
        f"- Compressed HTML artifacts: `{audit['compressed_html_artifact_count']}`",
        f"- Uncompressed HTML artifacts: `{audit['uncompressed_html_artifact_count']}`",
        f"- Archived payload bytes: `{audit['archived_payload_byte_count']}`",
        f"- Archived storage bytes: `{audit['archived_storage_byte_count']}`",
        f"- HTML payload bytes: `{audit['html_payload_byte_count']}`",
        f"- HTML storage bytes: `{audit['html_storage_byte_count']}`",
        "",
    ]
    if not rows:
        lines.append("No archived HTML source artifacts are currently published.")
        lines.append("")
        return "\n".join(lines)
    lines.extend(
        [
            "| Artifact id | Kind | Local path | Storage path | Encoding | Payload bytes | Storage bytes |",
            "| --- | --- | --- | --- | --- | ---: | ---: |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['artifact_id']} | {row['artifact_kind']} | "
            f"`{row['local_path']}` | `{row['storage_path']}` | "
            f"`{row['content_encoding']}` | {row['byte_size'] or 0} | "
            f"{row['storage_byte_size'] or row['byte_size'] or 0} |"
        )
    lines.append("")
    return "\n".join(lines)


def _project_intake_dossier(
    output_root: Path,
    bundle: AdnaSourceBundleManifest,
) -> dict[str, object]:
    from ..recovery import build_project_recovery_dossier

    return build_project_recovery_dossier(output_root, bundle.project_accession)


def _render_project_intake_dossier(
    output_root: Path,
    bundle: AdnaSourceBundleManifest,
) -> str:
    from ..recovery import render_project_recovery_dossier_markdown

    return render_project_recovery_dossier_markdown(
        _project_intake_dossier(output_root, bundle)
    )


def _render_tracked_project_and_paper_inventory(
    project_registry: tuple[AdnaProjectRegistryRow, ...],
    paper_registry: tuple[AdnaPaperRegistryRow, ...],
) -> str:
    project_rows = "\n".join(
        (
            f"| {row.species_latin_name} | {row.project_accession} | {row.archive_status} | "
            f"{row.inventory_disposition} | {row.expected_sample_count if row.expected_sample_count is not None else '-'} | "
            f"{row.expected_sample_count_status} | {row.primary_paper_doi or '-'} |"
        )
        for row in project_registry
    )
    paper_rows = "\n".join(
        (
            f"| {row.paper_doi} | {row.title} | {'; '.join(row.project_accessions)} | "
            f"{row.sample_extractability} | {row.supplementary_count} |"
        )
        for row in paper_registry
    )
    return (
        "# Tracked animal aDNA project and paper inventory\n\n"
        f"- Tracked projects: `{len(project_registry)}`\n"
        f"- Tracked papers: `{len(paper_registry)}`\n\n"
        "## Materialized source-library artifacts\n\n"
        "- Cross-project sample-master completeness: `project_sample_master_completeness.json`\n"
        "- Per-project sample masters: `projects/<project_accession>/sample_master.json`\n"
        "- Cross-project sample-site review: `project_sample_site_review.json`\n"
        "- Per-project sample-site tables: `projects/<project_accession>/sample_sites.json`\n\n"
        "- Per-project locality worksheets: `projects/<project_accession>/locality_worksheet.json`\n"
        "- Per-project sample locality evidence reviews: `projects/<project_accession>/sample_locality_evidence.json`\n"
        "- Cross-project sample locality conflicts: `sample_locality_conflict_ledger.json`\n"
        "- Cross-project locality manual curation workflow: `sample_locality_manual_curation_workflow.json`\n"
        "- Cross-project site-name normalization dictionary: `site_name_normalization_dictionary.json`\n"
        "- Cross-project locality completeness: `project_locality_completeness.json`\n\n"
        "- Cross-project sample-chronology review: `project_sample_chronology_review.json`\n"
        "- Per-project sample chronology tables: `projects/<project_accession>/sample_chronology.json`\n\n"
        "- Cross-project recovery stage review: `project_recovery_stage_review.json`\n"
        "- Cross-project expected sample yield review: `project_expected_sample_yield_review.json`\n"
        "- Cross-paper expected sample yield review: `paper_expected_sample_yield_review.json`\n"
        "- Cross-species project deficit ledger: `species_project_deficit_ledger.json`\n"
        "- Manual curation worklist: `manual_curation_worklist.json`\n"
        "- Source recovery progress: `source_recovery_progress.json`\n"
        "- Missing source queue: `missing_source_queue.json`\n"
        "- Source recovery release guard: `source_recovery_release_guard.json`\n\n"
        "## Projects\n\n"
        "| Species | Project accession | Archive status | Inventory disposition | Expected sample count | Sample count status | Primary paper DOI |\n"
        "| --- | --- | --- | --- | ---: | --- | --- |\n"
        f"{project_rows}\n\n"
        "## Papers\n\n"
        "| Paper DOI | Title | Project accessions | Sample extractability | Supplementary artifacts |\n"
        "| --- | --- | --- | --- | ---: |\n"
        f"{paper_rows}\n"
    )


def _render_csv(rows: list[dict[str, object]]) -> str:
    if not rows:
        return ""
    headers = tuple(rows[0].keys())
    lines = [",".join(headers)]
    for row in rows:
        rendered = []
        for key in headers:
            value = row[key]
            if isinstance(value, list):
                text = ";".join(str(item) for item in value)
            else:
                text = "" if value is None else str(value)
            if any(token in text for token in [",", '"', "\n"]):
                text = '"' + text.replace('"', '""') + '"'
            rendered.append(text)
        lines.append(",".join(rendered))
    return "\n".join(lines) + "\n"
