from __future__ import annotations

from dataclasses import dataclass

from .ena import build_species_archive_projects, classify_archive_project_evidence
from .governance import (
    AdnaProjectAdmissionReview,
    AdnaSpeciesDatasetReview,
    build_project_admission_review,
    build_species_dataset_review,
    classify_species_product_role,
)
from .manifests import AdnaSpeciesManifest, build_species_manifest

__all__ = [
    "AdnaProjectManifestChange",
    "AdnaSpeciesProjectManifest",
    "AdnaSpeciesProjectRow",
    "AdnaSpeciesManifestDiff",
    "AdnaSpeciesReviewPacket",
    "build_species_manifest_diff",
    "build_species_project_manifest",
    "build_species_review_packet",
]


@dataclass(frozen=True)
class AdnaSpeciesProjectRow:
    """Reviewable scientific summary row for one curated ancient-DNA project."""

    project_accession: str
    archive_status: str
    evidence_strength: str
    ancient_status: str
    paper_title: str | None
    paper_doi: str | None
    sequencing_target: str | None
    material_basis: str | None
    dating_basis: str | None
    geographic_basis: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "project_accession": self.project_accession,
            "archive_status": self.archive_status,
            "evidence_strength": self.evidence_strength,
            "ancient_status": self.ancient_status,
            "paper_title": self.paper_title,
            "paper_doi": self.paper_doi,
            "sequencing_target": self.sequencing_target,
            "material_basis": self.material_basis,
            "dating_basis": self.dating_basis,
            "geographic_basis": self.geographic_basis,
        }


@dataclass(frozen=True)
class AdnaSpeciesProjectManifest:
    """Species-owned project manifest snapshot for curated archive support."""

    species_latin_name: str
    projects: tuple[AdnaSpeciesProjectRow, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "projects": [project.as_dict() for project in self.projects],
        }


@dataclass(frozen=True)
class AdnaProjectManifestChange:
    """Changed scientific project row between two manifest snapshots."""

    project_accession: str
    changed_fields: tuple[str, ...]
    previous: AdnaSpeciesProjectRow
    current: AdnaSpeciesProjectRow

    def as_dict(self) -> dict[str, object]:
        return {
            "project_accession": self.project_accession,
            "changed_fields": list(self.changed_fields),
            "previous": self.previous.as_dict(),
            "current": self.current.as_dict(),
        }


@dataclass(frozen=True)
class AdnaSpeciesManifestDiff:
    """Diff between two project manifests for one species."""

    species_latin_name: str
    added_projects: tuple[AdnaSpeciesProjectRow, ...]
    removed_projects: tuple[AdnaSpeciesProjectRow, ...]
    changed_projects: tuple[AdnaProjectManifestChange, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "added_projects": [row.as_dict() for row in self.added_projects],
            "removed_projects": [row.as_dict() for row in self.removed_projects],
            "changed_projects": [row.as_dict() for row in self.changed_projects],
        }


@dataclass(frozen=True)
class AdnaSpeciesReviewPacket:
    """Scientist-facing species review packet for promotion from provisional support."""

    species_manifest: AdnaSpeciesManifest
    dataset_review: AdnaSpeciesDatasetReview
    project_manifest: AdnaSpeciesProjectManifest
    project_reviews: tuple[AdnaProjectAdmissionReview, ...]
    release_blockers: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "species_manifest": self.species_manifest.as_dict(),
            "dataset_review": self.dataset_review.as_dict(),
            "project_manifest": self.project_manifest.as_dict(),
            "project_reviews": [review.as_dict() for review in self.project_reviews],
            "release_blockers": list(self.release_blockers),
        }


def build_species_project_manifest(species_name: str) -> AdnaSpeciesProjectManifest:
    """Build the project manifest snapshot for one species."""
    species_manifest = build_species_manifest(species_name)
    rows = tuple(
        sorted(
            (
                AdnaSpeciesProjectRow(
                    project_accession=project.project_accession,
                    archive_status=project.archive_status,
                    evidence_strength=classify_archive_project_evidence(project),
                    ancient_status=project.ancient_status,
                    paper_title=None if project.paper_linkage is None else project.paper_linkage.paper_title,
                    paper_doi=None if project.paper_linkage is None else project.paper_linkage.doi,
                    sequencing_target=project.sequencing_target,
                    material_basis=project.material_basis,
                    dating_basis=project.dating_basis,
                    geographic_basis=project.geographic_basis,
                )
                for project in build_species_archive_projects(species_name)
            ),
            key=lambda row: row.project_accession,
        )
    )
    return AdnaSpeciesProjectManifest(
        species_latin_name=species_manifest.species.latin_name,
        projects=rows,
    )


def build_species_manifest_diff(
    previous: AdnaSpeciesProjectManifest,
    current: AdnaSpeciesProjectManifest,
) -> AdnaSpeciesManifestDiff:
    """Build a precise added/removed/changed diff for one species project manifest."""
    if previous.species_latin_name != current.species_latin_name:
        raise ValueError("Manifest diffs require the same species identity")

    previous_rows = {row.project_accession: row for row in previous.projects}
    current_rows = {row.project_accession: row for row in current.projects}
    added = tuple(
        current_rows[accession]
        for accession in sorted(set(current_rows) - set(previous_rows))
    )
    removed = tuple(
        previous_rows[accession]
        for accession in sorted(set(previous_rows) - set(current_rows))
    )
    changed: list[AdnaProjectManifestChange] = []
    for accession in sorted(set(previous_rows).intersection(current_rows)):
        before = previous_rows[accession]
        after = current_rows[accession]
        changed_fields = tuple(
            field
            for field in before.as_dict()
            if before.as_dict()[field] != after.as_dict()[field]
        )
        if changed_fields:
            changed.append(
                AdnaProjectManifestChange(
                    project_accession=accession,
                    changed_fields=changed_fields,
                    previous=before,
                    current=after,
                )
            )
    return AdnaSpeciesManifestDiff(
        species_latin_name=current.species_latin_name,
        added_projects=added,
        removed_projects=removed,
        changed_projects=tuple(changed),
    )


def build_species_review_packet(species_name: str) -> AdnaSpeciesReviewPacket:
    """Build the governed packet a scientist should inspect before species promotion."""
    species_manifest = build_species_manifest(species_name)
    dataset_review = build_species_dataset_review(species_name)
    product_role = classify_species_product_role(species_name)
    project_reviews = tuple(
        build_project_admission_review(project, product_role=product_role)
        for project in build_species_archive_projects(species_name)
    )
    project_manifest = build_species_project_manifest(species_name)
    return AdnaSpeciesReviewPacket(
        species_manifest=species_manifest,
        dataset_review=dataset_review,
        project_manifest=project_manifest,
        project_reviews=project_reviews,
        release_blockers=dataset_review.blocking_reasons,
    )
