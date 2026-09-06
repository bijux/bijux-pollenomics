"""Opt-in real-browser replay proof for deterministic atlas frame capture."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from bijux_pollenomics_dev.ci.atlas_browser.contracts import AtlasCandidate
from bijux_pollenomics_dev.ci.atlas_media import (
    AtlasMediaPlan,
    StorySelection,
    load_storyboard_manifest,
    select_stories,
)
from bijux_pollenomics_dev.ci.atlas_media.source_authority import (
    load_source_chronology_authority,
)
from bijux_pollenomics_dev.ci.atlas_media import admission, capture


def _command(root: Path, *arguments: str) -> str:
    git = shutil.which("git")
    if git is None:
        pytest.skip("git is required for candidate-bound browser replay")
    completed = subprocess.run(  # nosec B603
        (git, *arguments),
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def _required_binary(name: str, fallback: str | None = None) -> Path:
    value = shutil.which(name)
    if value is not None:
        return Path(value)
    if fallback is not None and Path(fallback).is_file():
        return Path(fallback)
    pytest.skip(f"{name} is required for real atlas browser replay")


@pytest.mark.skipif(
    os.environ.get("BIJUX_RUN_ATLAS_BROWSER_DETERMINISM") != "1",
    reason="set BIJUX_RUN_ATLAS_BROWSER_DETERMINISM=1 for real Brave replay",
)
def test_real_atlas_frame_is_pixel_identical_across_browser_replays() -> None:
    repository_root = Path(__file__).resolve().parents[4]
    if _command(
        repository_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=no",
    ):
        pytest.skip("real browser replay requires an immutable tracked candidate")
    atlas_document = "docs/report/regions/nordic/nordic_map.html"
    atlas_manifest = "docs/report/regions/nordic/nordic_map_assets.json"
    storyboard_manifest = "docs/report/regions/nordic/nordic_playback_storyboards.json"
    atlas = load_storyboard_manifest(
        repository_root / storyboard_manifest,
        repository_root / atlas_manifest,
    )
    identity = atlas["atlas_identity"]
    assert isinstance(identity, dict)
    candidate = AtlasCandidate(
        repository_head=_command(repository_root, "rev-parse", "HEAD"),
        repository_tree=_command(repository_root, "rev-parse", "HEAD^{tree}"),
        atlas_output_commit=_command(
            repository_root,
            "log",
            "-1",
            "--format=%H",
            "--",
            atlas_document,
        ),
        build_id=str(identity["build_id"]),
    )
    stories = select_stories(
        atlas,
        StorySelection(
            include_core_source_stories=False,
            exact_taxa=("source:neotoma:taxon:967",),
            modeled_metrics=(),
        ),
        source_authority=load_source_chronology_authority(
            repository_root, repository_root / atlas_manifest
        ),
    )
    expected_counts = stories[0].expected_visible_feature_counts
    assert expected_counts is not None
    story = replace(
        stories[0],
        frames=(stories[0].frames[0],),
        expected_visible_feature_counts=(expected_counts[0],),
    )
    candidate_succession = atlas["candidate_succession"]
    assert isinstance(candidate_succession, dict)
    evidence_root = (
        repository_root
        / "artifacts/test-runs/atlas-media-browser-determinism"
        / candidate.repository_head[:12]
    )
    assert not evidence_root.exists(), (
        "browser replay evidence already exists; provide a fresh candidate commit"
    )
    browser = _required_binary(
        "brave",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    )
    node = _required_binary("node")
    ffmpeg = _required_binary("ffmpeg")
    ffprobe = _required_binary("ffprobe")
    frame_digests = []
    for replay in ("first", "second"):
        artifact_root = evidence_root / replay
        artifact_root.mkdir(parents=True)
        plan = AtlasMediaPlan(
            repository_root=repository_root,
            artifact_root=artifact_root,
            browser_binary=browser,
            node_binary=node,
            ffmpeg_binary=ffmpeg,
            ffprobe_binary=ffprobe,
            atlas_document=atlas_document,
            atlas_manifest=atlas_manifest,
            storyboard_manifest=storyboard_manifest,
            candidate=candidate,
            selection=StorySelection(
                include_core_source_stories=False,
                exact_taxa=("source:neotoma:taxon:967",),
                modeled_metrics=(),
            ),
            width=960,
            height=600,
            timeout_seconds=60,
        )
        capture._render_frames(
            plan,
            (story,),
            candidate_succession=dict(candidate_succession),
            static_root=admission._materialize_candidate_inputs(plan),
        )
        frame = artifact_root / "frames" / story.story_id / "000000.png"
        frame_digests.append(hashlib.sha256(frame.read_bytes()).hexdigest())

    assert frame_digests[0] == frame_digests[1]
