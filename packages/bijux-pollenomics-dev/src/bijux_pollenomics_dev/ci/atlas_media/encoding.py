"""Deterministic atlas frame encoding and media probe evidence."""

from __future__ import annotations

import json
import math
from pathlib import Path
import shutil

from .contracts import AtlasMediaError, AtlasMediaPlan, SelectedStory
from .gallery import media_asset_row, sha256_file
from .poster_selection import poster_frame_ordinal
from .process_execution import _run_logged


def _encode_story(
    plan: AtlasMediaPlan,
    story: SelectedStory,
    capture_frames: list[dict[str, object]],
) -> list[dict[str, object]]:
    frames = plan.artifact_root / "frames" / story.story_id
    if not frames.is_dir():
        raise AtlasMediaError(f"captured PNG inventory differs: {story.story_id}")
    expected = [frames / f"{index:06d}.png" for index in range(len(story.frames))]
    observed = {
        path.name
        for path in frames.iterdir()
        if path.is_file() and path.suffix.casefold() == ".png"
    }
    if observed != {path.name for path in expected} or not all(
        path.is_file() for path in expected
    ):
        raise AtlasMediaError(f"captured PNG inventory differs: {story.story_id}")
    _require_capture_pngs(plan, story, capture_frames)
    media_root = plan.artifact_root / "media"
    media_root.mkdir(exist_ok=True)
    poster = media_root / f"{story.story_id}.poster.png"
    mp4 = media_root / f"{story.story_id}.mp4"
    gif = media_root / f"{story.story_id}.gif"
    poster_ordinal = poster_frame_ordinal(story.evidence_role, capture_frames)
    shutil.copyfile(expected[poster_ordinal], poster)
    pattern = frames / "%06d.png"
    common = (
        str(plan.ffmpeg_binary.resolve()),
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-framerate",
        str(plan.frames_per_second),
        "-i",
        str(pattern),
    )
    _run_logged(
        (
            *common,
            "-map_metadata",
            "-1",
            "-fflags",
            "+bitexact",
            "-c:v",
            "libx264",
            "-flags:v",
            "+bitexact",
            "-preset",
            "slow",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-threads",
            "1",
            "-movflags",
            "+faststart",
            str(mp4),
        ),
        cwd=plan.repository_root,
        stdout_path=plan.artifact_root / f"ffmpeg-{story.story_id}-mp4.stdout.log",
        stderr_path=plan.artifact_root / f"ffmpeg-{story.story_id}-mp4.stderr.log",
        timeout_seconds=max(120, plan.timeout_seconds * 4),
    )
    _run_logged(
        (
            *common,
            "-filter_complex",
            (
                f"[0:v]fps={plan.frames_per_second},split[a][b];"
                "[a]palettegen=stats_mode=diff[p];"
                "[b][p]paletteuse=dither=bayer:diff_mode=rectangle"
            ),
            "-map_metadata",
            "-1",
            "-fflags",
            "+bitexact",
            "-flags:v",
            "+bitexact",
            "-threads",
            "1",
            "-loop",
            "0",
            str(gif),
        ),
        cwd=plan.repository_root,
        stdout_path=plan.artifact_root / f"ffmpeg-{story.story_id}-gif.stdout.log",
        stderr_path=plan.artifact_root / f"ffmpeg-{story.story_id}-gif.stderr.log",
        timeout_seconds=max(120, plan.timeout_seconds * 4),
    )
    probes: dict[str, dict[str, object]] = {}
    for media_type, path in (("poster", poster), ("mp4", mp4), ("gif", gif)):
        _run_logged(
            (
                str(plan.ffmpeg_binary.resolve()),
                "-hide_banner",
                "-loglevel",
                "error",
                "-nostdin",
                "-i",
                str(path),
                "-f",
                "null",
                "-",
            ),
            cwd=plan.repository_root,
            stdout_path=(
                plan.artifact_root
                / f"ffmpeg-{story.story_id}-{media_type}-verify.stdout.log"
            ),
            stderr_path=(
                plan.artifact_root
                / f"ffmpeg-{story.story_id}-{media_type}-verify.stderr.log"
            ),
            timeout_seconds=max(60, plan.timeout_seconds * 2),
        )
        probes[media_type] = _probe_media(
            plan,
            path,
            media_type=media_type,
            expected_frame_count=(1 if media_type == "poster" else len(story.frames)),
        )
    _require_capture_pngs(plan, story, capture_frames)
    assets: list[dict[str, object]] = []
    for media_type, path in (("poster", poster), ("mp4", mp4), ("gif", gif)):
        asset = media_asset_row(plan.artifact_root, path, media_type=media_type)
        asset.update(probes[media_type])
        assets.append(asset)
    return assets


def _require_capture_pngs(
    plan: AtlasMediaPlan,
    story: SelectedStory,
    capture_frames: list[dict[str, object]],
) -> None:
    if len(capture_frames) != len(story.frames):
        raise AtlasMediaError(f"capture frame inventory differs: {story.story_id}")
    frame_root = plan.artifact_root / "frames" / story.story_id
    observed = {
        path.name
        for path in frame_root.iterdir()
        if path.is_file() and path.suffix.casefold() == ".png"
    }
    expected = {f"{ordinal:06d}.png" for ordinal in range(len(story.frames))}
    if observed != expected:
        raise AtlasMediaError(f"captured PNG inventory differs: {story.story_id}")
    for ordinal, row in enumerate(capture_frames):
        path = plan.artifact_root / "frames" / story.story_id / f"{ordinal:06d}.png"
        if (
            row.get("ordinal") != ordinal
            or row.get("file") != f"frames/{story.story_id}/{ordinal:06d}.png"
            or not path.is_file()
            or path.is_symlink()
            or plan.artifact_root.resolve() not in path.resolve().parents
            or row.get("png_sha256") != sha256_file(path)
            or row.get("byte_count") != path.stat().st_size
        ):
            raise AtlasMediaError(f"captured PNG bytes changed: {story.story_id}")


def _probe_media(
    plan: AtlasMediaPlan,
    path: Path,
    *,
    media_type: str,
    expected_frame_count: int,
) -> dict[str, object]:
    stdout_path = plan.artifact_root / f"ffprobe-{path.name}.stdout.log"
    _run_logged(
        (
            str(plan.ffprobe_binary.resolve()),
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-count_frames",
            "-show_entries",
            "stream=width,height,nb_read_frames,duration",
            "-of",
            "json",
            str(path),
        ),
        cwd=plan.repository_root,
        stdout_path=stdout_path,
        stderr_path=plan.artifact_root / f"ffprobe-{path.name}.stderr.log",
        timeout_seconds=max(30, plan.timeout_seconds),
    )
    try:
        payload = json.loads(stdout_path.read_text(encoding="utf-8"))
        streams = payload["streams"]
        stream = streams[0]
        width = stream["width"]
        height = stream["height"]
        frame_count = int(stream["nb_read_frames"])
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise AtlasMediaError(f"ffprobe metadata is invalid: {path.name}") from error
    if (
        len(streams) != 1
        or width != plan.width
        or height != plan.height
        or frame_count != expected_frame_count
    ):
        raise AtlasMediaError(f"encoded media dimensions or frames differ: {path.name}")
    result: dict[str, object] = {
        "width": width,
        "height": height,
        "frame_count": frame_count,
    }
    if media_type != "poster":
        try:
            duration = float(stream["duration"])
        except (KeyError, TypeError, ValueError) as error:
            raise AtlasMediaError(
                f"encoded media duration is absent: {path.name}"
            ) from error
        expected_duration = expected_frame_count / plan.frames_per_second
        if not math.isfinite(duration) or not math.isclose(
            duration,
            expected_duration,
            rel_tol=0,
            abs_tol=(1 / plan.frames_per_second) + 0.01,
        ):
            raise AtlasMediaError(f"encoded media duration differs: {path.name}")
        result["duration_seconds"] = duration
    return result


def _tool_identity(plan: AtlasMediaPlan, *, checkpoint: str) -> dict[str, object]:
    values: dict[str, object] = {}
    for name, binary, arguments in (
        ("node", plan.node_binary, ("--version",)),
        ("ffmpeg", plan.ffmpeg_binary, ("-version",)),
        ("ffprobe", plan.ffprobe_binary, ("-version",)),
        ("brave", plan.browser_binary, ("--version",)),
    ):
        stdout_path = plan.artifact_root / f"tool-{checkpoint}-{name}.stdout.log"
        stderr_path = plan.artifact_root / f"tool-{checkpoint}-{name}.stderr.log"
        _run_logged(
            (str(binary.resolve()), *arguments),
            cwd=plan.repository_root,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            timeout_seconds=plan.timeout_seconds,
        )
        output = stdout_path.read_text(encoding="utf-8") or stderr_path.read_text(
            encoding="utf-8"
        )
        lines = output.splitlines()
        if not lines:
            raise AtlasMediaError(f"cannot identify media tool: {name}")
        values[name] = {
            "binary_sha256": sha256_file(binary.resolve()),
            "version": lines[0].strip(),
        }
    return values


def _encoding_profile(plan: AtlasMediaPlan) -> dict[str, object]:
    return {
        "schema_version": "atlas-media-encoding-profile.v1",
        "width": plan.width,
        "height": plan.height,
        "frames_per_second": plan.frames_per_second,
        "poster": {
            "format": "png",
            "source_frame_selection": "maximum_selected_evidence_earliest_ordinal_on_tie",
        },
        "mp4": {
            "codec": "libx264",
            "preset": "slow",
            "crf": 20,
            "pixel_format": "yuv420p",
            "threads": 1,
            "metadata_removed": True,
            "bitexact": True,
            "faststart": True,
        },
        "gif": {
            "palette_stats_mode": "diff",
            "palette_dither": "bayer",
            "palette_diff_mode": "rectangle",
            "loop": 0,
            "threads": 1,
            "metadata_removed": True,
            "bitexact": True,
        },
    }


def _execution_receipts(root: Path) -> list[dict[str, object]]:
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "byte_count": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(root.glob("*.execution.json"))
    ]
