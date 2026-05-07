from __future__ import annotations

import json
from pathlib import Path

from .models import AtlasEvidenceSurface
from .scientific_review import ScientificReviewSurface

__all__ = [
    "build_atlas_evidence_surface_payload",
    "build_scientific_review_surface_payload",
    "render_atlas_evidence_surface_markdown",
    "render_scientific_review_surface_markdown",
    "write_scientific_review_surface_json",
    "write_atlas_evidence_surface_json",
]


def build_atlas_evidence_surface_payload(
    surface: AtlasEvidenceSurface,
) -> dict[str, object]:
    """Build the machine-readable atlas evidence payload."""
    return surface.as_dict()


def write_atlas_evidence_surface_json(
    path: Path,
    surface: AtlasEvidenceSurface,
) -> None:
    """Write the machine-readable atlas evidence surface."""
    path.write_text(
        json.dumps(build_atlas_evidence_surface_payload(surface), indent=2),
        encoding="utf-8",
    )


def build_scientific_review_surface_payload(
    surface: ScientificReviewSurface,
) -> dict[str, object]:
    """Build the machine-readable scientific review payload."""
    return surface.as_dict()


def write_scientific_review_surface_json(
    path: Path,
    surface: ScientificReviewSurface,
) -> None:
    """Write the machine-readable scientific review surface."""
    path.write_text(
        json.dumps(build_scientific_review_surface_payload(surface), indent=2),
        encoding="utf-8",
    )


def render_atlas_evidence_surface_markdown(surface: AtlasEvidenceSurface) -> str:
    """Render the atlas evidence surface as reviewable markdown."""
    species_rows = "\n".join(
        (
            f"| {row.species_latin_name} | {row.contribution_role} | "
            f"{row.interaction_posture} | {row.dataset_bucket} | "
            f"{row.curated_project_count} | {row.geography_posture} | "
            f"{row.chronology_posture} | {'; '.join(row.rationale)} |"
        )
        for row in surface.species_rows
    )
    if not species_rows:
        species_rows = "| No species rows | - | - | - | 0 | - | - | - |"

    country_rows = "\n".join(
        (
            f"| {profile.country} | {profile.evidence_posture} | "
            f"{profile.human_locality_count} | {profile.human_sample_count} | "
            f"{', '.join(profile.mapped_animal_direct_species) or 'none'} | "
            f"{profile.mapped_animal_locality_count} | "
            f"{', '.join(profile.unmapped_animal_context_species) or 'none'} | "
            f"{', '.join(profile.too_weak_animal_species) or 'none'} | "
            f"{profile.caution_note} |"
        )
        for profile in surface.country_profiles
    )
    if not country_rows:
        country_rows = "| No countries | - | 0 | 0 | none | 0 | none | none | - |"

    refusal_rows = "\n".join(
        f"| {refusal.subject} | {refusal.reason} | {refusal.detail} |"
        for refusal in surface.refusals
    )
    if not refusal_rows:
        refusal_rows = "| No refusals | - | - |"

    return f"""# Atlas Evidence Surface

{surface.north_star_boundary}

## Species Evidence

| Species | Contribution | Interaction | Dataset bucket | Curated projects | Geography posture | Chronology posture | Rationale |
| --- | --- | --- | --- | ---: | --- | --- | --- |
{species_rows}

## Country Evidence Profiles

| Country | Evidence posture | Human localities | Human samples | Mapped animal species | Mapped animal localities | Unmapped animal context | Too weak animal species | Caution |
| --- | --- | ---: | ---: | --- | ---: | --- | --- | --- |
{country_rows}

## Refusals

| Subject | Reason | Detail |
| --- | --- | --- |
{refusal_rows}
"""


def render_scientific_review_surface_markdown(surface: ScientificReviewSurface) -> str:
    """Render the scientific review surface as reviewable markdown."""
    descriptive_scope = "\n".join(f"- {item}" for item in surface.descriptive_scope)
    comparative_scope = "\n".join(f"- {item}" for item in surface.comparative_scope)
    exploratory_scope = "\n".join(f"- {item}" for item in surface.exploratory_scope)
    country_rows = "\n".join(
        (
            f"| {row.country} | {row.species_latin_name} | {row.evidence_scope} | "
            f"{row.mapped_locality_count} | {row.contextual_project_count} | "
            f"{row.assignment_confidence} | {row.caution_note} |"
        )
        for row in surface.country_coverage
    )
    period_rows = "\n".join(
        (
            f"| {row.species_latin_name} | {row.period_label} | {row.evidence_scope} | "
            f"{row.mapped_locality_count} | {row.contextual_project_count} | "
            f"{row.chronology_confidence} | {row.caution_note} |"
        )
        for row in surface.period_coverage
    )
    overlap_rows = "\n".join(
        (
            f"| {row.species_latin_name} | {row.context_layer_key} | {row.overlap_status} | "
            f"{row.overlapping_direct_localities} | {row.non_overlapping_direct_localities} | "
            f"{row.noncomparable_records} | {row.rationale} |"
        )
        for row in surface.chronology_overlaps
    )
    coordinate_review = surface.animal_coordinate_review
    uncertainty_rows = "\n".join(
        (
            f"| {row.subject} | {row.uncertainty_kind} | {row.severity} | "
            f"{row.reason} | {row.impact} |"
        )
        for row in surface.uncertainties
    )
    scenario_rows = "\n".join(
        (
            f"| {row.scenario_key} | {row.claim_scope} | {row.current_posture} | "
            f"{', '.join(row.usable_evidence)} | {', '.join(row.blockers)} |"
        )
        for row in surface.scenarios
    )
    return f"""# Scientific Review Surface

## Descriptive Scope

{descriptive_scope}

## Comparative Scope

{comparative_scope}

## Exploratory Scope

{exploratory_scope}

## Country Coverage

| Country | Species | Evidence scope | Mapped localities | Contextual projects | Assignment confidence | Caution |
| --- | --- | --- | ---: | ---: | --- | --- |
{country_rows}

## Period Coverage

| Species | Period | Evidence scope | Mapped localities | Contextual projects | Chronology confidence | Caution |
| --- | --- | --- | ---: | ---: | --- | --- |
{period_rows}

## Chronology Overlap

| Species | Context layer | Overlap status | Overlapping direct localities | Non-overlapping direct localities | Noncomparable records | Rationale |
| --- | --- | --- | ---: | ---: | ---: | --- |
{overlap_rows}

## Animal Coordinate Review

| Direct coordinates | Named-site geocoded | Weaker geography visible |
| ---: | ---: | ---: |
| {coordinate_review.direct_coordinate_feature_count} | {coordinate_review.named_site_geocoded_feature_count} | {coordinate_review.weaker_geography_feature_count} |

## Uncertainty Register

| Subject | Uncertainty kind | Severity | Reason | Impact |
| --- | --- | --- | --- | --- |
{uncertainty_rows}

## Scenario Assessments

| Scenario | Claim scope | Current posture | Usable evidence | Blockers |
| --- | --- | --- | --- | --- |
{scenario_rows}
"""
