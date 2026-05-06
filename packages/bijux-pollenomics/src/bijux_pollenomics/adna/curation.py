from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .manifests import AdnaSpeciesManifest, build_species_manifest
from .reviews import AdnaSpeciesProjectRow, build_species_project_manifest
from .species import AdnaSpeciesDefinition

__all__ = [
    "ADNA_CURATION_CLASSES",
    "ADNA_COVERAGE_POSTURES",
    "AdnaDomesticationCoverageReport",
    "AdnaDomesticationCoverageRow",
    "AdnaRejectedProject",
    "AdnaSpeciesCurationManifest",
    "build_domestication_coverage_report",
    "build_species_curation_manifest",
]

ADNA_CURATION_CLASSES: Final[tuple[str, ...]] = (
    "paper_pinned_core",
    "comparator_only",
    "genbank_only_or_non_project_archive",
    "weak_or_precuration",
    "provisional_unmaterialized",
)
ADNA_COVERAGE_POSTURES: Final[tuple[str, ...]] = ("strong", "thin", "pretending")

_PAPER_PINNED_CORE_SPECIES: Final[frozenset[str]] = frozenset(
    {
        "Equus caballus",
        "Sus scrofa domesticus",
        "Ovis aries",
        "Capra hircus",
        "Canis lupus familiaris",
        "Felis catus",
        "Camelus dromedarius",
    }
)
_COMPARATOR_SPECIES: Final[frozenset[str]] = frozenset(
    {"Equus asinus", "Rangifer tarandus"}
)
_GENBANK_ONLY_SPECIES: Final[frozenset[str]] = frozenset(
    {"Gallus gallus domesticus", "Meleagris gallopavo"}
)
_WEAK_PRECURATION_SPECIES: Final[frozenset[str]] = frozenset(
    {"Oryctolagus cuniculus", "Anas platyrhynchos domesticus"}
)


@dataclass(frozen=True)
class AdnaRejectedProject:
    """Explicit reject bucket entry inside one species curation manifest."""

    project_accession: str
    archive_status: str
    ancient_status: str
    rejection_reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "project_accession": self.project_accession,
            "archive_status": self.archive_status,
            "ancient_status": self.ancient_status,
            "rejection_reason": self.rejection_reason,
        }


@dataclass(frozen=True)
class AdnaSpeciesCurationManifest:
    """Species-owned curation manifest for the non-human aDNA intake program."""

    schema_version: str
    species_manifest: AdnaSpeciesManifest
    curation_class: str
    support_statement: str
    curated_projects: tuple[AdnaSpeciesProjectRow, ...]
    pending_projects: tuple[AdnaSpeciesProjectRow, ...]
    rejected_projects: tuple[AdnaRejectedProject, ...]

    @property
    def species(self) -> AdnaSpeciesDefinition:
        return self.species_manifest.species

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "species_manifest": self.species_manifest.as_dict(),
            "curation_class": self.curation_class,
            "support_statement": self.support_statement,
            "curated_projects": [row.as_dict() for row in self.curated_projects],
            "pending_projects": [row.as_dict() for row in self.pending_projects],
            "rejected_projects": [row.as_dict() for row in self.rejected_projects],
        }


@dataclass(frozen=True)
class AdnaDomesticationCoverageRow:
    """Cross-species view of where the domestication program is strong or thin."""

    species_latin_name: str
    common_name: str
    curation_class: str
    coverage_posture: str
    curated_project_count: int
    pending_project_count: int
    rejected_project_count: int
    support_statement: str

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "common_name": self.common_name,
            "curation_class": self.curation_class,
            "coverage_posture": self.coverage_posture,
            "curated_project_count": self.curated_project_count,
            "pending_project_count": self.pending_project_count,
            "rejected_project_count": self.rejected_project_count,
            "support_statement": self.support_statement,
        }


@dataclass(frozen=True)
class AdnaDomesticationCoverageReport:
    """Coverage report across the species-level domesticated-animal curation program."""

    rows: tuple[AdnaDomesticationCoverageRow, ...]

    def as_dict(self) -> dict[str, object]:
        return {"rows": [row.as_dict() for row in self.rows]}


def build_species_curation_manifest(species_name: str) -> AdnaSpeciesCurationManifest:
    """Build the curated species-program manifest for one registered species."""
    species_manifest = build_species_manifest(species_name)
    project_manifest = build_species_project_manifest(species_name)
    curated_projects = tuple(
        row for row in project_manifest.projects if row.archive_status == "paper_pinned_core"
    )
    pending_projects = tuple(
        row
        for row in project_manifest.projects
        if row.archive_status in {"archive_verified_needs_paper_pinning", "comparator_only"}
    )
    rejected_projects = tuple(
        AdnaRejectedProject(
            project_accession=row.project_accession,
            archive_status=row.archive_status,
            ancient_status=row.ancient_status,
            rejection_reason=_rejection_reason_for(row),
        )
        for row in project_manifest.projects
        if row.archive_status == "reject_or_out_of_scope"
    )
    curation_class = _curation_class_for(species_manifest.species)

    if curation_class == "paper_pinned_core":
        support_statement = (
            "Paper-pinned core domestication support exists for this species. "
            "Curated projects are fit for governed comparative use, while pending "
            "projects still need stronger archive-paper linkage."
        )
    elif curation_class == "comparator_only":
        support_statement = (
            "Ancient material is curated only as comparator support and must not be "
            "flattened into domesticated-core inference."
        )
    elif curation_class == "genbank_only_or_non_project_archive":
        support_statement = (
            "Current support is thinner than project-level archive intake. Use these "
            "species as paper or sequence-reference leads, not as first-class project support."
        )
    elif curation_class == "weak_or_precuration":
        support_statement = (
            "Current evidence is too thin for curated runtime support. The species "
            "stays visible only so weak coverage is explicit rather than implied."
        )
    else:
        support_statement = (
            "The species is provisionally listed, but the first curation manifest "
            "has not been built yet. Coverage here would be pretending if presented as mature."
        )

    return AdnaSpeciesCurationManifest(
        schema_version="adna-species-curation-manifest.v1",
        species_manifest=species_manifest,
        curation_class=curation_class,
        support_statement=support_statement,
        curated_projects=curated_projects,
        pending_projects=pending_projects,
        rejected_projects=rejected_projects,
    )


def build_domestication_coverage_report() -> AdnaDomesticationCoverageReport:
    """Build the cross-species report for domesticated-animal aDNA coverage honesty."""
    species_names = (
        "Equus caballus",
        "Sus scrofa domesticus",
        "Ovis aries",
        "Bos taurus",
        "Capra hircus",
        "Canis lupus familiaris",
        "Felis catus",
        "Camelus dromedarius",
        "Rangifer tarandus",
        "Equus asinus",
        "Gallus gallus domesticus",
        "Meleagris gallopavo",
        "Oryctolagus cuniculus",
        "Anas platyrhynchos domesticus",
    )
    rows = tuple(
        _coverage_row_for(build_species_curation_manifest(name))
        for name in species_names
    )
    return AdnaDomesticationCoverageReport(rows=rows)


def _coverage_row_for(
    manifest: AdnaSpeciesCurationManifest,
) -> AdnaDomesticationCoverageRow:
    if manifest.curation_class == "paper_pinned_core":
        posture = "strong"
    elif manifest.curation_class == "provisional_unmaterialized":
        posture = "pretending"
    else:
        posture = "thin"
    return AdnaDomesticationCoverageRow(
        species_latin_name=manifest.species.latin_name,
        common_name=manifest.species.common_name,
        curation_class=manifest.curation_class,
        coverage_posture=posture,
        curated_project_count=len(manifest.curated_projects),
        pending_project_count=len(manifest.pending_projects),
        rejected_project_count=len(manifest.rejected_projects),
        support_statement=manifest.support_statement,
    )


def _curation_class_for(species: AdnaSpeciesDefinition) -> str:
    if species.latin_name in _PAPER_PINNED_CORE_SPECIES:
        return "paper_pinned_core"
    if species.latin_name in _COMPARATOR_SPECIES:
        return "comparator_only"
    if species.latin_name in _GENBANK_ONLY_SPECIES:
        return "genbank_only_or_non_project_archive"
    if species.latin_name in _WEAK_PRECURATION_SPECIES:
        return "weak_or_precuration"
    return "provisional_unmaterialized"


def _rejection_reason_for(row: AdnaSpeciesProjectRow) -> str:
    if row.ancient_status == "modern_or_irrelevant":
        return "modern_or_irrelevant"
    if row.archive_status == "reject_or_out_of_scope":
        return "out_of_scope_or_non_downloadable"
    return "manual_rejection"
