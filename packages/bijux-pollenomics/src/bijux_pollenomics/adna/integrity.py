from __future__ import annotations

from dataclasses import dataclass

from .accessions import resolve_accession_reference
from .ena import AdnaArchiveProject, AdnaEnaRecord, build_archive_project_catalog
from .species import resolve_species_definition

__all__ = [
    "AdnaArchiveAccessFinding",
    "AdnaArchiveDuplicate",
    "AdnaArchiveIntegrityReport",
    "AdnaDomesticationScopeMismatch",
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
class AdnaArchiveAccessFinding:
    """Restricted, delayed, or embargoed archive access finding."""

    curated_species_latin_name: str
    project_accession: str
    access_policy: str
    public_release_date: str | None
    blocking_reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "curated_species_latin_name": self.curated_species_latin_name,
            "project_accession": self.project_accession,
            "access_policy": self.access_policy,
            "public_release_date": self.public_release_date,
            "blocking_reason": self.blocking_reason,
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
class AdnaDomesticationScopeMismatch:
    """Ancient project finding that is relevant but not domesticated-core for the species."""

    curated_species_latin_name: str
    project_accession: str
    domestication_scope: str
    archive_status: str
    notes: str

    def as_dict(self) -> dict[str, object]:
        return {
            "curated_species_latin_name": self.curated_species_latin_name,
            "project_accession": self.project_accession,
            "domestication_scope": self.domestication_scope,
            "archive_status": self.archive_status,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class AdnaArchiveIntegrityReport:
    """Duplicate and species-integrity findings for curated archive support."""

    schema_version: str
    duplicates: tuple[AdnaArchiveDuplicate, ...]
    access_findings: tuple[AdnaArchiveAccessFinding, ...]
    species_mismatches: tuple[AdnaSpeciesMismatch, ...]
    domestication_scope_mismatches: tuple[AdnaDomesticationScopeMismatch, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "duplicates": [item.as_dict() for item in self.duplicates],
            "access_findings": [item.as_dict() for item in self.access_findings],
            "species_mismatches": [item.as_dict() for item in self.species_mismatches],
            "domestication_scope_mismatches": [
                item.as_dict() for item in self.domestication_scope_mismatches
            ],
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
    access_findings = _find_access_policy_findings(catalog)
    mismatches = _find_species_mismatches(
        catalog=catalog,
        records=records,
        paper_species_name=paper_species_name,
    )
    domestication_scope_mismatches = _find_domestication_scope_mismatches(catalog)
    return AdnaArchiveIntegrityReport(
        schema_version="adna-archive-integrity-report.v1",
        duplicates=duplicates,
        access_findings=access_findings,
        species_mismatches=mismatches,
        domestication_scope_mismatches=domestication_scope_mismatches,
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


def _find_access_policy_findings(
    catalog: tuple[AdnaArchiveProject, ...],
) -> tuple[AdnaArchiveAccessFinding, ...]:
    findings = []
    for project in catalog:
        if project.access_policy == "public_downloadable":
            continue
        findings.append(
            AdnaArchiveAccessFinding(
                curated_species_latin_name=project.species_latin_name,
                project_accession=project.project_accession,
                access_policy=project.access_policy,
                public_release_date=project.public_release_date,
                blocking_reason="archive_not_publicly_usable",
            )
        )
    return tuple(findings)


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


def _find_domestication_scope_mismatches(
    catalog: tuple[AdnaArchiveProject, ...],
) -> tuple[AdnaDomesticationScopeMismatch, ...]:
    findings = []
    for project in catalog:
        if project.archive_status == "reject_or_out_of_scope":
            continue
        if project.domestication_scope == "domesticated_core":
            continue
        findings.append(
            AdnaDomesticationScopeMismatch(
                curated_species_latin_name=project.species_latin_name,
                project_accession=project.project_accession,
                domestication_scope=project.domestication_scope,
                archive_status=project.archive_status,
                notes=project.notes,
            )
        )
    return tuple(findings)
