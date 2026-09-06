"""Tests for source-exact modeled-context playback."""

from __future__ import annotations

from copy import deepcopy

import pytest

from bijux_pollenomics.reporting.map_playback import (
    PlaybackContractError,
    build_modeled_context_storyboards,
)
from tests.unit.reporting.map_playback.support import NORDIC_COUNTRIES, modeled_manifest


def test_every_modeled_metric_keeps_all_exact_source_windows() -> None:
    stories = build_modeled_context_storyboards(
        modeled_manifest(), countries=NORDIC_COUNTRIES
    )

    assert len(stories) == 47
    assert len({story.selector_value for story in stories}) == 47
    assert len({story.story_id for story in stories}) == 47
    assert all("." not in story.story_id for story in stories)
    assert (
        next(
            story.story_id for story in stories if story.selector_value == "Cerealia.t"
        )
        == "pangaea-937075-metric-cerealia-t"
    )
    assert {len(story.frames) for story in stories} == {25}
    open_land = next(story for story in stories if story.selector_value == "OL")
    assert open_land.frames[0].as_dict() == {
        "ordinal": 0,
        "time_start_bp": 11_200,
        "time_end_bp": 11_700,
        "label": "11200-11700 BP",
        "source_window_label": "11200-11700 BP",
        "feature_count": 75,
    }
    assert open_land.frames[-1].source_window_label == "0-100 BP"
    assert all(story.evidence_role == "modeled_context" for story in stories)
    assert all(story.interpolation_allowed is False for story in stories)
    assert all(story.propagation_claim_allowed is False for story in stories)
    serialized = open_land.as_dict()
    frames = serialized["frames"]
    assert isinstance(frames, list)
    assert frames[0]["story_kind"] == "modeled_context"
    assert frames[0]["metric_family_key"] == "source_land_cover_types"
    assert frames[0]["metric_key"] == "OL"
    assert frames[0]["basemap"] == "none"
    assert frames[0]["countries"] == list(NORDIC_COUNTRIES)


@pytest.mark.parametrize(
    "mutation", ["missing_window", "interpolation", "metric_count"]
)
def test_incomplete_or_promoted_modeled_context_fails_closed(mutation: str) -> None:
    manifest = deepcopy(modeled_manifest())
    if mutation == "missing_window":
        windows = manifest["windows_oldest_to_present"]
        assert isinstance(windows, list)
        windows.pop()
    elif mutation == "interpolation":
        manifest["interpolation_allowed"] = True
    else:
        manifest["metric_count"] = 46

    with pytest.raises(PlaybackContractError):
        build_modeled_context_storyboards(manifest, countries=NORDIC_COUNTRIES)


def test_modeled_metric_story_id_normalization_must_remain_unique() -> None:
    manifest = deepcopy(modeled_manifest())
    families = manifest["metric_families"]
    assert isinstance(families, list)
    family = next(
        row
        for row in families
        if isinstance(row, dict)
        and isinstance(row.get("metrics"), list)
        and any(
            isinstance(metric, dict) and metric.get("key") == "Cerealia.t"
            for metric in row["metrics"]
        )
    )
    metrics = family["metrics"]
    assert isinstance(metrics, list)
    metrics.append({"key": "Cerealia-t", "label": "Colliding cereal metric"})
    family["metric_count"] = len(metrics)
    manifest["metric_count"] = 48

    with pytest.raises(PlaybackContractError, match="identifiers collide"):
        build_modeled_context_storyboards(manifest, countries=NORDIC_COUNTRIES)
