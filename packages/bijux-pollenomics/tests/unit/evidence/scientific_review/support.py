"""Builders for focused scientific-review tests."""

from __future__ import annotations

from bijux_pollenomics.adna import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaLocalitySummary,
)
from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.evidence.models import AtlasEvidenceSpeciesRow


def locality(
    *,
    species: str = "Homo sapiens",
    country: str = "Sweden",
    younger_bp: int | None = 100,
    older_bp: int | None = 200,
    mean_bp: int | None = 150,
    coordinate_confidence: str = "exact",
) -> AdnaLocalitySummary:
    token = species.lower().replace(" ", "-")
    return AdnaLocalitySummary(
        identity=AdnaLocalityIdentity(
            namespace="test-locality",
            stable_token=f"{token}:site",
            locality_text="Test site",
            political_entity=country,
            source_anchor_tokens=(f"{token}-1",),
        ),
        species_latin_name=species,
        species_common_name="test species",
        source_family="test",
        source_releases=("test-release",),
        record_modalities=("metadata_only",),
        review_strengths=("published_release",),
        provenance_qualities=("curated_release",),
        locality="Test site",
        coordinates=AdnaCoordinate(
            latitude=59.0,
            longitude=17.0,
            latitude_text="59.0",
            longitude_text="17.0",
            confidence=coordinate_confidence,
        ),
        sample_count=1,
        sample_ids=(f"{token}-1",),
        datasets=("test",),
        chronology=AdnaChronology(
            original_text="test chronology",
            time_start_bp=younger_bp,
            time_end_bp=older_bp,
            time_mean_bp=mean_bp,
            dating_basis="bp_window",
        ),
        sample_namespace="test-sample",
    )


def context_point(
    *,
    layer_key: str = "test-context",
    younger_bp: int | None = 200,
    older_bp: int | None = 300,
) -> ContextPointRecord:
    return ContextPointRecord(
        source="test",
        layer_key=layer_key,
        layer_label="Test context",
        category="environment",
        country="Sweden",
        record_id="context-1",
        name="Test context",
        latitude=59.0,
        longitude=17.0,
        geometry_type="Point",
        subtitle="test",
        description="Test context point",
        source_url="https://example.org/context",
        record_count=1,
        popup_rows=(),
        time_start_bp=younger_bp,
        time_end_bp=older_bp,
        time_mean_bp=None,
        time_label="test chronology",
    )


def species_row(
    *,
    species: str = "Ovis aries",
    contribution_role: str = "contextual",
    blocking_reasons: tuple[str, ...] = (),
) -> AtlasEvidenceSpeciesRow:
    return AtlasEvidenceSpeciesRow(
        species_latin_name=species,
        species_common_name="test animal",
        support_status="tracked",
        product_role="animal_context",
        dataset_bucket="review",
        contribution_role=contribution_role,
        interaction_posture="suggestive_only",
        mapped_direct_record_count=0,
        curated_project_count=2,
        study_summary_count=1,
        chronology_posture="project_level_only",
        geography_posture="project_level_only",
        contextual_layer_dependencies=(),
        blocking_reasons=blocking_reasons,
        rationale=("test",),
    )
