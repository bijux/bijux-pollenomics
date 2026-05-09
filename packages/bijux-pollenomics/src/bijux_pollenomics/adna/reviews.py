from __future__ import annotations

from dataclasses import dataclass

from .governance import (
    AdnaProjectAdmissionReview,
    AdnaSpeciesDatasetReview,
    build_project_admission_review,
    build_species_dataset_review,
    classify_species_product_role,
)
from .manifests import AdnaSpeciesManifest, build_species_manifest
from .projects.context import resolve_project_context
from .sources.ena import (
    build_species_archive_projects,
    classify_archive_project_evidence,
)

__all__ = [
    "AdnaProjectManifestChange",
    "AdnaSpeciesProjectManifest",
    "AdnaSpeciesProjectRow",
    "AdnaSpeciesReviewTableRow",
    "AdnaSpeciesManifestDiff",
    "AdnaSpeciesReviewDossier",
    "build_species_manifest_diff",
    "build_species_project_manifest",
    "build_species_review_dossier",
]


@dataclass(frozen=True)
class AdnaSpeciesProjectRow:
    """Reviewable scientific summary row for one curated ancient-DNA project."""

    project_accession: str
    source_family: str
    accession_scope: str
    archive_status: str
    evidence_strength: str
    ancient_status: str
    paper_title: str | None
    paper_doi: str | None
    sequencing_target: str | None
    material_basis: str | None
    dating_basis: str | None
    geographic_basis: str | None
    access_policy: str
    public_release_date: str | None
    domestication_scope: str
    notes: str
    nordic_relevance: str
    nordic_relevance_reason: str
    last_checked_on: str

    def as_dict(self) -> dict[str, object]:
        return {
            "project_accession": self.project_accession,
            "source_family": self.source_family,
            "accession_scope": self.accession_scope,
            "archive_status": self.archive_status,
            "evidence_strength": self.evidence_strength,
            "ancient_status": self.ancient_status,
            "paper_title": self.paper_title,
            "paper_doi": self.paper_doi,
            "sequencing_target": self.sequencing_target,
            "material_basis": self.material_basis,
            "dating_basis": self.dating_basis,
            "geographic_basis": self.geographic_basis,
            "access_policy": self.access_policy,
            "public_release_date": self.public_release_date,
            "domestication_scope": self.domestication_scope,
            "notes": self.notes,
            "nordic_relevance": self.nordic_relevance,
            "nordic_relevance_reason": self.nordic_relevance_reason,
            "last_checked_on": self.last_checked_on,
        }


@dataclass(frozen=True)
class AdnaSpeciesProjectManifest:
    """Species-owned project manifest snapshot for curated archive support."""

    schema_version: str
    species_latin_name: str
    projects: tuple[AdnaSpeciesProjectRow, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "species_latin_name": self.species_latin_name,
            "projects": [project.as_dict() for project in self.projects],
        }


@dataclass(frozen=True)
class AdnaSpeciesReviewTableRow:
    """One reader-facing grouped review row for tracked animal evidence."""

    project_accession: str
    paper_title: str | None
    paper_doi: str | None
    archive_status: str
    support_class: str
    reason: str
    nordic_relevance: str
    nordic_relevance_reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "project_accession": self.project_accession,
            "paper_title": self.paper_title,
            "paper_doi": self.paper_doi,
            "archive_status": self.archive_status,
            "support_class": self.support_class,
            "reason": self.reason,
            "nordic_relevance": self.nordic_relevance,
            "nordic_relevance_reason": self.nordic_relevance_reason,
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

    schema_version: str
    species_latin_name: str
    added_projects: tuple[AdnaSpeciesProjectRow, ...]
    removed_projects: tuple[AdnaSpeciesProjectRow, ...]
    changed_projects: tuple[AdnaProjectManifestChange, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "species_latin_name": self.species_latin_name,
            "added_projects": [row.as_dict() for row in self.added_projects],
            "removed_projects": [row.as_dict() for row in self.removed_projects],
            "changed_projects": [row.as_dict() for row in self.changed_projects],
        }


@dataclass(frozen=True)
class AdnaSpeciesReviewDossier:
    """Scientist-facing species review dossier for promotion from provisional support."""

    schema_version: str
    species_manifest: AdnaSpeciesManifest
    dataset_review: AdnaSpeciesDatasetReview
    project_manifest: AdnaSpeciesProjectManifest
    project_reviews: tuple[AdnaProjectAdmissionReview, ...]
    accepted_projects: tuple[AdnaSpeciesReviewTableRow, ...]
    rejected_projects: tuple[AdnaSpeciesReviewTableRow, ...]
    too_weak_projects: tuple[AdnaSpeciesReviewTableRow, ...]
    comparator_projects: tuple[AdnaSpeciesReviewTableRow, ...]
    nordic_unmapped_leads: tuple[AdnaSpeciesReviewTableRow, ...]
    release_blockers: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "species_manifest": self.species_manifest.as_dict(),
            "dataset_review": self.dataset_review.as_dict(),
            "project_manifest": self.project_manifest.as_dict(),
            "project_reviews": [review.as_dict() for review in self.project_reviews],
            "accepted_projects": [row.as_dict() for row in self.accepted_projects],
            "rejected_projects": [row.as_dict() for row in self.rejected_projects],
            "too_weak_projects": [row.as_dict() for row in self.too_weak_projects],
            "comparator_projects": [row.as_dict() for row in self.comparator_projects],
            "nordic_unmapped_leads": [
                row.as_dict() for row in self.nordic_unmapped_leads
            ],
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
                    source_family=project.source_family,
                    accession_scope=project.accession_scope,
                    archive_status=project.archive_status,
                    evidence_strength=classify_archive_project_evidence(project),
                    ancient_status=project.ancient_status,
                    paper_title=None
                    if project.paper_linkage is None
                    else project.paper_linkage.paper_title,
                    paper_doi=None
                    if project.paper_linkage is None
                    else project.paper_linkage.doi,
                    sequencing_target=project.sequencing_target,
                    material_basis=project.material_basis,
                    dating_basis=project.dating_basis,
                    geographic_basis=project.geographic_basis,
                    access_policy=project.access_policy,
                    public_release_date=project.public_release_date,
                    domestication_scope=project.domestication_scope,
                    notes=project.notes,
                    nordic_relevance=resolve_project_context(project).nordic_relevance,
                    nordic_relevance_reason=resolve_project_context(
                        project
                    ).nordic_relevance_reason,
                    last_checked_on=resolve_project_context(project).last_checked_on,
                )
                for project in build_species_archive_projects(species_name)
            ),
            key=lambda row: row.project_accession,
        )
    )
    return AdnaSpeciesProjectManifest(
        schema_version="adna-species-project-manifest.v1",
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
        schema_version="adna-species-project-manifest-diff.v1",
        species_latin_name=current.species_latin_name,
        added_projects=added,
        removed_projects=removed,
        changed_projects=tuple(changed),
    )


def build_species_review_dossier(species_name: str) -> AdnaSpeciesReviewDossier:
    """Build the governed dossier a scientist should inspect before species promotion."""
    species_manifest = build_species_manifest(species_name)
    dataset_review = build_species_dataset_review(species_name)
    product_role = classify_species_product_role(species_name)
    project_reviews = tuple(
        build_project_admission_review(project, product_role=product_role)
        for project in build_species_archive_projects(species_name)
    )
    project_manifest = build_species_project_manifest(species_name)
    accepted_projects, rejected_projects, too_weak_projects, comparator_projects = (
        _build_grouped_review_rows(project_manifest, project_reviews)
    )
    nordic_unmapped_leads = tuple(
        row
        for row in (*accepted_projects, *too_weak_projects, *comparator_projects)
        if row.nordic_relevance == "nordic_relevant_unmapped"
    )
    return AdnaSpeciesReviewDossier(
        schema_version="adna-species-review-dossier.v1",
        species_manifest=species_manifest,
        dataset_review=dataset_review,
        project_manifest=project_manifest,
        project_reviews=project_reviews,
        accepted_projects=accepted_projects,
        rejected_projects=rejected_projects,
        too_weak_projects=too_weak_projects,
        comparator_projects=comparator_projects,
        nordic_unmapped_leads=nordic_unmapped_leads,
        release_blockers=dataset_review.blocking_reasons,
    )


def _build_grouped_review_rows(
    project_manifest: AdnaSpeciesProjectManifest,
    project_reviews: tuple[AdnaProjectAdmissionReview, ...],
) -> tuple[
    tuple[AdnaSpeciesReviewTableRow, ...],
    tuple[AdnaSpeciesReviewTableRow, ...],
    tuple[AdnaSpeciesReviewTableRow, ...],
    tuple[AdnaSpeciesReviewTableRow, ...],
]:
    review_lookup = {review.project_accession: review for review in project_reviews}
    accepted: list[AdnaSpeciesReviewTableRow] = []
    rejected: list[AdnaSpeciesReviewTableRow] = []
    too_weak: list[AdnaSpeciesReviewTableRow] = []
    comparator: list[AdnaSpeciesReviewTableRow] = []
    for row in project_manifest.projects:
        review = review_lookup.get(row.project_accession)
        if review is not None and review.admissible_for_curated_support:
            accepted.append(
                _review_table_row(row, "accepted", "admissible_for_curated_support")
            )
            continue
        if row.archive_status == "reject_or_out_of_scope":
            rejected.append(
                _review_table_row(
                    row,
                    "rejected",
                    row.notes,
                )
            )
            continue
        if (
            row.archive_status == "comparator_only"
            or row.domestication_scope == "ancient_comparator"
        ):
            comparator.append(
                _review_table_row(
                    row,
                    "comparator_only",
                    "scientifically useful comparator evidence that must not count as domesticated-core support",
                )
            )
            continue
        if (
            review is not None
            and review.core_project
            and not review.admissible_for_curated_support
        ):
            too_weak.append(
                _review_table_row(
                    row,
                    "ancient_but_too_weak",
                    ", ".join(review.blocking_reasons)
                    if review.blocking_reasons
                    else row.notes,
                )
            )
    return (
        tuple(accepted),
        tuple(rejected),
        tuple(too_weak),
        tuple(comparator),
    )


def _review_table_row(
    row: AdnaSpeciesProjectRow,
    support_class: str,
    reason: str,
) -> AdnaSpeciesReviewTableRow:
    return AdnaSpeciesReviewTableRow(
        project_accession=row.project_accession,
        paper_title=row.paper_title,
        paper_doi=row.paper_doi,
        archive_status=row.archive_status,
        support_class=support_class,
        reason=reason,
        nordic_relevance=row.nordic_relevance,
        nordic_relevance_reason=row.nordic_relevance_reason,
    )
