from __future__ import annotations

from dataclasses import dataclass

from .accessions import resolve_accession_reference
from .ena import AdnaArchiveProject, AdnaEnaRecord, build_archive_project_catalog
from .species import resolve_species_definition

__all__ = [
    "AdnaArchiveDuplicate",
    "AdnaArchiveIntegrityReport",
    "AdnaSpeciesMismatch",
    "build_archive_integrity_report",
]


@dataclass(frozen=True)
class AdnaArchiveDuplicate:
    """Duplicate archive accession finding for curated species support."""

    accession: str
    species_latin_names: tuple[str, ...]
    project_accessions: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "accession": self.accession,
            "species_latin_names": list(self.species_latin_names),
            "project_accessions": list(self.project_accessions),
        }


@dataclass(frozen=True)
class AdnaSpeciesMismatch:
    """Mismatch between curated species, archive metadata, and optional paper species."""

    curated_species_latin_name: str
    project_accession: str
    archive_scientific_name: str | None
    paper_species_name: str | None
    mismatch_fields: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "curated_species_latin_name": self.curated_species_latin_name,
            "project_accession": self.project_accession,
            "archive_scientific_name": self.archive_scientific_name,
            "paper_species_name": self.paper_species_name,
            "mismatch_fields": list(self.mismatch_fields),
        }


@dataclass(frozen=True)
class AdnaArchiveIntegrityReport:
    """Duplicate and species-integrity findings for curated archive support."""

    duplicates: tuple[AdnaArchiveDuplicate, ...]
    species_mismatches: tuple[AdnaSpeciesMismatch, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "duplicates": [item.as_dict() for item in self.duplicates],
            "species_mismatches": [item.as_dict() for item in self.species_mismatches],
        }


def build_archive_integrity_report(
    *,
    species_name: str | None = None,
    projects: tuple[AdnaArchiveProject, ...] | None = None,
    records: tuple[AdnaEnaRecord, ...] = (),
    paper_species_name: str | None = None,
) -> AdnaArchiveIntegrityReport:
    """Build duplicate and species-mismatch findings for archive curation."""
    catalog = projects if projects is not None else build_archive_project_catalog()
    if species_name is not None:
        curated_species = resolve_species_definition(species_name)
        catalog = tuple(
            item for item in catalog if item.species_latin_name == curated_species.latin_name
        )
    duplicates = _find_duplicate_projects(catalog)
    mismatches = _find_species_mismatches(
        catalog=catalog,
        records=records,
        paper_species_name=paper_species_name,
    )
    return AdnaArchiveIntegrityReport(
        duplicates=duplicates,
        species_mismatches=mismatches,
    )


def _find_duplicate_projects(
    catalog: tuple[AdnaArchiveProject, ...],
) -> tuple[AdnaArchiveDuplicate, ...]:
    grouped: dict[str, list[AdnaArchiveProject]] = {}
    for project in catalog:
        accession = resolve_accession_reference(project.project_accession).accession
        grouped.setdefault(accession, []).append(project)

    duplicates: list[AdnaArchiveDuplicate] = []
    for accession, projects in grouped.items():
        if len(projects) < 2:
            continue
        duplicates.append(
            AdnaArchiveDuplicate(
                accession=accession,
                species_latin_names=tuple(
                    sorted({project.species_latin_name for project in projects})
                ),
                project_accessions=tuple(project.project_accession for project in projects),
            )
        )
    return tuple(sorted(duplicates, key=lambda item: item.accession))


def _find_species_mismatches(
    *,
    catalog: tuple[AdnaArchiveProject, ...],
    records: tuple[AdnaEnaRecord, ...],
    paper_species_name: str | None,
) -> tuple[AdnaSpeciesMismatch, ...]:
    if not records:
        return ()
    if not catalog:
        return ()
    curated_species = resolve_species_definition(catalog[0].species_latin_name)
    allowed_names = {
        curated_species.latin_name.casefold(),
        curated_species.common_name.casefold(),
        *(alias.casefold() for alias in curated_species.aliases),
    }
    findings: list[AdnaSpeciesMismatch] = []
    accession_lookup = {item.project_accession for item in catalog}
    for record in records:
        project_accession = record.study_accession or "unknown_project"
        if project_accession not in accession_lookup:
            continue
        mismatch_fields: list[str] = []
        archive_name = record.scientific_name.casefold() if record.scientific_name else None
        if archive_name is not None and archive_name not in allowed_names:
            mismatch_fields.append("archive_scientific_name")
        paper_name = paper_species_name.casefold() if paper_species_name else None
        if paper_name is not None and paper_name not in allowed_names:
            mismatch_fields.append("paper_species_name")
        if mismatch_fields:
            findings.append(
                AdnaSpeciesMismatch(
                    curated_species_latin_name=curated_species.latin_name,
                    project_accession=project_accession,
                    archive_scientific_name=record.scientific_name,
                    paper_species_name=paper_species_name,
                    mismatch_fields=tuple(mismatch_fields),
                )
            )
    return tuple(findings)
