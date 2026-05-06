from __future__ import annotations

from bijux_pollenomics.adna import AdnaChronology, AdnaCoordinate, AdnaLocalityIdentity
from bijux_pollenomics.adna.models import AdnaLocalitySummary
from bijux_pollenomics.data_downloader.models import ContextPointRecord
from bijux_pollenomics.evidence import (
    build_atlas_evidence_surface,
    render_atlas_evidence_surface_markdown,
)


def test_atlas_evidence_surface_keeps_nonhuman_species_contextual_or_refused() -> None:
    surface = build_atlas_evidence_surface(
        countries=("Sweden", "Norway"),
        human_localities=(build_human_locality(country="Sweden"),),
        context_points=(build_context_point(layer_key="neotoma-pollen"),),
    )

    rows = {row.species_latin_name: row for row in surface.species_rows}

    assert rows["Homo sapiens"].contribution_role == "direct"
    assert rows["Ovis aries"].contribution_role == "contextual"
    assert rows["Bos taurus"].interaction_posture == "decreases_confidence"
    assert rows["Gallus gallus domesticus"].contribution_role == "too_weak"


def test_country_profiles_do_not_pretend_animal_context_is_country_assigned() -> None:
    surface = build_atlas_evidence_surface(
        countries=("Sweden",),
        human_localities=(build_human_locality(country="Sweden"),),
        context_points=(build_context_point(layer_key="landclim-sites"),),
    )

    profile = surface.country_profiles[0]

    assert profile.evidence_posture == "human_direct_plus_unmapped_animal_context"
    assert "Ovis aries" in profile.unmapped_animal_context_species
    assert "must not be read as country-assigned animal support" in profile.caution_note


def test_atlas_evidence_surface_markdown_makes_refusals_explicit() -> None:
    surface = build_atlas_evidence_surface(
        countries=("Sweden",),
        human_localities=(build_human_locality(country="Sweden"),),
        context_points=(),
    )

    markdown = render_atlas_evidence_surface_markdown(surface)

    assert "# Atlas Evidence Surface" in markdown
    assert "atlas_proximity_is_not_locality_evidence" in markdown
    assert "Country Evidence Profiles" in markdown


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
