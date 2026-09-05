from __future__ import annotations

from dataclasses import dataclass
from typing import Final


ADNA_ACCESSION_SCOPES: Final[tuple[str, ...]] = (
    "project",
    "sample",
    "accession_range",
)


ADNA_ACCESS_POLICIES: Final[tuple[str, ...]] = (
    "public_downloadable",
    "embargoed_until_release_date",
    "restricted_access",
    "delayed_release_unverified",
)


ADNA_DOMESTICATION_SCOPES: Final[tuple[str, ...]] = (
    "domesticated_core",
    "wild_or_progenitor_context",
    "ancient_comparator",
    "modern_or_irrelevant",
)


ADNA_PROJECT_EVIDENCE_STRENGTHS: Final[tuple[str, ...]] = (
    "primary_paper_pinned",
    "archive_only",
    "paper_only",
    "secondary_reference_only",
    "manual_note_only",
)


@dataclass(frozen=True)
class AdnaPaperLinkage:
    """Primary or secondary literature anchor for one curated ancient-DNA archive row."""

    paper_title: str
    doi: str | None = None
    pubmed_id: str | None = None
    pmc_id: str | None = None
    journal_title: str | None = None
    publication_year: int | None = None
    reference_kind: str = "primary_paper"
    pinning_evidence: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "paper_title": self.paper_title,
            "doi": self.doi,
            "pubmed_id": self.pubmed_id,
            "pmc_id": self.pmc_id,
            "journal_title": self.journal_title,
            "publication_year": self.publication_year,
            "reference_kind": self.reference_kind,
            "pinning_evidence": self.pinning_evidence,
        }


@dataclass(frozen=True)
class AdnaArchiveProject:
    """Species-aware archive project catalog entry for domesticated-animal aDNA."""

    species_latin_name: str
    project_accession: str
    result_kind: str
    metadata_url: str
    source_family: str
    accession_scope: str
    archive_status: str
    notes: str
    paper_linkage: AdnaPaperLinkage | None = None
    ancient_status: str = "archive_unreviewed"
    sequencing_target: str | None = None
    material_basis: str | None = None
    dating_basis: str | None = None
    geographic_basis: str | None = None
    access_policy: str = "public_downloadable"
    public_release_date: str | None = None
    domestication_scope: str = "domesticated_core"

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "project_accession": self.project_accession,
            "result_kind": self.result_kind,
            "metadata_url": self.metadata_url,
            "source_family": self.source_family,
            "accession_scope": self.accession_scope,
            "archive_status": self.archive_status,
            "notes": self.notes,
            "paper_linkage": None
            if self.paper_linkage is None
            else self.paper_linkage.as_dict(),
            "ancient_status": self.ancient_status,
            "sequencing_target": self.sequencing_target,
            "material_basis": self.material_basis,
            "dating_basis": self.dating_basis,
            "geographic_basis": self.geographic_basis,
            "access_policy": self.access_policy,
            "public_release_date": self.public_release_date,
            "domestication_scope": self.domestication_scope,
            "evidence_strength": classify_archive_project_evidence(self),
        }


def classify_archive_project_evidence(project: AdnaArchiveProject) -> str:
    """Classify how strongly one archive row is pinned to real scientific evidence."""
    has_archive = bool(project.metadata_url)
    linkage = project.paper_linkage
    if linkage is None:
        if has_archive:
            return "archive_only"
        return "manual_note_only"
    if linkage.reference_kind == "secondary_reference":
        return "secondary_reference_only"
    if has_archive:
        return "primary_paper_pinned"
    return "paper_only"
