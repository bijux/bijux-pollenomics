"""Render-plan candidate and static-input authority tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.atlas_media import admission, capture
from bijux_pollenomics_dev.ci.atlas_media.contracts import SelectedStory
from bijux_pollenomics_dev.ci.atlas_media.gallery import canonical_json_bytes
from tests.atlas_media.fixtures import BUILD_ID, SUCCESSION, plan
from tests.atlas_media.receipt_fixtures import make_story


def test_render_plan_passes_python_canonical_hash_for_integral_floats(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    media_plan = plan(tmp_path)
    media_plan.artifact_root.mkdir(parents=True)
    frame = dict(make_story().frames[0])
    frame["time_start_bp"] = 100.0
    frame["time_end_bp"] = 200.0
    story = SelectedStory(
        story_id="source-sample",
        title="Source sample presence",
        evidence_role="observation_chronology",
        selector_kind="source_sample_presence",
        selector_value="all",
        node_count=10,
        observation_denominator=20,
        expected_visible_feature_counts=(1,),
        source_authority_sha256="1" * 64,
        frames=(frame,),
    )
    observed: Any = {}

    def fake_run(
        _command: tuple[str, ...],
        *,
        cwd: Path,
        stdout_path: Path,
        stderr_path: Path,
        timeout_seconds: float,
    ) -> None:
        assert timeout_seconds > 0
        del cwd
        observed.update(
            json.loads(
                (media_plan.artifact_root / "render-plan.json").read_text(
                    encoding="utf-8"
                )
            )
        )
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        (media_plan.artifact_root / "capture-receipt.json").write_text(
            "{}\n", encoding="utf-8"
        )

    monkeypatch.setattr(capture, "_run_logged", fake_run)
    monkeypatch.setattr(capture, "_require_governed_inputs_at_head", lambda _plan: None)
    static_root = admission._materialize_candidate_inputs(media_plan)

    capture._render_frames(
        media_plan,
        (story,),
        candidate_succession=dict(SUCCESSION),
        static_root=static_root,
    )

    planned_frame = observed["stories"][0]["frames"][0]
    assert planned_frame["capture"] == frame
    assert (
        planned_frame["canonical_sha256"]
        == hashlib.sha256(canonical_json_bytes(frame)).hexdigest()
    )
    assert observed["frame_hash_contract"] == capture._FRAME_HASH_CONTRACT
    assert observed["atlas_identity"] == {
        "build_id": BUILD_ID,
        "scope_slug": "nordic",
        "version": "v66",
    }
    assert observed["governed_static_assets"] == admission._governed_static_assets(
        media_plan
    )


def test_render_plan_static_identity_comes_from_head_after_worktree_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    media_plan = plan(tmp_path)
    media_plan.artifact_root.mkdir(parents=True)
    static_root = admission._materialize_candidate_inputs(media_plan)
    document = media_plan.repository_root / media_plan.atlas_document
    candidate_payload = document.read_bytes()
    observed: dict[str, Any] = {}

    def mutate_after_admission(_plan: object) -> None:
        document.write_bytes(b"mutated after candidate admission")

    def inspect_plan(
        _command: tuple[str, ...],
        *,
        cwd: Path,
        stdout_path: Path,
        stderr_path: Path,
        timeout_seconds: float,
    ) -> None:
        del cwd, timeout_seconds
        observed.update(
            json.loads(
                (media_plan.artifact_root / "render-plan.json").read_text(
                    encoding="utf-8"
                )
            )
        )
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        (media_plan.artifact_root / "capture-receipt.json").write_text(
            "{}\n", encoding="utf-8"
        )

    monkeypatch.setattr(
        capture, "_require_governed_inputs_at_head", mutate_after_admission
    )
    monkeypatch.setattr(capture, "_run_logged", inspect_plan)

    capture._render_frames(
        media_plan,
        (make_story(),),
        candidate_succession=dict(SUCCESSION),
        static_root=static_root,
    )

    document_identity = next(
        row
        for row in observed["governed_static_assets"]
        if row["path"] == f"/{media_plan.atlas_document}"
    )
    assert document_identity == {
        "path": f"/{media_plan.atlas_document}",
        "byte_count": len(candidate_payload),
        "sha256": hashlib.sha256(candidate_payload).hexdigest(),
    }
    assert (
        hashlib.sha256(document.read_bytes()).hexdigest() != document_identity["sha256"]
    )
