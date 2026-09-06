from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.ci.atlas_media import (
    AtlasMediaError,
    admission,
    capture,
    runner,
)
from bijux_pollenomics_dev.ci.atlas_media.contracts import SelectedStory
from bijux_pollenomics_dev.ci.atlas_media.gallery import (
    canonical_json_bytes,
    media_asset_row,
)
from tests.atlas_media.fixtures import SUCCESSION, plan, source_authority
from tests.atlas_media.receipt_fixtures import (
    capture_evidence_layer_key,
    capture_layers,
    capture_layout,
    capture_presentation,
    network_receipt,
)


def test_materializer_reconciles_capture_encoding_and_gallery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    media_plan = plan(tmp_path)
    candidate_checks: list[object] = []
    monkeypatch.setattr(
        runner,
        "_require_candidate",
        lambda current_plan: candidate_checks.append(current_plan),
    )
    monkeypatch.setattr(runner, "audit_static_atlas", lambda *_args: {"ok": True})
    candidate_input_roots: list[Path] = []

    def snapshot_then_mutate(current_plan: object) -> Path:
        assert current_plan == media_plan
        snapshot = admission._materialize_candidate_inputs(media_plan)
        candidate_input_roots.append(snapshot)
        (media_plan.repository_root / media_plan.storyboard_manifest).write_text(
            '{"mutated_live_storyboard":true}\n', encoding="utf-8"
        )
        return snapshot

    monkeypatch.setattr(runner, "_materialize_candidate_inputs", snapshot_then_mutate)

    def load_authority(root: Path, manifest: Path) -> object:
        assert root == candidate_input_roots[0]
        assert manifest.is_relative_to(root)
        return source_authority()

    monkeypatch.setattr(runner, "load_source_chronology_authority", load_authority)
    tool_identity = {
        name: {"binary_sha256": character * 64, "version": "test"}
        for name, character in zip(
            ("node", "ffmpeg", "ffprobe", "brave"),
            ("1", "2", "3", "4"),
            strict=True,
        )
    }
    monkeypatch.setattr(
        runner,
        "_tool_identity",
        lambda _plan, *, checkpoint: tool_identity,
    )

    def fake_render(
        current_plan: object,
        stories: tuple[SelectedStory, ...],
        *,
        candidate_succession: dict[str, object],
        static_root: Path,
    ) -> Path:
        assert current_plan == media_plan
        assert candidate_succession == SUCCESSION
        assert static_root.name == "candidate-inputs"
        rows = []
        for story in stories:
            receipts = []
            for ordinal, frame in enumerate(story.frames):
                expected_source_counts = story.expected_visible_feature_counts
                if story.evidence_role == "observation_chronology":
                    assert expected_source_counts is not None
                    source_count = expected_source_counts[ordinal]
                else:
                    source_count = 0
                payload = f"{story.story_id}:{ordinal}".encode()
                relative = f"frames/{story.story_id}/{ordinal:06d}.png"
                path = media_plan.artifact_root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
                receipts.append(
                    {
                        "ordinal": ordinal,
                        "file": relative,
                        "capture_api_version": "atlas-capture.v1",
                        "ready": True,
                        "build_id": media_plan.candidate.build_id,
                        "scope_slug": "nordic",
                        "version": "v66",
                        "classifications_status": "unavailable",
                        "classifications_reason_code": (
                            "accepted_scientific_classifications_not_available"
                        ),
                        "observation_chronology_is_propagation": False,
                        "visible_governed_candidate_count": 0,
                        "time_start_bp": frame["time_start_bp"],
                        "time_end_bp": frame["time_end_bp"],
                        "frame_sha256": hashlib.sha256(
                            canonical_json_bytes(frame)
                        ).hexdigest(),
                        "node_count": story.node_count,
                        "observation_denominator": story.observation_denominator,
                        "feature_count": frame.get("feature_count"),
                        "source_level": frame.get("source_level"),
                        "source_code": frame.get("source_code"),
                        "source_taxon": frame.get("source_taxon"),
                        "source_window_label": frame.get("source_window_label"),
                        "metric_family_key": frame.get("metric_family_key"),
                        "metric_key": frame.get("metric_key"),
                        "no_pollen_data_count": frame.get("no_pollen_data_count"),
                        "visible_point_count": (
                            source_count
                            if story.evidence_role == "observation_chronology"
                            else 0
                        ),
                        "visible_polygon_layer_count": (
                            0 if story.evidence_role == "observation_chronology" else 2
                        ),
                        "visible_polygon_feature_count": (
                            0
                            if story.evidence_role == "observation_chronology"
                            else frame["feature_count"]
                        ),
                        "visible_feature_count": (
                            source_count
                            if story.evidence_role == "observation_chronology"
                            else frame["feature_count"]
                        ),
                        "visible_source_chronology_point_count": (source_count),
                        "visible_modeled_context_feature_count": (
                            0
                            if story.evidence_role == "observation_chronology"
                            else frame["feature_count"]
                        ),
                        "visible_modeled_no_pollen_data_count": (
                            4 if story.evidence_role == "modeled_context" else None
                        ),
                        "visible_source_node_count": (
                            source_count
                            if story.evidence_role == "observation_chronology"
                            else None
                        ),
                        "visible_source_observation_denominator": (
                            source_count
                            if story.evidence_role == "observation_chronology"
                            else None
                        ),
                        "capture_layers": capture_layers(
                            capture_evidence_layer_key(story.selector_kind)
                        ),
                        "capture_presentation": capture_presentation(
                            evidence_role=story.evidence_role,
                            source_level=story.selector_kind,
                            title=story.title,
                            younger_bp=cast(int, frame["time_start_bp"]),
                            older_bp=cast(int, frame["time_end_bp"]),
                            visible_source_count=source_count,
                            source_node_denominator=story.node_count or 0,
                            visible_source_observations=source_count,
                            source_observation_denominator=(
                                story.observation_denominator or 0
                            ),
                            modeled_feature_count=cast(
                                int, frame.get("feature_count") or 0
                            ),
                            modeled_no_pollen_data_count=4,
                            source_window_label=str(
                                frame.get("source_window_label") or ""
                            ),
                        ),
                        "capture_layout": capture_layout(),
                        "png_sha256": hashlib.sha256(payload).hexdigest(),
                        "byte_count": len(payload),
                    }
                )
            rows.append(
                {
                    "story_id": story.story_id,
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
                    "frame_no_pollen_data_counts": (
                        list(story.frame_no_pollen_data_counts)
                        if story.frame_no_pollen_data_counts is not None
                        else None
                    ),
                    "expected_visible_feature_counts": (
                        list(story.expected_visible_feature_counts)
                        if story.expected_visible_feature_counts is not None
                        else None
                    ),
                    "source_authority_sha256": story.source_authority_sha256,
                    "frame_count": len(story.frames),
                    "frames": receipts,
                }
            )
        receipt = media_plan.artifact_root / "capture-receipt.json"
        receipt.write_text(
            json.dumps(
                {
                    "schema_version": "atlas-media-capture-receipt.v2",
                    "candidate": media_plan.candidate.as_json(),
                    "capture_api_version": "atlas-capture.v1",
                    "basemap": "none",
                    "temporal_direction": "oldest_to_present",
                    "interpolation_allowed": False,
                    "frame_hash_contract": capture._FRAME_HASH_CONTRACT,
                    **network_receipt(media_plan),
                    "stories": rows,
                }
            ),
            encoding="utf-8",
        )
        (media_plan.artifact_root / "brave-browser.log").write_text(
            "browser log\n", encoding="utf-8"
        )
        stdout = media_plan.artifact_root / "renderer.stdout.log"
        stderr = media_plan.artifact_root / "renderer.stderr.log"
        stdout.write_text("rendered\n", encoding="utf-8")
        stderr.write_text("", encoding="utf-8")
        (media_plan.artifact_root / "renderer.execution.json").write_bytes(
            canonical_json_bytes(
                {
                    "stdout_log": stdout.name,
                    "stdout_byte_count": stdout.stat().st_size,
                    "stdout_sha256": hashlib.sha256(stdout.read_bytes()).hexdigest(),
                    "stderr_log": stderr.name,
                    "stderr_byte_count": stderr.stat().st_size,
                    "stderr_sha256": hashlib.sha256(stderr.read_bytes()).hexdigest(),
                }
            )
        )
        return receipt

    def fake_encode(
        current_plan: object,
        story: SelectedStory,
        _capture_frames: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        assert current_plan == media_plan
        rows = []
        for media_type, suffix in (
            ("poster", ".poster.png"),
            ("mp4", ".mp4"),
            ("gif", ".gif"),
        ):
            path = media_plan.artifact_root / "media" / f"{story.story_id}{suffix}"
            path.parent.mkdir(parents=True, exist_ok=True)
            if media_type == "poster":
                path.write_bytes(
                    (
                        media_plan.artifact_root
                        / "frames"
                        / story.story_id
                        / "000000.png"
                    ).read_bytes()
                )
            else:
                path.write_bytes(f"{story.story_id}:{media_type}".encode())
            asset = media_asset_row(
                media_plan.artifact_root, path, media_type=media_type
            )
            asset.update(
                {
                    "width": media_plan.width,
                    "height": media_plan.height,
                    "frame_count": (1 if media_type == "poster" else len(story.frames)),
                    **({"duration_seconds": 1.0} if media_type != "poster" else {}),
                }
            )
            rows.append(asset)
        return rows

    monkeypatch.setattr(runner, "_render_frames", fake_render)
    monkeypatch.setattr(runner, "_encode_story", fake_encode)

    gallery: Any = runner.materialize_atlas_media(media_plan)

    assert gallery["story_count"] == (
        4
        + len(media_plan.selection.exact_taxa)
        + len(media_plan.selection.modeled_metrics)
    )
    modeled_gallery = gallery["stories"][-1]
    assert modeled_gallery["selector"]["value"] == "OL"
    assert modeled_gallery["frame_feature_denominators"] == [75] * 25
    assert candidate_checks == [media_plan, media_plan]
    assert len(candidate_input_roots) == 1
    assert (media_plan.artifact_root / "gallery-manifest.json").is_file()
    assert (media_plan.artifact_root / "gallery-manifest.sha256").is_file()
    assert (media_plan.artifact_root / "run-evidence-index.json").is_file()
    assert (media_plan.artifact_root / "run-evidence-index.sha256").is_file()


def test_materializer_refuses_tracked_change_after_rendering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    media_plan = plan(tmp_path)
    candidate_checks = 0

    def require_stable_candidate(_plan: object) -> None:
        nonlocal candidate_checks
        candidate_checks += 1
        if candidate_checks == 2:
            raise AtlasMediaError("tracked worktree changes make the candidate mutable")

    def fake_render(
        _plan: object,
        _stories: object,
        *,
        candidate_succession: dict[str, object],
        static_root: Path,
    ) -> Path:
        assert candidate_succession == SUCCESSION
        assert static_root.name == "candidate-inputs"
        receipt = media_plan.artifact_root / "capture-receipt.json"
        receipt.write_text("{}\n", encoding="utf-8")
        return receipt

    monkeypatch.setattr(runner, "_require_candidate", require_stable_candidate)
    monkeypatch.setattr(runner, "audit_static_atlas", lambda *_args: {"ok": True})
    monkeypatch.setattr(
        runner, "load_source_chronology_authority", lambda *_args: source_authority()
    )
    monkeypatch.setattr(runner, "_render_frames", fake_render)

    def fake_validate(
        _receipt: object,
        *,
        plan: object,
        stories: tuple[SelectedStory, ...],
        candidate_succession: dict[str, object],
    ) -> dict[str, list[dict[str, object]]]:
        del plan
        assert candidate_succession == SUCCESSION
        return {story.story_id: [] for story in stories}

    monkeypatch.setattr(runner, "_validate_capture_receipt", fake_validate)
    monkeypatch.setattr(runner, "_encode_story", lambda *_args: [])
    monkeypatch.setattr(
        runner,
        "_tool_identity",
        lambda _plan, *, checkpoint: {
            name: {"binary_sha256": character * 64, "version": "test"}
            for name, character in zip(
                ("node", "ffmpeg", "ffprobe", "brave"),
                ("1", "2", "3", "4"),
                strict=True,
            )
        },
    )

    with pytest.raises(AtlasMediaError, match="tracked worktree"):
        runner.materialize_atlas_media(media_plan)

    assert candidate_checks == 2
    assert not (media_plan.artifact_root / "gallery-manifest.json").exists()
