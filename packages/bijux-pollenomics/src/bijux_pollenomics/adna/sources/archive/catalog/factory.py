from __future__ import annotations

from ..contracts import AdnaArchiveProject, AdnaPaperLinkage
from .urls import _metadata_url_for


def _paper(
    *,
    paper_title: str,
    pinning_evidence: str,
    doi: str | None = None,
    pubmed_id: str | None = None,
    pmc_id: str | None = None,
    journal_title: str | None = None,
    publication_year: int | None = None,
    reference_kind: str = "primary_paper",
) -> AdnaPaperLinkage:
    return AdnaPaperLinkage(
        paper_title=paper_title,
        doi=doi,
        pubmed_id=pubmed_id,
        pmc_id=pmc_id,
        journal_title=journal_title,
        publication_year=publication_year,
        reference_kind=reference_kind,
        pinning_evidence=pinning_evidence,
    )


def _project(
    species_latin_name: str,
    accession: str,
    *,
    source_family: str = "ENA",
    accession_scope: str = "project",
    archive_status: str,
    notes: str,
    paper_linkage: AdnaPaperLinkage | None = None,
    ancient_status: str,
    sequencing_target: str,
    material_basis: str,
    dating_basis: str,
    geographic_basis: str,
    result_kind: str = "read_run",
    access_policy: str = "public_downloadable",
    public_release_date: str | None = None,
    domestication_scope: str = "domesticated_core",
) -> AdnaArchiveProject:
    return AdnaArchiveProject(
        species_latin_name=species_latin_name,
        project_accession=accession,
        result_kind=result_kind,
        metadata_url=_metadata_url_for(
            accession=accession,
            source_family=source_family,
            accession_scope=accession_scope,
            result_kind=result_kind,
        ),
        source_family=source_family,
        accession_scope=accession_scope,
        archive_status=archive_status,
        notes=notes,
        paper_linkage=paper_linkage,
        ancient_status=ancient_status,
        sequencing_target=sequencing_target,
        material_basis=material_basis,
        dating_basis=dating_basis,
        geographic_basis=geographic_basis,
        access_policy=access_policy,
        public_release_date=public_release_date,
        domestication_scope=domestication_scope,
    )
