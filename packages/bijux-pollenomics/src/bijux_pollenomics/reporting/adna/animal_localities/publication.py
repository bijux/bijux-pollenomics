"""Deterministic GeoJSON, CSV, and JSON publication for animal atlas evidence."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from ..atlas_evidence_rows import AnimalAtlasEvidenceRow


def _write_feature_collection(
    path: Path,
    *,
    features: list[dict[str, object]],
    layer_key: str,
    layer_label: str,
    description: str,
) -> None:
    geojson_features = []
    for feature in features:
        geojson_features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [feature["longitude"], feature["latitude"]],
                },
                "properties": {
                    "name": feature["title"],
                    "feature_id": feature["feature_id"],
                    "evidence_row_id": feature["evidence_row_id"],
                    "site_record_id": feature["site_record_id"],
                    "category": feature["subtitle"],
                    "country": feature["country"],
                    "layer_key": layer_key,
                    "layer_label": layer_label,
                    "source_url": feature["source_url"],
                    "popup_rows": feature["popup_rows"],
                    "species_latin_name": feature["species_latin_name"],
                    "species_common_name": feature["species_common_name"],
                    "animal_scope": feature["animal_scope"],
                    "support_class": feature["support_class"],
                    "temporal_semantics": feature["temporal_semantics"],
                    "temporal_window_key": feature["temporal_window_key"],
                    "temporal_window_label": feature["temporal_window_label"],
                    "temporal_comparability_posture": feature[
                        "temporal_comparability_posture"
                    ],
                    "temporal_comparison_note": feature["temporal_comparison_note"],
                    "nordic_inclusion": feature["nordic_inclusion"],
                    "nordic_inclusion_reason": feature["nordic_inclusion_reason"],
                    "coordinate_basis": feature["coordinate_basis"],
                    "coordinate_confidence": feature["coordinate_confidence"],
                    "sample_count": feature["sample_count"],
                    "sample_record_ids": feature["sample_record_ids"],
                    "sample_group_ids": feature["sample_group_ids"],
                    "source_native_taxon_labels": feature[
                        "source_native_taxon_labels"
                    ],
                    "source_native_tax_ids": feature["source_native_tax_ids"],
                    "source_native_scientific_names": feature[
                        "source_native_scientific_names"
                    ],
                    "taxon_alignment_statuses": feature[
                        "taxon_alignment_statuses"
                    ],
                    "sample_namespace": feature["sample_namespace"],
                    "inclusion_notes": feature["inclusion_notes"],
                    "latitude_text": feature["latitude_text"],
                    "longitude_text": feature["longitude_text"],
                    "geocoding_method": feature["geocoding_method"],
                    "geocoder_or_gazetteer": feature["geocoder_or_gazetteer"],
                    "confidence_rationale": feature["confidence_rationale"],
                    "original_place_text": feature["original_place_text"],
                    "resolved_place_text": feature["resolved_place_text"],
                    "paper_title": feature["paper_title"],
                    "paper_doi": feature["paper_doi"],
                    "journal_title": feature["journal_title"],
                    "publication_year": feature["publication_year"],
                    "supplementary_sources": feature["supplementary_sources"],
                    "project_accessions": feature["project_accessions"],
                    "primary_project_accession": feature["primary_project_accession"],
                    "inclusion_statuses": feature["inclusion_statuses"],
                    "source_artifact_path": feature["source_artifact_path"],
                    "source_artifact_kind": feature["source_artifact_kind"],
                    "source_locator": feature["source_locator"],
                    "source_support_status": feature["source_support_status"],
                    "exact_source_text": feature["exact_source_text"],
                    "time_start_bp": feature["time_start_bp"],
                    "time_end_bp": feature["time_end_bp"],
                    "time_mean_bp": feature["time_mean_bp"],
                    "time_year_bp": feature["time_year_bp"],
                    "time_label": feature["time_label"],
                },
            }
        )
    path.write_text(
        json.dumps(
            {
                "schema_version": "animal-atlas-locality-collection.v1",
                "type": "FeatureCollection",
                "layer_key": layer_key,
                "layer_label": layer_label,
                "subtitle": description,
                "features": geojson_features,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_animal_atlas_evidence_csv(
    path: Path,
    rows: tuple[AnimalAtlasEvidenceRow, ...],
) -> None:
    fieldnames = (
        "feature_id",
        "evidence_row_id",
        "site_record_id",
        "species_latin_name",
        "species_common_name",
        "animal_scope",
        "support_class",
        "locality",
        "political_entity",
        "latitude",
        "longitude",
        "coordinate_basis",
        "coordinate_confidence",
        "sample_count",
        "sample_record_ids",
        "source_native_taxon_labels",
        "source_native_tax_ids",
        "source_native_scientific_names",
        "taxon_alignment_statuses",
        "project_accessions",
        "paper_doi",
        "supplementary_sources",
        "time_label",
        "nordic_inclusion",
    )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "feature_id": row.feature_id,
                    "evidence_row_id": row.evidence_row_id,
                    "site_record_id": row.site_record_id,
                    "species_latin_name": row.species_latin_name,
                    "species_common_name": row.species_common_name,
                    "animal_scope": row.animal_scope,
                    "support_class": row.support_class,
                    "locality": row.locality,
                    "political_entity": row.political_entity,
                    "latitude": row.latitude,
                    "longitude": row.longitude,
                    "coordinate_basis": row.coordinate_basis,
                    "coordinate_confidence": row.coordinate_confidence,
                    "sample_count": row.sample_count,
                    "sample_record_ids": ";".join(row.sample_record_ids),
                    "source_native_taxon_labels": ";".join(
                        row.source_native_taxon_labels
                    ),
                    "source_native_tax_ids": ";".join(row.source_native_tax_ids),
                    "source_native_scientific_names": ";".join(
                        row.source_native_scientific_names
                    ),
                    "taxon_alignment_statuses": ";".join(
                        row.taxon_alignment_statuses
                    ),
                    "project_accessions": ";".join(row.project_accessions),
                    "paper_doi": row.paper_doi,
                    "supplementary_sources": ";".join(row.supplementary_sources),
                    "time_label": row.chronology.original_text,
                    "nordic_inclusion": str(row.nordic_inclusion).lower(),
                }
            )


def _write_animal_atlas_evidence_json(
    path: Path,
    rows: tuple[AnimalAtlasEvidenceRow, ...],
) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "animal-atlas-evidence-rows.v1",
                "rows": [row.as_dict() for row in rows],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_animal_point_traceability_json(
    path: Path,
    rows: tuple[AnimalAtlasEvidenceRow, ...],
) -> None:
    payload = {
        "schema_version": "animal-atlas-point-traceability.v1",
        "rows": [
            {
                "feature_id": row.feature_id,
                "evidence_row_id": row.evidence_row_id,
                "site_record_id": row.site_record_id,
                "species_latin_name": row.species_latin_name,
                "primary_project_accession": row.primary_project_accession,
                "sample_record_ids": list(row.sample_record_ids),
                "sample_group_ids": list(row.sample_group_ids),
                "source_native_taxon_labels": list(row.source_native_taxon_labels),
                "taxon_alignment_statuses": list(row.taxon_alignment_statuses),
                "sample_count": row.sample_count,
                "coordinate_basis": row.coordinate_basis,
                "coordinate_confidence": row.coordinate_confidence,
                "source_artifact_path": row.source_artifact_path,
                "source_locator": row.source_locator,
                "paper_doi": row.paper_doi,
                "supplementary_sources": list(row.supplementary_sources),
            }
            for row in rows
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
