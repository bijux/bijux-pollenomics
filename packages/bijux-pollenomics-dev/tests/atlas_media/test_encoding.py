from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.atlas_media import AtlasMediaError, encoding
from bijux_pollenomics_dev.ci.atlas_media.poster_selection import (
    poster_frame_ordinal,
)
from tests.atlas_media.fixtures import plan
from tests.atlas_media.receipt_fixtures import build_capture_frames, make_story


def test_poster_selection_uses_maximum_evidence_and_earliest_tie() -> None:
    source_frames = [
        {"visible_source_chronology_point_count": count} for count in (0, 4, 4, 2)
    ]
    modeled_frames = [
        {"visible_modeled_context_feature_count": count} for count in (0, 75, 12)
    ]

    assert poster_frame_ordinal("observation_chronology", source_frames) == 1
    assert poster_frame_ordinal("modeled_context", modeled_frames) == 1


def test_ffmpeg_commands_are_single_threaded_and_metadata_free(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    media_plan = plan(tmp_path)
    frame_root = media_plan.artifact_root / "frames/source-sample"
    frame_root.mkdir(parents=True)
    (frame_root / "000000.png").write_bytes(b"png")
    commands: list[tuple[str, ...]] = []

    def fake_run(
        command: tuple[str, ...],
        *,
        cwd: Path,
        stdout_path: Path,
        stderr_path: Path,
        timeout_seconds: float,
    ) -> None:
        assert timeout_seconds > 0
        del cwd
        commands.append(command)
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        if command[-1] != "-":
            Path(command[-1]).write_bytes(b"encoded")

    monkeypatch.setattr(encoding, "_run_logged", fake_run)
    monkeypatch.setattr(
        encoding,
        "_probe_media",
        lambda *_args, media_type, expected_frame_count, **_kwargs: {
            "width": media_plan.width,
            "height": media_plan.height,
            "frame_count": expected_frame_count,
            **(
                {"duration_seconds": 1 / media_plan.frames_per_second}
                if media_type != "poster"
                else {}
            ),
        },
    )

    story = make_story()
    assets = encoding._encode_story(
        media_plan, story, build_capture_frames(media_plan, story)
    )

    assert {asset["media_type"] for asset in assets} == {"poster", "mp4", "gif"}
    mp4 = commands[0]
    assert mp4[mp4.index("-threads") : mp4.index("-threads") + 2] == ("-threads", "1")
    assert "-map_metadata" in mp4
    assert "+bitexact" in mp4
    assert "-flags:v" in mp4
    gif = commands[1]
    assert "-map_metadata" in gif
    assert "-fflags" in gif
    assert "-flags:v" in gif
    assert gif[gif.index("-threads") : gif.index("-threads") + 2] == ("-threads", "1")
    assert (
        "palettegen=stats_mode=diff"
        in commands[1][commands[1].index("-filter_complex") + 1]
    )
    assert len(commands) == 5
    assert all(command[-3:] == ("-f", "null", "-") for command in commands[2:])


def test_encoder_refuses_any_extra_png_before_ffmpeg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    media_plan = plan(tmp_path)
    frame_root = media_plan.artifact_root / "frames/source-sample"
    frame_root.mkdir(parents=True)
    (frame_root / "000000.png").write_bytes(b"expected")
    (frame_root / "000001.png").write_bytes(b"extra-contiguous-frame")
    monkeypatch.setattr(
        encoding,
        "_run_logged",
        lambda *_args, **_kwargs: pytest.fail("ffmpeg must not start"),
    )

    with pytest.raises(AtlasMediaError, match="PNG inventory differs"):
        encoding._encode_story(media_plan, make_story(), [])


def test_encoder_refuses_png_mutation_during_encoding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    media_plan = plan(tmp_path)
    story = make_story()
    frame = media_plan.artifact_root / "frames/source-sample/000000.png"
    frame.parent.mkdir(parents=True)
    frame.write_bytes(b"original")
    capture_frames = build_capture_frames(media_plan, story)

    def mutating_run(
        command: tuple[str, ...],
        *,
        cwd: Path,
        stdout_path: Path,
        stderr_path: Path,
        timeout_seconds: float,
    ) -> None:
        del cwd, timeout_seconds
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        frame.write_bytes(b"mutated")
        if command[-1] != "-":
            Path(command[-1]).write_bytes(b"encoded")

    monkeypatch.setattr(encoding, "_run_logged", mutating_run)
    monkeypatch.setattr(
        encoding,
        "_probe_media",
        lambda *_args, media_type, expected_frame_count, **_kwargs: {
            "width": media_plan.width,
            "height": media_plan.height,
            "frame_count": expected_frame_count,
            **({"duration_seconds": 1.0} if media_type != "poster" else {}),
        },
    )

    with pytest.raises(AtlasMediaError, match="PNG bytes changed"):
        encoding._encode_story(media_plan, story, capture_frames)
