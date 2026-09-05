from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.adna.governance.admission import build_species_dataset_review
from bijux_pollenomics.adna.governance.curation import build_species_curation_manifest
from bijux_pollenomics.adna.governance.reviews import (
    AdnaSpeciesReviewTableRow,
    build_species_review_dossier,
)
from bijux_pollenomics.adna.workflow.normalization import (
    build_species_normalization_bundle,
)

from ..definitions import resolve_species_definition
from .payloads import _species_project_recovery_deficits_payload


def _render_species_root_readme(output_root: Path, species_name: str) -> str:
    species = resolve_species_definition(species_name)
    review = build_species_dataset_review(species_name)
    curation = build_species_curation_manifest(species_name)
    normalization_bundle = build_species_normalization_bundle(species_name)
    sample_rows = normalization_bundle.sample_records
    site_rows = normalization_bundle.site_evidence_records
    coordinate_rows = normalization_bundle.coordinate_provenance_records
    direct_coordinate_count = sum(
        1
        for row in coordinate_rows
        if row.mapping_posture == "mappable_point"
        and row.coordinate_basis
        in {
            "direct_published_coordinates",
            "supplementary_table_coordinates",
            "archive_coordinates",
        }
    )
    geocoded_count = sum(
        1
        for row in coordinate_rows
        if row.mapping_posture == "mappable_point"
        and row.coordinate_basis
        in {
            "named_site_geocoding",
            "named_site_geocoded",
        }
    )
    unresolved_count = sum(
        1 for row in sample_rows if row.inclusion_status == "sample_context_blocked"
    )
    mapped_nordic_count = sum(
        1
        for row in normalization_bundle.locality_records
        if row.nordic_inclusion and row.coordinate_confidence != "withheld"
    )
    deficit_payload = _species_project_recovery_deficits_payload(
        output_root, species_name
    )
    lines = [
        f"# {species.common_name.title()} Evidence View",
        "",
        f"`{species.latin_name}` is a species-owned projection over project, paper,",
        "supplement, sample, locality, chronology, and coordinate evidence. This",
        "directory makes the current curation posture inspectable; it is not an",
        "independent source database and does not transfer fact ownership away from",
        "the project evidence under `../../governance/source_library/`.",
        "",
        "```mermaid",
        "flowchart LR",
        '    Source["paper, project, and supplement"] --> Sample["project-owned sample"]',
        '    Sample --> View["species-normalized evidence"]',
        '    View --> Review["species review and recovery deficits"]',
        '    Review --> Decision{"product-specific admission"}',
        '    Decision -->|supported| Member["atlas or report member"]',
        '    Decision -->|insufficient| Gap["qualified, excluded, or recovery state"]',
        "```",
        "",
        "## Current Curation Snapshot",
        "",
        f"- Latin name: `{species.latin_name}`",
        f"- Product role: `{review.product_role}`",
        f"- Dataset bucket: `{review.dataset_bucket}`",
        f"- Curation class: `{curation.curation_class}`",
        f"- Curated sample rows: `{len(sample_rows)}`",
        f"- Curated projects: `{len(curation.curated_projects)}`",
        f"- Curated site rows: `{len(site_rows)}`",
        f"- Direct-coordinate rows: `{direct_coordinate_count}`",
        f"- Geocoded rows: `{geocoded_count}`",
        f"- Unresolved sample rows: `{unresolved_count}`",
        f"- Mapped Nordic rows: `{mapped_nordic_count}`",
        f"- Tracked intake projects: `{review.archive_project_count}`",
        f"- Projects with sample recovery gaps: `{deficit_payload['counts']['projects_with_sample_gap']}`",
        f"- Projects with site-recovery gaps: `{deficit_payload['counts']['projects_with_site_gap']}`",
        f"- Projects with chronology gaps: `{deficit_payload['counts']['projects_with_chronology_gap']}`",
        f"- Projects blocked before publication review: `{deficit_payload['counts']['projects_blocked_before_publication']}`",
        f"- Pending projects: `{len(curation.pending_projects)}`",
        f"- Rejected projects: `{len(curation.rejected_projects)}`",
        "",
        "These values describe different observation units. Sample, project, site,",
        "coordinate, and publication counts are not one attrition funnel and must not",
        "be divided into a collection-wide completeness percentage.",
        "",
        "## Interpret The Posture",
        "",
        "| Signal | Meaning |",
        "| --- | --- |",
        f"| product role `{review.product_role}` | the intended contribution of this taxon to governed products |",
        f"| dataset bucket `{review.dataset_bucket}` | the present evidence grouping, not a biological category |",
        f"| curation class `{curation.curation_class}` | the evidence rule used to classify project support |",
        f"| release gate `{str(review.release_gate_satisfied).lower()}` | whether the current species review satisfies its declared release conditions |",
        f"| supported-status eligibility `{str(review.eligible_for_supported_status).lower()}` | whether current evidence permits the stronger supported posture |",
        "",
        "The species release gate evaluates the declared role and review contract. It",
        "does not assert that every tracked project is recovered or publication-ready;",
        "project deficits and product admission remain separate decisions.",
        "",
        curation.support_statement,
        "",
        "### Current Blocking Reasons",
        "",
    ]
    if review.blocking_reasons:
        lines.extend(f"- `{reason}`" for reason in review.blocking_reasons)
    else:
        lines.append("- none under the current species review")
    lines.extend(
        [
            "",
            "A clear blocker is retained evidence, not a failed attempt at presentation.",
            "It identifies the project, sample, locality, chronology, or source-recovery",
            "boundary that must change before a stronger species or publication claim.",
            "",
            "## Inspect The Evidence",
            "",
            "| Question | Governing surface |",
            "| --- | --- |",
            "| Which source projects and artifacts are represented? | `raw/archive_inventory.json` and `raw/source_snapshot.json` |",
            "| Which stable samples are recovered? | `normalized/sample_records.json` |",
            "| How are samples related to sites? | `normalized/site_evidence.json` |",
            "| What supports each mapped coordinate? | `normalized/coordinate_provenance.json` |",
            "| Which locality units are available? | `normalized/locality_summaries.json` |",
            "| Which curation and runtime revision produced the view? | `manifests/curation_manifest.json` and `manifests/runtime_manifest.json` |",
            "| What remains incomplete by project? | `reports/project_recovery_deficits.md` |",
            "| Why is the present posture accepted or blocked? | `review/species_review.md` |",
            "",
            "Start from the claim being inspected, recover its stable sample and project",
            "identity, then follow locality, chronology, coordinate, and admission evidence",
            "independently. A repeated value in a species view remains subordinate to the",
            "project-owned fact identified by its lineage.",
            "",
            "## Directory Contract",
            "",
            "| Directory | Responsibility |",
            "| --- | --- |",
            "| `raw/` | archive inventory and source wording snapshots |",
            "| `normalized/` | sample, site, coordinate, project, and locality projections |",
            "| `manifests/` | species, citation, curation, normalization, project, and runtime identities |",
            "| `reports/` | support summaries and project recovery deficits |",
            "| `review/` | release blockers, project rows, and archive-integrity evidence |",
            "",
            "## Evidence Boundary",
            "",
            "Species grouping does not prove project completeness, sample independence,",
            "exact locality, comparable chronology, Nordic membership, or publication",
            "fitness. Those claims require their own governing records and product rules.",
            "Rows that remain unresolved, pending, rejected, or blocked stay visible so",
            "the mapped subset cannot masquerade as the recovered collection.",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_support_summary_markdown(output_root: Path, species_name: str) -> str:
    species = resolve_species_definition(species_name)
    review = build_species_dataset_review(species_name)
    curation = build_species_curation_manifest(species_name)
    deficit_payload = _species_project_recovery_deficits_payload(
        output_root, species_name
    )
    return (
        f"# {species.common_name} support summary\n\n"
        f"- Product role: `{review.product_role}`\n"
        f"- Assignment rule: `{review.assignment_rule}`\n"
        f"- Dataset bucket: `{review.dataset_bucket}`\n"
        f"- Archive project count: `{review.archive_project_count}`\n"
        f"- Core project count: `{review.core_project_count}`\n"
        f"- Primary paper pin count: `{review.primary_paper_pin_count}`\n"
        f"- Curated support project count: `{review.curated_support_project_count}`\n"
        f"- Release gate satisfied: `{str(review.release_gate_satisfied).lower()}`\n"
        f"- Eligible for supported status: `{str(review.eligible_for_supported_status).lower()}`\n"
        f"- Projects with sample recovery gaps: `{deficit_payload['counts']['projects_with_sample_gap']}`\n"
        f"- Projects blocked before publication review: `{deficit_payload['counts']['projects_blocked_before_publication']}`\n\n"
        f"{curation.support_statement}\n\n"
        "## Blocking reasons\n\n"
        + (
            "\n".join(f"- `{reason}`" for reason in review.blocking_reasons)
            if review.blocking_reasons
            else "- none"
        )
        + "\n"
    )


def _render_species_project_recovery_deficits_markdown(
    output_root: Path,
    species_name: str,
) -> str:
    payload = _species_project_recovery_deficits_payload(output_root, species_name)
    lines = [
        f"# {species_name} project recovery deficits",
        "",
        f"- Project rows: `{payload['counts']['project_count']}`",
        f"- Projects with sample gaps: `{payload['counts']['projects_with_sample_gap']}`",
        f"- Projects with site gaps: `{payload['counts']['projects_with_site_gap']}`",
        f"- Projects with chronology gaps: `{payload['counts']['projects_with_chronology_gap']}`",
        f"- Projects blocked before publication review: `{payload['counts']['projects_blocked_before_publication']}`",
        "",
        "| Project | Minimum sample gap | Site gap | Chronology gap | Publication status |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| `{row['project_accession']}` | `{row['minimum_gap_count'] or 0}` | "
            f"`{row['lacking_defensible_site_assignment_count']}` | "
            f"`{row['missing_chronology_count']}` | "
            f"`{row['publication_readiness_status']}` |"
        )
    return "\n".join(lines) + "\n"


def _render_review_dossier_markdown(species_name: str) -> str:
    species = resolve_species_definition(species_name)
    dossier = build_species_review_dossier(species_name)
    lines = [
        f"# {species.common_name} species review",
        "",
        f"- Species: `{species.latin_name}`",
        f"- Dataset bucket: `{dossier.dataset_review.dataset_bucket}`",
        f"- Product role: `{dossier.dataset_review.product_role}`",
        "",
        "## Release blockers",
        "",
    ]
    if dossier.release_blockers:
        lines.extend(f"- `{reason}`" for reason in dossier.release_blockers)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Project rows",
            "",
            "| accession | archive status | ancient status | evidence strength | paper doi | domestication scope |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in dossier.project_manifest.projects:
        paper_doi = "" if row.paper_doi is None else row.paper_doi
        lines.append(
            f"| {row.project_accession} | {row.archive_status} | {row.ancient_status} | "
            f"{row.evidence_strength} | {paper_doi} | {row.domestication_scope} |"
        )
    lines.extend(
        _render_grouped_review_table(
            "Rejected projects",
            dossier.rejected_projects,
        )
    )
    lines.extend(
        _render_grouped_review_table(
            "Ancient but still too weak",
            dossier.too_weak_projects,
        )
    )
    lines.extend(
        _render_grouped_review_table(
            "Comparator-only projects",
            dossier.comparator_projects,
        )
    )
    lines.extend(
        _render_grouped_review_table(
            "Nordic-relevant leads not yet mapped confidently",
            dossier.nordic_unmapped_leads,
        )
    )
    lines.append("")
    return "\n".join(lines)


def _render_grouped_review_table(
    title: str,
    rows: tuple[AdnaSpeciesReviewTableRow, ...],
) -> list[str]:
    lines = ["", f"## {title}", ""]
    if not rows:
        lines.append("- none")
        return lines
    lines.extend(
        [
            "| accession | archive status | support class | nordic relevance | reason |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row.project_accession} | {row.archive_status} | {row.support_class} | "
            f"{row.nordic_relevance} | {row.reason} |"
        )
    return lines
