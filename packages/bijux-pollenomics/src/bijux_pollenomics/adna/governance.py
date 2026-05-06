from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Final

from .ena import (
    AdnaArchiveProject,
    build_species_archive_projects,
    classify_archive_project_evidence,
)
from .manifests import build_species_manifest
from .species import AdnaSpeciesDefinition, resolve_species_definition

__all__ = [
    "ADNA_ASSIGNMENT_RULES",
    "ADNA_DATASET_BUCKETS",
    "ADNA_PRODUCT_ROLES",
    "AdnaProjectAdmissionReview",
    "AdnaSpeciesDatasetReview",
    "build_project_admission_review",
    "build_species_dataset_review",
    "classify_species_assignment_rule",
    "classify_species_product_role",
]

ADNA_PRODUCT_ROLES: Final[tuple[str, ...]] = (
    "human_reference",
    "domesticated_core",
    "comparator",
    "genbank_only",
    "reject_or_out_of_scope",
)
ADNA_ASSIGNMENT_RULES: Final[tuple[str, ...]] = (
    "single_species_core",
    "single_species_comparator",
    "equid_comparator",
    "mixed_species_review_required",
)
ADNA_DATASET_BUCKETS: Final[tuple[str, ...]] = (
    "paper_pinned_core",
    "archive_verified_needs_paper_pinning",
    "comparator_only",
    "reject_or_out_of_scope",
)


@dataclass(frozen=True)
class AdnaProjectAdmissionReview:
    """Project-level admission review for whether one archive row can support curation."""

    species_latin_name: str
    project_accession: str
    source_family: str
    accession_scope: str
    archive_status: str
    evidence_strength: str
    ancient_status: str
    access_policy: str
    public_release_date: str | None
    domestication_scope: str
    core_project: bool
    admissible_for_curated_support: bool
    blocking_reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "species_latin_name": self.species_latin_name,
            "project_accession": self.project_accession,
            "source_family": self.source_family,
            "accession_scope": self.accession_scope,
            "archive_status": self.archive_status,
            "evidence_strength": self.evidence_strength,
            "ancient_status": self.ancient_status,
            "access_policy": self.access_policy,
            "public_release_date": self.public_release_date,
            "domestication_scope": self.domestication_scope,
            "core_project": self.core_project,
            "admissible_for_curated_support": self.admissible_for_curated_support,
            "blocking_reasons": list(self.blocking_reasons),
        }


@dataclass(frozen=True)
class AdnaSpeciesDatasetReview:
    """Governed review for whether a species dataset is real support or still thin."""

    species: AdnaSpeciesDefinition
    product_role: str
    assignment_rule: str
    dataset_bucket: str
    archive_project_count: int
    core_project_count: int
    primary_paper_pin_count: int
    curated_support_project_count: int
    archive_required: bool
    primary_paper_required: bool
    manifest_schema_required: bool
    release_gate_satisfied: bool
    eligible_for_supported_status: bool
    blocking_reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "species": self.species.as_dict(),
            "product_role": self.product_role,
            "assignment_rule": self.assignment_rule,
            "dataset_bucket": self.dataset_bucket,
            "archive_project_count": self.archive_project_count,
            "core_project_count": self.core_project_count,
            "primary_paper_pin_count": self.primary_paper_pin_count,
            "curated_support_project_count": self.curated_support_project_count,
            "archive_required": self.archive_required,
            "primary_paper_required": self.primary_paper_required,
            "manifest_schema_required": self.manifest_schema_required,
            "release_gate_satisfied": self.release_gate_satisfied,
            "eligible_for_supported_status": self.eligible_for_supported_status,
            "blocking_reasons": list(self.blocking_reasons),
        }


def classify_species_product_role(species_name: str) -> str:
    """Classify whether a species is core, comparator, or out of scope."""
    species = resolve_species_definition(species_name)
    if species.latin_name == "Homo sapiens":
        return "human_reference"
    if species.support_status == "provisional":
        return "domesticated_core"
    if species.support_status == "comparator_only":
        return "comparator"
    if species.support_status == "genbank_only":
        return "genbank_only"
    return "reject_or_out_of_scope"


def classify_species_assignment_rule(species_name: str) -> str:
    """Classify how project records must be assigned for one species."""
    species = resolve_species_definition(species_name)
    role = classify_species_product_role(species_name)
    if species.latin_name in {"Bos taurus", "Bos indicus"}:
        return "mixed_species_review_required"
    if role == "comparator" and species.latin_name.startswith("Equus "):
        return "equid_comparator"
    if role == "comparator":
        return "single_species_comparator"
    return "single_species_core"


def build_project_admission_review(
    project: AdnaArchiveProject,
    *,
    product_role: str,
) -> AdnaProjectAdmissionReview:
    """Review whether one archive project can count as curated scientific support."""
    evidence_strength = classify_archive_project_evidence(project)
    core_project = (
        product_role == "domesticated_core"
        and project.archive_status in {"paper_pinned_core", "archive_verified_needs_paper_pinning"}
    )
    blocking_reasons: list[str] = []
    if core_project and project.ancient_status != "ancient_confirmed":
        blocking_reasons.append("not_confirmed_ancient")
    if core_project and evidence_strength != "primary_paper_pinned":
        blocking_reasons.append("missing_primary_paper_anchor")
    if core_project and (
        project.paper_linkage is None or not project.paper_linkage.pinning_evidence.strip()
    ):
        blocking_reasons.append("missing_archive_paper_pinning_rationale")
    access_policy_blocker = _access_policy_blocker(project)
    if core_project and access_policy_blocker is not None:
        blocking_reasons.append(access_policy_blocker)
    if core_project and project.domestication_scope != "domesticated_core":
        blocking_reasons.append("ancient_but_not_domesticated_core")
    admissible = core_project and not blocking_reasons
    return AdnaProjectAdmissionReview(
        species_latin_name=project.species_latin_name,
        project_accession=project.project_accession,
        source_family=project.source_family,
        accession_scope=project.accession_scope,
        archive_status=project.archive_status,
        evidence_strength=evidence_strength,
        ancient_status=project.ancient_status,
        access_policy=project.access_policy,
        public_release_date=project.public_release_date,
        domestication_scope=project.domestication_scope,
        core_project=core_project,
        admissible_for_curated_support=admissible,
        blocking_reasons=tuple(blocking_reasons),
    )


def build_species_dataset_review(species_name: str) -> AdnaSpeciesDatasetReview:
    """Build the governed admission review for one species dataset."""
    species = resolve_species_definition(species_name)
    product_role = classify_species_product_role(species_name)
    assignment_rule = classify_species_assignment_rule(species_name)
    archive_projects = build_species_archive_projects(species_name)
    project_reviews = tuple(
        build_project_admission_review(project, product_role=product_role)
        for project in archive_projects
    )
    manifest_schema_required = bool(build_species_manifest(species_name).schema_version)
    archive_required = product_role in {"domesticated_core", "comparator"}
    primary_paper_required = product_role == "domesticated_core"
    archive_project_count = len(archive_projects)
    core_project_count = sum(1 for review in project_reviews if review.core_project)
    primary_paper_pin_count = sum(
        1 for review in project_reviews if review.evidence_strength == "primary_paper_pinned"
    )
    curated_support_project_count = sum(
        1 for review in project_reviews if review.admissible_for_curated_support
    )

    blocking_reasons: list[str] = []
    if archive_required and archive_project_count == 0:
        blocking_reasons.append("missing_archive_projects")
    if primary_paper_required and any(
        "missing_primary_paper_anchor" in review.blocking_reasons
        for review in project_reviews
        if review.core_project
    ):
        blocking_reasons.append("missing_primary_paper_pins")
    if product_role == "domesticated_core":
        if any(
            "missing_archive_paper_pinning_rationale" in review.blocking_reasons
            for review in project_reviews
            if review.core_project
        ):
            blocking_reasons.append("missing_archive_paper_pinning_rationale")
        if any(
            "not_confirmed_ancient" in review.blocking_reasons
            for review in project_reviews
            if review.core_project
        ):
            blocking_reasons.append("non_ancient_or_unconfirmed_core_projects")
        if any(
            "archive_not_publicly_usable" in review.blocking_reasons
            or "archive_release_still_embargoed" in review.blocking_reasons
            for review in project_reviews
            if review.core_project
        ):
            blocking_reasons.append("restricted_or_delayed_archive_projects")
        if any(
            "ancient_but_not_domesticated_core" in review.blocking_reasons
            for review in project_reviews
            if review.core_project
        ):
            blocking_reasons.append("ancient_but_not_domesticated_core_projects")
    if not manifest_schema_required:
        blocking_reasons.append("missing_manifest_schema")
    if assignment_rule == "mixed_species_review_required":
        blocking_reasons.append("mixed_species_rule_unresolved")

    dataset_bucket = _dataset_bucket_for(
        product_role=product_role,
        core_project_count=core_project_count,
        curated_support_project_count=curated_support_project_count,
    )
    release_gate_satisfied = product_role != "domesticated_core" or (
        core_project_count > 0 and curated_support_project_count == core_project_count
    )
    if (
        product_role == "domesticated_core"
        and not release_gate_satisfied
        and "missing_archive_paper_pinning_rationale" not in blocking_reasons
    ):
        blocking_reasons.append("missing_archive_paper_pinning_rationale")
    eligible = not blocking_reasons and dataset_bucket == "paper_pinned_core"
    if product_role == "human_reference":
        release_gate_satisfied = True
        eligible = True

    return AdnaSpeciesDatasetReview(
        species=species,
        product_role=product_role,
        assignment_rule=assignment_rule,
        dataset_bucket=dataset_bucket,
        archive_project_count=archive_project_count,
        core_project_count=core_project_count,
        primary_paper_pin_count=primary_paper_pin_count,
        curated_support_project_count=curated_support_project_count,
        archive_required=archive_required,
        primary_paper_required=primary_paper_required,
        manifest_schema_required=manifest_schema_required,
        release_gate_satisfied=release_gate_satisfied,
        eligible_for_supported_status=eligible,
        blocking_reasons=tuple(dict.fromkeys(blocking_reasons)),
    )


def _dataset_bucket_for(
    *,
    product_role: str,
    core_project_count: int,
    curated_support_project_count: int,
) -> str:
    if product_role == "human_reference":
        return "paper_pinned_core"
    if product_role == "reject_or_out_of_scope":
        return "reject_or_out_of_scope"
    if product_role == "comparator":
        return "comparator_only"
    if core_project_count == 0:
        return "reject_or_out_of_scope"
    if curated_support_project_count == core_project_count:
        return "paper_pinned_core"
    return "archive_verified_needs_paper_pinning"


def _access_policy_blocker(project: AdnaArchiveProject) -> str | None:
    if project.access_policy == "public_downloadable":
        return None
    if project.access_policy == "restricted_access":
        return "archive_not_publicly_usable"
    if project.access_policy == "delayed_release_unverified":
        return "archive_not_publicly_usable"
    if (
        project.access_policy == "embargoed_until_release_date"
        and project.public_release_date is not None
    ):
        try:
            release_date = date.fromisoformat(project.public_release_date)
        except ValueError:
            return "archive_not_publicly_usable"
        if release_date > date.today():
            return "archive_release_still_embargoed"
        return None
    return "archive_not_publicly_usable"
