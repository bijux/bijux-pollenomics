"""Tests for deterministic atlas-media website publication."""

from __future__ import annotations

import base64
import hashlib
import json
import shutil
import zlib
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest
from bijux_pollenomics.reporting.source_chronology.source_label_presets import (
    NEOTOMA_SOURCE_LABEL_PRESETS,
)
from bijux_pollenomics_dev.ci.atlas_media import AtlasMediaError, publication
from bijux_pollenomics_dev.ci.atlas_media.catalog import (
    LEGACY_PUBLICATION_SCHEMA_VERSION_V3,
    LEGACY_PUBLICATION_SCHEMA_VERSION_V4,
    LEGACY_PUBLICATION_STORY_TITLES_V3,
    LEGACY_PUBLICATION_STORY_TITLES_V4,
    LEGACY_PUBLICATION_STORY_TUPLES_V3,
    LEGACY_PUBLICATION_STORY_TUPLES_V4,
    PUBLICATION_ASSET_COUNT,
    PUBLICATION_SCHEMA_VERSION,
    PUBLICATION_STORIES,
    PUBLICATION_STORY_TITLES,
    PUBLICATION_STORY_TUPLES,
    SUPPORTED_EXISTING_PUBLICATION_CONTRACTS,
)
from bijux_pollenomics_dev.ci.atlas_media.contracts import SelectedStory
from bijux_pollenomics_dev.ci.atlas_media.gallery import (
    build_gallery_manifest,
    canonical_json_bytes,
    media_asset_row,
    sha256_file,
    write_gallery_manifest,
)

from tests.atlas_media.fixtures import (
    BUILD_ID,
    COUNTRIES,
    SUCCESSION,
    candidate,
    source_preset_catalog,
)
from tests.atlas_media.receipt_fixtures import (
    capture_evidence_layer_key,
    capture_layers,
    capture_layout,
    capture_presentation,
)

StorySpec = tuple[str, str, str, str, str | None]
STORIES: tuple[StorySpec, ...] = PUBLICATION_STORY_TUPLES
_PRESET_MEMBER_IDS = {
    preset.key: preset.member_taxon_ids for preset in NEOTOMA_SOURCE_LABEL_PRESETS
}
_PRESET_CATALOG_DIGEST = str(
    source_preset_catalog()["content_sha256"]
).removeprefix("sha256:")
_FRAME_COUNTS = dict(
    zip(
        (story[0] for story in STORIES),
        (
            230, 230, 230, 192,
            140, 124, 107, 45, 119,
            18, 67, 72, 45, 24, 92, 14, 31,
            25, 25, 25, 25, 25, 25, 25, 25,
        ),
        strict=True,
    )
)

_MINIMAL_MP4 = base64.b64decode(
    "AAAAJGZ0eXBpc29tAAACAGlzb21pc282aXNvMmF2YzFtcDQxAAAC7W1vb3YAAABs"
    "bXZoZAAAAAAAAAAAAAAAAAAAA+gAAAAAAAEAAAEAAAAAAAAAAAAAAAABAAAAAAAAAAAA"
    "AAAAAAAAAQAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "AAIAAAHvdHJhawAAAFx0a2hkAAAAAwAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAA"
    "AAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAQAAAAAAQAAAAEAAA"
    "AAABi21kaWEAAAAgbWRoZAAAAAAAAAAAAAAAAAAAQAAAAAAAVcQAAAAAAC1oZGxyAAAA"
    "AAAAAAB2aWRlAAAAAAAAAAAAAAAAVmlkZW9IYW5kbGVyAAAAATZtaW5mAAAAFHZtaGQA"
    "AAABAAAAAAAAAAAAAAAkZGluZgAAABxkcmVmAAAAAAAAAAEAAAAMdXJsIAAAAAEAAAD2"
    "c3RibAAAAKpzdHNkAAAAAAAAAAEAAACaYXZjMQAAAAAAAAABAAAAAAAAAAAAAAAAAAAA"
    "AAAQABAASAAAAEgAAAAAAAAAARVMYXZjNjIuMjguMTAyIGxpYngyNjQAAAAAAAAAAAAA"
    "ABj//wAAADRhdmNDAWQACv/hABdnZAAKrNlewEQAAAMABAAAAwAIPEiWWAEABmjr48si"
    "wP34+AAAAAAQcGFzcAAAAAEAAAABAAAAEHN0dHMAAAAAAAAAAAAAABBzdHNjAAAAAAAA"
    "AAAAAAAUc3RzegAAAAAAAAAAAAAAAAAAABBzdGNvAAAAAAAAAAAAAAAobXZleAAAACB0"
    "cmV4AAAAAAAAAAEAAAABAAAAAAAAAAAAAAAAAAAAYnVkdGEAAABabWV0YQAAAAAAAAAh"
    "aGRscgAAAAAAAAAAbWRpcmFwcGwAAAAAAAAAAAAAAAAtaWxzdAAAACWpdG9vAAAAHWRh"
    "dGEAAAABAAAAAExhdmY2Mi4xMi4xMDIAAABwbW9vZgAAABBtZmhkAAAAAAAAAAEAAABY"
    "dHJhZgAAACR0ZmhkAAAAOQAAAAEAAAAAAAADEQAAQAAAAALFAQEAAAAAABR0ZmR0AQAA"
    "AAAAAAAAAAAAAAAAGHRydW4AAAAFAAAAAQAAAHgCAAAAAAACzW1kYXQAAAKtBgX//6nc"
    "Rem95tlIt5Ys2CDZI+7veDI2NCAtIGNvcmUgMTY1IHIzMjIyIGIzNTYwNWEgLSBILjI2"
    "NC9NUEVHLTQgQVZDIGNvZGVjIC0gQ29weWxlZnQgMjAwMy0yMDI1IC0gaHR0cDovL3d3"
    "dy52aWRlb2xhbi5vcmcveDI2NC5odG1sIC0gb3B0aW9uczogY2FiYWM9MSByZWY9MyBk"
    "ZWJsb2NrPTE6MDowIGFuYWx5c2U9MHgzOjB4MTEzIG1lPWhleCBzdWJtZT03IHBzeT0x"
    "IHBzeV9yZD0xLjAwOjAuMDAgbWl4ZWRfcmVmPTEgbWVfcmFuZ2U9MTYgY2hyb21hX21l"
    "PTEgdHJlbGxpcz0xIDh4OGRjdD0xIGNxbT0wIGRlYWR6b25lPTIxLDExIGZhc3RfcHNr"
    "aXA9MSBjaHJvbWFfcXBfb2Zmc2V0PS0yIHRocmVhZHM9MSBsb29rYWhlYWRfdGhyZWFk"
    "cz0xIHNsaWNlZF90aHJlYWRzPTAgbnI9MCBkZWNpbWF0ZT0xIGludGVybGFjZWQ9MCBi"
    "bHVyYXlfY29tcGF0PTAgY29uc3RyYWluZWRfaW50cmE9MCBiZnJhbWVzPTMgYl9weXJh"
    "bWlkPTIgYl9hZGFwdD0xIGJfYmlhcz0wIGRpcmVjdD0xIHdlaWdodGI9MSBvcGVuX2dv"
    "cD0wIHdlaWdodHA9MiBrZXlpbnQ9MjUwIGtleWludF9taW49MSBzY2VuZWN1dD00MCBp"
    "bnRyYV9yZWZyZXNoPTAgcmNfbG9va2FoZWFkPTQwIHJjPWNyZiBtYnRyZWU9MSBjcmY9"
    "MjMuMCBxY29tcD0wLjYwIHFwbWluPTAgcXBtYXg9NjkgcXBzdGVwPTQgaXBfcmF0aW89"
    "MS40MCBhcT0xOjEuMDAAgAAAABBliIQAFf/+98nvwKbr29+BAAAAQ21mcmEAAAArdGZy"
    "YQEAAAAAAAABAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAMRAQEBAAAAEG1mcm8AAAAAAAAA"
    "Qw=="
)


def _png(width: int = 16, height: int = 16) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            len(data).to_bytes(4, "big")
            + kind
            + data
            + (zlib.crc32(kind + data) & 0xFFFFFFFF).to_bytes(4, "big")
        )

    header = (
        width.to_bytes(4, "big") + height.to_bytes(4, "big") + bytes((8, 2, 0, 0, 0))
    )
    pixels = b"".join(b"\x00" + b"\x00\x00\x00" * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(pixels))
        + chunk(b"IEND", b"")
    )


def _probe(path: Path) -> publication.ProbedMp4:
    story_id = path.name.removesuffix(".mp4")
    frame_count = _FRAME_COUNTS.get(story_id, 1)
    return publication.ProbedMp4(
        width=16,
        height=16,
        frame_count=frame_count,
        duration_seconds=float(frame_count),
        codec_name="h264",
        pixel_format="yuv420p",
    )


def _publish(source: Path, destination: Path) -> dict[str, object]:
    return publication.publish_atlas_media(source, destination, mp4_probe=_probe)


def _encoding_profile() -> dict[str, object]:
    return {
        "schema_version": "atlas-media-encoding-profile.v1",
        "width": 16,
        "height": 16,
        "frames_per_second": 1,
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


def _story(spec: StorySpec) -> SelectedStory:
    story_id, role, kind, value, family = spec
    frame_count = _FRAME_COUNTS[story_id]
    frames = tuple(
        {
            "ordinal": ordinal,
            "story_kind": (
                "source_chronology"
                if role == "observation_chronology"
                else "modeled_context"
            ),
            "time_start_bp": frame_count - ordinal - 1,
            "time_end_bp": frame_count - ordinal,
            "countries": list(COUNTRIES),
            "basemap": "none",
        }
        for ordinal in range(frame_count)
    )
    if role == "observation_chronology":
        for frame in frames:
            frame.update(
                {
                    "source_level": (
                        "source_taxon" if kind == "source_label_preset" else kind
                    ),
                    "source_window_label": None,
                    "feature_count": None,
                }
            )
            if kind == "source_ecological_code":
                frame["source_code"] = value
            if kind == "source_taxon":
                frame["source_taxon"] = value
            if kind == "source_label_preset":
                frame["source_taxon"] = "all"
                frame["source_preset"] = value
        return SelectedStory(
            story_id=story_id,
            title=PUBLICATION_STORY_TITLES[story_id],
            evidence_role=role,
            selector_kind=kind,
            selector_value=value,
            selector_family=family,
            site_count=3,
            node_count=3,
            observation_denominator=4,
            expected_visible_feature_counts=(1,) * frame_count,
            expected_visible_site_counts=(1,) * frame_count,
            expected_visible_observation_counts=(1,) * frame_count,
            source_authority_sha256="1" * 64,
            source_preset_member_taxon_ids=(
                _PRESET_MEMBER_IDS[value]
                if kind == "source_label_preset"
                else None
            ),
            source_preset_catalog_sha256=(
                _PRESET_CATALOG_DIGEST
                if kind == "source_label_preset"
                else None
            ),
            frames=frames,
        )
    for frame in frames:
        frame.update(
            {
                "metric_family_key": family,
                "metric_key": value,
                "source_window_label": "synthetic governed window",
                "feature_count": 75,
                "no_pollen_data_count": 4,
            }
        )
    return SelectedStory(
        story_id=story_id,
        title=PUBLICATION_STORY_TITLES[story_id],
        evidence_role=role,
        selector_kind=kind,
        selector_value=value,
        selector_family=family,
        frame_feature_denominators=(75,) * frame_count,
        frame_no_pollen_data_counts=(4,) * frame_count,
        frames=frames,
    )


def _gallery(tmp_path: Path, *, stories: tuple[StorySpec, ...] = STORIES) -> Path:
    root = tmp_path / "artifacts" / "media"
    media = root / "media"
    media.mkdir(parents=True)
    selected = tuple(_story(spec) for spec in stories)
    assets_by_story: dict[str, list[dict[str, object]]] = {}
    captures: dict[str, list[dict[str, object]]] = {}
    for story in selected:
        assets: list[dict[str, object]] = []
        for media_type, suffix in (
            ("poster", ".poster.png"),
            ("mp4", ".mp4"),
            ("gif", ".gif"),
        ):
            path = media / f"{story.story_id}{suffix}"
            path.write_bytes(
                _png()
                if media_type == "poster"
                else (
                    _MINIMAL_MP4
                    if media_type == "mp4"
                    else f"{story.story_id}-gif".encode()
                )
            )
            row = media_asset_row(root, path, media_type=media_type)
            row.update(
                {
                    "width": 16,
                    "height": 16,
                    "frame_count": (
                        1 if media_type == "poster" else len(story.frames)
                    ),
                    **(
                        {"duration_seconds": float(len(story.frames))}
                        if media_type in {"mp4", "gif"}
                        else {}
                    ),
                }
            )
            assets.append(row)
        assets_by_story[story.story_id] = assets
        poster = next(row for row in assets if row["media_type"] == "poster")
        captures[story.story_id] = [
            {
                "ordinal": ordinal,
                "file": f"frames/{story.story_id}/{ordinal:06d}.png",
                "frame_sha256": "2" * 64,
                "png_sha256": poster["sha256"],
                "byte_count": poster["byte_count"],
                "no_pollen_data_count": frame.get("no_pollen_data_count"),
                "source_preset": frame.get("source_preset"),
                "source_preset_member_taxon_ids": (
                    list(story.source_preset_member_taxon_ids)
                    if story.source_preset_member_taxon_ids is not None
                    else None
                ),
                "source_preset_catalog_sha256": story.source_preset_catalog_sha256,
                "facet_site_count": (
                    story.site_count
                    if story.evidence_role == "observation_chronology"
                    else None
                ),
                "visible_site_count": (
                    1 if story.evidence_role == "observation_chronology" else None
                ),
                "visible_point_count": (
                    1 if story.evidence_role == "observation_chronology" else 0
                ),
                "visible_polygon_layer_count": (
                    0 if story.evidence_role == "observation_chronology" else 2
                ),
                "visible_polygon_feature_count": (
                    0 if story.evidence_role == "observation_chronology" else 75
                ),
                "visible_feature_count": (
                    1 if story.evidence_role == "observation_chronology" else 75
                ),
                "visible_source_chronology_point_count": (
                    1 if story.evidence_role == "observation_chronology" else 0
                ),
                "visible_modeled_context_feature_count": (
                    75 if story.evidence_role == "modeled_context" else 0
                ),
                "visible_modeled_no_pollen_data_count": (
                    4 if story.evidence_role == "modeled_context" else None
                ),
                "visible_source_node_count": (
                    1 if story.evidence_role == "observation_chronology" else None
                ),
                "visible_source_observation_denominator": (
                    1 if story.evidence_role == "observation_chronology" else None
                ),
                "capture_layers": capture_layers(
                    capture_evidence_layer_key(story.selector_kind)
                ),
                "capture_presentation": capture_presentation(
                    evidence_role=story.evidence_role,
                    source_level=(
                        "source_taxon"
                        if story.selector_kind == "source_label_preset"
                        else story.selector_kind
                    ),
                    source_preset=cast(str | None, frame.get("source_preset")),
                    title=story.title,
                    younger_bp=cast(int, frame["time_start_bp"]),
                    older_bp=cast(int, frame["time_end_bp"]),
                    visible_source_count=1,
                    visible_source_site_count=1,
                    source_site_denominator=story.site_count or 0,
                    source_node_denominator=story.node_count or 0,
                    visible_source_observations=1,
                    source_observation_denominator=story.observation_denominator or 0,
                    modeled_feature_count=cast(
                        int, frame.get("feature_count") or 0
                    ),
                    modeled_no_pollen_data_count=4,
                    source_window_label=str(
                        frame.get("source_window_label") or ""
                    ),
                ),
                "capture_layout": capture_layout(),
            }
            for ordinal, frame in enumerate(story.frames)
        ]
    tools: dict[str, object] = {
        name: {"binary_sha256": digit * 64, "version": f"{name} fixture"}
        for name, digit in zip(
            ("node", "ffmpeg", "ffprobe", "brave"),
            ("3", "4", "5", "6"),
            strict=True,
        )
    }
    manifest = build_gallery_manifest(
        atlas_identity={
            "build_id": BUILD_ID,
            "scope_slug": "nordic",
            "version": "v66",
            "countries": list(COUNTRIES),
        },
        candidate_identity=candidate().as_json(),
        storyboard_sha256="7" * 64,
        source_preset_catalog=source_preset_catalog(),
        stories=selected,
        assets_by_story=assets_by_story,
        capture_frames_by_story=captures,
        tool_identity=tools,
        encoding_profile=_encoding_profile(),
        execution_receipts=[
            {"path": "renderer.execution.json", "byte_count": 1, "sha256": "8" * 64}
        ],
        candidate_succession=dict(SUCCESSION),
    )
    write_gallery_manifest(root, manifest)
    return root


def _rewrite_gallery(
    root: Path,
    mutation: Callable[[dict[str, Any]], None],
    *,
    repair_content_hash: bool = True,
) -> None:
    path = root / "gallery-manifest.json"
    value: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    mutation(value)
    if repair_content_hash:
        content = {key: item for key, item in value.items() if key != "content_sha256"}
        value["content_sha256"] = hashlib.sha256(
            canonical_json_bytes(content)
        ).hexdigest()
    payload = canonical_json_bytes(value)
    path.write_bytes(payload)
    (root / "gallery-manifest.sha256").write_text(
        f"{hashlib.sha256(payload).hexdigest()}  gallery-manifest.json\n",
        encoding="utf-8",
    )


def _rewrite_publication(
    root: Path, mutation: Callable[[dict[str, Any]], object]
) -> None:
    path = root / "publication-manifest.json"
    value: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    mutation(value)
    content = {key: item for key, item in value.items() if key != "content_sha256"}
    value["content_sha256"] = hashlib.sha256(canonical_json_bytes(content)).hexdigest()
    payload = canonical_json_bytes(value)
    path.write_bytes(payload)
    (root / "publication-manifest.sha256").write_text(
        f"{hashlib.sha256(payload).hexdigest()}  publication-manifest.json\n",
        encoding="utf-8",
    )


def _rewrite_as_legacy_v3(root: Path) -> None:
    legacy_story_ids = {story_id for story_id, *_ in LEGACY_PUBLICATION_STORY_TUPLES_V3}
    current_only_story_ids = {
        story_id for story_id, *_ in PUBLICATION_STORY_TUPLES
    } - legacy_story_ids
    for story_id in current_only_story_ids:
        for suffix in (".poster.png", ".mp4"):
            (root / "media" / f"{story_id}{suffix}").unlink()

    def downgrade(value: dict[str, Any]) -> None:
        value["schema_version"] = LEGACY_PUBLICATION_SCHEMA_VERSION_V3
        value.pop("source_label_preset_catalog")
        value["encoding_profile"]["poster"] = {
            "format": "png",
            "source_frame_ordinal": 0,
        }
        by_id = {story["story_id"]: story for story in value["stories"]}
        donor = by_id["neotoma-source-taxon-416"]
        for story_id, _role, kind, selector_value, family in (
            LEGACY_PUBLICATION_STORY_TUPLES_V3
        ):
            if story_id in by_id:
                continue
            story = deepcopy(donor)
            story["story_id"] = story_id
            story["selector"] = {
                "kind": kind,
                "value": selector_value,
                "family": family,
            }
            story["frame_count"] = 1
            story["expected_visible_feature_counts"] = [1]
            story["expected_visible_site_counts"] = [1]
            story["expected_visible_observation_counts"] = [1]
            story["poster_frame_ordinal"] = 0
            for boundary in (story["first_frame"], story["last_frame"]):
                boundary["ordinal"] = 0
                boundary["time_start_bp"] = 0
                boundary["time_end_bp"] = 1
                boundary["source_taxon"] = selector_value
            for asset in story["assets"]:
                suffix = ".poster.png" if asset["media_type"] == "poster" else ".mp4"
                source_path = root / "media" / f"neotoma-source-taxon-416{suffix}"
                target_path = root / "media" / f"{story_id}{suffix}"
                target_path.write_bytes(source_path.read_bytes())
                for identity in (asset["source"], asset["published"]):
                    identity["path"] = f"media/{story_id}{suffix}"
                    if asset["media_type"] == "mp4":
                        identity["frame_count"] = 1
                        identity["duration_seconds"] = 1.0
            by_id[story_id] = story
        value["stories"] = [
            by_id[story_id]
            for story_id, *_ in LEGACY_PUBLICATION_STORY_TUPLES_V3
        ]
        value["story_count"] = len(LEGACY_PUBLICATION_STORY_TUPLES_V3)
        value["publication_budget"]["published_asset_count"] = (
            len(LEGACY_PUBLICATION_STORY_TUPLES_V3) * 2
        )
        value["publication_budget"]["published_byte_count"] = sum(
            asset["published"]["byte_count"]
            for story in value["stories"]
            for asset in story["assets"]
        )
        for story in value["stories"]:
            story["title"] = LEGACY_PUBLICATION_STORY_TITLES_V3[story["story_id"]]
            story["interpretation"] = (
                "Dated source-observation chronology; not movement, migration, "
                "causation, or propagation."
                if story["evidence_role"] == "observation_chronology"
                else "Non-interpolated modeled context; not an observed pollen "
                "trajectory or propagation."
            )
            for field in (
                "site_count",
                "expected_visible_site_counts",
                "expected_visible_observation_counts",
                "source_preset_member_taxon_ids",
                "source_preset_catalog_sha256",
            ):
                story.pop(field)
            story.pop("poster_frame_ordinal")
            story.pop("frame_no_pollen_data_counts")
            if story["evidence_role"] == "modeled_context":
                story["first_frame"].pop("no_pollen_data_count")
                story["last_frame"].pop("no_pollen_data_count")

    _rewrite_publication(root, downgrade)


def _rewrite_as_pre_v4(
    root: Path,
    *,
    schema: str,
    inventory: tuple[StorySpec, ...],
) -> None:
    legacy_story_ids = {story_id for story_id, *_ in inventory}
    for story_id, *_ in PUBLICATION_STORY_TUPLES:
        if story_id not in legacy_story_ids:
            for suffix in (".poster.png", ".mp4"):
                (root / "media" / f"{story_id}{suffix}").unlink()

    def downgrade(value: dict[str, Any]) -> None:
        value["schema_version"] = schema
        value.pop("source_label_preset_catalog")
        value["encoding_profile"]["poster"] = {
            "format": "png",
            "source_frame_ordinal": 0,
        }
        value["stories"] = [
            story for story in value["stories"] if story["story_id"] in legacy_story_ids
        ]
        value["story_count"] = len(inventory)
        value["publication_budget"]["published_asset_count"] = len(inventory) * 2
        value["publication_budget"]["published_byte_count"] = sum(
            asset["published"]["byte_count"]
            for story in value["stories"]
            for asset in story["assets"]
        )
        for story in value["stories"]:
            story["title"] = LEGACY_PUBLICATION_STORY_TITLES_V3[story["story_id"]]
            story["interpretation"] = (
                "Dated source-observation chronology; not movement, migration, "
                "causation, or propagation."
                if story["evidence_role"] == "observation_chronology"
                else "Non-interpolated modeled context; not an observed pollen "
                "trajectory or propagation."
            )
            for field in (
                "site_count",
                "expected_visible_site_counts",
                "expected_visible_observation_counts",
                "source_preset_member_taxon_ids",
                "source_preset_catalog_sha256",
            ):
                story.pop(field)
            story.pop("poster_frame_ordinal")
            story.pop("frame_no_pollen_data_counts")
            if story["evidence_role"] == "modeled_context":
                story["first_frame"].pop("no_pollen_data_count")
                story["last_frame"].pop("no_pollen_data_count")

    _rewrite_publication(root, downgrade)


def _rewrite_as_legacy_v4(root: Path) -> None:
    legacy_ids = {story_id for story_id, *_ in LEGACY_PUBLICATION_STORY_TUPLES_V4}

    def downgrade(value: dict[str, Any]) -> None:
        value["schema_version"] = LEGACY_PUBLICATION_SCHEMA_VERSION_V4
        value.pop("source_label_preset_catalog")
        by_id = {story["story_id"]: story for story in value["stories"]}
        donor = by_id["neotoma-source-taxon-416"]
        for story_id, _role, kind, selector_value, family in (
            LEGACY_PUBLICATION_STORY_TUPLES_V4
        ):
            if story_id in by_id:
                continue
            story = deepcopy(donor)
            story["story_id"] = story_id
            story["selector"] = {
                "kind": kind,
                "value": selector_value,
                "family": family,
            }
            story["frame_count"] = 1
            story["poster_frame_ordinal"] = 0
            story["expected_visible_feature_counts"] = [1]
            story["expected_visible_site_counts"] = [1]
            story["expected_visible_observation_counts"] = [1]
            for boundary in (story["first_frame"], story["last_frame"]):
                boundary["ordinal"] = 0
                boundary["time_start_bp"] = 0
                boundary["time_end_bp"] = 1
                boundary["source_taxon"] = selector_value
            for asset in story["assets"]:
                suffix = ".poster.png" if asset["media_type"] == "poster" else ".mp4"
                source_path = root / "media" / f"neotoma-source-taxon-416{suffix}"
                target_path = root / "media" / f"{story_id}{suffix}"
                target_path.write_bytes(source_path.read_bytes())
                for identity in (asset["source"], asset["published"]):
                    identity["path"] = f"media/{story_id}{suffix}"
                    if asset["media_type"] == "mp4":
                        identity["frame_count"] = 1
                        identity["duration_seconds"] = 1.0
            by_id[story_id] = story
        value["stories"] = [
            by_id[story_id]
            for story_id, *_ in LEGACY_PUBLICATION_STORY_TUPLES_V4
        ]
        value["story_count"] = len(value["stories"])
        value["publication_budget"]["published_asset_count"] = len(value["stories"]) * 2
        value["publication_budget"]["published_byte_count"] = sum(
            asset["published"]["byte_count"]
            for story in value["stories"]
            for asset in story["assets"]
        )
        for story in value["stories"]:
            story["title"] = LEGACY_PUBLICATION_STORY_TITLES_V4[story["story_id"]]
            story["interpretation"] = (
                "Dated source-observation chronology; not movement, migration, "
                "causation, or propagation."
                if story["evidence_role"] == "observation_chronology"
                else "Non-interpolated modeled context; not an observed pollen "
                "trajectory or propagation."
            )
            for field in (
                "site_count",
                "expected_visible_site_counts",
                "expected_visible_observation_counts",
                "source_preset_member_taxon_ids",
                "source_preset_catalog_sha256",
            ):
                story.pop(field)

    _rewrite_publication(root, downgrade)
    for story_id, *_ in PUBLICATION_STORY_TUPLES:
        if story_id not in legacy_ids:
            for suffix in (".poster.png", ".mp4"):
                (root / "media" / f"{story_id}{suffix}").unlink()


def _file_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _files(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
    }


def test_publication_is_deterministic_bounded_and_excludes_run_artifacts(
    tmp_path: Path,
) -> None:
    source = _gallery(tmp_path)
    first = tmp_path / "published-first"
    second = tmp_path / "published-second"

    manifest: Any = _publish(source, first)
    _publish(source, second)
    gallery_manifest = json.loads(
        (source / "gallery-manifest.json").read_text(encoding="utf-8")
    )
    assert [story["interpretation"] for story in manifest["stories"]] == [
        story["interpretation"] for story in gallery_manifest["stories"]
    ]

    expected_media = {
        f"media/{story_id}{suffix}"
        for story_id, *_ in STORIES
        for suffix in (".poster.png", ".mp4")
    }
    assert _files(first) == expected_media | {
        "publication-manifest.json",
        "publication-manifest.sha256",
    }
    assert {
        path.relative_to(first).as_posix(): sha256_file(path)
        for path in first.rglob("*")
        if path.is_file()
    } == {
        path.relative_to(second).as_posix(): sha256_file(path)
        for path in second.rglob("*")
        if path.is_file()
    }
    assert manifest["schema_version"] == PUBLICATION_SCHEMA_VERSION
    assert manifest["story_count"] == len(PUBLICATION_STORIES)
    assert manifest["publication_budget"]["published_asset_count"] == (
        PUBLICATION_ASSET_COUNT
    )
    assert manifest["source_authority_sha256"] == "1" * 64
    assert manifest["scientific_posture"] == {
        "temporal_direction": "oldest_to_present",
        "interval_semantics": "[younger_bp, older_bp]",
        "null_not_zero": True,
        "interpolation_allowed": False,
        "observation_is_propagation": False,
        "modeled_context_is_observation": False,
    }
    published_stories: Any = manifest["stories"]
    first_asset = published_stories[0]["assets"][0]
    assert first_asset["media_type"] == "poster"
    assert first_asset["source"] == first_asset["published"]
    assert first_asset["published"]["path"] == (
        "media/neotoma-source-sample-presence.poster.png"
    )
    payload = (first / "publication-manifest.json").read_bytes()
    assert (first / "publication-manifest.sha256").read_text(encoding="utf-8") == (
        f"{hashlib.sha256(payload).hexdigest()}  publication-manifest.json\n"
    )
    text = payload.decode()
    assert ".gif" not in text
    assert "frames/" not in text
    assert ".log" not in text
    assert "execution" not in text
    assert "receipt" not in text
    assert "timestamp" not in text
    assert "run_id" not in text
    assert all(
        path.stat().st_mode & 0o777 == 0o644
        for path in first.rglob("*")
        if path.is_file()
    )

    # Replacing the same governed destination remains deterministic.
    _publish(source, first)
    assert (first / "publication-manifest.json").read_bytes() == payload


def test_public_validator_reconciles_complete_existing_bundle_and_real_ffprobe(
    tmp_path: Path,
) -> None:
    source = _gallery(tmp_path)
    destination = tmp_path / "published"
    expected = _publish(source, destination)

    assert (
        publication.validate_atlas_media_publication(destination, mp4_probe=_probe)
        == expected
    )
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        pytest.skip("ffprobe is unavailable for the real-media portability check")
    with pytest.raises(AtlasMediaError, match="MP4 properties differ"):
        publication.validate_atlas_media_publication(
            destination, ffprobe_binary=Path(ffprobe)
        )


@pytest.mark.parametrize(
    "mutation,error",
    (
        (
            lambda value: value["scientific_posture"].update(
                {"observation_is_propagation": True}
            ),
            "scientific posture differs",
        ),
        (
            lambda value: value["candidate_succession"].update(
                {"reason_code": "classification_available"}
            ),
            "not explicitly refused",
        ),
        (
            lambda value: value["stories"][0].update(
                {"source_authority_sha256": "9" * 64}
            ),
            "source-story evidence differs",
        ),
        (
            lambda value: value["stories"][0]["first_frame"].update(
                {"time_start_bp": 0}
            ),
            "boundary direction differs",
        ),
        (
            lambda value: value["publication_budget"].update(
                {"published_asset_count": PUBLICATION_ASSET_COUNT - 1}
            ),
            "budget contract differs",
        ),
        (
            lambda value: value["stories"][0].update({"poster_frame_ordinal": 1}),
            "poster frame ordinal differs",
        ),
    ),
)
def test_public_validator_refuses_rehashed_semantic_and_contract_forgery(
    tmp_path: Path,
    mutation: Callable[[dict[str, Any]], None],
    error: str,
) -> None:
    source = _gallery(tmp_path)
    destination = tmp_path / "published"
    _publish(source, destination)
    _rewrite_publication(destination, mutation)

    with pytest.raises(AtlasMediaError, match=error):
        publication.validate_atlas_media_publication(destination, mp4_probe=_probe)


@pytest.mark.parametrize(
    "mutation,error",
    (
        (
            lambda story: story.update(
                {"source_preset_member_taxon_ids": [414, 415]}
            ),
            "preset member IDs differ",
        ),
        (
            lambda story: story.update(
                {"source_preset_catalog_sha256": "9" * 64}
            ),
            "preset catalog differs",
        ),
    ),
)
def test_public_validator_refuses_rehashed_preset_authority_forgery(
    tmp_path: Path,
    mutation: Callable[[dict[str, Any]], None],
    error: str,
) -> None:
    source = _gallery(tmp_path)
    destination = tmp_path / "published"
    _publish(source, destination)

    def mutate(value: dict[str, Any]) -> None:
        story = next(
            row
            for row in value["stories"]
            if row["selector"]["kind"] == "source_label_preset"
        )
        mutation(story)

    _rewrite_publication(destination, mutate)
    with pytest.raises(AtlasMediaError, match=error):
        publication.validate_atlas_media_publication(destination, mp4_probe=_probe)


def test_public_validator_refuses_coordinated_preset_catalog_forgery(
    tmp_path: Path,
) -> None:
    source = _gallery(tmp_path)
    destination = tmp_path / "published"
    _publish(source, destination)

    def mutate(value: dict[str, Any]) -> None:
        for story in value["stories"]:
            if story["selector"]["kind"] == "source_label_preset":
                story["source_preset_catalog_sha256"] = "9" * 64

    _rewrite_publication(destination, mutate)
    with pytest.raises(AtlasMediaError, match="preset catalog differs"):
        publication.validate_atlas_media_publication(destination, mp4_probe=_probe)


def test_publication_and_validator_reject_real_media_corruption_and_probe_forgery(
    tmp_path: Path,
) -> None:
    corrupt_mp4 = _gallery(tmp_path / "source-mp4")
    mp4_path = corrupt_mp4 / "media/neotoma-source-sample-presence.mp4"
    mp4_path.write_bytes(b"not an MP4 despite its extension")

    def bind_corrupt_mp4(value: dict[str, Any]) -> None:
        asset = value["stories"][0]["assets"][1]
        asset["byte_count"] = mp4_path.stat().st_size
        asset["sha256"] = sha256_file(mp4_path)

    _rewrite_gallery(corrupt_mp4, bind_corrupt_mp4)
    with pytest.raises(AtlasMediaError, match="MP4"):
        _publish(corrupt_mp4, tmp_path / "source-mp4-output")

    corrupt_png = _gallery(tmp_path / "source-png")
    png_path = corrupt_png / "media/neotoma-source-sample-presence.poster.png"
    png_path.write_bytes(b"not a PNG despite its extension")

    def bind_corrupt_png(value: dict[str, Any]) -> None:
        story = value["stories"][0]
        asset = story["assets"][2]
        capture = story["capture_frames"][0]
        asset["byte_count"] = png_path.stat().st_size
        asset["sha256"] = sha256_file(png_path)
        capture["byte_count"] = png_path.stat().st_size
        capture["png_sha256"] = sha256_file(png_path)
        story["capture_frame_set_sha256"] = hashlib.sha256(
            canonical_json_bytes(story["capture_frames"])
        ).hexdigest()

    _rewrite_gallery(corrupt_png, bind_corrupt_png)
    with pytest.raises(AtlasMediaError, match="PNG"):
        _publish(corrupt_png, tmp_path / "source-png-output")

    source = _gallery(tmp_path / "probe")

    def forged_probe(_: Path) -> publication.ProbedMp4:
        return publication.ProbedMp4(
            width=32,
            height=16,
            frame_count=1,
            duration_seconds=1.0,
            codec_name="h264",
            pixel_format="yuv420p",
        )

    with pytest.raises(AtlasMediaError, match="MP4 properties differ"):
        publication.publish_atlas_media(
            source, tmp_path / "probe-output", mp4_probe=forged_probe
        )


def test_public_validator_rejects_rehashed_corrupt_published_media(
    tmp_path: Path,
) -> None:
    source = _gallery(tmp_path)
    destination = tmp_path / "published"
    _publish(source, destination)
    mp4_path = destination / "media/neotoma-source-code-trsh.mp4"
    mp4_path.write_bytes(b"forged MP4 payload")

    def bind_corrupt_media(value: dict[str, Any]) -> None:
        asset = value["stories"][1]["assets"][1]
        for identity in (asset["source"], asset["published"]):
            identity["byte_count"] = mp4_path.stat().st_size
            identity["sha256"] = sha256_file(mp4_path)
        value["publication_budget"]["published_byte_count"] = sum(
            item["published"]["byte_count"]
            for story in value["stories"]
            for item in story["assets"]
        )

    _rewrite_publication(destination, bind_corrupt_media)
    with pytest.raises(AtlasMediaError, match="MP4"):
        publication.validate_atlas_media_publication(destination, mp4_probe=_probe)


@pytest.mark.parametrize(
    "mutation,error",
    (
        (lambda value: value["stories"].reverse(), "identity or semantics"),
        (
            lambda value: value["stories"][1]["selector"].update({"value": "AQVP"}),
            "identity or semantics",
        ),
        (
            lambda value: value.update({"interpolation_allowed": True}),
            "playback semantics",
        ),
        (
            lambda value: value["candidate_succession"].update({"status": "available"}),
            "not explicitly refused",
        ),
        (
            lambda value: value["atlas_identity"].update(
                {"build_id": "atlas-" + "9" * 64}
            ),
            "build identities differ",
        ),
    ),
)
def test_publication_refuses_stale_selection_identity_and_scientific_semantics(
    tmp_path: Path,
    mutation: Callable[[dict[str, Any]], None],
    error: str,
) -> None:
    source = _gallery(tmp_path)
    _rewrite_gallery(source, mutation)

    with pytest.raises(AtlasMediaError, match=error):
        _publish(source, tmp_path / "published")


def test_publication_refuses_gallery_checksum_and_self_identity_mutations(
    tmp_path: Path,
) -> None:
    source = _gallery(tmp_path)
    checksum = source / "gallery-manifest.sha256"
    checksum.write_text(f"{'0' * 64}  gallery-manifest.json\n", encoding="utf-8")
    with pytest.raises(AtlasMediaError, match="checksum differs"):
        _publish(source, tmp_path / "published")

    source = _gallery(tmp_path / "second")
    _rewrite_gallery(
        source,
        lambda value: value.update({"temporal_direction": "present_to_oldest"}),
        repair_content_hash=False,
    )
    with pytest.raises(AtlasMediaError, match="content identity differs"):
        _publish(source, tmp_path / "published-second")


def test_publication_reconciles_capture_identity_and_selected_poster(
    tmp_path: Path,
) -> None:
    source = _gallery(tmp_path / "capture-set")
    _rewrite_gallery(
        source,
        lambda value: value["stories"][0]["capture_frames"][0].update(
            {"frame_sha256": "9" * 64}
        ),
    )
    with pytest.raises(AtlasMediaError, match="capture frame set identity differs"):
        _publish(source, tmp_path / "capture-set-output")

    source = _gallery(tmp_path / "poster")
    _rewrite_gallery(
        source,
        lambda value: value["stories"][0]["capture_frames"][0].update(
            {"png_sha256": "9" * 64}
        ),
    )
    value = json.loads((source / "gallery-manifest.json").read_text(encoding="utf-8"))
    captures = value["stories"][0]["capture_frames"]
    value["stories"][0]["capture_frame_set_sha256"] = hashlib.sha256(
        canonical_json_bytes(captures)
    ).hexdigest()
    content = {key: item for key, item in value.items() if key != "content_sha256"}
    value["content_sha256"] = hashlib.sha256(canonical_json_bytes(content)).hexdigest()
    payload = canonical_json_bytes(value)
    (source / "gallery-manifest.json").write_bytes(payload)
    (source / "gallery-manifest.sha256").write_text(
        f"{hashlib.sha256(payload).hexdigest()}  gallery-manifest.json\n",
        encoding="utf-8",
    )
    with pytest.raises(
        AtlasMediaError, match="poster differs from the selected capture"
    ):
        _publish(source, tmp_path / "poster-output")


def test_publication_refuses_traversal_symlink_mutation_and_extra_media(
    tmp_path: Path,
) -> None:
    traversal = _gallery(tmp_path / "traversal")
    _rewrite_gallery(
        traversal,
        lambda value: value["stories"][0]["assets"][2].update(
            {"path": "../outside.poster.png"}
        ),
    )
    with pytest.raises(AtlasMediaError, match="asset identity differs"):
        _publish(traversal, tmp_path / "traversal-output")

    linked = _gallery(tmp_path / "linked")
    poster = linked / "media/neotoma-source-sample-presence.poster.png"
    target = linked / "poster-target.png"
    target.write_bytes(poster.read_bytes())
    poster.unlink()
    poster.symlink_to(target)
    with pytest.raises(AtlasMediaError, match="symlink"):
        _publish(linked, tmp_path / "linked-output")

    mutated = _gallery(tmp_path / "mutated")
    (mutated / "media/neotoma-source-code-trsh.mp4").write_bytes(b"changed")
    with pytest.raises(AtlasMediaError, match="source bytes differ"):
        _publish(mutated, tmp_path / "mutated-output")

    extra = _gallery(tmp_path / "extra")
    (extra / "media/unlisted.mp4").write_bytes(b"extra")
    with pytest.raises(AtlasMediaError, match="missing or extra assets"):
        _publish(extra, tmp_path / "extra-output")


def test_publication_refuses_individual_and_aggregate_budget_overruns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _gallery(tmp_path / "individual")
    monkeypatch.setattr(publication, "MAX_MP4_BYTES", 1)
    with pytest.raises(AtlasMediaError, match="mp4 exceeds"):
        _publish(source, tmp_path / "individual-output")

    monkeypatch.setattr(publication, "MAX_MP4_BYTES", 16 * 1024 * 1024)
    source = _gallery(tmp_path / "aggregate")
    monkeypatch.setattr(publication, "MAX_PUBLICATION_BYTES", 1)
    with pytest.raises(AtlasMediaError, match="total budget"):
        _publish(source, tmp_path / "aggregate-output")


def test_publication_detects_source_mutation_during_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _gallery(tmp_path)
    original_copy = shutil.copyfile
    mutated = False

    def mutating_copy(source_path: str | Path, target_path: str | Path) -> str:
        nonlocal mutated
        result = original_copy(source_path, target_path)
        if not mutated:
            Path(source_path).write_bytes(b"changed-during-copy")
            mutated = True
        return str(result)

    monkeypatch.setattr(
        "bijux_pollenomics_dev.ci.atlas_media.publication.shutil.copyfile",
        mutating_copy,
    )
    with pytest.raises(AtlasMediaError, match="source media changed"):
        _publish(source, tmp_path / "published")
    assert not (tmp_path / "published").exists()
    assert not list(tmp_path.glob(".atlas-media-publication-pending-*"))


def test_publication_refuses_uncontrolled_existing_destination(
    tmp_path: Path,
) -> None:
    source = _gallery(tmp_path)
    destination = tmp_path / "published"
    destination.mkdir()
    (destination / "manual-file.txt").write_text("preserve me\n", encoding="utf-8")

    with pytest.raises(AtlasMediaError, match="publication-manifest.json"):
        _publish(source, destination)
    assert (destination / "manual-file.txt").read_text(
        encoding="utf-8"
    ) == "preserve me\n"

    governed_destination = tmp_path / "governed-publication"
    _publish(source, governed_destination)
    unexpected = governed_destination / "manual-file.txt"
    unexpected.write_text("preserve me too\n", encoding="utf-8")
    with pytest.raises(AtlasMediaError, match="missing or extra files"):
        _publish(source, governed_destination)
    assert unexpected.read_text(encoding="utf-8") == "preserve me too\n"


@pytest.mark.parametrize(
    "legacy_contract", SUPPORTED_EXISTING_PUBLICATION_CONTRACTS[:2]
)
def test_publication_replaces_recognized_existing_inventory(
    tmp_path: Path,
    legacy_contract: tuple[str, tuple[StorySpec, ...]],
) -> None:
    legacy_schema, legacy_inventory = legacy_contract
    destination = tmp_path / "published"
    current_source = _gallery(tmp_path / "current")
    _publish(current_source, destination)
    _rewrite_as_pre_v4(
        destination,
        schema=legacy_schema,
        inventory=legacy_inventory,
    )
    legacy_manifest = json.loads(
        (destination / "publication-manifest.json").read_text(encoding="utf-8")
    )
    assert len(legacy_manifest["stories"]) == len(legacy_inventory)

    manifest: Any = _publish(current_source, destination)

    assert manifest["story_count"] == len(STORIES)
    assert {story["story_id"] for story in manifest["stories"]} == {
        story_id for story_id, *_ in STORIES
    }


def test_publication_replaces_exact_legacy_v3_destination_with_current(
    tmp_path: Path,
) -> None:
    source = _gallery(tmp_path / "source")
    destination = tmp_path / "published"
    _publish(source, destination)
    _rewrite_as_legacy_v3(destination)

    legacy = json.loads(
        (destination / "publication-manifest.json").read_text(encoding="utf-8")
    )
    assert legacy["schema_version"] == LEGACY_PUBLICATION_SCHEMA_VERSION_V3
    assert legacy["encoding_profile"]["poster"] == {
        "format": "png",
        "source_frame_ordinal": 0,
    }
    assert all("poster_frame_ordinal" not in story for story in legacy["stories"])
    assert all(
        "frame_no_pollen_data_counts" not in story for story in legacy["stories"]
    )
    with pytest.raises(AtlasMediaError, match="content identity differs"):
        publication.validate_atlas_media_publication(destination, mp4_probe=_probe)

    manifest = _publish(source, destination)

    assert manifest["schema_version"] == PUBLICATION_SCHEMA_VERSION
    assert (
        json.loads(
            (destination / "publication-manifest.json").read_text(encoding="utf-8")
        )
        == manifest
    )


def test_publication_replaces_exact_legacy_v4_destination_with_current(
    tmp_path: Path,
) -> None:
    source = _gallery(tmp_path / "source")
    destination = tmp_path / "published"
    _publish(source, destination)
    _rewrite_as_legacy_v4(destination)

    legacy = json.loads(
        (destination / "publication-manifest.json").read_text(encoding="utf-8")
    )
    assert legacy["schema_version"] == LEGACY_PUBLICATION_SCHEMA_VERSION_V4
    assert all("poster_frame_ordinal" in story for story in legacy["stories"])
    assert all(
        "frame_no_pollen_data_counts" in story
        for story in legacy["stories"]
        if story["evidence_role"] == "modeled_context"
    )

    manifest = _publish(source, destination)

    assert manifest["schema_version"] == PUBLICATION_SCHEMA_VERSION
    assert (
        json.loads(
            (destination / "publication-manifest.json").read_text(encoding="utf-8")
        )
        == manifest
    )


@pytest.mark.parametrize(
    "mutation",
    (
        lambda root: _rewrite_publication(
            root,
            lambda value: value["stories"][1]["selector"].update({"value": "AQVP"}),
        ),
        lambda root: _rewrite_publication(
            root,
            lambda value: value["encoding_profile"].update(
                {
                    "poster": {
                        "format": "png",
                        "source_frame_selection": (
                            "maximum_selected_evidence_earliest_ordinal_on_tie"
                        ),
                    }
                }
            ),
        ),
        lambda root: _rewrite_publication(
            root,
            lambda value: value["stories"][-1]["first_frame"].update(
                {"no_pollen_data_count": 4}
            ),
        ),
        lambda root: _rewrite_publication(
            root,
            lambda value: value["stories"][0].update({"title": "Forged title"}),
        ),
        lambda root: (root / "media/neotoma-source-code-trsh.mp4").write_bytes(
            b"changed legacy media"
        ),
        lambda root: (root / "unexpected.txt").write_text(
            "uncontrolled\n", encoding="utf-8"
        ),
        lambda root: (root / "publication-manifest.sha256").write_text(
            f"{'0' * 64}  publication-manifest.json\n", encoding="utf-8"
        ),
    ),
)
def test_publication_refuses_mutated_legacy_v3_and_preserves_destination(
    tmp_path: Path,
    mutation: Callable[[Path], object],
) -> None:
    source = _gallery(tmp_path / "source")
    destination = tmp_path / "published"
    _publish(source, destination)
    _rewrite_as_legacy_v3(destination)
    mutation(destination)
    before = _file_bytes(destination)

    with pytest.raises(AtlasMediaError):
        _publish(source, destination)

    assert _file_bytes(destination) == before


@pytest.mark.parametrize(
    "mutation",
    (
        lambda value: value["stories"][0].pop("poster_frame_ordinal"),
        lambda value: value["stories"][-1].pop("frame_no_pollen_data_counts"),
    ),
)
def test_v4_validator_requires_poster_selection_and_modeled_quality_counts(
    tmp_path: Path,
    mutation: Callable[[dict[str, Any]], object],
) -> None:
    source = _gallery(tmp_path)
    destination = tmp_path / "published"
    _publish(source, destination)
    _rewrite_as_legacy_v4(destination)
    _rewrite_publication(destination, mutation)
    before = _file_bytes(destination)

    with pytest.raises(AtlasMediaError, match="identity or semantics differ"):
        _publish(source, destination)

    assert _file_bytes(destination) == before


def test_publication_rejects_duplicate_json_fields(tmp_path: Path) -> None:
    source = _gallery(tmp_path)
    path = source / "gallery-manifest.json"
    payload = path.read_text(encoding="utf-8").replace(
        '{"atlas_identity":', '{"schema_version":"duplicate","atlas_identity":', 1
    )
    path.write_text(payload, encoding="utf-8")
    (source / "gallery-manifest.sha256").write_text(
        f"{sha256_file(path)}  gallery-manifest.json\n", encoding="utf-8"
    )

    with pytest.raises(AtlasMediaError, match="duplicate fields"):
        _publish(source, tmp_path / "published")
