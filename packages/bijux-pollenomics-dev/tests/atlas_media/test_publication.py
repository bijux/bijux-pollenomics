"""Tests for deterministic atlas-media website publication."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.atlas_media import AtlasMediaError
from bijux_pollenomics_dev.ci.atlas_media.contracts import SelectedStory
from bijux_pollenomics_dev.ci.atlas_media.gallery import (
    build_gallery_manifest,
    canonical_json_bytes,
    media_asset_row,
    sha256_file,
    write_gallery_manifest,
)
from bijux_pollenomics_dev.ci.atlas_media import publication
from tests.atlas_media.fixtures import BUILD_ID, COUNTRIES, SUCCESSION, candidate

StorySpec = tuple[str, str, str, str, str | None]
STORIES: tuple[StorySpec, ...] = (
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


def _encoding_profile() -> dict[str, object]:
    return {
        "schema_version": "atlas-media-encoding-profile.v1",
        "width": 640,
        "height": 480,
        "frames_per_second": 1,
        "poster": {"format": "png", "source_frame_ordinal": 0},
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
        frame["source_level"] = kind
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
        frames=(frame,),
    )


def _gallery(tmp_path: Path) -> Path:
    root = tmp_path / "artifacts" / "media"
    media = root / "media"
    media.mkdir(parents=True)
    selected = tuple(_story(spec) for spec in STORIES)
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
            path.write_bytes(f"{story.story_id}-{media_type}".encode())
            row = media_asset_row(root, path, media_type=media_type)
            row.update(
                {
                    "width": 640,
                    "height": 480,
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
                "visible_source_chronology_point_count": (
                    1 if story.evidence_role == "observation_chronology" else 0
                ),
                "visible_modeled_context_feature_count": (
                    75 if story.evidence_role == "modeled_context" else 0
                ),
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

    manifest = publication.publish_atlas_media(source, first)
    publication.publish_atlas_media(source, second)

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
    assert manifest["schema_version"] == "atlas-media-publication.v1"
    assert manifest["story_count"] == 6
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
    publication.publish_atlas_media(source, first)
    assert (first / "publication-manifest.json").read_bytes() == payload


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
        publication.publish_atlas_media(source, tmp_path / "published")


def test_publication_refuses_gallery_checksum_and_self_identity_mutations(
    tmp_path: Path,
) -> None:
    source = _gallery(tmp_path)
    checksum = source / "gallery-manifest.sha256"
    checksum.write_text(f"{'0' * 64}  gallery-manifest.json\n", encoding="utf-8")
    with pytest.raises(AtlasMediaError, match="checksum differs"):
        publication.publish_atlas_media(source, tmp_path / "published")

    source = _gallery(tmp_path / "second")
    _rewrite_gallery(
        source,
        lambda value: value.update({"temporal_direction": "present_to_oldest"}),
        repair_content_hash=False,
    )
    with pytest.raises(AtlasMediaError, match="content identity differs"):
        publication.publish_atlas_media(source, tmp_path / "published-second")


def test_publication_reconciles_capture_identity_and_oldest_poster(
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
        publication.publish_atlas_media(source, tmp_path / "capture-set-output")

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
    with pytest.raises(AtlasMediaError, match="poster differs from the oldest capture"):
        publication.publish_atlas_media(source, tmp_path / "poster-output")


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
        publication.publish_atlas_media(traversal, tmp_path / "traversal-output")

    linked = _gallery(tmp_path / "linked")
    poster = linked / "media/neotoma-source-sample-presence.poster.png"
    target = linked / "poster-target.png"
    target.write_bytes(poster.read_bytes())
    poster.unlink()
    poster.symlink_to(target)
    with pytest.raises(AtlasMediaError, match="symlink"):
        publication.publish_atlas_media(linked, tmp_path / "linked-output")

    mutated = _gallery(tmp_path / "mutated")
    (mutated / "media/neotoma-source-code-trsh.mp4").write_bytes(b"changed")
    with pytest.raises(AtlasMediaError, match="source bytes differ"):
        publication.publish_atlas_media(mutated, tmp_path / "mutated-output")

    extra = _gallery(tmp_path / "extra")
    (extra / "media/unlisted.mp4").write_bytes(b"extra")
    with pytest.raises(AtlasMediaError, match="missing or extra assets"):
        publication.publish_atlas_media(extra, tmp_path / "extra-output")


def test_publication_refuses_individual_and_aggregate_budget_overruns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _gallery(tmp_path / "individual")
    monkeypatch.setattr(publication, "MAX_MP4_BYTES", 1)
    with pytest.raises(AtlasMediaError, match="mp4 exceeds"):
        publication.publish_atlas_media(source, tmp_path / "individual-output")

    monkeypatch.setattr(publication, "MAX_MP4_BYTES", 16 * 1024 * 1024)
    source = _gallery(tmp_path / "aggregate")
    monkeypatch.setattr(publication, "MAX_PUBLICATION_BYTES", 1)
    with pytest.raises(AtlasMediaError, match="total budget"):
        publication.publish_atlas_media(source, tmp_path / "aggregate-output")


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
        publication.publish_atlas_media(source, tmp_path / "published")
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
        publication.publish_atlas_media(source, destination)
    assert (destination / "manual-file.txt").read_text(
        encoding="utf-8"
    ) == "preserve me\n"

    governed_destination = tmp_path / "governed-publication"
    publication.publish_atlas_media(source, governed_destination)
    unexpected = governed_destination / "manual-file.txt"
    unexpected.write_text("preserve me too\n", encoding="utf-8")
    with pytest.raises(AtlasMediaError, match="missing or extra files"):
        publication.publish_atlas_media(source, governed_destination)
    assert unexpected.read_text(encoding="utf-8") == "preserve me too\n"


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
        publication.publish_atlas_media(source, tmp_path / "published")
