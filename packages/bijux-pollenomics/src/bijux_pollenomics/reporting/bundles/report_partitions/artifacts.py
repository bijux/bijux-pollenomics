"""Stable root-level artifact identities emitted by report partitions."""

_PUBLIC_ANIMAL_STEMS = (
    "animal_country_species_coverage",
    "animal_output_honesty",
    "animal_human_chronology_overlap",
    "animal_pollen_chronology_overlap",
    "animal_first_appearance_by_country",
    "animal_atlas_readiness",
    "animal_atlas_exclusion_report",
    "nordic_farming_history_scenario",
)
_ANIMAL_FOUNDATION_STEMS = (
    "animal_foundation_validation",
    "animal_cross_surface_drift",
    "animal_scientific_caveat_ledger",
    "animal_point_evidence_review",
    "animal_project_publication_gap_review",
    "animal_foundation_review",
    "animal_sample_chronology_review",
    "animal_temporal_comparison_review",
    "animal_intake_recovery_review",
    "animal_sample_database_review",
    "animal_publication_release_gate",
)


def scientific_artifact_inventory() -> dict[str, str]:
    """Return summary identities for every foundation-owned scientific artifact."""
    public_artifacts = {
        key: filename
        for stem in _PUBLIC_ANIMAL_STEMS
        for key, filename in (
            (f"{stem}_json", f"{stem}.json"),
            (f"{stem}_markdown", f"{stem}.md"),
        )
    }
    foundation_json = {
        f"{stem}_json": f"{stem}.json" for stem in _ANIMAL_FOUNDATION_STEMS
    }
    foundation_markdown = {
        f"{stem}_markdown": f"{stem}.md" for stem in _ANIMAL_FOUNDATION_STEMS
    }
    return public_artifacts | foundation_json | foundation_markdown
