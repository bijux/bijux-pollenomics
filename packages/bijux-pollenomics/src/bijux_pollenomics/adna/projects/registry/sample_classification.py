from __future__ import annotations


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
    if nordic_relevance in {
        "nordic_relevant_mapped",
        "nordic_relevant_unmapped",
    }:
        return "nordic_lead_site_curated"
    return "site_curated"


def _data_type_for(accession_scope: str, *, sample_basis: str) -> str:
    if sample_basis == "supplementary_table_sample_label_anchor":
        return "supplementary_table_sample_context"
    if accession_scope == "sample":
        return "archive_sample_context"
    if accession_scope == "accession_range":
        return "archive_accession_range_context"
    return "archive_project_context"
