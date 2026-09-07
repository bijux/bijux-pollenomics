"""Promote governed atlas media into a deterministic website asset bundle."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import NoReturn, cast
import zlib

from bijux_pollenomics.reporting.source_chronology.source_label_presets import (
    NEOTOMA_SOURCE_LABEL_PRESETS,
)

from .capture_evidence import capture_frame_evidence_valid, expected_capture_layer_key
from .catalog import (
    LEGACY_PUBLICATION_SCHEMA_VERSION_V3,
    LEGACY_PUBLICATION_SCHEMA_VERSION_V4,
    LEGACY_PUBLICATION_STORY_TITLES_V3,
    LEGACY_PUBLICATION_STORY_TITLES_V4,
    PUBLICATION_FRAME_COUNT,
    PUBLICATION_SCHEMA_VERSION,
    PUBLICATION_STORY_TITLES,
    PUBLICATION_STORY_TUPLES,
    SUPPORTED_EXISTING_PUBLICATION_CONTRACTS,
)
from .contracts import AtlasMediaError, story_interpretation
from .gallery import (
    canonical_json_bytes,
    sha256_file,
    validate_source_preset_catalog,
)
from .poster_selection import poster_frame_ordinal
from .process_execution import BoundedProcessError, run_bounded_argv

MAX_MP4_BYTES = 16 * 1024 * 1024
MAX_POSTER_BYTES = 2 * 1024 * 1024
MAX_PUBLICATION_BYTES = 96 * 1024 * 1024

_SHA256 = re.compile(r"[0-9a-f]{64}")
_GIT_OBJECT = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
_BUILD_ID = re.compile(r"atlas-[0-9a-f]{64}")
_LEGACY_SOURCE_INTERPRETATION = (
    "Dated source-observation chronology; not movement, migration, causation, "
    "or propagation."
)
_LEGACY_MODELED_INTERPRETATION = (
    "Non-interpolated modeled context; not an observed pollen trajectory or "
    "propagation."
)
_EXPECTED_STORIES = PUBLICATION_STORY_TUPLES
_PRESET_MEMBER_IDS = {
    preset.key: preset.member_taxon_ids for preset in NEOTOMA_SOURCE_LABEL_PRESETS
}


def _source_level(selector_kind: str) -> str:
    return "source_taxon" if selector_kind == "source_label_preset" else selector_kind


_GALLERY_FIELDS = {
    "schema_version",
    "atlas_identity",
    "candidate_identity",
    "storyboard_sha256",
    "source_label_preset_catalog",
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
    "site_count",
    "node_count",
    "observation_denominator",
    "frame_feature_denominators",
    "frame_no_pollen_data_counts",
    "expected_visible_feature_counts",
    "expected_visible_site_counts",
    "expected_visible_observation_counts",
    "source_authority_sha256",
    "source_preset_member_taxon_ids",
    "source_preset_catalog_sha256",
    "interpretation",
    "temporal_direction",
    "interval_semantics",
    "frame_count",
    "poster_frame_ordinal",
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
    "source_label_preset_catalog",
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
_LEGACY_PUBLICATION_FIELDS = _PUBLICATION_FIELDS - {"source_label_preset_catalog"}
_PUBLIC_STORY_FIELDS = {
    "story_id",
    "title",
    "evidence_role",
    "selector",
    "interpretation",
    "temporal_direction",
    "interval_semantics",
    "site_count",
    "node_count",
    "observation_denominator",
    "frame_feature_denominators",
    "frame_no_pollen_data_counts",
    "expected_visible_feature_counts",
    "expected_visible_site_counts",
    "expected_visible_observation_counts",
    "source_authority_sha256",
    "source_preset_member_taxon_ids",
    "source_preset_catalog_sha256",
    "frame_count",
    "poster_frame_ordinal",
    "first_frame",
    "last_frame",
    "frame_set_sha256",
    "capture_frame_set_sha256",
    "assets",
}
_LEGACY_V4_PUBLIC_STORY_FIELDS = _PUBLIC_STORY_FIELDS - {
    "source_preset_member_taxon_ids",
    "source_preset_catalog_sha256",
    "site_count",
    "expected_visible_site_counts",
    "expected_visible_observation_counts",
}
_LEGACY_V3_PUBLIC_STORY_FIELDS = _LEGACY_V4_PUBLIC_STORY_FIELDS - {
    "frame_no_pollen_data_counts",
    "poster_frame_ordinal",
}


@dataclass(frozen=True, slots=True)
class ProbedMp4:
    """Independently observed properties of one MP4 video stream."""

    width: int
    height: int
    frame_count: int
    duration_seconds: float
    codec_name: str
    pixel_format: str


Mp4Probe = Callable[[Path], ProbedMp4]


def publish_atlas_media(
    gallery_root: Path,
    destination: Path,
    *,
    ffprobe_binary: Path | None = None,
    mp4_probe: Mp4Probe | None = None,
) -> dict[str, object]:
    """Validate and atomically publish the canonical website media bundle."""
    probe = _resolve_mp4_probe(ffprobe_binary=ffprobe_binary, mp4_probe=mp4_probe)
    source_root = _existing_directory(gallery_root, label="gallery_root")
    target = _publication_destination(destination)
    if (
        source_root == target
        or source_root in target.parents
        or target in source_root.parents
    ):
        raise AtlasMediaError("gallery and publication directories must be disjoint")

    gallery, gallery_bytes, gallery_digest = _load_gallery(source_root)
    manifest, transfers = _build_publication(
        gallery, gallery_digest, source_root, mp4_probe=probe
    )
    _require_media_inventory(source_root, transfers)
    _require_existing_destination_is_governed(target, mp4_probe=probe)

    stage = Path(
        tempfile.mkdtemp(prefix=".atlas-media-publication-pending-", dir=target.parent)
    )
    try:
        _materialize_stage(stage, transfers, manifest)
        _require_sources_unchanged(transfers)
        observed_manifest = validate_atlas_media_publication(stage, mp4_probe=probe)
        if observed_manifest != manifest:
            raise AtlasMediaError("publication manifest differs after materialization")
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
    if value.get("schema_version") != "atlas-media-gallery.v4":
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
    gallery: Mapping[str, object],
    gallery_digest: str,
    source_root: Path,
    *,
    mp4_probe: Mp4Probe,
) -> tuple[dict[str, object], tuple[dict[str, object], ...]]:
    atlas_identity = _atlas_identity(gallery.get("atlas_identity"))
    candidate_identity = _candidate_identity(gallery.get("candidate_identity"))
    if atlas_identity["build_id"] != candidate_identity["build_id"]:
        raise AtlasMediaError("atlas and candidate build identities differ")
    storyboard_sha256 = _digest(gallery.get("storyboard_sha256"), "storyboard")
    source_preset_catalog, source_preset_catalog_sha256 = (
        validate_source_preset_catalog(gallery.get("source_label_preset_catalog"))
    )
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
        raise AtlasMediaError("gallery must contain the canonical governed stories")
    if (
        sum(
            _positive_integer(story.get("frame_count"), "story frame_count")
            for story in stories
        )
        != PUBLICATION_FRAME_COUNT
    ):
        raise AtlasMediaError(
            "gallery frame inventory differs from the governed publication"
        )

    public_stories: list[dict[str, object]] = []
    transfers: list[dict[str, object]] = []
    source_authorities: set[str] = set()
    preset_catalogs: set[str] = set()
    for story, expected in zip(stories, _EXPECTED_STORIES, strict=True):
        public_story, story_transfers = _publication_story(
            story,
            expected=expected,
            source_root=source_root,
            encoding=encoding,
            mp4_probe=mp4_probe,
        )
        authority = public_story["source_authority_sha256"]
        if isinstance(authority, str):
            source_authorities.add(authority)
        preset_catalog = public_story["source_preset_catalog_sha256"]
        if isinstance(preset_catalog, str):
            preset_catalogs.add(preset_catalog)
        public_stories.append(public_story)
        transfers.extend(story_transfers)
    if len(source_authorities) != 1:
        raise AtlasMediaError("source stories do not share one authority identity")
    if preset_catalogs != {source_preset_catalog_sha256}:
        raise AtlasMediaError(
            "source-label preset stories differ from governed catalog"
        )
    total_bytes = sum(cast(int, row["byte_count"]) for row in transfers)
    if total_bytes > MAX_PUBLICATION_BYTES:
        raise AtlasMediaError("publication exceeds the 96 MiB total budget")
    content: dict[str, object] = {
        "schema_version": PUBLICATION_SCHEMA_VERSION,
        "source_gallery": {
            "manifest_sha256": gallery_digest,
            "content_sha256": gallery["content_sha256"],
        },
        "atlas_identity": atlas_identity,
        "candidate_identity": candidate_identity,
        "storyboard_sha256": storyboard_sha256,
        "source_label_preset_catalog": source_preset_catalog,
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
    mp4_probe: Mp4Probe,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    if set(story) != _STORY_FIELDS:
        raise AtlasMediaError("gallery story fields differ")
    story_id, role, selector_kind, selector_value, selector_family = expected
    selector = _object(story.get("selector"), "story selector")
    if (
        story.get("story_id") != story_id
        or story.get("title") != PUBLICATION_STORY_TITLES[story_id]
        or story.get("evidence_role") != role
        or selector
        != {"kind": selector_kind, "value": selector_value, "family": selector_family}
        or story.get("temporal_direction") != "oldest_to_present"
        or story.get("interval_semantics") != "[younger_bp, older_bp]"
        or story.get("interpretation") != story_interpretation(role, selector_kind)
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
    if (
        cast(float | int, first_frame["time_start_bp"])
        < cast(float | int, last_frame["time_start_bp"])
        or cast(float | int, first_frame["time_end_bp"])
        < cast(float | int, last_frame["time_end_bp"])
        or (
            frame_count > 1
            and cast(float | int, first_frame["time_start_bp"])
            == cast(float | int, last_frame["time_start_bp"])
        )
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
        source_counts = story.get("expected_visible_feature_counts")
        source_site_counts = story.get("expected_visible_site_counts")
        source_observation_counts = story.get("expected_visible_observation_counts")
        modeled_counts = story.get("frame_feature_denominators")
        modeled_no_pollen_counts = story.get("frame_no_pollen_data_counts")
        if (
            set(capture)
            != {
                "ordinal",
                "file",
                "frame_sha256",
                "png_sha256",
                "byte_count",
                "time_start_bp",
                "time_end_bp",
                "source_window_label",
                "source_preset",
                "source_preset_member_taxon_ids",
                "source_preset_catalog_sha256",
                "no_pollen_data_count",
                "facet_site_count",
                "visible_site_count",
                "visible_point_count",
                "visible_polygon_layer_count",
                "visible_polygon_feature_count",
                "visible_feature_count",
                "visible_source_chronology_point_count",
                "visible_modeled_context_feature_count",
                "visible_modeled_no_pollen_data_count",
                "visible_source_node_count",
                "visible_source_observation_denominator",
                "capture_layers",
                "capture_presentation",
                "capture_layout",
            }
            or capture.get("ordinal") != ordinal
            or capture.get("file") != expected_path
            or not _is_sha256(capture.get("frame_sha256"))
            or not _is_sha256(capture.get("png_sha256"))
            or _positive_integer(capture.get("byte_count"), "capture byte_count") <= 0
            or capture.get("source_preset")
            != (selector_value if selector_kind == "source_label_preset" else None)
            or capture.get("source_preset_member_taxon_ids")
            != story.get("source_preset_member_taxon_ids")
            or capture.get("source_preset_catalog_sha256")
            != story.get("source_preset_catalog_sha256")
            or not capture_frame_evidence_valid(
                capture,
                evidence_role=role,
                source_level=(
                    _source_level(selector_kind)
                    if role == "observation_chronology"
                    else None
                ),
                expected_evidence_layer_key=expected_capture_layer_key(
                    story_kind=(
                        "source_chronology"
                        if role == "observation_chronology"
                        else "modeled_context"
                    ),
                    source_level=_source_level(selector_kind),
                ),
                expected_title=cast(str, story.get("title")),
                expected_source_count=(
                    source_counts[ordinal] if isinstance(source_counts, list) else None
                ),
                expected_source_site_count=(
                    source_site_counts[ordinal]
                    if isinstance(source_site_counts, list)
                    else None
                ),
                expected_source_observation_count=(
                    source_observation_counts[ordinal]
                    if isinstance(source_observation_counts, list)
                    else None
                ),
                source_site_denominator=story.get("site_count"),
                source_node_denominator=story.get("node_count"),
                source_observation_denominator=story.get("observation_denominator"),
                expected_modeled_count=(
                    modeled_counts[ordinal]
                    if isinstance(modeled_counts, list)
                    else None
                ),
                expected_modeled_no_pollen_data_count=(
                    modeled_no_pollen_counts[ordinal]
                    if isinstance(modeled_no_pollen_counts, list)
                    else None
                ),
                source_window_label=capture.get("source_window_label"),
                time_start_bp=capture.get("time_start_bp"),
                time_end_bp=capture.get("time_end_bp"),
            )
        ):
            raise AtlasMediaError(f"capture frame identity differs: {story_id}")
        published_captures.append(dict(capture))
    poster_ordinal = poster_frame_ordinal(role, published_captures)
    if story.get("poster_frame_ordinal") != poster_ordinal:
        raise AtlasMediaError(f"poster frame selection differs: {story_id}")
    if (
        capture_set
        != hashlib.sha256(canonical_json_bytes(published_captures)).hexdigest()
    ):
        raise AtlasMediaError(f"capture frame set identity differs: {story_id}")

    if role == "observation_chronology":
        site_count: int | None = _positive_integer(
            story.get("site_count"), "site_count"
        )
        node_count: int | None = _positive_integer(
            story.get("node_count"), "node_count"
        )
        observations: int | None = _positive_integer(
            story.get("observation_denominator"), "observation_denominator"
        )
        modeled_denominators: list[object] | None = None
        modeled_no_pollen_denominators: list[object] | None = None
        visible_counts = _nonnegative_integer_list(
            story.get("expected_visible_feature_counts"),
            length=frame_count,
            label="source visibility denominators",
        )
        visible_site_counts = _nonnegative_integer_list(
            story.get("expected_visible_site_counts"),
            length=frame_count,
            label="source site visibility denominators",
        )
        visible_observation_counts = _nonnegative_integer_list(
            story.get("expected_visible_observation_counts"),
            length=frame_count,
            label="source observation visibility denominators",
        )
        authority: str | None = _digest(
            story.get("source_authority_sha256"), "source authority"
        )
        if selector_kind == "source_label_preset":
            preset_member_ids: list[object] | None = _positive_integer_list(
                story.get("source_preset_member_taxon_ids"),
                length=None,
                label="source-label preset member IDs",
            )
            if len(set(cast(list[int], preset_member_ids))) != len(
                cast(list[object], preset_member_ids)
            ):
                raise AtlasMediaError("source-label preset member IDs differ")
            preset_catalog: str | None = _digest(
                story.get("source_preset_catalog_sha256"),
                "source-label preset catalog",
            )
            if tuple(cast(list[object], preset_member_ids)) != _PRESET_MEMBER_IDS.get(
                selector_value
            ):
                raise AtlasMediaError("source-label preset member IDs differ")
        else:
            if (
                story.get("source_preset_member_taxon_ids") is not None
                or story.get("source_preset_catalog_sha256") is not None
            ):
                raise AtlasMediaError(
                    "non-preset source story carries preset authority"
                )
            preset_member_ids = None
            preset_catalog = None
        if story.get("frame_feature_denominators") is not None:
            raise AtlasMediaError(f"source story has modeled denominators: {story_id}")
        if story.get("frame_no_pollen_data_counts") is not None:
            raise AtlasMediaError(
                f"source story has modeled quality counts: {story_id}"
            )
        if (
            sum(cast(list[int], visible_counts)) <= 0
            or sum(cast(list[int], visible_site_counts)) <= 0
            or any(cast(int, count) > cast(int, node_count) for count in visible_counts)
            or any(
                cast(int, count) > cast(int, site_count)
                for count in visible_site_counts
            )
            or any(
                capture.get("visible_source_chronology_point_count") != count
                or capture.get("facet_site_count") != site_count
                or capture.get("visible_site_count") != visible_site_count
                or cast(int, visible_site_count) > cast(int, count)
                or capture.get("visible_point_count") != count
                or capture.get("visible_modeled_context_feature_count") != 0
                or capture.get("visible_source_node_count") != count
                or not _valid_visible_source_observations(
                    capture.get("visible_source_observation_denominator"),
                    denominator=cast(int, observations),
                )
                or capture.get("visible_source_observation_denominator")
                != visible_observation_count
                for capture, count, visible_site_count, visible_observation_count in zip(
                    published_captures,
                    visible_counts,
                    visible_site_counts,
                    visible_observation_counts,
                    strict=True,
                )
            )
        ):
            raise AtlasMediaError(f"source visibility evidence differs: {story_id}")
        interpretation = story_interpretation(role, selector_kind)
    else:
        if (
            story.get("site_count") is not None
            or story.get("node_count") is not None
            or story.get("observation_denominator") is not None
            or story.get("expected_visible_feature_counts") is not None
            or story.get("expected_visible_site_counts") is not None
            or story.get("expected_visible_observation_counts") is not None
            or story.get("source_authority_sha256") is not None
            or story.get("source_preset_member_taxon_ids") is not None
            or story.get("source_preset_catalog_sha256") is not None
        ):
            raise AtlasMediaError("modeled story carries source evidence")
        site_count = None
        node_count = None
        observations = None
        visible_counts = None
        visible_site_counts = None
        visible_observation_counts = None
        authority = None
        preset_member_ids = None
        preset_catalog = None
        modeled_denominators = _positive_integer_list(
            story.get("frame_feature_denominators"),
            length=frame_count,
            label="modeled feature denominators",
        )
        modeled_no_pollen_denominators = _nonnegative_integer_list(
            story.get("frame_no_pollen_data_counts"),
            length=frame_count,
            label="modeled no-pollen-data counts",
        )
        if any(
            cast(int, count) > cast(int, denominator)
            for count, denominator in zip(
                modeled_no_pollen_denominators,
                modeled_denominators,
                strict=True,
            )
        ):
            raise AtlasMediaError("modeled no-pollen-data count exceeds denominator")
        if any(
            capture.get("visible_source_chronology_point_count") != 0
            or capture.get("visible_point_count") != 0
            or capture.get("visible_modeled_context_feature_count") != denominator
            or capture.get("visible_source_node_count") is not None
            or capture.get("visible_source_observation_denominator") is not None
            or capture.get("facet_site_count") is not None
            or capture.get("visible_site_count") is not None
            or capture.get("no_pollen_data_count") != no_pollen_count
            or capture.get("visible_modeled_no_pollen_data_count") != no_pollen_count
            for capture, denominator, no_pollen_count in zip(
                published_captures,
                modeled_denominators,
                modeled_no_pollen_denominators,
                strict=True,
            )
        ):
            raise AtlasMediaError("modeled visibility evidence differs")
        interpretation = story_interpretation(role, selector_kind)

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
            poster_capture=published_captures[poster_ordinal],
            mp4_probe=mp4_probe,
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
            "site_count": site_count,
            "node_count": node_count,
            "observation_denominator": observations,
            "frame_feature_denominators": modeled_denominators,
            "frame_no_pollen_data_counts": modeled_no_pollen_denominators,
            "expected_visible_feature_counts": visible_counts,
            "expected_visible_site_counts": visible_site_counts,
            "expected_visible_observation_counts": visible_observation_counts,
            "source_authority_sha256": authority,
            "source_preset_member_taxon_ids": preset_member_ids,
            "source_preset_catalog_sha256": preset_catalog,
            "frame_count": frame_count,
            "poster_frame_ordinal": poster_ordinal,
            "first_frame": first_frame,
            "last_frame": last_frame,
            "frame_set_sha256": frame_set,
            "capture_frame_set_sha256": capture_set,
            "assets": [_public_asset_row(row) for row in transfers],
        },
        transfers,
    )


def _valid_visible_source_observations(value: object, *, denominator: int) -> bool:
    return value is None or (
        isinstance(value, int)
        and not isinstance(value, bool)
        and 0 <= value <= denominator
    )


def _publication_asset(
    story_id: str,
    asset: Mapping[str, object],
    *,
    media_type: str,
    source_root: Path,
    frame_count: int,
    encoding: Mapping[str, object],
    poster_capture: Mapping[str, object],
    mp4_probe: Mp4Probe,
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
    elif digest != poster_capture.get("png_sha256") or byte_count != poster_capture.get(
        "byte_count"
    ):
        raise AtlasMediaError(f"poster differs from the selected capture: {story_id}")
    path = _regular_child(source_root, source_path)
    if path.stat().st_size != byte_count or sha256_file(path) != digest:
        raise AtlasMediaError(f"{media_type} source bytes differ: {story_id}")
    _validate_media_properties(
        path,
        media_type=media_type,
        width=width,
        height=height,
        frame_count=expected_frames,
        duration_seconds=duration,
        mp4_probe=mp4_probe,
    )
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


def validate_atlas_media_publication(
    publication_root: Path,
    *,
    ffprobe_binary: Path | None = None,
    mp4_probe: Mp4Probe | None = None,
) -> dict[str, object]:
    """Validate every contract and media byte in one published website bundle."""
    probe = _resolve_mp4_probe(ffprobe_binary=ffprobe_binary, mp4_probe=mp4_probe)
    return _validate_atlas_media_publication_inventory(
        publication_root,
        expected_schema_version=PUBLICATION_SCHEMA_VERSION,
        expected_stories=_EXPECTED_STORIES,
        mp4_probe=probe,
    )


def _validate_atlas_media_publication_inventory(
    publication_root: Path,
    *,
    expected_schema_version: str,
    expected_stories: tuple[tuple[str, str, str, str, str | None], ...],
    mp4_probe: Mp4Probe,
    legacy_v3: bool = False,
) -> dict[str, object]:
    """Validate one publication against an explicitly recognized inventory."""
    if legacy_v3 != (
        expected_schema_version
        in {
            "atlas-media-publication.v1",
            "atlas-media-publication.v2",
            LEGACY_PUBLICATION_SCHEMA_VERSION_V3,
        }
    ):
        raise AtlasMediaError("publication validator contract is inconsistent")
    expected_asset_count = len(expected_stories) * 2
    root = _existing_directory(publication_root, label="publication_root")
    manifest_path = _direct_regular_file(root, "publication-manifest.json")
    checksum_path = _direct_regular_file(root, "publication-manifest.sha256")
    payload = manifest_path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if checksum_path.read_bytes() != f"{digest}  publication-manifest.json\n".encode():
        raise AtlasMediaError("publication manifest checksum differs")
    manifest = _load_json_object(payload, label="publication manifest")
    content_digest = manifest.get("content_sha256")
    content = {key: value for key, value in manifest.items() if key != "content_sha256"}
    expected_manifest_fields = (
        _PUBLICATION_FIELDS
        if expected_schema_version == PUBLICATION_SCHEMA_VERSION
        else _LEGACY_PUBLICATION_FIELDS
    )
    if (
        set(manifest) != expected_manifest_fields
        or manifest.get("schema_version") != expected_schema_version
        or not _is_sha256(content_digest)
        or content_digest != hashlib.sha256(canonical_json_bytes(content)).hexdigest()
    ):
        raise AtlasMediaError("publication content identity differs")

    source_gallery = _object(manifest.get("source_gallery"), "source gallery")
    if set(source_gallery) != {"manifest_sha256", "content_sha256"}:
        raise AtlasMediaError("source gallery identity fields differ")
    _digest(source_gallery.get("manifest_sha256"), "source gallery manifest")
    _digest(source_gallery.get("content_sha256"), "source gallery content")
    atlas_identity = _atlas_identity(manifest.get("atlas_identity"))
    candidate_identity = _candidate_identity(manifest.get("candidate_identity"))
    if atlas_identity["build_id"] != candidate_identity["build_id"]:
        raise AtlasMediaError("published atlas and candidate build identities differ")
    _digest(manifest.get("storyboard_sha256"), "published storyboard")
    source_authority = _digest(
        manifest.get("source_authority_sha256"), "published source authority"
    )
    source_preset_catalog_sha256 = None
    if expected_schema_version == PUBLICATION_SCHEMA_VERSION:
        _catalog, source_preset_catalog_sha256 = validate_source_preset_catalog(
            manifest.get("source_label_preset_catalog")
        )
    if manifest.get("scientific_posture") != {
        "temporal_direction": "oldest_to_present",
        "interval_semantics": "[younger_bp, older_bp]",
        "null_not_zero": True,
        "interpolation_allowed": False,
        "observation_is_propagation": False,
        "modeled_context_is_observation": False,
    }:
        raise AtlasMediaError("publication scientific posture differs")
    _candidate_succession(manifest.get("candidate_succession"))
    _tool_identity(manifest.get("tool_identity"))
    encoding = _published_encoding(
        manifest.get("encoding_profile"), legacy_v3=legacy_v3
    )
    budget = _object(manifest.get("publication_budget"), "publication budget")
    if (
        set(budget)
        != {
            "maximum_mp4_bytes",
            "maximum_poster_bytes",
            "maximum_total_bytes",
            "published_asset_count",
            "published_byte_count",
        }
        or budget.get("maximum_mp4_bytes") != MAX_MP4_BYTES
        or budget.get("maximum_poster_bytes") != MAX_POSTER_BYTES
        or budget.get("maximum_total_bytes") != MAX_PUBLICATION_BYTES
        or budget.get("published_asset_count") != expected_asset_count
    ):
        raise AtlasMediaError("publication budget contract differs")
    stories = _object_list(manifest.get("stories"), "publication stories")
    if manifest.get("story_count") != len(expected_stories) or len(stories) != len(
        expected_stories
    ):
        raise AtlasMediaError("publication story inventory differs")
    if (
        expected_schema_version == PUBLICATION_SCHEMA_VERSION
        and sum(
            _positive_integer(story.get("frame_count"), "publication story frame_count")
            for story in stories
        )
        != PUBLICATION_FRAME_COUNT
    ):
        raise AtlasMediaError("publication frame inventory differs")
    expected_files = {"publication-manifest.json", "publication-manifest.sha256"}
    published_bytes = 0
    published_assets = 0
    preset_catalogs: set[str] = set()
    for story, expected in zip(stories, expected_stories, strict=True):
        _validate_published_story(
            story,
            expected=expected,
            source_authority_sha256=source_authority,
            source_preset_catalog_sha256=source_preset_catalog_sha256,
            legacy_v3=legacy_v3,
            legacy_v4=(expected_schema_version == LEGACY_PUBLICATION_SCHEMA_VERSION_V4),
        )
        preset_catalog = story.get("source_preset_catalog_sha256")
        if isinstance(preset_catalog, str):
            preset_catalogs.add(preset_catalog)
        story_id = expected[0]
        frame_count = cast(int, story["frame_count"])
        assets = _object_list(story.get("assets"), "publication assets")
        if len(assets) != 2 or [asset.get("media_type") for asset in assets] != [
            "poster",
            "mp4",
        ]:
            raise AtlasMediaError("publication asset inventory differs")
        for asset in assets:
            if set(asset) != {"media_type", "source", "published"}:
                raise AtlasMediaError("publication asset fields differ")
            media_type = asset.get("media_type")
            published = _object(asset.get("published"), "published asset identity")
            source = _object(asset.get("source"), "source asset identity")
            if source != published or set(published) != {
                "path",
                "byte_count",
                "sha256",
                "width",
                "height",
                "frame_count",
                "duration_seconds",
            }:
                raise AtlasMediaError("source and published asset identities differ")
            suffix = ".poster.png" if media_type == "poster" else ".mp4"
            expected_path = f"media/{story_id}{suffix}"
            path_text = published.get("path")
            if path_text != expected_path:
                raise AtlasMediaError("published asset path differs")
            byte_count = _positive_integer(
                published.get("byte_count"), "published byte_count"
            )
            maximum = MAX_POSTER_BYTES if media_type == "poster" else MAX_MP4_BYTES
            if byte_count > maximum:
                raise AtlasMediaError("published asset exceeds its budget")
            asset_digest = _digest(published.get("sha256"), "published asset")
            width = _positive_integer(published.get("width"), "published width")
            height = _positive_integer(published.get("height"), "published height")
            expected_frames = 1 if media_type == "poster" else frame_count
            if (
                width != encoding["width"]
                or height != encoding["height"]
                or published.get("frame_count") != expected_frames
            ):
                raise AtlasMediaError("published media dimensions or frames differ")
            duration: float | int | None = None
            if media_type == "poster":
                if published.get("duration_seconds") is not None:
                    raise AtlasMediaError("published poster duration must be null")
            else:
                duration = _positive_number(
                    published.get("duration_seconds"), "published MP4 duration"
                )
                expected_duration = frame_count / cast(
                    int, encoding["frames_per_second"]
                )
                if not math.isclose(
                    float(duration),
                    expected_duration,
                    rel_tol=0,
                    abs_tol=(1 / cast(int, encoding["frames_per_second"])) + 0.01,
                ):
                    raise AtlasMediaError("published MP4 duration differs")
            path = _regular_child(root, path_text)
            if path.stat().st_size != byte_count or sha256_file(path) != asset_digest:
                raise AtlasMediaError("published asset bytes differ")
            _validate_media_properties(
                path,
                media_type=cast(str, media_type),
                width=width,
                height=height,
                frame_count=expected_frames,
                duration_seconds=duration,
                mp4_probe=mp4_probe,
            )
            expected_files.add(path_text)
            published_bytes += byte_count
            published_assets += 1
    if expected_schema_version == PUBLICATION_SCHEMA_VERSION and preset_catalogs != {
        source_preset_catalog_sha256
    }:
        raise AtlasMediaError(
            "source-label preset stories differ from governed catalog"
        )
    observed = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    if observed != expected_files:
        raise AtlasMediaError("publication contains missing or extra files")
    if (
        published_assets != expected_asset_count
        or published_bytes > MAX_PUBLICATION_BYTES
        or budget.get("published_asset_count") != published_assets
        or budget.get("published_byte_count") != published_bytes
    ):
        raise AtlasMediaError("publication observed budget totals differ")
    return manifest


def _validate_published_story(
    story: Mapping[str, object],
    *,
    expected: tuple[str, str, str, str, str | None],
    source_authority_sha256: str,
    source_preset_catalog_sha256: str | None,
    legacy_v3: bool = False,
    legacy_v4: bool = False,
) -> None:
    story_id, role, selector_kind, selector_value, selector_family = expected
    expected_title = (
        LEGACY_PUBLICATION_STORY_TITLES_V3[story_id]
        if legacy_v3
        else LEGACY_PUBLICATION_STORY_TITLES_V4[story_id]
        if legacy_v4
        else PUBLICATION_STORY_TITLES[story_id]
    )
    expected_fields = (
        _LEGACY_V3_PUBLIC_STORY_FIELDS if legacy_v3 else _PUBLIC_STORY_FIELDS
    )
    if legacy_v4:
        expected_fields = _LEGACY_V4_PUBLIC_STORY_FIELDS
    if (
        set(story) != expected_fields
        or story.get("story_id") != story_id
        or story.get("title") != expected_title
        or story.get("evidence_role") != role
        or story.get("selector")
        != {"kind": selector_kind, "value": selector_value, "family": selector_family}
        or story.get("temporal_direction") != "oldest_to_present"
        or story.get("interval_semantics") != "[younger_bp, older_bp]"
        or story.get("interpretation")
        != (
            _LEGACY_SOURCE_INTERPRETATION
            if (legacy_v3 or legacy_v4) and role == "observation_chronology"
            else _LEGACY_MODELED_INTERPRETATION
            if legacy_v3 or legacy_v4
            else story_interpretation(role, selector_kind)
        )
    ):
        raise AtlasMediaError("publication story identity or semantics differ")
    title = story.get("title")
    if not isinstance(title, str) or not title.strip():
        raise AtlasMediaError("publication story title is absent")
    frame_count = _positive_integer(
        story.get("frame_count"), "publication story frame_count"
    )
    if not legacy_v3:
        poster_ordinal = story.get("poster_frame_ordinal")
        if (
            isinstance(poster_ordinal, bool)
            or not isinstance(poster_ordinal, int)
            or not 0 <= poster_ordinal < frame_count
        ):
            raise AtlasMediaError("publication poster frame ordinal differs")
    first_frame = _frame_boundary(story.get("first_frame"), "published first_frame")
    last_frame = _frame_boundary(story.get("last_frame"), "published last_frame")
    _validate_boundary_selector(
        first_frame,
        ordinal=0,
        expected=expected,
        legacy_v3=legacy_v3,
    )
    _validate_boundary_selector(
        last_frame,
        ordinal=frame_count - 1,
        expected=expected,
        legacy_v3=legacy_v3,
    )
    if (
        cast(float | int, first_frame["time_start_bp"])
        < cast(float | int, last_frame["time_start_bp"])
        or cast(float | int, first_frame["time_end_bp"])
        < cast(float | int, last_frame["time_end_bp"])
        or (
            frame_count > 1
            and cast(float | int, first_frame["time_start_bp"])
            == cast(float | int, last_frame["time_start_bp"])
        )
    ):
        raise AtlasMediaError("publication story boundary direction differs")
    _digest(story.get("frame_set_sha256"), "published frame set")
    _digest(story.get("capture_frame_set_sha256"), "published capture frame set")
    if role == "observation_chronology":
        site_count = (
            None
            if legacy_v3 or legacy_v4
            else _positive_integer(story.get("site_count"), "published site_count")
        )
        node_count = _positive_integer(story.get("node_count"), "published node_count")
        _positive_integer(
            story.get("observation_denominator"),
            "published observation_denominator",
        )
        visible = _nonnegative_integer_list(
            story.get("expected_visible_feature_counts"),
            length=frame_count,
            label="published visibility denominators",
        )
        visible_sites = (
            None
            if legacy_v3 or legacy_v4
            else _nonnegative_integer_list(
                story.get("expected_visible_site_counts"),
                length=frame_count,
                label="published site visibility denominators",
            )
        )
        visible_observations = (
            None
            if legacy_v3 or legacy_v4
            else _nonnegative_integer_list(
                story.get("expected_visible_observation_counts"),
                length=frame_count,
                label="published observation visibility denominators",
            )
        )
        if selector_kind == "source_label_preset":
            member_ids = _positive_integer_list(
                story.get("source_preset_member_taxon_ids"),
                length=None,
                label="published source-label preset member IDs",
            )
            if len(set(cast(list[int], member_ids))) != len(member_ids):
                raise AtlasMediaError("published source-label preset member IDs differ")
            if tuple(member_ids) != _PRESET_MEMBER_IDS.get(selector_value):
                raise AtlasMediaError("published source-label preset member IDs differ")
            preset_catalog = _digest(
                story.get("source_preset_catalog_sha256"),
                "published source-label preset catalog",
            )
            if preset_catalog != source_preset_catalog_sha256:
                raise AtlasMediaError("published source-label preset catalog differs")
        elif (
            not legacy_v3
            and not legacy_v4
            and (
                story.get("source_preset_member_taxon_ids") is not None
                or story.get("source_preset_catalog_sha256") is not None
            )
        ):
            raise AtlasMediaError(
                "published non-preset source story carries preset authority"
            )
        if (
            story.get("frame_feature_denominators") is not None
            or (not legacy_v3 and story.get("frame_no_pollen_data_counts") is not None)
            or story.get("source_authority_sha256") != source_authority_sha256
            or sum(cast(list[int], visible)) <= 0
            or any(cast(int, count) > node_count for count in visible)
            or (
                visible_sites is not None
                and (
                    site_count is None
                    or sum(cast(list[int], visible_sites)) <= 0
                    or any(cast(int, count) > site_count for count in visible_sites)
                )
            )
            or (
                visible_observations is not None
                and sum(cast(list[int], visible_observations)) <= 0
            )
        ):
            raise AtlasMediaError("published source-story evidence differs")
    elif (
        (not legacy_v3 and not legacy_v4 and story.get("site_count") is not None)
        or story.get("node_count") is not None
        or story.get("observation_denominator") is not None
        or story.get("expected_visible_feature_counts") is not None
        or (
            not legacy_v3
            and not legacy_v4
            and story.get("expected_visible_site_counts") is not None
        )
        or (
            not legacy_v3
            and not legacy_v4
            and story.get("expected_visible_observation_counts") is not None
        )
        or story.get("source_authority_sha256") is not None
        or (
            not legacy_v3
            and not legacy_v4
            and (
                story.get("source_preset_member_taxon_ids") is not None
                or story.get("source_preset_catalog_sha256") is not None
            )
        )
    ):
        raise AtlasMediaError("published modeled story carries source evidence")
    else:
        modeled_denominators = _positive_integer_list(
            story.get("frame_feature_denominators"),
            length=frame_count,
            label="published modeled denominators",
        )
        if not legacy_v3:
            no_pollen_counts = _nonnegative_integer_list(
                story.get("frame_no_pollen_data_counts"),
                length=frame_count,
                label="published modeled no-pollen-data counts",
            )
            if any(
                cast(int, count) > cast(int, denominator)
                for count, denominator in zip(
                    no_pollen_counts, modeled_denominators, strict=True
                )
            ):
                raise AtlasMediaError(
                    "published modeled no-pollen-data count exceeds denominator"
                )

    if not legacy_v3:
        poster_counts = (
            visible
            if role == "observation_chronology"
            else _positive_integer_list(
                story.get("frame_feature_denominators"),
                length=frame_count,
                label="published modeled feature denominators",
            )
        )
        expected_poster = max(
            range(frame_count),
            key=lambda ordinal: (cast(list[int], poster_counts)[ordinal], -ordinal),
        )
        if story.get("poster_frame_ordinal") != expected_poster:
            raise AtlasMediaError("publication poster frame ordinal differs")


def _published_encoding(value: object, *, legacy_v3: bool = False) -> dict[str, object]:
    row = _object(value, "published encoding profile")
    _positive_integer(row.get("width"), "published encoding width")
    _positive_integer(row.get("height"), "published encoding height")
    frames_per_second = _positive_integer(
        row.get("frames_per_second"), "published encoding frame rate"
    )
    if (
        set(row)
        != {
            "schema_version",
            "width",
            "height",
            "frames_per_second",
            "poster",
            "mp4",
        }
        or row.get("schema_version") != "atlas-media-publication-encoding.v1"
        or row.get("poster")
        != (
            {"format": "png", "source_frame_ordinal": 0}
            if legacy_v3
            else {
                "format": "png",
                "source_frame_selection": (
                    "maximum_selected_evidence_earliest_ordinal_on_tie"
                ),
            }
        )
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
        or frames_per_second > 60
    ):
        raise AtlasMediaError("published encoding profile differs")
    return dict(row)


def _require_existing_destination_is_governed(
    destination: Path, *, mp4_probe: Mp4Probe
) -> None:
    if destination.is_symlink():
        raise AtlasMediaError("publication destination must not be a symlink")
    if not destination.exists():
        return
    if not destination.is_dir():
        raise AtlasMediaError("publication destination must be a directory")
    root = _existing_directory(destination, label="publication destination")
    manifest_path = _direct_regular_file(root, "publication-manifest.json")
    manifest = _load_json_object(
        manifest_path.read_bytes(), label="existing publication manifest"
    )
    schema_version = manifest.get("schema_version")
    contract = next(
        (
            (supported_schema, inventory)
            for supported_schema, inventory in SUPPORTED_EXISTING_PUBLICATION_CONTRACTS
            if supported_schema == schema_version
        ),
        None,
    )
    if contract is None:
        raise AtlasMediaError("existing publication schema_version is unsupported")
    supported_schema, inventory = contract
    _validate_atlas_media_publication_inventory(
        root,
        expected_schema_version=supported_schema,
        expected_stories=inventory,
        mp4_probe=mp4_probe,
        legacy_v3=(
            supported_schema
            not in {LEGACY_PUBLICATION_SCHEMA_VERSION_V4, PUBLICATION_SCHEMA_VERSION}
        ),
    )


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


def _resolve_mp4_probe(
    *, ffprobe_binary: Path | None, mp4_probe: Mp4Probe | None
) -> Mp4Probe:
    if ffprobe_binary is not None and mp4_probe is not None:
        raise AtlasMediaError("provide ffprobe_binary or mp4_probe, not both")
    if mp4_probe is not None:
        return mp4_probe
    candidate = ffprobe_binary
    if candidate is None:
        discovered = shutil.which("ffprobe")
        if discovered is None:
            raise AtlasMediaError(
                "ffprobe is required unless an explicit MP4 probe is supplied"
            )
        candidate = Path(discovered)
    try:
        binary = candidate.resolve(strict=True)
    except OSError as error:
        raise AtlasMediaError("ffprobe binary is unavailable") from error
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise AtlasMediaError("ffprobe binary must be an executable file")

    def probe(path: Path) -> ProbedMp4:
        return _ffprobe_mp4(binary, path)

    return probe


def _ffprobe_mp4(binary: Path, path: Path) -> ProbedMp4:
    try:
        completed = run_bounded_argv(
            (
                str(binary),
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-count_frames",
                "-show_entries",
                "stream=codec_name,pix_fmt,width,height,nb_read_frames,duration",
                "-of",
                "json",
                str(path),
            ),
            cwd=path.parent,
            timeout_seconds=30,
            max_output_bytes=1024 * 1024,
        )
    except BoundedProcessError as error:
        raise AtlasMediaError("ffprobe could not inspect published MP4") from error
    if completed.timed_out or completed.returncode != 0:
        raise AtlasMediaError("ffprobe rejected published MP4")
    try:
        value = json.loads(completed.stdout.decode("utf-8"))
        streams = value["streams"]
        stream = streams[0]
        if len(streams) != 1:
            raise ValueError("expected exactly one selected video stream")
        result = ProbedMp4(
            width=int(stream["width"]),
            height=int(stream["height"]),
            frame_count=int(stream["nb_read_frames"]),
            duration_seconds=float(stream["duration"]),
            codec_name=str(stream["codec_name"]),
            pixel_format=str(stream["pix_fmt"]),
        )
    except (
        KeyError,
        IndexError,
        TypeError,
        ValueError,
        UnicodeError,
        json.JSONDecodeError,
    ) as error:
        raise AtlasMediaError("ffprobe MP4 evidence is incomplete") from error
    return result


def _validate_media_properties(
    path: Path,
    *,
    media_type: str,
    width: int,
    height: int,
    frame_count: int,
    duration_seconds: float | None,
    mp4_probe: Mp4Probe,
) -> None:
    if media_type == "poster":
        observed_width, observed_height = _inspect_png(path)
        if (observed_width, observed_height) != (width, height):
            raise AtlasMediaError("PNG dimensions differ from publication evidence")
        return
    if media_type != "mp4":
        raise AtlasMediaError("published media type is unsupported")
    _inspect_mp4_boxes(path)
    try:
        observed = mp4_probe(path)
    except AtlasMediaError:
        raise
    except Exception as error:
        raise AtlasMediaError("MP4 probe failed") from error
    if (
        isinstance(observed.width, bool)
        or observed.width != width
        or isinstance(observed.height, bool)
        or observed.height != height
        or isinstance(observed.frame_count, bool)
        or observed.frame_count != frame_count
        or not math.isfinite(observed.duration_seconds)
        or duration_seconds is None
        or not math.isclose(
            observed.duration_seconds,
            float(duration_seconds),
            rel_tol=0,
            abs_tol=0.01,
        )
        or observed.codec_name != "h264"
        or observed.pixel_format != "yuv420p"
    ):
        raise AtlasMediaError("MP4 properties differ from publication evidence")


def _inspect_png(path: Path) -> tuple[int, int]:
    if path.stat().st_size > MAX_POSTER_BYTES:
        raise AtlasMediaError("poster exceeds the PNG inspection bound")
    payload = path.read_bytes()
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise AtlasMediaError("poster is not a bounded PNG")
    offset = 8
    chunks: list[bytes] = []
    ihdr: bytes | None = None
    saw_iend = False
    while offset < len(payload):
        if offset + 12 > len(payload):
            raise AtlasMediaError("PNG chunk header is truncated")
        length = int.from_bytes(payload[offset : offset + 4], "big")
        chunk_type = payload[offset + 4 : offset + 8]
        end = offset + 12 + length
        if length > MAX_POSTER_BYTES or end > len(payload):
            raise AtlasMediaError("PNG chunk is out of bounds")
        data = payload[offset + 8 : offset + 8 + length]
        expected_crc = int.from_bytes(payload[offset + 8 + length : end], "big")
        if zlib.crc32(chunk_type + data) & 0xFFFFFFFF != expected_crc:
            raise AtlasMediaError("PNG chunk checksum differs")
        if offset == 8 and chunk_type != b"IHDR":
            raise AtlasMediaError("PNG IHDR must be the first chunk")
        if chunk_type == b"IHDR":
            if ihdr is not None or length != 13:
                raise AtlasMediaError("PNG IHDR is invalid")
            ihdr = data
        elif chunk_type == b"IDAT":
            chunks.append(data)
        elif chunk_type == b"IEND":
            if length != 0 or end != len(payload):
                raise AtlasMediaError("PNG IEND or trailing bytes are invalid")
            saw_iend = True
        offset = end
    if ihdr is None or not chunks or not saw_iend:
        raise AtlasMediaError("PNG structural chunks are incomplete")
    width = int.from_bytes(ihdr[0:4], "big")
    height = int.from_bytes(ihdr[4:8], "big")
    bit_depth, color_type, compression, filtering, interlace = ihdr[8:13]
    valid_depths = {
        0: {1, 2, 4, 8, 16},
        2: {8, 16},
        3: {1, 2, 4, 8},
        4: {8, 16},
        6: {8, 16},
    }
    if (
        not 1 <= width <= 3840
        or not 1 <= height <= 2160
        or bit_depth not in valid_depths.get(color_type, set())
        or compression != 0
        or filtering != 0
        or interlace not in {0, 1}
    ):
        raise AtlasMediaError("PNG IHDR properties are invalid")
    maximum_image_bytes = (3840 * 2160 * 8) + 2160
    try:
        decompressor = zlib.decompressobj()
        image_bytes = decompressor.decompress(b"".join(chunks), maximum_image_bytes + 1)
    except zlib.error as error:
        raise AtlasMediaError("PNG image data is not decompressible") from error
    if (
        len(image_bytes) > maximum_image_bytes
        or decompressor.unconsumed_tail
        or decompressor.unused_data
        or not decompressor.eof
    ):
        raise AtlasMediaError("PNG decompressed data exceeds its structural bound")
    if interlace == 0:
        channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
        row_bytes = (width * channels * bit_depth + 7) // 8
        if len(image_bytes) != height * (row_bytes + 1):
            raise AtlasMediaError("PNG image data length differs")
    return width, height


def _inspect_mp4_boxes(path: Path) -> None:
    if path.stat().st_size > MAX_MP4_BYTES:
        raise AtlasMediaError("MP4 exceeds the structural inspection bound")
    payload = path.read_bytes()
    if len(payload) < 24:
        raise AtlasMediaError("MP4 is outside structural size bounds")
    offset = 0
    boxes: list[bytes] = []
    while offset < len(payload):
        if offset + 8 > len(payload):
            raise AtlasMediaError("MP4 box header is truncated")
        size = int.from_bytes(payload[offset : offset + 4], "big")
        box_type = payload[offset + 4 : offset + 8]
        header_size = 8
        if size == 1:
            if offset + 16 > len(payload):
                raise AtlasMediaError("MP4 extended box header is truncated")
            size = int.from_bytes(payload[offset + 8 : offset + 16], "big")
            header_size = 16
        elif size == 0:
            size = len(payload) - offset
        if size < header_size or offset + size > len(payload):
            raise AtlasMediaError("MP4 box is out of bounds")
        if any(character < 0x20 or character > 0x7E for character in box_type):
            raise AtlasMediaError("MP4 box type is invalid")
        boxes.append(box_type)
        offset += size
    if (
        not boxes
        or boxes[0] != b"ftyp"
        or b"moov" not in boxes
        or b"mdat" not in boxes
        or boxes.index(b"moov") > boxes.index(b"mdat")
    ):
        raise AtlasMediaError("MP4 required boxes or fast-start order differ")


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
        or row.get("poster")
        != {
            "format": "png",
            "source_frame_selection": "maximum_selected_evidence_earliest_ordinal_on_tie",
        }
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
    legacy_v3: bool = False,
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
        expected_fields.update({"source_level", "source_window_label", "feature_count"})
        if selector_kind == "source_ecological_code":
            expected_fields.add("source_code")
        elif selector_kind == "source_taxon":
            expected_fields.add("source_taxon")
        elif selector_kind == "source_label_preset":
            expected_fields.update({"source_taxon", "source_preset"})
    else:
        expected_fields.update(
            {
                "source_window_label",
                "metric_family_key",
                "metric_key",
                "feature_count",
            }
        )
        if not legacy_v3:
            expected_fields.add("no_pollen_data_count")
    if (
        set(frame) != expected_fields
        or frame.get("ordinal") != ordinal
        or frame.get("countries") != ["Denmark", "Finland", "Norway", "Sweden"]
    ):
        raise AtlasMediaError("story boundary identity differs")
    if role == "observation_chronology":
        if (
            frame.get("story_kind") != "source_chronology"
            or frame.get("source_level") != _source_level(selector_kind)
            or frame.get("source_window_label") is not None
            or frame.get("feature_count") is not None
            or (
                selector_kind == "source_ecological_code"
                and frame.get("source_code") != selector_value
            )
            or (
                selector_kind == "source_taxon"
                and frame.get("source_taxon") != selector_value
            )
            or (
                selector_kind == "source_label_preset"
                and (
                    frame.get("source_taxon") != "all"
                    or frame.get("source_preset") != selector_value
                )
            )
        ):
            raise AtlasMediaError("source story boundary selector differs")
    elif (
        frame.get("story_kind") != "modeled_context"
        or frame.get("metric_key") != selector_value
        or frame.get("metric_family_key") != selector_family
        or _positive_integer(frame.get("feature_count"), "boundary feature_count") <= 0
        or (
            not legacy_v3
            and (
                isinstance(frame.get("no_pollen_data_count"), bool)
                or not isinstance(frame.get("no_pollen_data_count"), int)
                or cast(int, frame["no_pollen_data_count"]) < 0
                or cast(int, frame["no_pollen_data_count"])
                > cast(int, frame["feature_count"])
            )
        )
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


def _positive_integer_list(
    value: object, *, length: int | None, label: str
) -> list[object]:
    if (
        not isinstance(value, list)
        or (length is not None and len(value) != length)
        or not value
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
    parser.add_argument(
        "--ffprobe",
        dest="ffprobe_binary",
        type=Path,
        help="Explicit ffprobe binary used for bounded MP4 verification.",
    )
    arguments = parser.parse_args(argv)
    publish_atlas_media(
        arguments.gallery_root,
        arguments.destination,
        ffprobe_binary=arguments.ffprobe_binary,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through the API
    raise SystemExit(main())


__all__ = [
    "MAX_MP4_BYTES",
    "MAX_POSTER_BYTES",
    "MAX_PUBLICATION_BYTES",
    "Mp4Probe",
    "ProbedMp4",
    "main",
    "publish_atlas_media",
    "validate_atlas_media_publication",
]
