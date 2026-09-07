"""Tests for content-addressed media gallery publication."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.atlas_media import AtlasMediaError
from bijux_pollenomics_dev.ci.atlas_media.contracts import SelectedStory
from bijux_pollenomics_dev.ci.atlas_media.gallery import (
    build_gallery_manifest,
    canonical_json_bytes,
    media_asset_row,
    sha256_file,
    validate_source_preset_catalog,
    write_gallery_manifest,
)
from bijux_pollenomics_dev.ci.atlas_media.run_evidence import (
    build_run_evidence_index,
    write_run_evidence_index,
)
from tests.atlas_media.fixtures import (
    BUILD_ID,
    COUNTRIES,
    candidate,
    source_preset_catalog,
)
from tests.atlas_media.receipt_fixtures import (
    capture_layers,
    capture_layout,
    capture_presentation,
)


def _tool_identity() -> dict[str, object]:
    return {
        name: {"binary_sha256": character * 64, "version": f"{name} test"}
        for name, character in zip(
            ("node", "ffmpeg", "ffprobe", "brave"),
            ("1", "2", "3", "4"),
            strict=True,
        )
    }


def test_source_preset_catalog_rejects_malformed_identity() -> None:
    catalog = source_preset_catalog()
    catalog["source_snapshot_id"] = "bogus"

    with pytest.raises(AtlasMediaError, match="catalog identity differs"):
        validate_source_preset_catalog(catalog)


def _encoding_profile() -> dict[str, object]:
    return {
        "schema_version": "atlas-media-encoding-profile.v1",
        "width": 640,
        "height": 480,
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


def test_gallery_checksums_every_story_asset_and_its_own_manifest(
    tmp_path: Path,
) -> None:
    root = tmp_path / "artifacts/media"
    media = root / "media"
    media.mkdir(parents=True)
    assets = []
    for media_type, suffix in (
        ("poster", ".poster.png"),
        ("mp4", ".mp4"),
        ("gif", ".gif"),
    ):
        path = media / f"sample{suffix}"
        path.write_bytes(f"{media_type}-payload".encode())
        asset = media_asset_row(root, path, media_type=media_type)
        asset.update(
            {
                "width": 640,
                "height": 480,
                "frame_count": 1,
                **({"duration_seconds": 1.0} if media_type != "poster" else {}),
            }
        )
        assets.append(asset)
    story = SelectedStory(
        story_id="sample-story",
        title="Source sample presence",
        evidence_role="observation_chronology",
        selector_kind="source_sample_presence",
        selector_value="all",
        site_count=10,
        node_count=10,
        observation_denominator=20,
        expected_visible_feature_counts=(1,),
        expected_visible_site_counts=(1,),
        expected_visible_observation_counts=(2,),
        source_authority_sha256="1" * 64,
        frames=(
            {
                "ordinal": 0,
                "story_kind": "source_chronology",
                "source_level": "source_sample_presence",
                "time_start_bp": 100,
                "time_end_bp": 200,
                "countries": list(COUNTRIES),
                "basemap": "none",
            },
        ),
    )
    poster_asset = next(asset for asset in assets if asset["media_type"] == "poster")
    manifest: Any = build_gallery_manifest(
        atlas_identity={
            "build_id": BUILD_ID,
            "scope_slug": "nordic",
            "version": "v66",
            "countries": list(COUNTRIES),
        },
        candidate_identity=candidate().as_json(),
        storyboard_sha256="e" * 64,
        source_preset_catalog=source_preset_catalog(),
        stories=(story,),
        assets_by_story={story.story_id: assets},
        capture_frames_by_story={
            story.story_id: [
                {
                    "ordinal": 0,
                    "file": "frames/sample-story/000000.png",
                    "frame_sha256": "6" * 64,
                        "png_sha256": poster_asset["sha256"],
                        "byte_count": poster_asset["byte_count"],
                        "facet_site_count": 10,
                        "visible_site_count": 1,
                    "visible_point_count": 1,
                    "visible_polygon_layer_count": 0,
                    "visible_polygon_feature_count": 0,
                    "visible_feature_count": 1,
                    "visible_source_chronology_point_count": 1,
                    "visible_modeled_context_feature_count": 0,
                    "visible_modeled_no_pollen_data_count": None,
                    "visible_source_node_count": 1,
                    "visible_source_observation_denominator": 2,
                    "capture_layers": capture_layers(),
                    "capture_presentation": capture_presentation(
                        evidence_role="observation_chronology"
                    ),
                    "capture_layout": capture_layout(),
                }
            ]
        },
        tool_identity=_tool_identity(),
        encoding_profile=_encoding_profile(),
        execution_receipts=[
            {
                "path": "renderer.execution.json",
                "byte_count": 100,
                "sha256": "5" * 64,
            }
        ],
        candidate_succession={
            "product_key": "candidate_succession",
            "status": "refused",
            "reason_code": "accepted_scientific_classifications_not_available",
            "detail": "No candidate-succession story is published.",
            "story_count": 0,
            "edge_count": 0,
        },
    )

    content = {key: value for key, value in manifest.items() if key != "content_sha256"}
    assert (
        manifest["content_sha256"]
        == hashlib.sha256(canonical_json_bytes(content)).hexdigest()
    )
    assert manifest["stories"][0]["interpretation"] == (
        "Dated source-observation chronology; site, node, and cluster counts are not "
        "abundance; not flow, propagation, migration, or causation."
    )
    assert manifest["stories"][0]["selector"] == {
        "kind": "source_sample_presence",
        "value": "all",
        "family": None,
    }
    assert manifest["stories"][0]["node_count"] == 10
    assert manifest["stories"][0]["observation_denominator"] == 20
    assert manifest["encoding_profile"]["frames_per_second"] == 1
    assert manifest["stories"][0]["poster_frame_ordinal"] == 0
    assert manifest["command_execution_receipts"] == ["renderer.execution.json"]
    assert "capture_receipt_sha256" not in manifest
    assert (
        manifest["stories"][0]["capture_frames"][0]["png_sha256"]
        == poster_asset["sha256"]
    )
    assert len(manifest["stories"][0]["capture_frame_set_sha256"]) == 64
    manifest_path, checksum_path = write_gallery_manifest(root, manifest)
    checksum = checksum_path.read_text(encoding="utf-8").split()[0]
    assert checksum == hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def test_gallery_bytes_are_stable_for_identical_content(tmp_path: Path) -> None:
    value = {"schema_version": "fixture.v1", "countries": list(COUNTRIES)}

    assert canonical_json_bytes(value) == canonical_json_bytes(
        dict(reversed(list(value.items())))
    )


def test_media_asset_refuses_symlink(tmp_path: Path) -> None:
    root = tmp_path / "media"
    root.mkdir()
    target = root / "target.png"
    target.write_bytes(b"png")
    link = root / "poster.png"
    link.symlink_to(target)

    with pytest.raises(AtlasMediaError, match="symlink"):
        media_asset_row(root, link, media_type="poster")


def test_run_evidence_binds_gallery_receipts_logs_and_browser_log(
    tmp_path: Path,
) -> None:
    root = tmp_path / "media"
    root.mkdir()
    gallery: dict[str, object] = {
        "schema_version": "fixture.v1",
        "command_execution_receipts": ["renderer.execution.json"],
        "stories": [],
    }
    gallery["content_sha256"] = hashlib.sha256(
        canonical_json_bytes(gallery)
    ).hexdigest()
    gallery_path, _ = write_gallery_manifest(root, gallery)
    capture = root / "capture-receipt.json"
    capture.write_text('{"port":8123}\n', encoding="utf-8")
    (root / "brave-browser.log").write_text("brave\n", encoding="utf-8")
    stdout = root / "renderer.stdout.log"
    stderr = root / "renderer.stderr.log"
    stdout.write_text("rendered\n", encoding="utf-8")
    stderr.write_text("", encoding="utf-8")
    execution_path = root / "renderer.execution.json"
    execution_path.write_bytes(
        canonical_json_bytes(
            {
                "stdout_log": stdout.name,
                "stdout_byte_count": stdout.stat().st_size,
                "stdout_sha256": sha256_file(stdout),
                "stderr_log": stderr.name,
                "stderr_byte_count": stderr.stat().st_size,
                "stderr_sha256": sha256_file(stderr),
            }
        )
    )
    execution = {
        "path": execution_path.name,
        "byte_count": execution_path.stat().st_size,
        "sha256": sha256_file(execution_path),
    }

    index: Any = build_run_evidence_index(
        root,
        gallery_manifest_path=gallery_path,
        capture_receipt_path=capture,
        execution_receipts=[execution],
    )
    paths = {row["path"] for row in index["run_artifacts"]}
    assert paths == {
        "brave-browser.log",
        "capture-receipt.json",
        "renderer.execution.json",
        "renderer.stderr.log",
        "renderer.stdout.log",
    }
    index_path, checksum_path = write_run_evidence_index(root, index)
    assert checksum_path.read_text(encoding="utf-8") == (
        f"{sha256_file(index_path)}  run-evidence-index.json\n"
    )

    stdout.write_text("mutated\n", encoding="utf-8")
    with pytest.raises(AtlasMediaError, match="differs from its receipt"):
        build_run_evidence_index(
            root,
            gallery_manifest_path=gallery_path,
            capture_receipt_path=capture,
            execution_receipts=[execution],
        )


def test_run_evidence_refuses_mutated_gallery_and_symlinked_receipt(
    tmp_path: Path,
) -> None:
    root = tmp_path / "media"
    root.mkdir()
    content: dict[str, object] = {"schema_version": "fixture.v1"}
    manifest = {
        **content,
        "content_sha256": hashlib.sha256(canonical_json_bytes(content)).hexdigest(),
    }
    gallery_path, _ = write_gallery_manifest(root, manifest)
    capture_target = root / "capture-target.json"
    capture_target.write_text("{}\n", encoding="utf-8")
    capture = root / "capture-receipt.json"
    capture.symlink_to(capture_target)
    (root / "brave-browser.log").write_text("", encoding="utf-8")

    with pytest.raises(AtlasMediaError, match="symlink"):
        build_run_evidence_index(
            root,
            gallery_manifest_path=gallery_path,
            capture_receipt_path=capture,
            execution_receipts=[
                {"path": "renderer.execution.json", "byte_count": 1, "sha256": "1" * 64}
            ],
        )

    capture.unlink()
    capture.write_text("{}\n", encoding="utf-8")
    gallery_path.write_text('{"schema_version":"fixture.v2"}\n', encoding="utf-8")
    with pytest.raises(AtlasMediaError, match="gallery content identity"):
        build_run_evidence_index(
            root,
            gallery_manifest_path=gallery_path,
            capture_receipt_path=capture,
            execution_receipts=[
                {"path": "renderer.execution.json", "byte_count": 1, "sha256": "1" * 64}
            ],
        )


def test_run_evidence_refuses_media_mutated_after_gallery_publication(
    tmp_path: Path,
) -> None:
    root = tmp_path / "media-run"
    frame = root / "frames/story/000000.png"
    asset = root / "media/story.poster.png"
    frame.parent.mkdir(parents=True)
    asset.parent.mkdir(parents=True)
    frame.write_bytes(b"frame")
    asset.write_bytes(b"poster")
    content: dict[str, object] = {
        "schema_version": "atlas-media-gallery.v4",
        "command_execution_receipts": ["renderer.execution.json"],
        "stories": [
            {
                "capture_frames": [
                    {
                        "file": "frames/story/000000.png",
                        "byte_count": frame.stat().st_size,
                        "png_sha256": sha256_file(frame),
                    }
                ],
                "assets": [
                    {
                        "path": "media/story.poster.png",
                        "byte_count": asset.stat().st_size,
                        "sha256": sha256_file(asset),
                    }
                ],
            }
        ],
    }
    manifest = {
        **content,
        "content_sha256": hashlib.sha256(canonical_json_bytes(content)).hexdigest(),
    }
    gallery_path, _ = write_gallery_manifest(root, manifest)
    capture = root / "capture-receipt.json"
    capture.write_text("{}\n", encoding="utf-8")
    (root / "brave-browser.log").write_text("", encoding="utf-8")
    stdout = root / "renderer.stdout.log"
    stderr = root / "renderer.stderr.log"
    stdout.write_text("", encoding="utf-8")
    stderr.write_text("", encoding="utf-8")
    execution_path = root / "renderer.execution.json"
    execution_path.write_bytes(
        canonical_json_bytes(
            {
                "stdout_log": stdout.name,
                "stdout_byte_count": 0,
                "stdout_sha256": sha256_file(stdout),
                "stderr_log": stderr.name,
                "stderr_byte_count": 0,
                "stderr_sha256": sha256_file(stderr),
            }
        )
    )
    execution = {
        "path": execution_path.name,
        "byte_count": execution_path.stat().st_size,
        "sha256": sha256_file(execution_path),
    }
    asset.write_bytes(b"mutated poster")

    with pytest.raises(AtlasMediaError, match="output bytes differ"):
        build_run_evidence_index(
            root,
            gallery_manifest_path=gallery_path,
            capture_receipt_path=capture,
            execution_receipts=[execution],
        )
