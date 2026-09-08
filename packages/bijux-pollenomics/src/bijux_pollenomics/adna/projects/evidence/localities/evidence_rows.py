from __future__ import annotations

from functools import cache
from pathlib import Path

from ...registry.sites import build_project_sample_site_rows
from .semantics import (
    _classify_sample_site_row,
    _geocoding_safe_token,
    _locality_evidence_bucket,
    _normalized_display_spelling,
    _source_surface_for_packet,
)


@cache
def build_project_sample_locality_evidence_rows(
    output_root: Path,
    project_accession: str,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for row in build_project_sample_site_rows(output_root, project_accession):
        locality_class = _classify_sample_site_row(row)
        rows.append(
            {
                "project_accession": row.project_accession,
                "species_latin_name": row.species_latin_name,
                "species_common_name": row.species_common_name,
                "repo_stable_sample_id": row.repo_stable_sample_id,
                "preferred_sample_label": row.preferred_sample_label,
                "sample_basis": row.sample_basis,
                "sample_evidence_status": row.sample_evidence_status,
                "sample_identity_resolution": row.sample_identity_resolution,
                "sample_ambiguity_note": row.sample_ambiguity_note,
                "assigned_locality_text": row.locality_text,
                "locality_resolution_status": row.locality_resolution_status,
                "assigned_locality_class": locality_class,
                "normalized_display_spelling": _normalized_display_spelling(
                    row.locality_text,
                    row.site_name,
                ),
                "geocoding_safe_token": _geocoding_safe_token(
                    _normalized_display_spelling(row.locality_text, row.site_name)
                ),
                "site_name": row.site_name,
                "municipality_name": row.municipality_name,
                "region_name": row.region_name,
                "country_name": row.country_name,
                "broader_geography": row.broader_geography,
                "evidence_source_surface": _source_surface_for_packet(row),
                "location_evidence_artifact_path": row.location_evidence_artifact_path,
                "location_evidence_artifact_kind": row.location_evidence_artifact_kind,
                "location_evidence_locator": row.location_evidence_locator,
                "location_evidence_text": row.location_evidence_text,
                "coordinate_basis": row.coordinate_basis,
                "coordinate_mapping_posture": row.coordinate_mapping_posture,
                "coordinate_confidence": row.coordinate_confidence,
                "chronology_text": row.chronology_text,
                "locality_evidence_bucket": _locality_evidence_bucket(
                    locality_class=locality_class,
                    locality_resolution_status=row.locality_resolution_status,
                ),
                "review_note": row.review_note,
            }
        )
    rows.sort(
        key=lambda item: (
            str(item["project_accession"]),
            str(item["repo_stable_sample_id"]),
        )
    )
    return tuple(rows)
