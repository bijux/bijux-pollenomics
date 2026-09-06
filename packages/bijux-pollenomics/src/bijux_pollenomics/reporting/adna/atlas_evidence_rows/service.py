"""Select source-backed animal localities for atlas publication."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import cast

from ....adna import build_species_support_matrix
from ....adna.workflow.paths import adna_species_dir
from .chronology import (
    _atlas_chronology_supports_publication,
    _atlas_public_chronology,
    _optional_float,
    _parse_chronology,
)
from .models import AnimalAtlasEvidenceRow
from .row_factory import _build_evidence_row
from .sample_support import (
    _atlas_admitted_sample_rows,
    _sample_locality_token,
    _sample_record_ids_for,
)
from .source_records import (
    _load_citation_lookup,
    _load_coordinate_provenance_lookup,
    _load_locality_rows,
    _load_project_animal_scope_lookup,
    _load_review_lookup,
    _load_sample_rows,
    _load_site_evidence_lookup,
    _lookup_project_locality_row,
    _project_sample_animal_scope_for,
)
from .validation import _assert_no_project_level_flattening


def build_tracked_animal_atlas_evidence_rows(
    data_root: Path,
) -> tuple[AnimalAtlasEvidenceRow, ...]:
    """Build the exact set of animal rows eligible for atlas point publication."""
    rows: list[AnimalAtlasEvidenceRow] = []
    species_dir = adna_species_dir(Path(data_root))
    for species in build_species_support_matrix():
        if species.latin_name == "Homo sapiens":
            continue
        species_root = species_dir / species.slug
        if not species_root.is_dir():
            continue
        locality_rows = _load_locality_rows(species_root)
        sample_rows = _load_sample_rows(species_root)
        provenance_lookup = _load_coordinate_provenance_lookup(species_root)
        site_evidence_lookup = _load_site_evidence_lookup(species_root)
        citation_lookup = _load_citation_lookup(species_root)
        review_lookup = _load_review_lookup(species_root)
        project_scope_lookup = _load_project_animal_scope_lookup(species_root)
        for locality in locality_rows:
            project_accessions = tuple(
                str(item)
                for item in cast(
                    Iterable[object], locality.get("project_accessions", [])
                )
                if str(item).strip()
            )
            if not project_accessions:
                continue
            primary_project_accession = project_accessions[0]
            site_identity = locality.get("identity", {})
            if not isinstance(site_identity, dict):
                continue
            locality_label = str(
                locality.get("locality") or site_identity.get("locality_text", "")
            )
            provenance = _lookup_project_locality_row(
                provenance_lookup,
                project_accession=primary_project_accession,
                locality_text=locality_label,
            )
            if provenance is None:
                continue
            if str(provenance.get("mapping_posture", "")) != "mappable_point":
                continue
            coordinates = locality.get("coordinates", {})
            if not isinstance(coordinates, dict):
                continue
            latitude = _optional_float(coordinates.get("latitude"))
            longitude = _optional_float(coordinates.get("longitude"))
            if latitude is None or longitude is None:
                continue
            site_record_id = str(site_identity.get("stable_token", "")).strip()
            if not site_record_id:
                continue
            matched_sample_rows = _atlas_admitted_sample_rows(
                tuple(
                    row
                    for row in sample_rows
                    if str(row.get("project_accession", "")).strip()
                    in project_accessions
                    and _sample_locality_token(row) == site_record_id
                )
            )
            _assert_no_project_level_flattening(
                primary_project_accession=primary_project_accession,
                site_record_id=site_record_id,
                sample_rows=matched_sample_rows,
            )
            if not _sample_record_ids_for(matched_sample_rows):
                continue
            animal_scope = _project_sample_animal_scope_for(
                species_root,
                project_scope_lookup,
                project_accessions=project_accessions,
                sample_rows=matched_sample_rows,
            )
            if animal_scope is None:
                continue
            public_chronology = _atlas_public_chronology(
                _parse_chronology(locality.get("chronology", {}))
            )
            if not _atlas_chronology_supports_publication(public_chronology):
                continue
            site_evidence = _lookup_project_locality_row(
                site_evidence_lookup,
                project_accession=primary_project_accession,
                locality_text=locality_label,
            )
            if site_evidence is None:
                continue
            rows.append(
                _build_evidence_row(
                    species_slug=species.slug,
                    locality=locality,
                    site_identity=site_identity,
                    coordinates=coordinates,
                    provenance=provenance,
                    site_evidence=site_evidence,
                    citation=citation_lookup.get(primary_project_accession, {}),
                    review=review_lookup.get(primary_project_accession, {}),
                    animal_scope=animal_scope,
                    project_accessions=project_accessions,
                    primary_project_accession=primary_project_accession,
                    site_record_id=site_record_id,
                    latitude=latitude,
                    longitude=longitude,
                    sample_rows=matched_sample_rows,
                )
            )
    rows.sort(
        key=lambda row: (
            row.species_latin_name,
            not row.nordic_inclusion,
            row.primary_project_accession,
            row.site_record_id,
        )
    )
    return tuple(rows)
