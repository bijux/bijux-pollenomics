from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.adna.species.tracked_species import TRACKED_ADNA_SPECIES
from .repository import (
    _load_coordinate_provenance_rows,
    _load_sample_rows,
    _species_root,
)


def build_unresolved_site_ledger(data_root: Path) -> tuple[dict[str, object], ...]:
    """List accession-backed sample rows whose site context is still unresolved."""
    rows: list[dict[str, object]] = []
    for species_name in TRACKED_ADNA_SPECIES:
        species_root = _species_root(Path(data_root), species_name)
        for sample in _load_sample_rows(species_root):
            if str(sample.get("inclusion_status", "")) != "sample_context_blocked":
                continue
            rows.append(
                {
                    "species_latin_name": sample.get("species_latin_name", ""),
                    "species_common_name": sample.get("species_common_name", ""),
                    "project_accession": sample.get("project_accession", ""),
                    "stable_sample_id": sample.get("identity", {}).get(
                        "stable_token", ""
                    ),
                    "site_label": sample.get("locality_identity", {}).get(
                        "locality_text", ""
                    ),
                    "paper_doi": sample.get("paper_doi", ""),
                    "supplementary_source": sample.get("supplementary_source", ""),
                    "inclusion_note": sample.get("inclusion_note", ""),
                }
            )
    return tuple(
        sorted(
            rows,
            key=lambda item: (
                str(item["species_latin_name"]),
                str(item["project_accession"]),
            ),
        )
    )


def build_overbroad_site_ledger(data_root: Path) -> tuple[dict[str, object], ...]:
    """List curated site leads refused from point mapping because geography is too broad."""
    rows: list[dict[str, object]] = []
    for species_name in TRACKED_ADNA_SPECIES:
        species_root = _species_root(Path(data_root), species_name)
        for provenance in _load_coordinate_provenance_rows(species_root):
            if str(provenance.get("mapping_posture", "")) != "refused_region_only":
                continue
            rows.append(
                {
                    "species_latin_name": provenance.get("species_latin_name", ""),
                    "species_common_name": provenance.get("species_common_name", ""),
                    "project_accession": provenance.get("project_accession", ""),
                    "site_label": provenance.get("site_label", ""),
                    "original_place_text": provenance.get("original_place_text", ""),
                    "resolved_place_text": provenance.get("resolved_place_text", ""),
                    "coordinate_basis": provenance.get("coordinate_basis", ""),
                    "confidence_rationale": provenance.get("confidence_rationale", ""),
                    "support_gap_note": provenance.get("support_gap_note", ""),
                }
            )
    return tuple(
        sorted(
            rows,
            key=lambda item: (
                str(item["species_latin_name"]),
                str(item["project_accession"]),
            ),
        )
    )


def build_coordinate_caveat_surface(data_root: Path) -> dict[str, object]:
    """Group current animal coordinate posture into reader-visible categories."""
    direct_coordinates: list[dict[str, object]] = []
    point_resolution: list[dict[str, object]] = []
    weak_geography: list[dict[str, object]] = []
    for species_name in TRACKED_ADNA_SPECIES:
        species_root = _species_root(Path(data_root), species_name)
        for provenance in _load_coordinate_provenance_rows(species_root):
            row = {
                "species_latin_name": provenance.get("species_latin_name", ""),
                "species_common_name": provenance.get("species_common_name", ""),
                "project_accession": provenance.get("project_accession", ""),
                "site_label": provenance.get("site_label", ""),
                "original_place_text": provenance.get("original_place_text", ""),
                "resolved_place_text": provenance.get("resolved_place_text", ""),
                "coordinate_basis": provenance.get("coordinate_basis", ""),
                "coordinate_confidence": provenance.get("coordinate_confidence", ""),
                "mapping_posture": provenance.get("mapping_posture", ""),
                "confidence_rationale": provenance.get("confidence_rationale", ""),
            }
            if str(provenance.get("mapping_posture", "")) == "mappable_point":
                if str(provenance.get("coordinate_basis", "")) in {
                    "direct_published_coordinates",
                    "supplementary_table_coordinates",
                    "archive_coordinates",
                }:
                    direct_coordinates.append(row)
                else:
                    point_resolution.append(row)
            else:
                weak_geography.append(row)
    return {
        "schema_version": "adna-coordinate-caveat-surface.v1",
        "direct_coordinates": direct_coordinates,
        "place_name_resolution": point_resolution,
        "still_weak_geography": weak_geography,
    }
