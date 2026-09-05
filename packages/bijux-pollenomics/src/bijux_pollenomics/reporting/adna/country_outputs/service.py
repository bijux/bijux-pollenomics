from __future__ import annotations

from pathlib import Path

from ..atlas_evidence_rows import build_tracked_animal_atlas_evidence_rows
from .models import CountryAnimalOutputBundle
from .projection.assignment import assign_evidence_row_to_country, assignment_sort_key
from .projection.citations import build_citation_rows
from .projection.samples import build_sample_rows, load_country_sample_lookup
from .projection.species import build_species_rows
from .projection.summaries import (
    build_evidence_quality_summary,
    build_traceability_summary,
    published_chronology_value,
)
from .projection.warnings import build_warning_rows


def build_country_animal_output_bundle(
    *,
    data_root: Path,
    country: str,
    version: str,
    generated_on: str,
) -> CountryAnimalOutputBundle:
    """Assign tracked animal atlas evidence rows into one governed country bundle."""
    evidence_rows = build_tracked_animal_atlas_evidence_rows(data_root)
    sample_lookup = load_country_sample_lookup(Path(data_root))
    locality_rows: list[dict[str, object]] = []
    for row in evidence_rows:
        assignment = assign_evidence_row_to_country(row, country)
        if assignment is None:
            continue
        temporal_semantics = row.chronology.as_temporal_semantics(
            source_family="animal_adna",
            provenance_path=row.source_artifact_path,
            provenance_locator=row.source_locator,
            provenance_excerpt=row.exact_source_text,
        )
        locality_rows.append(
            {
                "country": country,
                "feature_id": row.feature_id,
                "evidence_row_id": row.evidence_row_id,
                "site_record_id": row.site_record_id,
                "species_latin_name": row.species_latin_name,
                "species_common_name": row.species_common_name,
                "animal_scope": row.animal_scope,
                "project_accession": row.primary_project_accession,
                "project_accessions": list(row.project_accessions),
                "support_class": row.support_class,
                "locality": row.locality,
                "political_entity": row.political_entity,
                "country_assignment_confidence": assignment["confidence"],
                "country_assignment_reason": assignment["reason"],
                "latitude": row.latitude,
                "longitude": row.longitude,
                "latitude_text": row.latitude_text,
                "longitude_text": row.longitude_text,
                "coordinate_basis": row.coordinate_basis,
                "coordinate_confidence": row.coordinate_confidence,
                "geocoding_method": row.geocoding_method,
                "geocoder_or_gazetteer": row.geocoder_or_gazetteer,
                "confidence_rationale": row.confidence_rationale,
                "original_place_text": row.original_place_text,
                "resolved_place_text": row.resolved_place_text,
                "coordinate_source_artifact_path": row.coordinate_source_artifact_path,
                "coordinate_source_locator": row.coordinate_source_locator,
                "coordinate_supplementary_source": row.coordinate_supplementary_source,
                "coordinate_support_gap_note": row.coordinate_support_gap_note,
                "time_start_bp": published_chronology_value(
                    row.chronology.time_start_bp,
                    row.chronology.precision_posture,
                ),
                "time_end_bp": published_chronology_value(
                    row.chronology.time_end_bp,
                    row.chronology.precision_posture,
                ),
                "time_mean_bp": published_chronology_value(
                    row.chronology.time_mean_bp,
                    row.chronology.precision_posture,
                ),
                "time_label": row.chronology.original_text,
                "temporal_semantics": temporal_semantics,
                "temporal_window_key": temporal_semantics["temporal_window_key"],
                "temporal_window_label": temporal_semantics["temporal_window_label"],
                "temporal_comparability_posture": temporal_semantics[
                    "comparability_posture"
                ],
                "temporal_comparison_note": temporal_semantics["comparison_note"],
                "dating_basis": row.chronology.dating_basis,
                "chronology_evidence_class": row.chronology.evidence_class,
                "chronology_precision_posture": row.chronology.precision_posture,
                "nordic_inclusion": row.nordic_inclusion,
                "nordic_inclusion_reason": row.nordic_inclusion_reason,
                "interpretation_note": row.interpretation_note,
                "paper_title": row.paper_title,
                "paper_doi": row.paper_doi,
                "publication_year": row.publication_year,
                "journal_title": row.journal_title,
                "source_url": row.paper_url,
                "sample_count": row.sample_count,
                "sample_record_ids": list(row.sample_record_ids),
                "sample_group_ids": list(row.sample_group_ids),
                "sample_namespace": row.sample_namespace,
                "inclusion_statuses": list(row.inclusion_statuses),
                "inclusion_notes": list(row.inclusion_notes),
                "supplementary_sources": list(row.supplementary_sources),
                "source_artifact_path": row.source_artifact_path,
                "source_artifact_kind": row.source_artifact_kind,
                "source_locator": row.source_locator,
                "source_support_status": row.source_support_status,
                "exact_source_text": row.exact_source_text,
            }
        )

    locality_rows.sort(
        key=lambda row: (
            str(row["species_latin_name"]),
            assignment_sort_key(str(row["country_assignment_confidence"])),
            -(
                int(row["time_start_bp"])
                if isinstance(row["time_start_bp"], int)
                else 0
            ),
            str(row["locality"]),
        )
    )
    sample_rows = build_sample_rows(country, locality_rows, sample_lookup)
    species_rows = build_species_rows(country, locality_rows, sample_rows)
    citations = build_citation_rows(country, locality_rows, sample_rows)
    warnings = build_warning_rows(country, locality_rows, sample_rows, species_rows)
    evidence_quality_summary = build_evidence_quality_summary(
        sample_rows=sample_rows,
        species_rows=species_rows,
    )
    traceability_summary = build_traceability_summary(
        sample_rows=sample_rows,
        locality_rows=locality_rows,
    )
    return CountryAnimalOutputBundle(
        country=country,
        version=version,
        generated_on=generated_on,
        sample_rows=tuple(sample_rows),
        species_rows=tuple(species_rows),
        localities=tuple(locality_rows),
        citations=tuple(citations),
        warnings=tuple(warnings),
        evidence_quality_summary=evidence_quality_summary,
        traceability_summary=traceability_summary,
    )
