"""Tests for governed source and modeled storyboard selection."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.reporting.map_playback import canonical_json_bytes
from bijux_pollenomics_dev.ci.atlas_media import (
    AtlasMediaError,
    AtlasMediaPlan,
    StorySelection,
    load_storyboard_manifest,
    select_stories,
)
from tests.atlas_media.fixtures import plan, source_authority


def _manifest(tmp_path: Path) -> tuple[Any, AtlasMediaPlan]:
    media_plan = plan(tmp_path)
    manifest = load_storyboard_manifest(
        media_plan.repository_root / media_plan.storyboard_manifest,
        media_plan.repository_root / media_plan.atlas_manifest,
    )
    return manifest, media_plan


def test_default_selection_covers_core_secale_and_open_land(tmp_path: Path) -> None:
    manifest, media_plan = _manifest(tmp_path)
    stories = select_stories(
        manifest, media_plan.selection, source_authority=source_authority()
    )

    assert [story.story_id for story in stories] == [
        "neotoma-source-sample-presence",
        "neotoma-source-code-trsh",
        "neotoma-source-code-uphe",
        "neotoma-source-code-aqvp",
        "neotoma-source-taxon-secale",
        "pangaea-937075-metric-cerealia-t",
        "pangaea-937075-metric-secale",
        "pangaea-937075-metric-ol",
    ]
    assert all(
        frame["basemap"] == "none" for story in stories for frame in story.frames
    )
    assert all(
        frame["countries"] == ["Denmark", "Finland", "Norway", "Sweden"]
        for story in stories
        for frame in story.frames
    )
    secale = stories[4]
    assert secale.evidence_role == "observation_chronology"
    assert secale.selector_kind == "source_taxon"
    assert secale.node_count == 3
    assert secale.observation_denominator == 4
    assert secale.frames[0]["time_end_bp"] == 236.75
    assert secale.frames[-1]["time_start_bp"] == 36.16162
    assert all(
        newer["time_end_bp"] == older["time_start_bp"]
        for older, newer in zip(secale.frames, secale.frames[1:], strict=False)
    )
    modeled = stories[-1]
    assert modeled.evidence_role == "modeled_context"
    assert modeled.selector_value == "OL"
    assert modeled.frame_feature_denominators == (75,) * 25
    assert len(modeled.frames) == 25
    assert modeled.frames[0]["source_window_label"] == "11200-11700 BP"


def test_selection_requires_exact_four_country_identity(tmp_path: Path) -> None:
    manifest, media_plan = _manifest(tmp_path)
    mutated = deepcopy(manifest)
    mutated["atlas_identity"]["countries"] = ["Denmark", "Sweden"]

    with pytest.raises(AtlasMediaError, match="exact four Nordic countries"):
        select_stories(
            mutated, media_plan.selection, source_authority=source_authority()
        )


@pytest.mark.parametrize("domain", ("source_chronology", "modeled_context"))
def test_selection_refuses_duplicate_story_selectors(
    tmp_path: Path, domain: str
) -> None:
    manifest, media_plan = _manifest(tmp_path)
    mutated = deepcopy(manifest)
    mutated[domain]["stories"].append(deepcopy(mutated[domain]["stories"][0]))
    mutated[domain]["story_count"] += 1

    with pytest.raises(AtlasMediaError, match="duplicate .* story selector"):
        select_stories(
            mutated, media_plan.selection, source_authority=source_authority()
        )


def test_core_source_selector_requires_its_governed_kind(tmp_path: Path) -> None:
    manifest, media_plan = _manifest(tmp_path)
    mutated = deepcopy(manifest)
    story = next(
        row
        for row in mutated["source_chronology"]["stories"]
        if row["selector"]["value"] == "all"
    )
    story["selector"]["kind"] = "source_ecological_code"
    for frame in story["frames"]:
        frame["source_level"] = "source_ecological_code"
        frame["source_code"] = "all"

    with pytest.raises(AtlasMediaError, match="core source selector kind"):
        select_stories(
            mutated, media_plan.selection, source_authority=source_authority()
        )


def test_explicit_instant_taxon_preserves_equal_closed_bounds(tmp_path: Path) -> None:
    manifest, _media_plan = _manifest(tmp_path)
    stories = select_stories(
        manifest,
        StorySelection(
            include_core_source_stories=False,
            exact_taxa=("Exact instant",),
            modeled_metrics=(),
        ),
        source_authority=source_authority(),
    )

    assert len(stories) == 1
    assert len(stories[0].frames) == 1
    frame = stories[0].frames[0]
    assert frame["time_start_bp"] == frame["time_end_bp"] == 100.5


@pytest.mark.parametrize(
    ("domain", "selector", "field", "replacement"),
    (
        ("source_chronology", "TRSH", "source_code", "UPHE"),
        ("modeled_context", "OL", "metric_key", "AL"),
        ("modeled_context", "OL", "metric_family_key", "exact_taxa"),
        ("modeled_context", "OL", "story_kind", "source_chronology"),
    ),
)
def test_each_frame_must_match_its_story_selector(
    tmp_path: Path,
    domain: str,
    selector: str,
    field: str,
    replacement: str,
) -> None:
    manifest, media_plan = _manifest(tmp_path)
    mutated = deepcopy(manifest)
    stories = mutated[domain]["stories"]
    story = next(row for row in stories if row["selector"]["value"] == selector)
    story["frames"][0][field] = replacement

    with pytest.raises(AtlasMediaError, match="selector|kind"):
        select_stories(
            mutated, media_plan.selection, source_authority=source_authority()
        )


@pytest.mark.parametrize("domain", ("source_chronology", "modeled_context"))
@pytest.mark.parametrize("delta", (-0.25, 0.25), ids=("gap", "overlap"))
def test_story_frames_must_have_exact_temporal_continuity(
    tmp_path: Path, domain: str, delta: float
) -> None:
    manifest, media_plan = _manifest(tmp_path)
    mutated = deepcopy(manifest)
    selector = "TRSH" if domain == "source_chronology" else "OL"
    story = next(
        row
        for row in mutated[domain]["stories"]
        if row["selector"]["value"] == selector
    )
    story["frames"][1]["time_end_bp"] = story["frames"][0]["time_start_bp"] + delta

    with pytest.raises(AtlasMediaError, match="exactly continuous"):
        select_stories(
            mutated, media_plan.selection, source_authority=source_authority()
        )


@pytest.mark.parametrize(
    ("domain", "selector", "field", "replacement"),
    (
        ("source_chronology", "TRSH", "node_count", 0),
        ("source_chronology", "TRSH", "observation_denominator", None),
        ("modeled_context", "OL", "feature_count", 0),
    ),
)
def test_story_denominators_are_required_and_positive(
    tmp_path: Path,
    domain: str,
    selector: str,
    field: str,
    replacement: object,
) -> None:
    manifest, media_plan = _manifest(tmp_path)
    mutated = deepcopy(manifest)
    story = next(
        row
        for row in mutated[domain]["stories"]
        if row["selector"]["value"] == selector
    )
    if field == "feature_count":
        story["frames"][0][field] = replacement
    else:
        story[field] = replacement

    with pytest.raises(AtlasMediaError, match="positive"):
        select_stories(
            mutated, media_plan.selection, source_authority=source_authority()
        )


def test_source_denominators_are_bound_to_governed_atlas_assets(
    tmp_path: Path,
) -> None:
    manifest, media_plan = _manifest(tmp_path)
    mutated = deepcopy(manifest)
    story = next(
        row
        for row in mutated["source_chronology"]["stories"]
        if row["selector"]["value"] == "TRSH"
    )
    story["node_count"] = 1
    story["observation_denominator"] = 1

    with pytest.raises(AtlasMediaError, match="governed atlas assets"):
        select_stories(
            mutated, media_plan.selection, source_authority=source_authority()
        )


def test_selection_is_bounded_and_only_one_exact_instant_story_is_allowed(
    tmp_path: Path,
) -> None:
    with pytest.raises(AtlasMediaError, match="exceeds eight"):
        StorySelection(exact_taxa=tuple(f"taxon-{index}" for index in range(9)))
    manifest, _media_plan = _manifest(tmp_path)
    mutated = deepcopy(manifest)
    discovery = mutated["source_chronology"]["exact_taxon_discovery"]
    duplicate = deepcopy(
        next(
            facet for facet in discovery["facets"] if facet["label"] == "Exact instant"
        )
    )
    duplicate["value"] = "source:neotoma:taxon:instant-two"
    duplicate["feature_key"] = "source:neotoma:taxon:instant-two"
    duplicate["source_taxon_id"] = "instant-two"
    duplicate["label"] = "Second instant"
    discovery["facets"].append(duplicate)
    discovery["facet_count"] += 1
    authority = source_authority()
    authority.facets[("source_taxon", "source:neotoma:taxon:instant-two")] = replace(
        authority.facets[("source_taxon", "source:neotoma:taxon:instant")],
        selector_value="source:neotoma:taxon:instant-two",
    )
    with pytest.raises(AtlasMediaError, match="only one exact-instant"):
        select_stories(
            mutated,
            StorySelection(
                include_core_source_stories=False,
                exact_taxa=("Exact instant", "Second instant"),
                modeled_metrics=(),
            ),
            source_authority=authority,
        )


@pytest.mark.parametrize("mutation", ["digest", "identity", "succession", "reason"])
def test_manifest_mutations_fail_closed(tmp_path: Path, mutation: str) -> None:
    media_plan = plan(tmp_path)
    storyboard_path = media_plan.repository_root / media_plan.storyboard_manifest
    value = json.loads(storyboard_path.read_text(encoding="utf-8"))
    if mutation == "digest":
        value["content_sha256"] = "0" * 64
    elif mutation == "identity":
        value["atlas_identity"]["build_id"] = "atlas-" + ("e" * 64)
    elif mutation == "reason":
        value["candidate_succession"]["reason_code"] = "unreviewed_placeholder"
    else:
        value["candidate_succession"]["story_count"] = 1
    if mutation != "digest":
        content = {key: item for key, item in value.items() if key != "content_sha256"}
        value["content_sha256"] = hashlib.sha256(
            canonical_json_bytes(content)
        ).hexdigest()
    storyboard_path.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(AtlasMediaError):
        load_storyboard_manifest(
            storyboard_path,
            media_plan.repository_root / media_plan.atlas_manifest,
        )
