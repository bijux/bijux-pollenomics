from __future__ import annotations

from bijux_pollenomics.adna import AdnaChronology, AdnaCoordinate, AdnaLocalityIdentity
from bijux_pollenomics.adna.models import AdnaLocalitySummary
from bijux_pollenomics.data_downloader.models import ContextPointRecord
from bijux_pollenomics.evidence import (
    build_scientific_review_surface,
    render_scientific_review_surface_markdown,
)


def test_scientific_review_surface_exposes_country_and_period_coverage() -> None:
    surface = build_scientific_review_surface(
        countries=("Sweden", "Norway"),
        human_localities=(build_human_locality(country="Sweden"),),
        context_points=(build_context_point(layer_key="neotoma-pollen"),),
    )

    assert surface.schema_version == "scientific-review-surface.v3"
    assert any(
        row.species_latin_name == "Ovis aries" for row in surface.country_coverage
    )
    assert any(row.period_label == "1001-3000 BP" for row in surface.period_coverage)
    assert surface.animal_coordinate_review.named_site_geocoded_feature_count == 0


def test_scientific_review_surface_keeps_nonhuman_chronology_not_comparable() -> None:
    surface = build_scientific_review_surface(
        countries=("Sweden",),
        human_localities=(build_human_locality(country="Sweden"),),
        context_points=(build_context_point(layer_key="sead-sites"),),
    )

    nonhuman_row = next(
        row
        for row in surface.chronology_overlaps
        if row.species_latin_name == "Ovis aries"
    )

    assert nonhuman_row.overlap_status == "not_comparable_project_level_only"
    assert "project-level" in nonhuman_row.rationale


def test_scientific_review_surface_marks_scenarios_as_scope_limited() -> None:
    surface = build_scientific_review_surface(
        countries=("Sweden",),
        human_localities=(build_human_locality(country="Sweden"),),
        context_points=(build_context_point(layer_key="landclim-sites"),),
    )

    scenarios = {row.scenario_key: row for row in surface.scenarios}

    assert scenarios["nordic_farming_arrival"].current_posture == "exploratory_only"
    assert scenarios["cattle_management_split"].claim_scope == "descriptive"


def test_scientific_review_surface_markdown_makes_scope_and_blockers_explicit() -> None:
    surface = build_scientific_review_surface(
        countries=("Sweden",),
        human_localities=(build_human_locality(country="Sweden"),),
        context_points=(build_context_point(layer_key="landclim-sites"),),
    )

    markdown = render_scientific_review_surface_markdown(surface)

    assert "# Scientific Review Surface" in markdown
    assert "Exploratory Scope" in markdown
    assert "Animal Coordinate Review" in markdown
    assert "nordic_farming_arrival" in markdown
    assert (
        "animal_evidence_not_yet_dense_enough_for_fieldwork_recommendation" in markdown
    )


def build_human_locality(*, country: str) -> AdnaLocalitySummary:
    return AdnaLocalitySummary(
        identity=AdnaLocalityIdentity(
            namespace="aadr-locality",
            stable_token="homo-sapiens:uppsala",
            locality_text="Uppsala",
            political_entity=country,
            source_anchor_tokens=("SE1",),
        ),
        species_latin_name="Homo sapiens",
        species_common_name="human",
        source_family="AADR",
        source_releases=("v66",),
        record_modalities=("metadata_only",),
        review_strengths=("published_release",),
        provenance_qualities=("curated_release",),
        locality="Uppsala",
        coordinates=AdnaCoordinate(
            latitude=59.8586,
            longitude=17.6389,
            latitude_text="59.8586",
            longitude_text="17.6389",
            confidence="exact",
        ),
        sample_count=2,
        sample_ids=("SE1", "SE2"),
        datasets=("1240k", "ho"),
        chronology=AdnaChronology(
            original_text="2450-2550 BP",
            time_start_bp=2450,
            time_end_bp=2550,
            time_mean_bp=2500,
            dating_basis="bp_window",
        ),
        sample_namespace="aadr-sample",
    )


def build_context_point(*, layer_key: str) -> ContextPointRecord:
    return ContextPointRecord(
        source="Context",
        layer_key=layer_key,
        layer_label=layer_key,
        category="environment",
        country="Sweden",
        record_id="ctx-1",
        name="Context 1",
        latitude=59.9,
        longitude=17.7,
        geometry_type="Point",
        subtitle="environment",
        description="Context point",
        source_url="https://example.org/context",
        record_count=1,
        popup_rows=(),
        time_start_bp=2400,
        time_end_bp=2600,
        time_mean_bp=2500,
        time_label="2400-2600 BP",
    )
