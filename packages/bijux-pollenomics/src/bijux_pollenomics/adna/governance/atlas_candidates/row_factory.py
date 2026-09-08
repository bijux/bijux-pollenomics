"""Construct published animal-atlas rows from reconciled source records."""

from __future__ import annotations

from typing import cast

from ....core.text import slugify
from .chronology import _atlas_public_chronology, _parse_chronology
from .models import AnimalAtlasEvidenceRow
from .sample_support import (
    _inclusion_notes_for,
    _inclusion_statuses_for,
    _sample_group_ids_for,
    _sample_record_ids_for,
    _source_native_taxonomy_for,
    _supplementary_sources_for,
)


def _build_evidence_row(
    *,
    species_slug: str,
    locality: dict[str, object],
    site_identity: dict[str, object],
    coordinates: dict[str, object],
    provenance: dict[str, object],
    site_evidence: dict[str, object],
    citation: dict[str, str],
    review: dict[str, str],
    animal_scope: str,
    project_accessions: tuple[str, ...],
    primary_project_accession: str,
    site_record_id: str,
    latitude: float,
    longitude: float,
    sample_rows: tuple[dict[str, object], ...],
) -> AnimalAtlasEvidenceRow:
    feature_token = slugify(site_record_id)
    evidence_token = slugify(
        f"{species_slug}:{primary_project_accession}:{site_record_id}"
    )
    paper_doi = str(citation.get("paper_doi") or review.get("paper_doi", ""))
    (
        source_native_taxon_labels,
        source_native_tax_ids,
        source_native_scientific_names,
        taxon_alignment_statuses,
    ) = _source_native_taxonomy_for(sample_rows)
    return AnimalAtlasEvidenceRow(
        feature_id=f"animal-atlas-feature:{feature_token}",
        evidence_row_id=f"animal-atlas-row:{evidence_token}",
        site_record_id=site_record_id,
        species_latin_name=str(locality.get("species_latin_name", "")),
        species_common_name=str(locality.get("species_common_name", "")),
        animal_scope=animal_scope,
        support_class=str(review.get("support_class", "mapped_locality")),
        support_note=str(review.get("reason", "")),
        locality=str(
            locality.get("locality") or site_identity.get("locality_text", "")
        ),
        political_entity=str(
            locality.get("political_entity")
            or site_identity.get("political_entity", "")
        ),
        latitude=latitude,
        longitude=longitude,
        latitude_text=str(coordinates.get("latitude_text", "")),
        longitude_text=str(coordinates.get("longitude_text", "")),
        coordinate_basis=str(provenance.get("coordinate_basis", "")),
        coordinate_confidence=str(provenance.get("coordinate_confidence", "")),
        geocoding_method=str(provenance.get("geocoding_method", "")),
        geocoder_or_gazetteer=str(provenance.get("geocoder_or_gazetteer", "")),
        confidence_rationale=str(provenance.get("confidence_rationale", "")),
        original_place_text=str(provenance.get("original_place_text", "")),
        resolved_place_text=str(provenance.get("resolved_place_text", "")),
        coordinate_source_artifact_path=str(provenance.get("source_artifact_path", "")),
        coordinate_source_locator=str(provenance.get("source_locator", "")),
        coordinate_supplementary_source=str(provenance.get("supplementary_source", "")),
        coordinate_support_gap_note=str(provenance.get("support_gap_note", "")),
        chronology=_atlas_public_chronology(
            _parse_chronology(locality.get("chronology", {}))
        ),
        project_accessions=project_accessions,
        primary_project_accession=primary_project_accession,
        sample_record_ids=_sample_record_ids_for(sample_rows),
        sample_group_ids=_sample_group_ids_for(sample_rows),
        source_native_taxon_labels=source_native_taxon_labels,
        source_native_tax_ids=source_native_tax_ids,
        source_native_scientific_names=source_native_scientific_names,
        taxon_alignment_statuses=taxon_alignment_statuses,
        sample_count=int(cast(str, locality.get("sample_count", 0) or 0)),
        sample_namespace=str(locality.get("sample_namespace", "")),
        inclusion_statuses=_inclusion_statuses_for(sample_rows),
        inclusion_notes=_inclusion_notes_for(sample_rows),
        paper_title=str(citation.get("paper_title") or review.get("paper_title", "")),
        paper_doi=paper_doi,
        publication_year=str(citation.get("publication_year", "")),
        journal_title=str(citation.get("journal_title", "")),
        paper_url=_paper_url_for(paper_doi),
        supplementary_sources=_supplementary_sources_for(
            sample_rows,
            provenance,
            site_evidence,
        ),
        source_artifact_path=str(site_evidence.get("source_artifact_path", "")),
        source_artifact_kind=str(site_evidence.get("source_artifact_kind", "")),
        source_locator=str(site_evidence.get("source_locator", "")),
        source_support_status=str(site_evidence.get("source_support_status", "")),
        exact_source_text=str(site_evidence.get("exact_source_text", "")),
        nordic_inclusion=bool(locality.get("nordic_inclusion", False)),
        nordic_inclusion_reason=str(locality.get("nordic_inclusion_reason", "")),
        interpretation_note=str(locality.get("interpretation_note", "")),
    )


def _paper_url_for(doi: str) -> str:
    return f"https://doi.org/{doi}" if doi else ""
