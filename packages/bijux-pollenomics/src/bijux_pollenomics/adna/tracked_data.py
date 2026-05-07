from __future__ import annotations

import csv
import io
from pathlib import Path

from ..core.files import write_json, write_text
from .catalogs import (
    build_cross_species_archive_inventory,
    build_cross_species_bibliography,
    build_cross_species_coverage_dashboard,
    build_shipped_adna_product_audit,
    build_species_freshness_table,
    render_csv_rows,
)
from .curation import build_species_curation_manifest
from .ena import build_species_archive_projects, classify_archive_project_evidence
from .governance import build_species_dataset_review
from .integrity import build_archive_integrity_report
from .layout import build_species_layout
from .manifests import build_species_manifest
from .normalization import build_species_normalization_bundle
from .reviews import build_species_project_manifest, build_species_review_packet
from .runtime import build_species_runtime_manifest
from .source_library import materialize_source_library
from .source_snapshots import (
    build_species_source_snapshots,
    resolve_archive_source_snapshot,
)
from .species import resolve_species_definition
from .tracked_species import TRACKED_ADNA_SPECIES, tracked_species_slugs

__all__ = [
    "TRACKED_ADNA_SPECIES",
    "materialize_tracked_species_adna",
    "materialize_tracked_species_root",
    "tracked_species_slugs",
]


def materialize_tracked_species_adna(
    output_root: Path,
    *,
    species_names: tuple[str, ...] = TRACKED_ADNA_SPECIES,
) -> None:
    """Write the tracked species-owned animal aDNA files under one data root."""
    for species_name in species_names:
        materialize_tracked_species_root(output_root, species_name)
    _materialize_cross_species_adna_artifacts(Path(output_root))
    materialize_source_library(Path(output_root))


def materialize_tracked_species_root(output_root: Path, species_name: str) -> None:
    """Write all tracked data files for one non-human species root."""
    output_root = Path(output_root)
    layout = build_species_layout(species_name)
    species_root = output_root / "adna" / layout.species.slug
    raw_root = species_root / "raw"
    normalized_root = species_root / "normalized"
    manifests_root = species_root / "manifests"
    reports_root = species_root / "reports"
    review_root = species_root / "review"
    for directory in (
        species_root,
        raw_root,
        normalized_root,
        manifests_root,
        reports_root,
        review_root,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    species_manifest = build_species_manifest(species_name)
    dataset_review = build_species_dataset_review(species_name)
    curation_manifest = build_species_curation_manifest(species_name)
    project_manifest = build_species_project_manifest(species_name)
    runtime_manifest = build_species_runtime_manifest(species_name)
    normalization_bundle = build_species_normalization_bundle(species_name)
    review_packet = build_species_review_packet(species_name)
    integrity_report = build_archive_integrity_report(species_name=species_name)
    archive_projects = build_species_archive_projects(species_name)

    write_text(species_root / "README.md", _render_species_root_readme(species_name))
    write_json(raw_root / "archive_inventory.json", _archive_inventory_payload(archive_projects))
    write_text(raw_root / "archive_inventory.csv", _render_archive_inventory_csv(archive_projects))
    write_json(raw_root / "source_snapshot.json", _source_snapshot_payload(species_name))
    write_text(raw_root / "source_snapshot.csv", _render_source_snapshot_csv(species_name))
    write_text(
        normalized_root / "sample_records.csv",
        _render_sample_records_csv(normalization_bundle),
    )
    write_json(
        normalized_root / "sample_records.json",
        _sample_records_payload(normalization_bundle),
    )
    write_text(
        normalized_root / "project_summaries.csv",
        _render_project_summaries_csv(normalization_bundle),
    )
    write_json(
        normalized_root / "project_summaries.json",
        _project_summaries_payload(normalization_bundle),
    )
    write_text(
        normalized_root / "locality_summaries.csv",
        _render_locality_summaries_csv(normalization_bundle),
    )
    write_json(
        normalized_root / "locality_summaries.json",
        _locality_summaries_payload(normalization_bundle),
    )
    write_json(manifests_root / "species_manifest.json", species_manifest.as_dict())
    write_json(manifests_root / "curation_manifest.json", curation_manifest.as_dict())
    write_json(manifests_root / "project_manifest.json", project_manifest.as_dict())
    write_json(manifests_root / "runtime_manifest.json", runtime_manifest.as_dict())
    write_json(
        manifests_root / "normalization_bundle.json",
        normalization_bundle.as_dict(),
    )
    write_text(
        manifests_root / "citation_manifest.csv",
        _render_citation_manifest_csv(archive_projects),
    )
    write_json(reports_root / "support_summary.json", _support_summary_payload(
        species_manifest=species_manifest.as_dict(),
        dataset_review=dataset_review.as_dict(),
        curation_manifest=curation_manifest.as_dict(),
        project_manifest=project_manifest.as_dict(),
        normalization_bundle=normalization_bundle.as_dict(),
    ))
    write_text(reports_root / "support_summary.md", _render_support_summary_markdown(species_name))
    write_json(review_root / "species_review.json", review_packet.as_dict())
    write_json(review_root / "archive_integrity.json", integrity_report.as_dict())
    write_text(review_root / "species_review.md", _render_review_packet_markdown(species_name))


def _archive_inventory_payload(archive_projects: tuple[object, ...]) -> dict[str, object]:
    projects = []
    for project in archive_projects:
        payload = project.as_dict()
        payload["evidence_strength"] = classify_archive_project_evidence(project)
        payload["source_snapshot"] = resolve_archive_source_snapshot(project).as_dict()
        projects.append(payload)
    return {"projects": projects}


def _source_snapshot_payload(species_name: str) -> dict[str, object]:
    snapshots = build_species_source_snapshots(species_name)
    return {
        "schema_version": "adna-species-source-snapshot.v1",
        "species_latin_name": resolve_species_definition(species_name).latin_name,
        "projects": [snapshot.as_dict() for snapshot in snapshots],
    }


def _support_summary_payload(
    *,
    species_manifest: dict[str, object],
    dataset_review: dict[str, object],
    curation_manifest: dict[str, object],
    project_manifest: dict[str, object],
    normalization_bundle: dict[str, object],
) -> dict[str, object]:
    return {
        "species_manifest": species_manifest,
        "dataset_review": dataset_review,
        "curation_manifest": curation_manifest,
        "project_manifest": project_manifest,
        "normalization_bundle": normalization_bundle,
    }


def _render_archive_inventory_csv(archive_projects: tuple[object, ...]) -> str:
    fieldnames = (
        "species_latin_name",
        "project_accession",
        "source_family",
        "accession_scope",
        "result_kind",
        "source_title",
        "source_description",
        "source_title_basis",
        "source_description_basis",
        "archive_status",
        "evidence_strength",
        "ancient_status",
        "metadata_url",
        "paper_title",
        "paper_doi",
        "journal_title",
        "publication_year",
        "sequencing_target",
        "material_basis",
        "dating_basis",
        "geographic_basis",
        "access_policy",
        "public_release_date",
        "domestication_scope",
        "notes",
    )
    rows = []
    for project in archive_projects:
        linkage = project.paper_linkage
        source_snapshot = resolve_archive_source_snapshot(project)
        rows.append(
            {
                "species_latin_name": project.species_latin_name,
                "project_accession": project.project_accession,
                "source_family": project.source_family,
                "accession_scope": project.accession_scope,
                "result_kind": project.result_kind,
                "source_title": source_snapshot.source_title,
                "source_description": source_snapshot.source_description,
                "source_title_basis": source_snapshot.title_basis,
                "source_description_basis": source_snapshot.description_basis,
                "archive_status": project.archive_status,
                "evidence_strength": classify_archive_project_evidence(project),
                "ancient_status": project.ancient_status,
                "metadata_url": project.metadata_url,
                "paper_title": "" if linkage is None else linkage.paper_title,
                "paper_doi": "" if linkage is None or linkage.doi is None else linkage.doi,
                "journal_title": (
                    "" if linkage is None or linkage.journal_title is None else linkage.journal_title
                ),
                "publication_year": (
                    "" if linkage is None or linkage.publication_year is None else linkage.publication_year
                ),
                "sequencing_target": "" if project.sequencing_target is None else project.sequencing_target,
                "material_basis": "" if project.material_basis is None else project.material_basis,
                "dating_basis": "" if project.dating_basis is None else project.dating_basis,
                "geographic_basis": "" if project.geographic_basis is None else project.geographic_basis,
                "access_policy": project.access_policy,
                "public_release_date": "" if project.public_release_date is None else project.public_release_date,
                "domestication_scope": project.domestication_scope,
                "notes": project.notes,
            }
        )
    return _render_csv(fieldnames, rows)


def _render_source_snapshot_csv(species_name: str) -> str:
    fieldnames = (
        "project_accession",
        "source_family",
        "result_kind",
        "metadata_url",
        "source_title",
        "source_description",
        "title_basis",
        "description_basis",
        "captured_on",
    )
    rows = [snapshot.as_dict() for snapshot in build_species_source_snapshots(species_name)]
    return _render_csv(fieldnames, rows)


def _render_citation_manifest_csv(archive_projects: tuple[object, ...]) -> str:
    fieldnames = (
        "species_latin_name",
        "project_accession",
        "archive_status",
        "evidence_strength",
        "paper_title",
        "paper_doi",
        "pubmed_id",
        "pmc_id",
        "journal_title",
        "publication_year",
        "reference_kind",
        "pinning_evidence",
    )
    rows = []
    for project in archive_projects:
        linkage = project.paper_linkage
        rows.append(
            {
                "species_latin_name": project.species_latin_name,
                "project_accession": project.project_accession,
                "archive_status": project.archive_status,
                "evidence_strength": classify_archive_project_evidence(project),
                "paper_title": "" if linkage is None else linkage.paper_title,
                "paper_doi": "" if linkage is None or linkage.doi is None else linkage.doi,
                "pubmed_id": "" if linkage is None or linkage.pubmed_id is None else linkage.pubmed_id,
                "pmc_id": "" if linkage is None or linkage.pmc_id is None else linkage.pmc_id,
                "journal_title": (
                    "" if linkage is None or linkage.journal_title is None else linkage.journal_title
                ),
                "publication_year": (
                    "" if linkage is None or linkage.publication_year is None else linkage.publication_year
                ),
                "reference_kind": "" if linkage is None else linkage.reference_kind,
                "pinning_evidence": "" if linkage is None else linkage.pinning_evidence,
            }
        )
    return _render_csv(fieldnames, rows)


def _render_project_summaries_csv(bundle: object) -> str:
    fieldnames = (
        "summary_token",
        "species_latin_name",
        "species_common_name",
        "project_accession",
        "study_token",
        "source_family",
        "source_release",
        "result_kind",
        "archive_status",
        "evidence_strength",
        "review_strength",
        "support_class",
        "record_modality",
        "domestication_status",
        "domestication_scope",
        "comparator_status",
        "normalized_breed_label",
        "sequencing_target",
        "material_basis",
        "chronology_basis",
        "dating_basis",
        "geographic_basis",
        "coordinate_policy",
        "chronology_policy",
        "paper_title",
        "paper_doi",
        "paper_url",
        "nordic_relevance",
        "nordic_relevance_reason",
        "interpretation_caveat",
        "notes",
    )
    rows = []
    for summary in bundle.project_summaries:
        rows.append(
            {
                "summary_token": summary.summary_token,
                "species_latin_name": summary.species_latin_name,
                "species_common_name": summary.species_common_name,
                "project_accession": summary.project_accession,
                "study_token": summary.study_token,
                "source_family": summary.source_family,
                "source_release": summary.source_release,
                "result_kind": summary.result_kind,
                "archive_status": summary.archive_status,
                "evidence_strength": summary.evidence_strength,
                "review_strength": summary.review_strength,
                "support_class": summary.support_class,
                "record_modality": summary.record_modality,
                "domestication_status": summary.domestication_status,
                "domestication_scope": summary.domestication_scope,
                "comparator_status": str(summary.comparator_status).lower(),
                "normalized_breed_label": "" if summary.normalized_breed_label is None else summary.normalized_breed_label,
                "sequencing_target": "" if summary.sequencing_target is None else summary.sequencing_target,
                "material_basis": "" if summary.material_basis is None else summary.material_basis,
                "chronology_basis": "" if summary.chronology_basis is None else summary.chronology_basis,
                "dating_basis": "" if summary.dating_basis is None else summary.dating_basis,
                "geographic_basis": "" if summary.geographic_basis is None else summary.geographic_basis,
                "coordinate_policy": summary.coordinate_policy,
                "chronology_policy": summary.chronology_policy,
                "paper_title": "" if summary.paper_title is None else summary.paper_title,
                "paper_doi": "" if summary.paper_doi is None else summary.paper_doi,
                "paper_url": "" if summary.paper_url is None else summary.paper_url,
                "nordic_relevance": summary.nordic_relevance,
                "nordic_relevance_reason": summary.nordic_relevance_reason,
                "interpretation_caveat": summary.interpretation_caveat,
                "notes": summary.notes,
            }
        )
    return _render_csv(fieldnames, rows)


def _render_sample_records_csv(bundle: object) -> str:
    fieldnames = (
        "stable_sample_id",
        "project_accession",
        "sample_basis",
        "inclusion_status",
        "species_latin_name",
        "species_common_name",
        "source_family",
        "source_release",
        "record_modality",
        "review_strength",
        "provenance_quality",
        "publication",
        "paper_doi",
        "paper_url",
        "supplementary_source",
        "site_label",
        "political_entity",
        "latitude",
        "longitude",
        "latitude_text",
        "longitude_text",
        "coordinate_confidence",
        "chronology_text",
        "time_start_bp",
        "time_end_bp",
        "time_mean_bp",
        "dating_basis",
        "inclusion_note",
    )
    rows = []
    for sample in bundle.sample_records:
        site_label = sample.locality_identity.locality_text
        rows.append(
            {
                "stable_sample_id": sample.genetic_id,
                "project_accession": sample.project_accession,
                "sample_basis": sample.sample_basis,
                "inclusion_status": sample.inclusion_status,
                "species_latin_name": sample.species_latin_name,
                "species_common_name": sample.species_common_name,
                "source_family": sample.source_family,
                "source_release": sample.source_release,
                "record_modality": sample.record_modality,
                "review_strength": sample.review_strength,
                "provenance_quality": sample.provenance_quality,
                "publication": sample.publication,
                "paper_doi": sample.paper_doi,
                "paper_url": sample.paper_url,
                "supplementary_source": sample.supplementary_source,
                "site_label": site_label,
                "political_entity": "" if sample.political_entity is None else sample.political_entity,
                "latitude": "" if sample.latitude is None else sample.latitude,
                "longitude": "" if sample.longitude is None else sample.longitude,
                "latitude_text": sample.latitude_text,
                "longitude_text": sample.longitude_text,
                "coordinate_confidence": sample.coordinate_confidence,
                "chronology_text": sample.time_label,
                "time_start_bp": "" if sample.time_start_bp is None else sample.time_start_bp,
                "time_end_bp": "" if sample.time_end_bp is None else sample.time_end_bp,
                "time_mean_bp": "" if sample.time_mean_bp is None else sample.time_mean_bp,
                "dating_basis": sample.dating_basis,
                "inclusion_note": sample.inclusion_note,
            }
        )
    return _render_csv(fieldnames, rows)


def _sample_records_payload(bundle: object) -> dict[str, object]:
    return {
        "schema_version": "adna-sample-record-export.v1",
        "species_latin_name": bundle.species.latin_name,
        "samples": [record.as_dict() for record in bundle.sample_records],
    }


def _project_summaries_payload(bundle: object) -> dict[str, object]:
    return {
        "schema_version": "adna-project-summary-export.v1",
        "species_latin_name": bundle.species.latin_name,
        "projects": [summary.as_dict() for summary in bundle.project_summaries],
    }


def _render_locality_summaries_csv(bundle: object) -> str:
    fieldnames = (
        "locality_token",
        "species_latin_name",
        "species_common_name",
        "project_accessions",
        "source_family",
        "source_releases",
        "record_modalities",
        "review_strengths",
        "provenance_qualities",
        "original_location_text",
        "locality",
        "political_entity",
        "latitude",
        "longitude",
        "latitude_text",
        "longitude_text",
        "coordinate_confidence",
        "chronology_text",
        "time_start_bp",
        "time_end_bp",
        "time_mean_bp",
        "dating_basis",
        "nordic_inclusion",
        "nordic_inclusion_reason",
        "interpretation_note",
    )
    rows = []
    for summary in bundle.locality_records:
        rows.append(
            {
                "locality_token": summary.locality_token,
                "species_latin_name": summary.species_latin_name,
                "species_common_name": summary.species_common_name,
                "project_accessions": ";".join(summary.project_accessions),
                "source_family": summary.source_family,
                "source_releases": ";".join(summary.source_releases),
                "record_modalities": ";".join(summary.record_modalities),
                "review_strengths": ";".join(summary.review_strengths),
                "provenance_qualities": ";".join(summary.provenance_qualities),
                "original_location_text": summary.original_location_text,
                "locality": "" if summary.locality is None else summary.locality,
                "political_entity": ""
                if summary.identity.political_entity is None
                else summary.identity.political_entity,
                "latitude": "" if summary.latitude is None else summary.latitude,
                "longitude": "" if summary.longitude is None else summary.longitude,
                "latitude_text": summary.latitude_text,
                "longitude_text": summary.longitude_text,
                "coordinate_confidence": summary.coordinate_confidence,
                "chronology_text": summary.time_label,
                "time_start_bp": ""
                if summary.time_start_bp is None
                else summary.time_start_bp,
                "time_end_bp": "" if summary.time_end_bp is None else summary.time_end_bp,
                "time_mean_bp": ""
                if summary.time_mean_bp is None
                else summary.time_mean_bp,
                "dating_basis": summary.dating_basis,
                "nordic_inclusion": str(summary.nordic_inclusion).lower(),
                "nordic_inclusion_reason": summary.nordic_inclusion_reason,
                "interpretation_note": summary.interpretation_note,
            }
        )
    return _render_csv(fieldnames, rows)


def _locality_summaries_payload(bundle: object) -> dict[str, object]:
    return {
        "schema_version": "adna-locality-summary-export.v1",
        "species_latin_name": bundle.species.latin_name,
        "localities": [summary.as_dict() for summary in bundle.locality_records],
    }


def _render_species_root_readme(species_name: str) -> str:
    species = resolve_species_definition(species_name)
    review = build_species_dataset_review(species_name)
    curation = build_species_curation_manifest(species_name)
    return (
        f"# {species.common_name}\n\n"
        f"- Latin name: `{species.latin_name}`\n"
        f"- Product role: `{review.product_role}`\n"
        f"- Dataset bucket: `{review.dataset_bucket}`\n"
        f"- Curation class: `{curation.curation_class}`\n"
        f"- Curated projects: `{len(curation.curated_projects)}`\n"
        f"- Pending projects: `{len(curation.pending_projects)}`\n"
        f"- Rejected projects: `{len(curation.rejected_projects)}`\n\n"
        "This species root is a tracked repository surface. `raw/` keeps archive "
        "inventory artifacts and source wording snapshots, `normalized/` keeps sample-level, project-level, and locality-level normalized outputs, "
        "`manifests/` keeps species and citation manifests, `reports/` keeps support "
        "summaries, and `review/` keeps reader-facing review packets.\n"
    )


def _render_support_summary_markdown(species_name: str) -> str:
    species = resolve_species_definition(species_name)
    review = build_species_dataset_review(species_name)
    curation = build_species_curation_manifest(species_name)
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
        f"- Eligible for supported status: `{str(review.eligible_for_supported_status).lower()}`\n\n"
        f"{curation.support_statement}\n\n"
        "## Blocking reasons\n\n"
        + (
            "\n".join(f"- `{reason}`" for reason in review.blocking_reasons)
            if review.blocking_reasons
            else "- none\n"
        )
        + "\n"
    )


def _render_review_packet_markdown(species_name: str) -> str:
    species = resolve_species_definition(species_name)
    packet = build_species_review_packet(species_name)
    lines = [
        f"# {species.common_name} species review",
        "",
        f"- Species: `{species.latin_name}`",
        f"- Dataset bucket: `{packet.dataset_review.dataset_bucket}`",
        f"- Product role: `{packet.dataset_review.product_role}`",
        "",
        "## Release blockers",
        "",
    ]
    if packet.release_blockers:
        lines.extend(f"- `{reason}`" for reason in packet.release_blockers)
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
    for row in packet.project_manifest.projects:
        paper_doi = "" if row.paper_doi is None else row.paper_doi
        lines.append(
            f"| {row.project_accession} | {row.archive_status} | {row.ancient_status} | "
            f"{row.evidence_strength} | {paper_doi} | {row.domestication_scope} |"
        )
    lines.extend(
        _render_grouped_review_table(
            "Rejected projects",
            packet.rejected_projects,
        )
    )
    lines.extend(
        _render_grouped_review_table(
            "Ancient but still too weak",
            packet.too_weak_projects,
        )
    )
    lines.extend(
        _render_grouped_review_table(
            "Comparator-only projects",
            packet.comparator_projects,
        )
    )
    lines.extend(
        _render_grouped_review_table(
            "Nordic-relevant leads not yet mapped confidently",
            packet.nordic_unmapped_leads,
        )
    )
    lines.append("")
    return "\n".join(lines)


def _render_csv(fieldnames: tuple[str, ...], rows: list[dict[str, object]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def _render_grouped_review_table(title: str, rows: tuple[object, ...]) -> list[str]:
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


def _materialize_cross_species_adna_artifacts(output_root: Path) -> None:
    adna_root = output_root / "adna"
    adna_root.mkdir(parents=True, exist_ok=True)
    report_root = output_root.parent / "docs" / "report"
    bibliography_rows = build_cross_species_bibliography()
    archive_rows = build_cross_species_archive_inventory()
    freshness_rows = build_species_freshness_table()
    coverage_dashboard = build_cross_species_coverage_dashboard(output_root, report_root)
    product_audit = build_shipped_adna_product_audit(output_root, report_root)
    write_json(
        adna_root / "cross_species_bibliography.json",
        {"schema_version": "adna-cross-species-bibliography.v1", "rows": bibliography_rows},
    )
    write_text(
        adna_root / "cross_species_bibliography.csv",
        render_csv_rows(bibliography_rows),
    )
    write_json(
        adna_root / "cross_species_archive_inventory.json",
        {"schema_version": "adna-cross-species-archive-inventory.v1", "rows": archive_rows},
    )
    write_text(
        adna_root / "cross_species_archive_inventory.csv",
        render_csv_rows(archive_rows),
    )
    write_json(adna_root / "cross_species_freshness.json", {"rows": freshness_rows})
    write_text(
        adna_root / "cross_species_freshness.csv",
        render_csv_rows(freshness_rows),
    )
    write_json(adna_root / "cross_species_coverage_dashboard.json", coverage_dashboard)
    write_text(
        adna_root / "cross_species_coverage_dashboard.csv",
        render_csv_rows(tuple(coverage_dashboard["rows"])),
    )
    write_json(adna_root / "shipped_product_audit.json", product_audit)
