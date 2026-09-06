"""Tests for literal-source observation chronology playback."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from bijux_pollenomics.reporting.map_playback import (
    PlaybackContractError,
    build_exact_taxon_storyboard,
    build_source_chronology_storyboards,
)
from tests.unit.reporting.map_playback.support import (
    NORDIC_COUNTRIES,
    mutable_source_layers,
    source_layers,
)


def test_core_source_stories_partition_observed_extents_oldest_to_present() -> None:
    stories, exact_taxa = build_source_chronology_storyboards(
        source_layers(), countries=NORDIC_COUNTRIES
    )
    by_selector = {story.selector_value: story for story in stories}

    assert set(by_selector) == {"all", "TRSH", "UPHE", "AQVP"}
    assert {key: len(story.frames) for key, story in by_selector.items()} == {
        "all": 230,
        "TRSH": 230,
        "UPHE": 230,
        "AQVP": 192,
    }
    for story in stories:
        assert story.evidence_role == "observation_chronology"
        assert story.propagation_claim_allowed is False
        assert story.interpolation_allowed is False
        assert story.edge_count == 0
        assert story.frames[0].older_bp in {22_911, 19_190}
        assert story.frames[-1].younger_bp == 0
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
    assert frames[0]["story_kind"] == "source_chronology"
    assert frames[0]["source_level"] == "source_taxon"
    assert frames[0]["source_taxon"] == exact_taxa[0].feature_key
    assert frames[0]["countries"] == list(NORDIC_COUNTRIES)


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
        stories[0].title = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        exact_taxa[0].label = "changed"  # type: ignore[misc]


@pytest.mark.parametrize("mutation", ["promoted", "edge", "reversed_interval"])
def test_unsupported_source_semantics_fail_closed(mutation: str) -> None:
    layers = mutable_source_layers()
    if mutation == "promoted":
        layers[0]["propagation_status"] = "available"
    elif mutation == "edge":
        layers[1]["edge_count"] = 1
    else:
        facets = layers[0]["facet_metadata"]
        assert isinstance(facets, dict)
        facets["time_min_bp"] = 30_000

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


def test_country_selection_must_be_explicit_and_canonical() -> None:
    with pytest.raises(PlaybackContractError, match="canonical tuple"):
        build_source_chronology_storyboards(
            source_layers(), countries=("Sweden", "Denmark")
        )
