from __future__ import annotations

from dataclasses import dataclass

from .coordinate_provenance import (
    build_species_coordinate_provenance_rows,
    resolve_project_coordinate_provenance,
)

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
    return tuple(
        AdnaProjectLocalityLead(
            project_accession=row.project_accession,
            locality_text=row.site_label,
            political_entity=row.political_entity or "",
            latitude_text=row.latitude_text,
            longitude_text=row.longitude_text,
            coordinate_basis=row.coordinate_basis,
            chronology_text=row.chronology_text,
            time_start_bp=row.time_start_bp,
            time_end_bp=row.time_end_bp,
            interpretation_note=row.interpretation_note,
        )
        for row in resolve_project_coordinate_provenance(project_accession)
    )


def build_species_project_locality_leads(
    project_accessions: tuple[str, ...],
) -> tuple[AdnaProjectLocalityLead, ...]:
    """Collect all curated locality leads for one species in stable accession order."""
    return tuple(
        AdnaProjectLocalityLead(
            project_accession=row.project_accession,
            locality_text=row.site_label,
            political_entity=row.political_entity or "",
            latitude_text=row.latitude_text,
            longitude_text=row.longitude_text,
            coordinate_basis=row.coordinate_basis,
            chronology_text=row.chronology_text,
            time_start_bp=row.time_start_bp,
            time_end_bp=row.time_end_bp,
            interpretation_note=row.interpretation_note,
        )
        for row in build_species_coordinate_provenance_rows(project_accessions)
    )
