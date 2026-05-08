from __future__ import annotations

from dataclasses import dataclass

from .coordinate_provenance import (
    build_species_coordinate_provenance_rows,
    resolve_project_coordinate_provenance,
)
from .site_evidence import build_species_site_evidence_rows, resolve_project_site_evidence

__all__ = [
    "AdnaProjectLocalityLead",
    "build_species_project_locality_leads",
    "resolve_project_locality_leads",
]


@dataclass(frozen=True)
class AdnaProjectLocalityLead:
    """Curated locality lead that anchors one project to one mappable context row."""

    project_accession: str
    locality_text: str
    political_entity: str
    latitude_text: str
    longitude_text: str
    coordinate_basis: str
    chronology_text: str
    time_start_bp: int | None
    time_end_bp: int | None
    interpretation_note: str

    def as_dict(self) -> dict[str, object]:
        return {
            "project_accession": self.project_accession,
            "locality_text": self.locality_text,
            "political_entity": self.political_entity,
            "latitude_text": self.latitude_text,
            "longitude_text": self.longitude_text,
            "coordinate_basis": self.coordinate_basis,
            "chronology_text": self.chronology_text,
            "time_start_bp": self.time_start_bp,
            "time_end_bp": self.time_end_bp,
            "interpretation_note": self.interpretation_note,
        }

def resolve_project_locality_leads(project_accession: str) -> tuple[AdnaProjectLocalityLead, ...]:
    """Return the curated locality leads for one project accession."""
    return _lead_rows(
        site_rows=resolve_project_site_evidence(project_accession),
        coordinate_rows=resolve_project_coordinate_provenance(project_accession),
    )


def build_species_project_locality_leads(
    project_accessions: tuple[str, ...],
) -> tuple[AdnaProjectLocalityLead, ...]:
    """Collect all curated locality leads for one species in stable accession order."""
    return _lead_rows(
        site_rows=build_species_site_evidence_rows(project_accessions),
        coordinate_rows=build_species_coordinate_provenance_rows(project_accessions),
    )


def _lead_rows(
    *,
    site_rows: tuple[object, ...],
    coordinate_rows: tuple[object, ...],
) -> tuple[AdnaProjectLocalityLead, ...]:
    coordinate_lookup = {
        (
            row.project_accession,
            _normalized_group_key(row.site_label, row.political_entity),
        ): row
        for row in coordinate_rows
    }
    leads: list[AdnaProjectLocalityLead] = []
    for row in site_rows:
        coordinate_row = coordinate_lookup.get(
            (
                row.project_accession,
                _normalized_group_key(row.site_label, row.political_entity),
            )
        )
        uses_direct_coordinates = row.coordinate_basis == "supplementary_table_coordinates"
        latitude_text = (
            row.latitude_text
            if uses_direct_coordinates
            else "" if coordinate_row is None else coordinate_row.latitude_text
        )
        longitude_text = (
            row.longitude_text
            if uses_direct_coordinates
            else "" if coordinate_row is None else coordinate_row.longitude_text
        )
        coordinate_basis = (
            row.coordinate_basis
            if uses_direct_coordinates and row.latitude_text and row.longitude_text
            else "" if coordinate_row is None else coordinate_row.coordinate_basis
        )
        time_start_bp = None if coordinate_row is None else coordinate_row.time_start_bp
        time_end_bp = None if coordinate_row is None else coordinate_row.time_end_bp
        interpretation_note = (
            row.interpretation_note
            if row.interpretation_note
            else "" if coordinate_row is None else coordinate_row.interpretation_note
        )
        leads.append(
            AdnaProjectLocalityLead(
                project_accession=row.project_accession,
                locality_text=row.site_label,
                political_entity=row.political_entity or "",
                latitude_text=latitude_text,
                longitude_text=longitude_text,
                coordinate_basis=coordinate_basis,
                chronology_text=row.chronology_text,
                time_start_bp=time_start_bp,
                time_end_bp=time_end_bp,
                interpretation_note=interpretation_note,
            )
        )
    leads.sort(
        key=lambda row: (
            row.project_accession,
            row.locality_text,
            row.political_entity,
        )
    )
    return tuple(leads)


def _normalized_group_key(locality_text: str, political_entity: str | None) -> tuple[str, str]:
    return (_normalize_text(locality_text), _normalize_text(political_entity or ""))


def _normalize_text(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())
