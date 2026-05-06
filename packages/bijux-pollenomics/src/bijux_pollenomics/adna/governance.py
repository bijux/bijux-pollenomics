from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .ena import build_species_archive_projects
from .manifests import build_species_manifest
from .species import AdnaSpeciesDefinition, resolve_species_definition

__all__ = [
    "ADNA_ASSIGNMENT_RULES",
    "ADNA_DATASET_BUCKETS",
    "ADNA_PRODUCT_ROLES",
    "AdnaSpeciesDatasetReview",
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
class AdnaSpeciesDatasetReview:
    """Governed review for whether a species dataset is real support or still thin."""

    species: AdnaSpeciesDefinition
    product_role: str
    assignment_rule: str
    dataset_bucket: str
    archive_project_count: int
    archive_required: bool
    primary_paper_required: bool
    manifest_schema_required: bool
    eligible_for_supported_status: bool
    blocking_reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "species": self.species.as_dict(),
            "product_role": self.product_role,
            "assignment_rule": self.assignment_rule,
            "dataset_bucket": self.dataset_bucket,
            "archive_project_count": self.archive_project_count,
            "archive_required": self.archive_required,
            "primary_paper_required": self.primary_paper_required,
            "manifest_schema_required": self.manifest_schema_required,
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
    if species.latin_name == "Bos taurus":
        return "mixed_species_review_required"
    if role == "comparator" and species.latin_name.startswith("Equus "):
        return "equid_comparator"
    if role == "comparator":
        return "single_species_comparator"
    return "single_species_core"


def build_species_dataset_review(species_name: str) -> AdnaSpeciesDatasetReview:
    """Build the governed admission review for one species dataset."""
    species = resolve_species_definition(species_name)
    product_role = classify_species_product_role(species_name)
    assignment_rule = classify_species_assignment_rule(species_name)
    archive_project_count = len(build_species_archive_projects(species_name))
    manifest_schema_required = bool(build_species_manifest(species_name).schema_version)
    archive_required = product_role in {"domesticated_core", "comparator"}
    primary_paper_required = product_role in {
        "human_reference",
        "domesticated_core",
        "comparator",
    }
    paper_pin_count = 1 if species.latin_name == "Homo sapiens" else 0

    blocking_reasons: list[str] = []
    if archive_required and archive_project_count == 0:
        blocking_reasons.append("missing_archive_projects")
    if primary_paper_required and paper_pin_count == 0:
        blocking_reasons.append("missing_primary_paper_pins")
    if not manifest_schema_required:
        blocking_reasons.append("missing_manifest_schema")
    if assignment_rule == "mixed_species_review_required":
        blocking_reasons.append("mixed_species_rule_unresolved")

    dataset_bucket = _dataset_bucket_for(
        product_role=product_role,
        archive_project_count=archive_project_count,
        paper_pin_count=paper_pin_count,
    )
    eligible = not blocking_reasons and dataset_bucket == "paper_pinned_core"

    return AdnaSpeciesDatasetReview(
        species=species,
        product_role=product_role,
        assignment_rule=assignment_rule,
        dataset_bucket=dataset_bucket,
        archive_project_count=archive_project_count,
        archive_required=archive_required,
        primary_paper_required=primary_paper_required,
        manifest_schema_required=manifest_schema_required,
        eligible_for_supported_status=eligible,
        blocking_reasons=tuple(blocking_reasons),
    )


def _dataset_bucket_for(
    *,
    product_role: str,
    archive_project_count: int,
    paper_pin_count: int,
) -> str:
    if product_role == "reject_or_out_of_scope":
        return "reject_or_out_of_scope"
    if product_role == "comparator":
        return "comparator_only"
    if paper_pin_count > 0:
        return "paper_pinned_core"
    if archive_project_count > 0:
        return "archive_verified_needs_paper_pinning"
    return "reject_or_out_of_scope"
