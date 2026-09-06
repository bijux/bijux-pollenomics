"""Promote governed atlas media into a deterministic website asset bundle."""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping, Sequence
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import tempfile
from typing import NoReturn, cast

from .contracts import AtlasMediaError
from .gallery import canonical_json_bytes, sha256_file

MAX_MP4_BYTES = 16 * 1024 * 1024
MAX_POSTER_BYTES = 2 * 1024 * 1024
MAX_PUBLICATION_BYTES = 96 * 1024 * 1024

_SHA256 = re.compile(r"[0-9a-f]{64}")
_GIT_OBJECT = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
_BUILD_ID = re.compile(r"atlas-[0-9a-f]{64}")
_SOURCE_INTERPRETATION = (
    "Dated source-observation chronology; not movement, migration, causation, "
    "or propagation."
)
_MODELED_INTERPRETATION = (
    "Non-interpolated modeled context; not an observed pollen trajectory or "
    "propagation."
)
_EXPECTED_STORIES = (
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
_GALLERY_FIELDS = {
    "schema_version",
    "atlas_identity",
    "candidate_identity",
    "storyboard_sha256",
    "temporal_direction",
    "interpolation_allowed",
    "candidate_succession",
    "tool_identity",
    "encoding_profile",
    "command_execution_receipts",
    "story_count",
    "stories",
    "content_sha256",
}
_STORY_FIELDS = {
    "story_id",
    "title",
    "evidence_role",
    "selector",
    "node_count",
    "observation_denominator",
    "frame_feature_denominators",
    "expected_visible_feature_counts",
    "source_authority_sha256",
    "interpretation",
    "temporal_direction",
    "interval_semantics",
    "frame_count",
    "first_frame",
    "last_frame",
    "frame_set_sha256",
    "capture_frame_set_sha256",
    "capture_frames",
    "assets",
}
_PUBLICATION_FIELDS = {
    "schema_version",
    "source_gallery",
    "atlas_identity",
    "candidate_identity",
    "storyboard_sha256",
    "source_authority_sha256",
    "scientific_posture",
    "candidate_succession",
    "tool_identity",
    "encoding_profile",
    "publication_budget",
    "story_count",
    "stories",
    "content_sha256",
}
_PUBLIC_STORY_FIELDS = {
    "story_id",
    "title",
    "evidence_role",
    "selector",
    "interpretation",
    "temporal_direction",
    "interval_semantics",
    "node_count",
    "observation_denominator",
    "frame_feature_denominators",
    "expected_visible_feature_counts",
    "source_authority_sha256",
    "frame_count",
    "first_frame",
    "last_frame",
    "frame_set_sha256",
    "capture_frame_set_sha256",
    "assets",
}


def publish_atlas_media(gallery_root: Path, destination: Path) -> dict[str, object]:
    """Validate and atomically publish one exact six-story website bundle."""
    source_root = _existing_directory(gallery_root, label="gallery_root")
    target = _publication_destination(destination)
    if (
        source_root == target
        or source_root in target.parents
        or target in source_root.parents
    ):
        raise AtlasMediaError("gallery and publication directories must be disjoint")

    gallery, gallery_bytes, gallery_digest = _load_gallery(source_root)
    manifest, transfers = _build_publication(gallery, gallery_digest, source_root)
    _require_media_inventory(source_root, transfers)
    _require_existing_destination_is_governed(target)

    stage = Path(
        tempfile.mkdtemp(prefix=".atlas-media-publication-pending-", dir=target.parent)
    )
    try:
        _materialize_stage(stage, transfers, manifest)
        _require_sources_unchanged(transfers)
        _validate_publication_tree(stage, manifest)
        final_gallery, final_bytes, final_digest = _load_gallery(source_root)
        if (
            gallery_bytes != final_bytes
            or gallery_digest != final_digest
            or gallery != final_gallery
        ):
            raise AtlasMediaError("gallery manifest changed during publication")
        _install_stage(stage, target)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return manifest


def _load_gallery(root: Path) -> tuple[dict[str, object], bytes, str]:
    manifest_path = _direct_regular_file(root, "gallery-manifest.json")
    checksum_path = _direct_regular_file(root, "gallery-manifest.sha256")
    payload = manifest_path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    expected_checksum = f"{digest}  gallery-manifest.json\n".encode()
    if checksum_path.read_bytes() != expected_checksum:
        raise AtlasMediaError("gallery manifest checksum differs")
    value = _load_json_object(payload, label="gallery manifest")
    if set(value) != _GALLERY_FIELDS:
        raise AtlasMediaError("gallery manifest fields differ")
    if value.get("schema_version") != "atlas-media-gallery.v3":
        raise AtlasMediaError("gallery manifest schema is unsupported")
    claimed_content = value.get("content_sha256")
    content = {key: item for key, item in value.items() if key != "content_sha256"}
    if (
        not _is_sha256(claimed_content)
        or claimed_content != hashlib.sha256(canonical_json_bytes(content)).hexdigest()
    ):
        raise AtlasMediaError("gallery manifest content identity differs")
    return value, payload, digest


def _build_publication(
    gallery: Mapping[str, object], gallery_digest: str, source_root: Path
) -> tuple[dict[str, object], tuple[dict[str, object], ...]]:
    atlas_identity = _atlas_identity(gallery.get("atlas_identity"))
    candidate_identity = _candidate_identity(gallery.get("candidate_identity"))
    if atlas_identity["build_id"] != candidate_identity["build_id"]:
        raise AtlasMediaError("atlas and candidate build identities differ")
    storyboard_sha256 = _digest(gallery.get("storyboard_sha256"), "storyboard")
    if (
        gallery.get("temporal_direction") != "oldest_to_present"
        or gallery.get("interpolation_allowed") is not False
    ):
        raise AtlasMediaError("gallery playback semantics are stale")
    succession = _candidate_succession(gallery.get("candidate_succession"))
    tools = _tool_identity(gallery.get("tool_identity"))
    encoding = _public_encoding(gallery.get("encoding_profile"))
    stories = _object_list(gallery.get("stories"), "gallery stories")
    if gallery.get("story_count") != len(_EXPECTED_STORIES) or len(stories) != len(
        _EXPECTED_STORIES
    ):
        raise AtlasMediaError("gallery must contain the exact six governed stories")

    public_stories: list[dict[str, object]] = []
    transfers: list[dict[str, object]] = []
    source_authorities: set[str] = set()
    for story, expected in zip(stories, _EXPECTED_STORIES, strict=True):
        public_story, story_transfers = _publication_story(
            story, expected=expected, source_root=source_root, encoding=encoding
        )
        authority = public_story["source_authority_sha256"]
        if isinstance(authority, str):
            source_authorities.add(authority)
        public_stories.append(public_story)
        transfers.extend(story_transfers)
    if len(source_authorities) != 1:
        raise AtlasMediaError("source stories do not share one authority identity")
    total_bytes = sum(cast(int, row["byte_count"]) for row in transfers)
    if total_bytes > MAX_PUBLICATION_BYTES:
        raise AtlasMediaError("publication exceeds the 96 MiB total budget")
    content: dict[str, object] = {
        "schema_version": "atlas-media-publication.v1",
        "source_gallery": {
            "manifest_sha256": gallery_digest,
            "content_sha256": gallery["content_sha256"],
        },
        "atlas_identity": atlas_identity,
        "candidate_identity": candidate_identity,
        "storyboard_sha256": storyboard_sha256,
        "source_authority_sha256": next(iter(source_authorities)),
        "scientific_posture": {
            "temporal_direction": "oldest_to_present",
            "interval_semantics": "[younger_bp, older_bp]",
            "null_not_zero": True,
            "interpolation_allowed": False,
            "observation_is_propagation": False,
            "modeled_context_is_observation": False,
        },
        "candidate_succession": succession,
        "tool_identity": tools,
        "encoding_profile": encoding,
        "publication_budget": {
            "maximum_mp4_bytes": MAX_MP4_BYTES,
            "maximum_poster_bytes": MAX_POSTER_BYTES,
            "maximum_total_bytes": MAX_PUBLICATION_BYTES,
            "published_asset_count": len(transfers),
            "published_byte_count": total_bytes,
        },
        "story_count": len(public_stories),
        "stories": public_stories,
    }
    return (
        {
            **content,
            "content_sha256": hashlib.sha256(canonical_json_bytes(content)).hexdigest(),
        },
        tuple(transfers),
    )


def _publication_story(
    story: Mapping[str, object],
    *,
    expected: tuple[str, str, str, str, str | None],
    source_root: Path,
    encoding: Mapping[str, object],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    if set(story) != _STORY_FIELDS:
        raise AtlasMediaError("gallery story fields differ")
    story_id, role, selector_kind, selector_value, selector_family = expected
    selector = _object(story.get("selector"), "story selector")
    if (
        story.get("story_id") != story_id
        or story.get("evidence_role") != role
        or selector
        != {"kind": selector_kind, "value": selector_value, "family": selector_family}
        or story.get("temporal_direction") != "oldest_to_present"
        or story.get("interval_semantics") != "[younger_bp, older_bp]"
        or story.get("interpretation")
        != (
            "Dated observation chronology; not movement or causation."
            if role == "observation_chronology"
            else "Non-interpolated modeled context; not observed movement or causation."
        )
    ):
        raise AtlasMediaError(
            f"governed story identity or semantics differ: {story_id}"
        )
    title = story.get("title")
    frame_count = _positive_integer(story.get("frame_count"), "story frame_count")
    if not isinstance(title, str) or not title.strip():
        raise AtlasMediaError(f"story title is absent: {story_id}")
    first_frame = _frame_boundary(story.get("first_frame"), "first_frame")
    last_frame = _frame_boundary(story.get("last_frame"), "last_frame")
    _validate_boundary_selector(
        first_frame,
        ordinal=0,
        expected=expected,
    )
    _validate_boundary_selector(
        last_frame,
        ordinal=frame_count - 1,
        expected=expected,
    )
    if cast(float | int, first_frame["time_start_bp"]) < cast(
        float | int, last_frame["time_start_bp"]
    ) or cast(float | int, first_frame["time_end_bp"]) < cast(
        float | int, last_frame["time_end_bp"]
    ):
        raise AtlasMediaError(f"story boundary direction differs: {story_id}")
    frame_set = _digest(story.get("frame_set_sha256"), "frame set")
    capture_set = _digest(story.get("capture_frame_set_sha256"), "capture frame set")
    captures = _object_list(story.get("capture_frames"), "capture frames")
    if len(captures) != frame_count:
        raise AtlasMediaError(f"capture frame denominator differs: {story_id}")
    published_captures: list[dict[str, object]] = []
    for ordinal, capture in enumerate(captures):
        expected_path = f"frames/{story_id}/{ordinal:06d}.png"
        if (
            set(capture)
            != {
                "ordinal",
                "file",
                "frame_sha256",
                "png_sha256",
                "byte_count",
                "visible_source_chronology_point_count",
                "visible_modeled_context_feature_count",
            }
            or capture.get("ordinal") != ordinal
            or capture.get("file") != expected_path
            or not _is_sha256(capture.get("frame_sha256"))
            or not _is_sha256(capture.get("png_sha256"))
            or _positive_integer(capture.get("byte_count"), "capture byte_count") <= 0
        ):
            raise AtlasMediaError(f"capture frame identity differs: {story_id}")
        published_captures.append(dict(capture))
    if (
        capture_set
        != hashlib.sha256(canonical_json_bytes(published_captures)).hexdigest()
    ):
        raise AtlasMediaError(f"capture frame set identity differs: {story_id}")

    if role == "observation_chronology":
        node_count: int | None = _positive_integer(
            story.get("node_count"), "node_count"
        )
        observations: int | None = _positive_integer(
            story.get("observation_denominator"), "observation_denominator"
        )
        modeled_denominators: list[object] | None = None
        visible_counts = _nonnegative_integer_list(
            story.get("expected_visible_feature_counts"),
            length=frame_count,
            label="source visibility denominators",
        )
        authority: str | None = _digest(
            story.get("source_authority_sha256"), "source authority"
        )
        if story.get("frame_feature_denominators") is not None:
            raise AtlasMediaError(f"source story has modeled denominators: {story_id}")
        if (
            sum(cast(list[int], visible_counts)) <= 0
            or any(cast(int, count) > cast(int, node_count) for count in visible_counts)
            or any(
                capture.get("visible_source_chronology_point_count") != count
                or capture.get("visible_modeled_context_feature_count") != 0
                for capture, count in zip(
                    published_captures, visible_counts, strict=True
                )
            )
        ):
            raise AtlasMediaError(f"source visibility evidence differs: {story_id}")
        interpretation = _SOURCE_INTERPRETATION
    else:
        if (
            story.get("node_count") is not None
            or story.get("observation_denominator") is not None
            or story.get("expected_visible_feature_counts") is not None
            or story.get("source_authority_sha256") is not None
        ):
            raise AtlasMediaError("modeled story carries source evidence")
        node_count = None
        observations = None
        visible_counts = None
        authority = None
        modeled_denominators = _positive_integer_list(
            story.get("frame_feature_denominators"),
            length=frame_count,
            label="modeled feature denominators",
        )
        if any(
            capture.get("visible_source_chronology_point_count") != 0
            or capture.get("visible_modeled_context_feature_count") != denominator
            for capture, denominator in zip(
                published_captures, modeled_denominators, strict=True
            )
        ):
            raise AtlasMediaError("modeled visibility evidence differs")
        interpretation = _MODELED_INTERPRETATION

    assets = _object_list(story.get("assets"), "story assets")
    if len(assets) != 3 or [asset.get("media_type") for asset in assets] != [
        "gif",
        "mp4",
        "poster",
    ]:
        raise AtlasMediaError(f"story media inventory differs: {story_id}")
    by_type = {cast(str, asset["media_type"]): asset for asset in assets}
    transfers = [
        _publication_asset(
            story_id,
            by_type[media_type],
            media_type=media_type,
            source_root=source_root,
            frame_count=frame_count,
            encoding=encoding,
            first_capture=published_captures[0],
        )
        for media_type in ("poster", "mp4")
    ]
    return (
        {
            "story_id": story_id,
            "title": title,
            "evidence_role": role,
            "selector": dict(selector),
            "interpretation": interpretation,
            "temporal_direction": "oldest_to_present",
            "interval_semantics": "[younger_bp, older_bp]",
            "node_count": node_count,
            "observation_denominator": observations,
            "frame_feature_denominators": modeled_denominators,
            "expected_visible_feature_counts": visible_counts,
            "source_authority_sha256": authority,
            "frame_count": frame_count,
            "first_frame": first_frame,
            "last_frame": last_frame,
            "frame_set_sha256": frame_set,
            "capture_frame_set_sha256": capture_set,
            "assets": [_public_asset_row(row) for row in transfers],
        },
        transfers,
    )


def _publication_asset(
    story_id: str,
    asset: Mapping[str, object],
    *,
    media_type: str,
    source_root: Path,
    frame_count: int,
    encoding: Mapping[str, object],
    first_capture: Mapping[str, object],
) -> dict[str, object]:
    expected_fields = {
        "media_type",
        "path",
        "byte_count",
        "sha256",
        "width",
        "height",
        "frame_count",
    } | ({"duration_seconds"} if media_type == "mp4" else set())
    if set(asset) != expected_fields:
        raise AtlasMediaError(f"{media_type} asset fields differ: {story_id}")
    suffix = ".poster.png" if media_type == "poster" else ".mp4"
    source_path = f"media/{story_id}{suffix}"
    if asset.get("media_type") != media_type or asset.get("path") != source_path:
        raise AtlasMediaError(f"{media_type} asset identity differs: {story_id}")
    byte_count = _positive_integer(asset.get("byte_count"), "asset byte_count")
    maximum = MAX_POSTER_BYTES if media_type == "poster" else MAX_MP4_BYTES
    if byte_count > maximum:
        raise AtlasMediaError(f"{media_type} exceeds its publication budget")
    digest = _digest(asset.get("sha256"), f"{media_type} asset")
    width = _positive_integer(asset.get("width"), "asset width")
    height = _positive_integer(asset.get("height"), "asset height")
    if width != encoding["width"] or height != encoding["height"]:
        raise AtlasMediaError(f"{media_type} dimensions differ: {story_id}")
    expected_frames = 1 if media_type == "poster" else frame_count
    if asset.get("frame_count") != expected_frames:
        raise AtlasMediaError(f"{media_type} frame count differs: {story_id}")
    duration: float | int | None = None
    if media_type == "mp4":
        duration = _positive_number(asset.get("duration_seconds"), "mp4 duration")
        expected_duration = frame_count / cast(int, encoding["frames_per_second"])
        if not math.isclose(
            float(duration),
            expected_duration,
            rel_tol=0,
            abs_tol=(1 / cast(int, encoding["frames_per_second"])) + 0.01,
        ):
            raise AtlasMediaError(f"mp4 duration differs: {story_id}")
    elif digest != first_capture.get("png_sha256") or byte_count != first_capture.get(
        "byte_count"
    ):
        raise AtlasMediaError(f"poster differs from the oldest capture: {story_id}")
    path = _regular_child(source_root, source_path)
    if path.stat().st_size != byte_count or sha256_file(path) != digest:
        raise AtlasMediaError(f"{media_type} source bytes differ: {story_id}")
    return {
        "story_id": story_id,
        "media_type": media_type,
        "source_path": source_path,
        "published_path": source_path,
        "byte_count": byte_count,
        "sha256": digest,
        "width": width,
        "height": height,
        "frame_count": expected_frames,
        "duration_seconds": duration,
        "source_file": path,
    }


def _public_asset_row(transfer: Mapping[str, object]) -> dict[str, object]:
    identity_keys = (
        "byte_count",
        "sha256",
        "width",
        "height",
        "frame_count",
        "duration_seconds",
    )
    identity = {key: transfer[key] for key in identity_keys}
    return {
        "media_type": transfer["media_type"],
        "source": {"path": transfer["source_path"], **identity},
        "published": {"path": transfer["published_path"], **identity},
    }


def _materialize_stage(
    stage: Path,
    transfers: Sequence[Mapping[str, object]],
    manifest: Mapping[str, object],
) -> None:
    media_root = stage / "media"
    media_root.mkdir()
    for row in transfers:
        source = cast(Path, row["source_file"])
        target = stage / cast(str, row["published_path"])
        shutil.copyfile(source, target)
        target.chmod(0o644)
        if (
            target.stat().st_size != row["byte_count"]
            or sha256_file(target) != row["sha256"]
        ):
            raise AtlasMediaError("published media differs after copy")
    payload = canonical_json_bytes(dict(manifest))
    manifest_path = stage / "publication-manifest.json"
    manifest_path.write_bytes(payload)
    manifest_path.chmod(0o644)
    checksum_path = stage / "publication-manifest.sha256"
    checksum_path.write_text(
        f"{hashlib.sha256(payload).hexdigest()}  publication-manifest.json\n",
        encoding="utf-8",
    )
    checksum_path.chmod(0o644)


def _require_sources_unchanged(transfers: Iterable[Mapping[str, object]]) -> None:
    for row in transfers:
        source = cast(Path, row["source_file"])
        if (
            source.is_symlink()
            or source.stat().st_size != row["byte_count"]
            or sha256_file(source) != row["sha256"]
        ):
            raise AtlasMediaError("source media changed during publication")


def _require_media_inventory(
    source_root: Path, transfers: Sequence[Mapping[str, object]]
) -> None:
    media_root = source_root / "media"
    if not media_root.is_dir() or media_root.is_symlink():
        raise AtlasMediaError("gallery media directory is absent or linked")
    expected_public = {cast(str, row["source_path"]) for row in transfers}
    expected_gifs = {f"media/{story_id}.gif" for story_id, *_ in _EXPECTED_STORIES}
    observed: set[str] = set()
    for path in media_root.iterdir():
        if path.is_symlink() or not path.is_file():
            raise AtlasMediaError(
                "gallery media inventory contains a linked or non-file entry"
            )
        observed.add(path.relative_to(source_root).as_posix())
    if observed != expected_public | expected_gifs:
        raise AtlasMediaError(
            "gallery media inventory contains missing or extra assets"
        )


def _validate_publication_tree(
    root: Path, expected_manifest: Mapping[str, object] | None = None
) -> dict[str, object]:
    manifest_path = _direct_regular_file(root, "publication-manifest.json")
    checksum_path = _direct_regular_file(root, "publication-manifest.sha256")
    payload = manifest_path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if checksum_path.read_bytes() != f"{digest}  publication-manifest.json\n".encode():
        raise AtlasMediaError("publication manifest checksum differs")
    manifest = _load_json_object(payload, label="publication manifest")
    if expected_manifest is not None and manifest != expected_manifest:
        raise AtlasMediaError("publication manifest differs after materialization")
    content_digest = manifest.get("content_sha256")
    content = {key: value for key, value in manifest.items() if key != "content_sha256"}
    if (
        set(manifest) != _PUBLICATION_FIELDS
        or manifest.get("schema_version") != "atlas-media-publication.v1"
        or not _is_sha256(content_digest)
        or content_digest != hashlib.sha256(canonical_json_bytes(content)).hexdigest()
    ):
        raise AtlasMediaError("publication content identity differs")
    stories = _object_list(manifest.get("stories"), "publication stories")
    if manifest.get("story_count") != 6 or len(stories) != 6:
        raise AtlasMediaError("publication story inventory differs")
    expected_files = {"publication-manifest.json", "publication-manifest.sha256"}
    for story, expected in zip(stories, _EXPECTED_STORIES, strict=True):
        if (
            set(story) != _PUBLIC_STORY_FIELDS
            or story.get("story_id") != expected[0]
            or story.get("evidence_role") != expected[1]
            or story.get("selector")
            != {"kind": expected[2], "value": expected[3], "family": expected[4]}
        ):
            raise AtlasMediaError("publication story identity differs")
        assets = _object_list(story.get("assets"), "publication assets")
        if len(assets) != 2 or [asset.get("media_type") for asset in assets] != [
            "poster",
            "mp4",
        ]:
            raise AtlasMediaError("publication asset inventory differs")
        for asset in assets:
            published = _object(asset.get("published"), "published asset identity")
            source = _object(asset.get("source"), "source asset identity")
            if source != published:
                raise AtlasMediaError("source and published asset identities differ")
            path_text = published.get("path")
            if not isinstance(path_text, str):
                raise AtlasMediaError("published asset path is invalid")
            path = _regular_child(root, path_text)
            if path.stat().st_size != published.get("byte_count") or sha256_file(
                path
            ) != published.get("sha256"):
                raise AtlasMediaError("published asset bytes differ")
            expected_files.add(path_text)
    observed = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    if observed != expected_files:
        raise AtlasMediaError("publication contains missing or extra files")
    return manifest


def _require_existing_destination_is_governed(destination: Path) -> None:
    if destination.is_symlink():
        raise AtlasMediaError("publication destination must not be a symlink")
    if not destination.exists():
        return
    if not destination.is_dir():
        raise AtlasMediaError("publication destination must be a directory")
    _validate_publication_tree(destination)


def _install_stage(stage: Path, destination: Path) -> None:
    if not destination.exists():
        stage.replace(destination)
        return
    backup = stage.with_name(f"{stage.name}-previous")
    if backup.exists():
        raise AtlasMediaError("publication backup path unexpectedly exists")
    destination.replace(backup)
    try:
        stage.replace(destination)
    except Exception:
        backup.replace(destination)
        raise
    shutil.rmtree(backup)


def _atlas_identity(value: object) -> dict[str, object]:
    row = _object(value, "atlas identity")
    if set(row) != {"build_id", "scope_slug", "version", "countries"}:
        raise AtlasMediaError("atlas identity fields differ")
    if (
        not isinstance(row.get("build_id"), str)
        or _BUILD_ID.fullmatch(cast(str, row["build_id"])) is None
        or row.get("scope_slug") != "nordic"
        or not isinstance(row.get("version"), str)
        or not cast(str, row["version"]).strip()
        or row.get("countries") != ["Denmark", "Finland", "Norway", "Sweden"]
    ):
        raise AtlasMediaError("atlas identity is invalid")
    return dict(row)


def _candidate_identity(value: object) -> dict[str, object]:
    row = _object(value, "candidate identity")
    if set(row) != {
        "repository_head",
        "repository_tree",
        "atlas_output_commit",
        "build_id",
    }:
        raise AtlasMediaError("candidate identity fields differ")
    for field in ("repository_head", "repository_tree", "atlas_output_commit"):
        item = row.get(field)
        if not isinstance(item, str) or _GIT_OBJECT.fullmatch(item) is None:
            raise AtlasMediaError("candidate Git identity is invalid")
    build_id = row.get("build_id")
    if not isinstance(build_id, str) or _BUILD_ID.fullmatch(build_id) is None:
        raise AtlasMediaError("candidate build identity is invalid")
    return dict(row)


def _candidate_succession(value: object) -> dict[str, object]:
    row = _object(value, "candidate succession")
    if (
        set(row)
        != {
            "product_key",
            "status",
            "reason_code",
            "detail",
            "story_count",
            "edge_count",
        }
        or row.get("product_key") != "candidate_succession"
        or row.get("status") != "refused"
        or row.get("reason_code") != "accepted_scientific_classifications_not_available"
        or row.get("story_count") != 0
        or row.get("edge_count") != 0
        or not isinstance(row.get("detail"), str)
        or not cast(str, row["detail"]).strip()
    ):
        raise AtlasMediaError("candidate succession is not explicitly refused")
    return dict(row)


def _tool_identity(value: object) -> dict[str, object]:
    row = _object(value, "tool identity")
    if set(row) != {"node", "ffmpeg", "ffprobe", "brave"}:
        raise AtlasMediaError("tool identity inventory differs")
    for item in row.values():
        tool = _object(item, "tool identity entry")
        if (
            set(tool) != {"binary_sha256", "version"}
            or not _is_sha256(tool.get("binary_sha256"))
            or not isinstance(tool.get("version"), str)
            or not cast(str, tool["version"]).strip()
        ):
            raise AtlasMediaError("tool identity entry is invalid")
    return {key: dict(cast(Mapping[str, object], item)) for key, item in row.items()}


def _public_encoding(value: object) -> dict[str, object]:
    row = _object(value, "encoding profile")
    width = _positive_integer(row.get("width"), "encoding width")
    height = _positive_integer(row.get("height"), "encoding height")
    fps = _positive_integer(row.get("frames_per_second"), "encoding frame rate")
    if (
        row.get("schema_version") != "atlas-media-encoding-profile.v1"
        or row.get("poster") != {"format": "png", "source_frame_ordinal": 0}
        or row.get("mp4")
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
        or set(row)
        != {
            "schema_version",
            "width",
            "height",
            "frames_per_second",
            "poster",
            "mp4",
            "gif",
        }
        or row.get("gif")
        != {
            "palette_stats_mode": "diff",
            "palette_dither": "bayer",
            "palette_diff_mode": "rectangle",
            "loop": 0,
            "threads": 1,
            "metadata_removed": True,
            "bitexact": True,
        }
        or fps > 60
    ):
        raise AtlasMediaError("gallery encoding profile is invalid")
    return {
        "schema_version": "atlas-media-publication-encoding.v1",
        "width": width,
        "height": height,
        "frames_per_second": fps,
        "poster": dict(cast(Mapping[str, object], row["poster"])),
        "mp4": dict(cast(Mapping[str, object], row["mp4"])),
    }


def _frame_boundary(value: object, label: str) -> dict[str, object]:
    row = _object(value, label)
    younger = _nonnegative_number(row.get("time_start_bp"), f"{label} time_start_bp")
    older = _nonnegative_number(row.get("time_end_bp"), f"{label} time_end_bp")
    if younger > older:
        raise AtlasMediaError(f"{label} BP interval is reversed")
    return dict(row)


def _validate_boundary_selector(
    frame: Mapping[str, object],
    *,
    ordinal: int,
    expected: tuple[str, str, str, str, str | None],
) -> None:
    _, role, selector_kind, selector_value, selector_family = expected
    expected_fields = {
        "ordinal",
        "story_kind",
        "time_start_bp",
        "time_end_bp",
        "countries",
    }
    if role == "observation_chronology":
        expected_fields.add("source_level")
        if selector_kind == "source_ecological_code":
            expected_fields.add("source_code")
        elif selector_kind == "source_taxon":
            expected_fields.add("source_taxon")
    else:
        expected_fields.update(
            {"source_window_label", "metric_family_key", "metric_key", "feature_count"}
        )
    if (
        set(frame) != expected_fields
        or frame.get("ordinal") != ordinal
        or frame.get("countries") != ["Denmark", "Finland", "Norway", "Sweden"]
    ):
        raise AtlasMediaError("story boundary identity differs")
    if role == "observation_chronology":
        if (
            frame.get("story_kind") != "source_chronology"
            or frame.get("source_level") != selector_kind
            or (
                selector_kind == "source_ecological_code"
                and frame.get("source_code") != selector_value
            )
            or (
                selector_kind == "source_taxon"
                and frame.get("source_taxon") != selector_value
            )
        ):
            raise AtlasMediaError("source story boundary selector differs")
    elif (
        frame.get("story_kind") != "modeled_context"
        or frame.get("metric_key") != selector_value
        or frame.get("metric_family_key") != selector_family
        or _positive_integer(frame.get("feature_count"), "boundary feature_count") <= 0
    ):
        raise AtlasMediaError("modeled story boundary selector differs")


def _load_json_object(payload: bytes, *, label: str) -> dict[str, object]:
    def pairs(values: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in values:
            if key in result:
                raise AtlasMediaError(f"{label} contains duplicate fields")
            result[key] = value
        return result

    def invalid_constant(value: str) -> NoReturn:
        raise AtlasMediaError(f"{label} contains non-finite JSON: {value}")

    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=pairs,
            parse_constant=invalid_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise AtlasMediaError(f"{label} is not strict UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise AtlasMediaError(f"{label} must be an object")
    return cast(dict[str, object], value)


def _publication_destination(path: Path) -> Path:
    if path.name in {"", ".", ".."} or path.is_symlink():
        raise AtlasMediaError("publication destination is unsafe")
    try:
        parent = path.parent.resolve(strict=True)
    except OSError as error:
        raise AtlasMediaError(
            "publication destination parent is unavailable"
        ) from error
    if not parent.is_dir():
        raise AtlasMediaError("publication destination parent is not a directory")
    return parent / path.name


def _existing_directory(path: Path, *, label: str) -> Path:
    if path.is_symlink():
        raise AtlasMediaError(f"{label} must not be a symlink")
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise AtlasMediaError(f"{label} is unavailable") from error
    if not resolved.is_dir():
        raise AtlasMediaError(f"{label} must be a directory")
    return resolved


def _direct_regular_file(root: Path, name: str) -> Path:
    path = root / name
    if path.is_symlink() or not path.is_file() or path.resolve().parent != root:
        raise AtlasMediaError(f"{name} must be a direct regular file")
    return path


def _regular_child(root: Path, value: str) -> Path:
    relative = Path(value)
    if (
        not value
        or relative.is_absolute()
        or ".." in relative.parts
        or any(part in {"", "."} for part in relative.parts)
    ):
        raise AtlasMediaError("media path is unsafe")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise AtlasMediaError("media path contains a symlink")
    try:
        resolved = current.resolve(strict=True)
    except OSError as error:
        raise AtlasMediaError("media asset is unavailable") from error
    if root not in resolved.parents or not resolved.is_file():
        raise AtlasMediaError("media asset escapes its governed root")
    return resolved


def _object(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise AtlasMediaError(f"{label} must be an object")
    return cast(Mapping[str, object], value)


def _object_list(value: object, label: str) -> list[Mapping[str, object]]:
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise AtlasMediaError(f"{label} must be an object array")
    return cast(list[Mapping[str, object]], value)


def _positive_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise AtlasMediaError(f"{label} must be a positive integer")
    return value


def _positive_integer_list(value: object, *, length: int, label: str) -> list[object]:
    if (
        not isinstance(value, list)
        or len(value) != length
        or any(
            isinstance(item, bool) or not isinstance(item, int) or item <= 0
            for item in value
        )
    ):
        raise AtlasMediaError(f"{label} differ")
    return list(value)


def _nonnegative_integer_list(
    value: object, *, length: int, label: str
) -> list[object]:
    if (
        not isinstance(value, list)
        or len(value) != length
        or any(
            isinstance(item, bool) or not isinstance(item, int) or item < 0
            for item in value
        )
    ):
        raise AtlasMediaError(f"{label} differ")
    return list(value)


def _positive_number(value: object, label: str) -> float | int:
    number = _nonnegative_number(value, label)
    if number <= 0:
        raise AtlasMediaError(f"{label} must be positive")
    return number


def _nonnegative_number(value: object, label: str) -> float | int:
    if (
        isinstance(value, bool)
        or not isinstance(value, (float, int))
        or not math.isfinite(float(value))
        or value < 0
    ):
        raise AtlasMediaError(f"{label} must be finite and non-negative")
    return value


def _digest(value: object, label: str) -> str:
    if not _is_sha256(value):
        raise AtlasMediaError(f"{label} SHA-256 is invalid")
    return cast(str, value)


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def main(argv: Sequence[str] | None = None) -> int:
    """Publish one validated gallery from a command-line invocation."""
    parser = argparse.ArgumentParser(
        description="Publish deterministic Nordic atlas chronology media."
    )
    parser.add_argument("gallery_root", type=Path)
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args(argv)
    publish_atlas_media(arguments.gallery_root, arguments.destination)
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through the API
    raise SystemExit(main())


__all__ = [
    "MAX_MP4_BYTES",
    "MAX_POSTER_BYTES",
    "MAX_PUBLICATION_BYTES",
    "main",
    "publish_atlas_media",
]
