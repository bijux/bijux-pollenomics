"""Tests for literal-source observation chronology playback."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from bijux_pollenomics.reporting.map_playback import (
    PlaybackContractError,
    build_exact_taxon_storyboard,
    build_source_chronology_storyboards,
)
from bijux_pollenomics.reporting.source_chronology.source_label_presets import (
    build_neotoma_source_label_preset_catalog,
)
from tests.unit.reporting.map_playback.support import (
    NORDIC_COUNTRIES,
    mutable_source_layers,
    source_layers,
)


def test_core_source_stories_partition_observed_extents_oldest_to_present() -> None:
    result = build_source_chronology_storyboards(
        source_layers(), countries=NORDIC_COUNTRIES
    )
    stories, exact_taxa = result
    by_selector = {story.selector_value: story for story in stories}

    assert set(by_selector) == {
        "all",
        "TRSH",
        "UPHE",
        "AQVP",
        "avena",
        "hordeum",
        "triticum",
        "secale",
        "cerealia",
    }
    assert {
        key: len(by_selector[key].frames) for key in ("all", "TRSH", "UPHE", "AQVP")
    } == {
        "all": 230,
        "TRSH": 230,
        "UPHE": 230,
        "AQVP": 192,
    }
    preset_stories = [
        story for story in stories if story.selector_kind == "source_label_preset"
    ]
    assert [story.story_id for story in preset_stories] == [
        "neotoma-source-preset-avena",
        "neotoma-source-preset-hordeum",
        "neotoma-source-preset-triticum",
        "neotoma-source-preset-secale",
        "neotoma-source-preset-cerealia",
    ]
    assert all(
        story.title.startswith("Neotoma literal exact-ID union — ")
        and story.selector_family == "literal_source_label_membership"
        and story.site_count is not None
        for story in preset_stories
    )
    preset_frame = by_selector["avena"].as_dict()["frames"][0]
    assert preset_frame["source_level"] == "source_taxon"
    assert preset_frame["source_taxon"] == "all"
    assert preset_frame["source_preset"] == "avena"
    for selector in ("all", "TRSH", "UPHE", "AQVP"):
        assert by_selector[selector].frames[0].older_bp in {22_911, 19_190}
        assert by_selector[selector].frames[-1].younger_bp == 0
    for story in stories:
        assert story.evidence_role == "observation_chronology"
        assert story.propagation_claim_allowed is False
        assert story.interpolation_allowed is False
        assert story.edge_count == 0
        assert all(
            older.younger_bp == newer.older_bp
            for older, newer in zip(story.frames, story.frames[1:], strict=False)
        )

    assert len(exact_taxa) == 972
    assert len({taxon.feature_key for taxon in exact_taxa}) == 972
    assert all(
        taxon.as_dict()["story_materialization"] == "user_selected_only"
        for taxon in exact_taxa
    )
    assert not any("taxon" in story.story_id for story in stories)
    serialized = by_selector["TRSH"].as_dict()
    assert serialized["site_count"] == 1
    frames = serialized["frames"]
    assert isinstance(frames, list)
    assert frames[0] == {
        "ordinal": 0,
        "time_start_bp": 22_811,
        "time_end_bp": 22_911,
        "label": "22811–22911 BP",
        "source_window_label": None,
        "feature_count": None,
        "basemap": "none",
        "countries": ["Denmark", "Finland", "Norway", "Sweden"],
        "story_kind": "source_chronology",
        "source_level": "source_ecological_code",
        "source_code": "TRSH",
    }


def test_exact_taxon_story_is_materialized_only_after_explicit_selection() -> None:
    default_stories, exact_taxa = build_source_chronology_storyboards(
        source_layers(), countries=NORDIC_COUNTRIES
    )

    selected = build_exact_taxon_storyboard(exact_taxa[0], countries=NORDIC_COUNTRIES)
    frames = selected.as_dict()["frames"]
    assert isinstance(frames, list)
    assert selected not in default_stories
    assert selected.title == (
        f"Neotoma exact source-reported taxon — {exact_taxa[0].label}"
    )
    assert frames[0]["story_kind"] == "source_chronology"
    assert frames[0]["source_level"] == "source_taxon"
    assert frames[0]["source_taxon"] == exact_taxa[0].feature_key
    assert frames[0]["countries"] == list(NORDIC_COUNTRIES)
    assert selected.site_count == exact_taxa[0].site_count
    assert selected.as_dict()["site_count"] == exact_taxa[0].site_count


def test_exact_instant_taxon_remains_discoverable_and_capturable() -> None:
    _stories, exact_taxa = build_source_chronology_storyboards(
        source_layers(), countries=NORDIC_COUNTRIES
    )
    zero_duration = replace(
        exact_taxa[0],
        older_bp=exact_taxa[0].younger_bp,
    )

    assert zero_duration.as_dict()["story_materialization"] == "user_selected_only"
    selected = build_exact_taxon_storyboard(
        zero_duration,
        countries=NORDIC_COUNTRIES,
    )
    frames = selected.as_dict()["frames"]
    assert isinstance(frames, list)
    assert len(frames) == 1
    assert frames[0]["time_start_bp"] == frames[0]["time_end_bp"]


def test_playback_contracts_are_immutable() -> None:
    stories, exact_taxa = build_source_chronology_storyboards(
        source_layers(), countries=NORDIC_COUNTRIES
    )

    with pytest.raises(FrozenInstanceError):
        stories[0].title = "changed"
    with pytest.raises(FrozenInstanceError):
        exact_taxa[0].label = "changed"


@pytest.mark.parametrize(
    "mutation", ["promoted", "edge", "reversed_interval", "density_drift"]
)
def test_unsupported_source_semantics_fail_closed(mutation: str) -> None:
    layers = mutable_source_layers()
    if mutation == "promoted":
        layers[0]["propagation_status"] = "available"
    elif mutation == "edge":
        layers[1]["edge_count"] = 1
    elif mutation == "reversed_interval":
        facets = layers[0]["facet_metadata"]
        assert isinstance(facets, dict)
        facets["time_min_bp"] = 30_000
    else:
        facets = layers[1]["facet_metadata"]
        assert isinstance(facets, dict)
        rows = facets["source_ecological_codes"]
        assert isinstance(rows, list) and isinstance(rows[0], dict)
        density = rows[0]["time_density"]
        assert isinstance(density, dict)
        density["node_count"] = 0

    with pytest.raises(PlaybackContractError):
        build_source_chronology_storyboards(layers, countries=NORDIC_COUNTRIES)


def test_missing_required_literal_code_fails_closed() -> None:
    layers = mutable_source_layers()
    facets = layers[1]["facet_metadata"]
    assert isinstance(facets, dict)
    rows = facets["source_ecological_codes"]
    assert isinstance(rows, list)
    facets["source_ecological_codes"] = [
        row for row in rows if isinstance(row, dict) and row["value"] != "AQVP"
    ]

    with pytest.raises(PlaybackContractError, match="AQVP"):
        build_source_chronology_storyboards(layers, countries=NORDIC_COUNTRIES)


def test_legacy_facet_schema_is_rejected_instead_of_silently_mutated() -> None:
    layers = mutable_source_layers()
    facets = layers[0]["facet_metadata"]
    assert isinstance(facets, dict)
    facets["schema_version"] = "neotoma-source-chronology-facets.v3"

    with pytest.raises(PlaybackContractError, match="contract is incompatible"):
        build_source_chronology_storyboards(layers, countries=NORDIC_COUNTRIES)


@pytest.mark.parametrize(
    "mutation",
    ["country_omitted", "country_name", "preset_propagation", "foreign_catalog"],
)
def test_complete_v4_accountability_is_required_for_playback(mutation: str) -> None:
    layers = mutable_source_layers()
    facets = layers[2]["facet_metadata"]
    assert isinstance(facets, dict)
    countries = facets["country_counts"]
    assert isinstance(countries, list) and isinstance(countries[0], dict)
    accountability = facets["source_label_preset_accountability"]
    assert isinstance(accountability, dict)
    presets = accountability["presets"]
    assert isinstance(presets, list) and isinstance(presets[0], dict)

    if mutation == "country_omitted":
        countries.pop()
    elif mutation == "country_name":
        countries[0]["value"] = "Not Sweden"
    elif mutation == "preset_propagation":
        presets[0]["propagation_allowed"] = True
    else:
        catalog = build_neotoma_source_label_preset_catalog(
            source_snapshot_id="sha256:" + "c" * 64,
            build_id="sha256:" + "d" * 64,
        )
        facets["source_label_preset_catalog"] = catalog
        accountability["catalog_content_sha256"] = catalog["content_sha256"]

    with pytest.raises(PlaybackContractError, match="accountability is incompatible"):
        build_source_chronology_storyboards(layers, countries=NORDIC_COUNTRIES)


def test_playback_requires_one_shared_layer_source_identity() -> None:
    layers = mutable_source_layers()
    layers[0]["source_snapshot_id"] = "sha256:" + "c" * 64

    with pytest.raises(PlaybackContractError, match="do not share one source identity"):
        build_source_chronology_storyboards(layers, countries=NORDIC_COUNTRIES)


def test_preset_site_union_tampering_is_reconciled_against_layer_features() -> None:
    layers = mutable_source_layers()
    facets = layers[2]["facet_metadata"]
    assert isinstance(facets, dict)
    accountability = facets["source_label_preset_accountability"]
    assert isinstance(accountability, dict)
    presets = accountability["presets"]
    assert isinstance(presets, list) and isinstance(presets[0], dict)
    avena = presets[0]
    avena["site_count"] = 1
    countries = avena["country_counts"]
    assert isinstance(countries, list) and isinstance(countries[0], dict)
    countries[0]["site_count"] = 1

    with pytest.raises(PlaybackContractError, match="feature aggregate differs"):
        build_source_chronology_storyboards(layers, countries=NORDIC_COUNTRIES)


def test_country_selection_must_be_explicit_and_canonical() -> None:
    with pytest.raises(PlaybackContractError, match="canonical tuple"):
        build_source_chronology_storyboards(
            source_layers(), countries=("Sweden", "Denmark")
        )


def test_explicit_zero_observation_layers_publish_no_playback() -> None:
    layers = mutable_source_layers()

    def empty_accountability(row: dict[str, object]) -> None:
        row.update(
            {
                "site_count": 0,
                "node_count": 0,
                "observation_denominator": 0,
                "time_min_bp": None,
                "time_max_bp": None,
            }
        )
        density = row.get("time_density")
        if isinstance(density, dict):
            density.update(
                {
                    "node_count": 0,
                    "observation_denominator": 0,
                    "time_min_bp": None,
                    "time_max_bp": None,
                    "bins": [],
                }
            )
        countries = row.get("country_counts")
        if isinstance(countries, list):
            for country in countries:
                assert isinstance(country, dict)
                country.update(
                    {
                        "site_count": 0,
                        "node_count": 0,
                        "observation_denominator": 0,
                        "time_min_bp": None,
                        "time_max_bp": None,
                    }
                )

    for layer in layers:
        layer["count"] = 0
        layer["features"] = []
        facets = layer["facet_metadata"]
        assert isinstance(facets, dict)
        empty_accountability(facets)
        facets["source_ecological_codes"] = []
        facets["source_taxa"] = []
        facets["source_unit_counts"] = []
        preset_accountability = facets.get("source_label_preset_accountability")
        if isinstance(preset_accountability, dict):
            preset_rows = preset_accountability["presets"]
            assert isinstance(preset_rows, list)
            for preset in preset_rows:
                assert isinstance(preset, dict)
                empty_accountability(preset)
            union = preset_accountability["union"]
            assert isinstance(union, dict)
            empty_accountability(union)

    result = build_source_chronology_storyboards(
        layers, countries=NORDIC_COUNTRIES
    )
    assert result.stories == ()
    assert result.exact_taxa == ()
