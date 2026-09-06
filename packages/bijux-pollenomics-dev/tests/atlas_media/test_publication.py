"""Tests for deterministic atlas-media website publication."""

from __future__ import annotations

import base64
from collections.abc import Callable
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, cast
import zlib

import pytest

from bijux_pollenomics_dev.ci.atlas_media import AtlasMediaError, publication
from bijux_pollenomics_dev.ci.atlas_media.catalog import (
    PUBLICATION_ASSET_COUNT,
    PUBLICATION_SCHEMA_VERSION,
    PUBLICATION_STORIES,
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
from tests.atlas_media.fixtures import BUILD_ID, COUNTRIES, SUCCESSION, candidate
from tests.atlas_media.receipt_fixtures import (
    capture_evidence_layer_key,
    capture_layers,
    capture_layout,
    capture_presentation,
)

StorySpec = tuple[str, str, str, str, str | None]
STORIES: tuple[StorySpec, ...] = PUBLICATION_STORY_TUPLES

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


def _probe(_: Path) -> publication.ProbedMp4:
    return publication.ProbedMp4(
        width=16,
        height=16,
        frame_count=1,
        duration_seconds=1.0,
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
    frame: dict[str, object] = {
        "ordinal": 0,
        "story_kind": (
            "source_chronology"
            if role == "observation_chronology"
            else "modeled_context"
        ),
        "time_start_bp": 100,
        "time_end_bp": 200,
        "countries": list(COUNTRIES),
        "basemap": "none",
    }
    if role == "observation_chronology":
        frame.update(
            {
                "source_level": kind,
                "source_window_label": None,
                "feature_count": None,
            }
        )
        if kind == "source_ecological_code":
            frame["source_code"] = value
        if kind == "source_taxon":
            frame["source_taxon"] = value
        return SelectedStory(
            story_id=story_id,
            title=story_id,
            evidence_role=role,
            selector_kind=kind,
            selector_value=value,
            node_count=3,
            observation_denominator=4,
            expected_visible_feature_counts=(1,),
            source_authority_sha256="1" * 64,
            frames=(frame,),
        )
    frame.update(
        {
            "metric_family_key": family,
            "metric_key": value,
            "source_window_label": "100-200 BP",
            "feature_count": 75,
            "no_pollen_data_count": 4,
        }
    )
    return SelectedStory(
        story_id=story_id,
        title=story_id,
        evidence_role=role,
        selector_kind=kind,
        selector_value=value,
        selector_family=family,
        frame_feature_denominators=(75,),
        frame_no_pollen_data_counts=(4,),
        frames=(frame,),
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
                    "frame_count": 1,
                    **(
                        {"duration_seconds": 1.0}
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
                "ordinal": 0,
                "file": f"frames/{story.story_id}/000000.png",
                "frame_sha256": "2" * 64,
                "png_sha256": poster["sha256"],
                "byte_count": poster["byte_count"],
                "no_pollen_data_count": story.frames[0].get("no_pollen_data_count"),
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
                    source_level=story.selector_kind,
                    title=story.title,
                    younger_bp=cast(int, story.frames[0]["time_start_bp"]),
                    older_bp=cast(int, story.frames[0]["time_end_bp"]),
                    visible_source_count=1,
                    source_node_denominator=story.node_count or 0,
                    visible_source_observations=1,
                    source_observation_denominator=story.observation_denominator or 0,
                    modeled_feature_count=cast(
                        int, story.frames[0].get("feature_count") or 0
                    ),
                    modeled_no_pollen_data_count=4,
                    source_window_label=str(
                        story.frames[0].get("source_window_label") or ""
                    ),
                ),
                "capture_layout": capture_layout(),
            }
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
    root: Path, mutation: Callable[[dict[str, Any]], None]
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
    assert (
        publication.validate_atlas_media_publication(
            destination, ffprobe_binary=Path(ffprobe)
        )
        == expected
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
    "legacy_contract", SUPPORTED_EXISTING_PUBLICATION_CONTRACTS[:-1]
)
def test_publication_replaces_recognized_existing_inventory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    legacy_contract: tuple[str, tuple[StorySpec, ...]],
) -> None:
    legacy_schema, legacy_inventory = legacy_contract
    destination = tmp_path / "published"
    legacy_source = _gallery(tmp_path / "legacy", stories=legacy_inventory)

    monkeypatch.setattr(publication, "_EXPECTED_STORIES", legacy_inventory)
    monkeypatch.setattr(publication, "PUBLICATION_SCHEMA_VERSION", legacy_schema)
    _publish(legacy_source, destination)
    legacy_manifest = json.loads(
        (destination / "publication-manifest.json").read_text(encoding="utf-8")
    )
    assert len(legacy_manifest["stories"]) == len(legacy_inventory)

    monkeypatch.setattr(publication, "_EXPECTED_STORIES", STORIES)
    monkeypatch.setattr(
        publication, "PUBLICATION_SCHEMA_VERSION", PUBLICATION_SCHEMA_VERSION
    )
    current_source = _gallery(tmp_path / "current")
    manifest: Any = _publish(current_source, destination)

    assert manifest["story_count"] == len(STORIES)
    assert {story["story_id"] for story in manifest["stories"]} == {
        story_id for story_id, *_ in STORIES
    }


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
