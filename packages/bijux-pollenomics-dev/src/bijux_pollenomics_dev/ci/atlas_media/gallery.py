"""Checksummed gallery manifest for rendered atlas stories."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from .contracts import AtlasMediaError, SelectedStory


def sha256_file(path: Path) -> str:
    """Hash a file without loading a rendered video into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    """Encode deterministic strict JSON."""
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def media_asset_row(root: Path, path: Path, *, media_type: str) -> dict[str, object]:
    """Describe one materialized file relative to the dedicated artifact root."""
    resolved_root = root.resolve()
    if path.is_symlink():
        raise AtlasMediaError("gallery media asset must not be a symlink")
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise AtlasMediaError("gallery media asset is unavailable") from error
    if (
        resolved_root not in resolved.parents
        or not resolved.is_file()
        or resolved.stat().st_size <= 0
    ):
        raise AtlasMediaError("gallery media asset is outside the artifact root")
    return {
        "media_type": media_type,
        "path": resolved.relative_to(resolved_root).as_posix(),
        "byte_count": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def build_gallery_manifest(
    *,
    atlas_identity: dict[str, object],
    candidate_identity: dict[str, object],
    storyboard_sha256: str,
    stories: tuple[SelectedStory, ...],
    assets_by_story: dict[str, list[dict[str, object]]],
    capture_frames_by_story: dict[str, list[dict[str, object]]],
    tool_identity: dict[str, object],
    encoding_profile: dict[str, object],
    execution_receipts: list[dict[str, object]],
    candidate_succession: dict[str, object],
) -> dict[str, object]:
    """Build one content-addressed, semantics-explicit gallery contract."""
    if (
        candidate_succession.get("status") != "refused"
        or candidate_succession.get("product_key") != "candidate_succession"
        or candidate_succession.get("reason_code")
        != "accepted_scientific_classifications_not_available"
        or candidate_succession.get("story_count") != 0
        or candidate_succession.get("edge_count") != 0
        or not isinstance(candidate_succession.get("detail"), str)
        or not candidate_succession["detail"]
    ):
        raise AtlasMediaError("gallery candidate succession posture is not refused")
    _validate_tool_identity(tool_identity)
    _validate_encoding_profile(encoding_profile)
    _validate_execution_receipts(execution_receipts)
    story_rows: list[dict[str, object]] = []
    for story in stories:
        assets = assets_by_story.get(story.story_id)
        capture_frames = capture_frames_by_story.get(story.story_id)
        if not assets or {asset.get("media_type") for asset in assets} != {
            "poster",
            "mp4",
            "gif",
        }:
            raise AtlasMediaError(
                f"story media inventory is incomplete: {story.story_id}"
            )
        if not isinstance(capture_frames, list) or len(capture_frames) != len(
            story.frames
        ):
            raise AtlasMediaError(
                f"story capture inventory is incomplete: {story.story_id}"
            )
        published_capture_frames = [
            _capture_frame_identity(row, ordinal=ordinal, story=story)
            for ordinal, row in enumerate(capture_frames)
        ]
        assets_by_type = {str(asset["media_type"]): asset for asset in assets}
        dimensions = {(asset.get("width"), asset.get("height")) for asset in assets}
        expected_dimensions = {(encoding_profile["width"], encoding_profile["height"])}
        if (
            len(assets) != 3
            or len(assets_by_type) != 3
            or len(dimensions) != 1
            or dimensions != expected_dimensions
            or any(
                isinstance(dimension, bool)
                or not isinstance(dimension, int)
                or dimension <= 0
                for pair in dimensions
                for dimension in pair
            )
            or assets_by_type["poster"].get("frame_count") != 1
            or assets_by_type["poster"].get("sha256")
            != published_capture_frames[0]["png_sha256"]
            or assets_by_type["poster"].get("byte_count")
            != published_capture_frames[0]["byte_count"]
            or any(
                assets_by_type[media_type].get("frame_count") != len(story.frames)
                or not _positive_number(
                    assets_by_type[media_type].get("duration_seconds")
                )
                for media_type in ("mp4", "gif")
            )
        ):
            raise AtlasMediaError(
                f"story media probe evidence differs: {story.story_id}"
            )
        frames = list(story.frames)
        story_rows.append(
            {
                "story_id": story.story_id,
                "title": story.title,
                "evidence_role": story.evidence_role,
                "selector": {
                    "kind": story.selector_kind,
                    "value": story.selector_value,
                    "family": story.selector_family,
                },
                "node_count": story.node_count,
                "observation_denominator": story.observation_denominator,
                "frame_feature_denominators": (
                    list(story.frame_feature_denominators)
                    if story.frame_feature_denominators is not None
                    else None
                ),
                "expected_visible_feature_counts": (
                    list(story.expected_visible_feature_counts)
                    if story.expected_visible_feature_counts is not None
                    else None
                ),
                "source_authority_sha256": story.source_authority_sha256,
                "interpretation": (
                    "Dated observation chronology; not movement or causation."
                    if story.evidence_role == "observation_chronology"
                    else "Non-interpolated modeled context; not observed movement or causation."
                ),
                "temporal_direction": "oldest_to_present",
                "interval_semantics": "[younger_bp, older_bp]",
                "frame_count": len(frames),
                "first_frame": _frame_identity(frames[0]),
                "last_frame": _frame_identity(frames[-1]),
                "frame_set_sha256": hashlib.sha256(
                    canonical_json_bytes(frames)
                ).hexdigest(),
                "capture_frame_set_sha256": hashlib.sha256(
                    canonical_json_bytes(published_capture_frames)
                ).hexdigest(),
                "capture_frames": published_capture_frames,
                "assets": sorted(assets, key=lambda row: str(row["media_type"])),
            }
        )
    content: dict[str, object] = {
        "schema_version": "atlas-media-gallery.v3",
        "atlas_identity": atlas_identity,
        "candidate_identity": candidate_identity,
        "storyboard_sha256": storyboard_sha256,
        "temporal_direction": "oldest_to_present",
        "interpolation_allowed": False,
        "candidate_succession": candidate_succession,
        "tool_identity": tool_identity,
        "encoding_profile": encoding_profile,
        # Execution receipts contain timestamps and durations. The gallery binds their
        # stable locations while each receipt independently hashes its logs; this keeps
        # the content manifest reproducible without erasing run-specific evidence.
        "command_execution_receipts": sorted(
            str(receipt["path"]) for receipt in execution_receipts
        ),
        "story_count": len(story_rows),
        "stories": story_rows,
    }
    return {
        **content,
        "content_sha256": hashlib.sha256(canonical_json_bytes(content)).hexdigest(),
    }


def _validate_tool_identity(value: dict[str, object]) -> None:
    if set(value) != {"node", "ffmpeg", "ffprobe", "brave"}:
        raise AtlasMediaError("gallery tool identity inventory differs")
    for row in value.values():
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("version"), str)
            or not row["version"]
            or not isinstance(row.get("binary_sha256"), str)
            or not _is_sha256(row["binary_sha256"])
        ):
            raise AtlasMediaError("gallery tool identity is invalid")


def _validate_encoding_profile(value: dict[str, object]) -> None:
    width = value.get("width")
    height = value.get("height")
    frames_per_second = value.get("frames_per_second")
    if (
        value.get("schema_version") != "atlas-media-encoding-profile.v1"
        or isinstance(width, bool)
        or not isinstance(width, int)
        or width <= 0
        or isinstance(height, bool)
        or not isinstance(height, int)
        or height <= 0
        or isinstance(frames_per_second, bool)
        or not isinstance(frames_per_second, int)
        or not 1 <= frames_per_second <= 60
        or value.get("poster") != {"format": "png", "source_frame_ordinal": 0}
        or value.get("mp4")
        != {
            "codec": "libx264",
            "preset": "slow",
            "crf": 20,
            "pixel_format": "yuv420p",
            "threads": 1,
            "metadata_removed": True,
            "bitexact": True,
            "faststart": True,
        }
        or value.get("gif")
        != {
            "palette_stats_mode": "diff",
            "palette_dither": "bayer",
            "palette_diff_mode": "rectangle",
            "loop": 0,
            "threads": 1,
            "metadata_removed": True,
            "bitexact": True,
        }
    ):
        raise AtlasMediaError("gallery encoding profile is invalid")


def _validate_execution_receipts(values: list[dict[str, object]]) -> None:
    paths: set[str] = set()
    if not values:
        raise AtlasMediaError("gallery command execution receipts are absent")
    for value in values:
        path = value.get("path")
        byte_count = value.get("byte_count")
        digest = value.get("sha256")
        if (
            not isinstance(path, str)
            or not path.endswith(".execution.json")
            or Path(path).is_absolute()
            or ".." in Path(path).parts
            or path in paths
            or isinstance(byte_count, bool)
            or not isinstance(byte_count, int)
            or byte_count <= 0
            or not isinstance(digest, str)
            or not _is_sha256(digest)
        ):
            raise AtlasMediaError("gallery command execution receipt is invalid")
        paths.add(path)


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def _positive_number(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (float, int))
        and math.isfinite(float(value))
        and value > 0
    )


def _capture_frame_identity(
    value: dict[str, object], *, ordinal: int, story: SelectedStory
) -> dict[str, object]:
    expected_file = f"frames/{story.story_id}/{ordinal:06d}.png"
    byte_count = value.get("byte_count")
    if (
        value.get("ordinal") != ordinal
        or value.get("file") != expected_file
        or not isinstance(value.get("frame_sha256"), str)
        or not _is_sha256(str(value["frame_sha256"]))
        or not isinstance(value.get("png_sha256"), str)
        or not _is_sha256(str(value["png_sha256"]))
        or isinstance(byte_count, bool)
        or not isinstance(byte_count, int)
        or byte_count <= 0
    ):
        raise AtlasMediaError("gallery capture frame identity is invalid")
    return {
        "ordinal": ordinal,
        "file": expected_file,
        "frame_sha256": value["frame_sha256"],
        "png_sha256": value["png_sha256"],
        "byte_count": byte_count,
        "visible_source_chronology_point_count": value.get(
            "visible_source_chronology_point_count"
        ),
        "visible_modeled_context_feature_count": value.get(
            "visible_modeled_context_feature_count"
        ),
    }


def write_gallery_manifest(
    root: Path, manifest: dict[str, object]
) -> tuple[Path, Path]:
    """Atomically write the gallery and its external SHA-256 receipt."""
    payload = canonical_json_bytes(manifest)
    manifest_path = root / "gallery-manifest.json"
    pending_manifest = root / "gallery-manifest.json.pending"
    pending_manifest.write_bytes(payload)
    pending_manifest.replace(manifest_path)
    digest = hashlib.sha256(payload).hexdigest()
    checksum_path = root / "gallery-manifest.sha256"
    pending_checksum = root / "gallery-manifest.sha256.pending"
    pending_checksum.write_text(f"{digest}  gallery-manifest.json\n", encoding="utf-8")
    pending_checksum.replace(checksum_path)
    return manifest_path, checksum_path


def _frame_identity(frame: dict[str, object]) -> dict[str, object]:
    return {
        key: frame.get(key)
        for key in (
            "ordinal",
            "story_kind",
            "source_level",
            "source_code",
            "source_taxon",
            "source_window_label",
            "metric_family_key",
            "metric_key",
            "time_start_bp",
            "time_end_bp",
            "feature_count",
            "countries",
        )
        if key in frame
    }


__all__ = [
    "build_gallery_manifest",
    "canonical_json_bytes",
    "media_asset_row",
    "sha256_file",
    "write_gallery_manifest",
]
