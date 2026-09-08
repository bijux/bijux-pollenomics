from __future__ import annotations

from bijux_pollenomics.adna.sources.archive import (
    AdnaArchiveProject,
    classify_archive_project_evidence,
)
from bijux_pollenomics.adna.sources.snapshots import (
    build_species_source_snapshots,
    resolve_archive_source_snapshot,
)

from .common import _render_csv


def _render_archive_inventory_csv(
    archive_projects: tuple[AdnaArchiveProject, ...],
) -> str:
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
                "paper_doi": ""
                if linkage is None or linkage.doi is None
                else linkage.doi,
                "journal_title": (
                    ""
                    if linkage is None or linkage.journal_title is None
                    else linkage.journal_title
                ),
                "publication_year": (
                    ""
                    if linkage is None or linkage.publication_year is None
                    else linkage.publication_year
                ),
                "sequencing_target": ""
                if project.sequencing_target is None
                else project.sequencing_target,
                "material_basis": ""
                if project.material_basis is None
                else project.material_basis,
                "dating_basis": ""
                if project.dating_basis is None
                else project.dating_basis,
                "geographic_basis": ""
                if project.geographic_basis is None
                else project.geographic_basis,
                "access_policy": project.access_policy,
                "public_release_date": ""
                if project.public_release_date is None
                else project.public_release_date,
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
    rows = [
        snapshot.as_dict() for snapshot in build_species_source_snapshots(species_name)
    ]
    return _render_csv(fieldnames, rows)


def _render_citation_manifest_csv(
    archive_projects: tuple[AdnaArchiveProject, ...],
) -> str:
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
                "paper_doi": ""
                if linkage is None or linkage.doi is None
                else linkage.doi,
                "pubmed_id": ""
                if linkage is None or linkage.pubmed_id is None
                else linkage.pubmed_id,
                "pmc_id": ""
                if linkage is None or linkage.pmc_id is None
                else linkage.pmc_id,
                "journal_title": (
                    ""
                    if linkage is None or linkage.journal_title is None
                    else linkage.journal_title
                ),
                "publication_year": (
                    ""
                    if linkage is None or linkage.publication_year is None
                    else linkage.publication_year
                ),
                "reference_kind": "" if linkage is None else linkage.reference_kind,
                "pinning_evidence": "" if linkage is None else linkage.pinning_evidence,
            }
        )
    return _render_csv(fieldnames, rows)
