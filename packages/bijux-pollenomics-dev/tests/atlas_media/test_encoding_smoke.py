"""Real deterministic ffmpeg and ffprobe reconciliation smoke tests."""

from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
import shutil
import subprocess

import pytest

from bijux_pollenomics_dev.ci.atlas_media import encoding
from bijux_pollenomics_dev.ci.atlas_media.contracts import SelectedStory
from tests.atlas_media.fixtures import COUNTRIES, plan


def _two_frame_story() -> SelectedStory:
    frames: tuple[dict[str, object], ...] = tuple(
        {
            "ordinal": ordinal,
            "story_kind": "source_chronology",
            "source_level": "source_sample_presence",
            "time_start_bp": younger,
            "time_end_bp": older,
            "feature_count": None,
            "countries": list(COUNTRIES),
            "basemap": "none",
        }
        for ordinal, younger, older in ((0, 100, 200), (1, 0, 100))
    )
    return SelectedStory(
        story_id="source-sample",
        title="Source sample presence",
        evidence_role="observation_chronology",
        selector_kind="source_sample_presence",
        selector_value="all",
        node_count=10,
        observation_denominator=20,
        expected_visible_feature_counts=(1, 1),
        source_authority_sha256="1" * 64,
        frames=frames,
    )


def _write_source_frames(ffmpeg: Path, root: Path, story: SelectedStory) -> None:
    frame_root = root / "frames" / story.story_id
    frame_root.mkdir(parents=True)
    for ordinal, color in enumerate(("#8b1a1a", "#1a4f8b")):
        completed = subprocess.run(
            (
                str(ffmpeg),
                "-hide_banner",
                "-loglevel",
                "error",
                "-nostdin",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c={color}:s=640x480:d=0.1",
                "-frames:v",
                "1",
                "-threads",
                "1",
                str(frame_root / f"{ordinal:06d}.png"),
            ),
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stderr


def _capture_frames(root: Path, story: SelectedStory) -> list[dict[str, object]]:
    rows = []
    for ordinal in range(len(story.frames)):
        path = root / "frames" / story.story_id / f"{ordinal:06d}.png"
        payload = path.read_bytes()
        rows.append(
            {
                "ordinal": ordinal,
                "file": f"frames/{story.story_id}/{ordinal:06d}.png",
                "png_sha256": hashlib.sha256(payload).hexdigest(),
                "byte_count": len(payload),
            }
        )
    return rows


def test_real_encodes_are_byte_identical_and_probe_reconciled(
    tmp_path: Path,
) -> None:
    ffmpeg_value = shutil.which("ffmpeg")
    ffprobe_value = shutil.which("ffprobe")
    if ffmpeg_value is None or ffprobe_value is None:
        pytest.skip("real ffmpeg and ffprobe are required for encoding smoke")
    ffmpeg = Path(ffmpeg_value)
    ffprobe = Path(ffprobe_value)
    story = _two_frame_story()
    encoded: list[dict[str, Path]] = []
    evidence: list[list[dict[str, object]]] = []
    for name in ("first", "second"):
        media_plan = replace(
            plan(tmp_path / name),
            ffmpeg_binary=ffmpeg,
            ffprobe_binary=ffprobe,
            width=640,
            height=480,
            frames_per_second=2,
        )
        _write_source_frames(ffmpeg, media_plan.artifact_root, story)
        assets = encoding._encode_story(
            media_plan, story, _capture_frames(media_plan.artifact_root, story)
        )
        evidence.append(assets)
        encoded.append(
            {
                media_type: media_plan.artifact_root / str(asset["path"])
                for asset in assets
                if (media_type := str(asset["media_type"])) in {"mp4", "gif"}
            }
        )

    assert encoded[0]["mp4"].read_bytes() == encoded[1]["mp4"].read_bytes()
    assert encoded[0]["gif"].read_bytes() == encoded[1]["gif"].read_bytes()
    for assets in evidence:
        by_type = {str(asset["media_type"]): asset for asset in assets}
        assert by_type["poster"]["frame_count"] == 1
        for media_type in ("mp4", "gif"):
            assert by_type[media_type]["frame_count"] == 2
            assert by_type[media_type]["width"] == 640
            assert by_type[media_type]["height"] == 480
            duration = by_type[media_type]["duration_seconds"]
            assert isinstance(duration, (int, float))
            assert float(duration) == pytest.approx(
                1.0,
                abs=0.01,
            )
