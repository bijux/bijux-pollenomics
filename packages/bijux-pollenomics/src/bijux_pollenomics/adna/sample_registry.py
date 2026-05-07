from __future__ import annotations

from dataclasses import dataclass

from .ena import build_species_archive_projects
from .project_context import resolve_project_context
from .project_localities import resolve_project_locality_leads
from .species import resolve_species_definition

__all__ = [
    "AdnaCuratedSampleRow",
    "build_species_curated_sample_rows",
]


@dataclass(frozen=True)
class AdnaCuratedSampleRow:
    """One curated accession-backed animal aDNA sample-master row."""

    species_latin_name: str
    species_common_name: str
    stable_sample_id: str
    project_accession: str
    sample_basis: str
    source_family: str
    source_release: str
    record_modality: str
    review_strength: str
    provenance_quality: str
    site_label: str
    political_entity: str | None
    latitude_text: str
    longitude_text: str
    coordinate_basis: str
    chronology_text: str
    time_start_bp: int | None
    time_end_bp: int | None
    dating_basis: str
    publication: str
    publication_year: str
    paper_doi: str
    paper_url: str
    supplementary_source: str
    inclusion_status: str
    inclusion_note: str
    data_type: str

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "species_common_name": self.species_common_name,
            "stable_sample_id": self.stable_sample_id,
            "project_accession": self.project_accession,
            "sample_basis": self.sample_basis,
            "source_family": self.source_family,
            "source_release": self.source_release,
            "record_modality": self.record_modality,
            "review_strength": self.review_strength,
            "provenance_quality": self.provenance_quality,
            "site_label": self.site_label,
            "political_entity": self.political_entity,
            "latitude_text": self.latitude_text,
            "longitude_text": self.longitude_text,
            "coordinate_basis": self.coordinate_basis,
            "chronology_text": self.chronology_text,
            "time_start_bp": self.time_start_bp,
            "time_end_bp": self.time_end_bp,
            "dating_basis": self.dating_basis,
            "publication": self.publication,
            "publication_year": self.publication_year,
            "paper_doi": self.paper_doi,
            "paper_url": self.paper_url,
            "supplementary_source": self.supplementary_source,
            "inclusion_status": self.inclusion_status,
            "inclusion_note": self.inclusion_note,
            "data_type": self.data_type,
        }


_SUPPLEMENTARY_SOURCE_BY_DOI: dict[str, str] = {
    "10.1038/s42003-021-02794-8": (
        "data/adna/source_library/papers/10.1038-s42003-021-02794-8/"
        "supplementary/42003_2021_2794_MOESM4_ESM.zip"
    ),
}


def build_species_curated_sample_rows(
    species_name: str,
) -> tuple[AdnaCuratedSampleRow, ...]:
    """Build the species-owned accession-backed sample master rows."""
    species = resolve_species_definition(species_name)
    rows: list[AdnaCuratedSampleRow] = []
    for project in build_species_archive_projects(species_name):
        linkage = project.paper_linkage
        leads = resolve_project_locality_leads(project.project_accession)
        lead = leads[0] if leads else None
        project_context = resolve_project_context(project)
        sample_basis = _sample_basis_for(project.accession_scope)
        paper_doi = "" if linkage is None or linkage.doi is None else linkage.doi
        paper_url = f"https://doi.org/{paper_doi}" if paper_doi else ""
        if lead is None:
            site_label = "site detail not yet extracted from tracked source support"
            political_entity = None
            latitude_text = ""
            longitude_text = ""
            coordinate_basis = "withheld_site_detail_unextracted"
            chronology_text = "chronology not yet extracted from tracked source support"
            time_start_bp = None
            time_end_bp = None
            inclusion_status = "sample_context_blocked"
            inclusion_note = (
                "This accession-backed sample row is curated into the species master table, "
                "but site and chronology extraction are still blocked until a project-owned "
                "site evidence row is curated from paper or supplementary support."
            )
        else:
            site_label = lead.locality_text
            political_entity = lead.political_entity
            latitude_text = lead.latitude_text
            longitude_text = lead.longitude_text
            coordinate_basis = lead.coordinate_basis
            chronology_text = lead.chronology_text
            time_start_bp = lead.time_start_bp
            time_end_bp = lead.time_end_bp
            inclusion_status = _inclusion_status_for(project.archive_status, project_context.nordic_relevance)
            inclusion_note = lead.interpretation_note
        rows.append(
            AdnaCuratedSampleRow(
                species_latin_name=species.latin_name,
                species_common_name=species.common_name,
                stable_sample_id=project.project_accession,
                project_accession=project.project_accession,
                sample_basis=sample_basis,
                source_family=project.source_family,
                source_release=project.project_accession,
                record_modality=_record_modality_for(project),
                review_strength=_review_strength_for(project.archive_status, bool(paper_doi)),
                provenance_quality=_provenance_quality_for(project.accession_scope, lead is not None),
                site_label=site_label,
                political_entity=political_entity,
                latitude_text=latitude_text,
                longitude_text=longitude_text,
                coordinate_basis=coordinate_basis,
                chronology_text=chronology_text,
                time_start_bp=time_start_bp,
                time_end_bp=time_end_bp,
                dating_basis=project.dating_basis or "unknown",
                publication="" if linkage is None else linkage.paper_title,
                publication_year="" if linkage is None or linkage.publication_year is None else str(linkage.publication_year),
                paper_doi=paper_doi,
                paper_url=paper_url,
                supplementary_source=_SUPPLEMENTARY_SOURCE_BY_DOI.get(paper_doi, ""),
                inclusion_status=inclusion_status,
                inclusion_note=inclusion_note,
                data_type=_data_type_for(project.accession_scope),
            )
        )
    rows.sort(key=lambda item: (item.project_accession, item.stable_sample_id))
    return tuple(rows)


def _sample_basis_for(accession_scope: str) -> str:
    if accession_scope == "sample":
        return "sample_accession_anchor"
    if accession_scope == "accession_range":
        return "accession_range_anchor"
    return "project_accession_anchor"


def _review_strength_for(archive_status: str, has_paper_doi: bool) -> str:
    if archive_status == "comparator_only":
        return "comparator_only"
    if has_paper_doi:
        return "primary_paper_pinned"
    return "archive_verified_needs_paper_pinning"


def _provenance_quality_for(accession_scope: str, has_site_curation: bool) -> str:
    if accession_scope == "sample" and has_site_curation:
        return "archive_project_catalog"
    return "manual_curation_only"


def _record_modality_for(project: object) -> str:
    target = (getattr(project, "sequencing_target", None) or "").casefold()
    if "mitogenome" in target:
        return "mitogenome_only"
    return "archive_reads"


def _inclusion_status_for(archive_status: str, nordic_relevance: str) -> str:
    if archive_status == "comparator_only":
        return "comparator_site_curated"
    if nordic_relevance == "nordic_relevant_unmapped":
        return "nordic_lead_site_curated"
    return "site_curated"


def _data_type_for(accession_scope: str) -> str:
    if accession_scope == "sample":
        return "archive_sample_context"
    if accession_scope == "accession_range":
        return "archive_accession_range_context"
    return "archive_project_context"
