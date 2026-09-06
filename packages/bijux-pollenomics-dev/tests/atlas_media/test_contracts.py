"""Tests for immutable atlas media execution contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.atlas_media import (
    AtlasMediaError,
    SelectedStory,
    StorySelection,
)
from bijux_pollenomics_dev.ci.atlas_media.catalog import (
    DEFAULT_EXACT_TAXA,
    DEFAULT_MODELED_METRICS,
    LEGACY_PUBLICATION_STORY_TUPLES_V1,
    PUBLICATION_ASSET_COUNT,
    PUBLICATION_STORIES,
)
from tests.atlas_media.fixtures import COUNTRIES
from tests.atlas_media.fixtures import plan


def test_plan_requires_dedicated_repository_artifact_output(tmp_path: Path) -> None:
    media_plan = plan(tmp_path)

    assert media_plan.artifact_root == tmp_path / "artifacts/media"
    assert media_plan.selection == StorySelection()
    with pytest.raises(FrozenInstanceError):
        media_plan.width = 10  # type: ignore[misc]
    with pytest.raises(AtlasMediaError, match="even"):
        replace(media_plan, width=641)


def test_default_publication_catalog_has_one_ordered_source_of_truth() -> None:
    assert DEFAULT_EXACT_TAXA == ("source:neotoma:taxon:967",)
    assert DEFAULT_MODELED_METRICS == ("Cerealia.t", "Secale", "OL")
    assert len(PUBLICATION_STORIES) == 8
    assert PUBLICATION_ASSET_COUNT == 16
    assert LEGACY_PUBLICATION_STORY_TUPLES_V1 == (
        (
            "neotoma-source-sample-presence",
            "observation_chronology",
            "source_sample_presence",
            "all",
            None,
        ),
        (
            "neotoma-source-code-trsh",
            "observation_chronology",
            "source_ecological_code",
            "TRSH",
            None,
        ),
        (
            "neotoma-source-code-uphe",
            "observation_chronology",
            "source_ecological_code",
            "UPHE",
            None,
        ),
        (
            "neotoma-source-code-aqvp",
            "observation_chronology",
            "source_ecological_code",
            "AQVP",
            None,
        ),
        (
            "neotoma-source-taxon-967",
            "observation_chronology",
            "source_taxon",
            "source:neotoma:taxon:967",
            None,
        ),
        (
            "pangaea-937075-metric-ol",
            "modeled_context",
            "modeled_metric",
            "OL",
            "source_land_cover_types",
        ),
    )
    assert len({story.story_id for story in PUBLICATION_STORIES}) == 8
    assert (
        len(
            {
                (story.selector_kind, story.selector_value, story.selector_family)
                for story in PUBLICATION_STORIES
            }
        )
        == 8
    )


def test_story_selection_refuses_empty_or_duplicate_requests() -> None:
    with pytest.raises(AtlasMediaError, match="at least one"):
        StorySelection(
            include_core_source_stories=False,
            exact_taxa=(),
            modeled_metrics=(),
        )
    with pytest.raises(AtlasMediaError, match="unique"):
        StorySelection(exact_taxa=("Secale", "Secale"))


def test_sample_presence_selector_is_exactly_all() -> None:
    with pytest.raises(AtlasMediaError, match="must be all"):
        SelectedStory(
            story_id="invalid-sample",
            title="Mislabeled sample presence",
            evidence_role="observation_chronology",
            selector_kind="source_sample_presence",
            selector_value="TRSH",
            node_count=1,
            observation_denominator=1,
            frames=(
                {
                    "ordinal": 0,
                    "story_kind": "source_chronology",
                    "source_level": "source_sample_presence",
                    "time_start_bp": 0,
                    "time_end_bp": 1,
                    "countries": list(COUNTRIES),
                    "basemap": "none",
                },
            ),
        )


def test_plan_refuses_governed_input_symlink_escaping_repository(
    tmp_path: Path,
) -> None:
    media_plan = plan(tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-outside.html"
    outside.write_text("<!doctype html>\n", encoding="utf-8")
    document = media_plan.repository_root / media_plan.atlas_document
    document.unlink()
    document.symlink_to(outside)

    with pytest.raises(AtlasMediaError, match="escapes repository"):
        replace(media_plan, atlas_document=media_plan.atlas_document)


def test_source_story_allows_governed_empty_interval_but_not_empty_playback() -> None:
    frames = (
        {
            "ordinal": 0,
            "story_kind": "source_chronology",
            "source_level": "source_sample_presence",
            "time_start_bp": 100,
            "time_end_bp": 200,
            "countries": list(COUNTRIES),
            "basemap": "none",
        },
        {
            "ordinal": 1,
            "story_kind": "source_chronology",
            "source_level": "source_sample_presence",
            "time_start_bp": 0,
            "time_end_bp": 100,
            "countries": list(COUNTRIES),
            "basemap": "none",
        },
    )
    story = SelectedStory(
        story_id="truthful-empty-interval",
        title="Truthful empty interval",
        evidence_role="observation_chronology",
        selector_kind="source_sample_presence",
        selector_value="all",
        node_count=1,
        observation_denominator=1,
        expected_visible_feature_counts=(0, 1),
        source_authority_sha256="1" * 64,
        frames=frames,
    )
    assert story.expected_visible_feature_counts == (0, 1)
    with pytest.raises(AtlasMediaError, match="nonempty frame visibility"):
        replace(story, expected_visible_feature_counts=(0, 0))
