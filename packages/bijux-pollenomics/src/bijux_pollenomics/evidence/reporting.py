from __future__ import annotations

import json
from pathlib import Path

from .models import AtlasEvidenceSurface

__all__ = [
    "build_atlas_evidence_surface_payload",
    "render_atlas_evidence_surface_markdown",
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
            f"{', '.join(profile.unmapped_animal_context_species) or 'none'} | "
            f"{', '.join(profile.too_weak_animal_species) or 'none'} | "
            f"{profile.caution_note} |"
        )
        for profile in surface.country_profiles
    )
    if not country_rows:
        country_rows = "| No countries | - | 0 | 0 | none | none | - |"

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

| Country | Evidence posture | Human localities | Human samples | Unmapped animal context | Too weak animal species | Caution |
| --- | --- | ---: | ---: | --- | --- | --- |
{country_rows}

## Refusals

| Subject | Reason | Detail |
| --- | --- | --- |
{refusal_rows}
"""
