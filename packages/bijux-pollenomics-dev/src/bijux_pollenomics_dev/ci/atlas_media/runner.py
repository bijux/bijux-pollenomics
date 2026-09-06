"""Coordinate immutable atlas media materialization."""

from __future__ import annotations

import json
from typing import cast

from bijux_pollenomics_dev.ci.atlas_browser.contracts import AtlasScope
from bijux_pollenomics_dev.ci.atlas_browser.static_integrity import audit_static_atlas

from .admission import _materialize_candidate_inputs, _require_candidate
from .capture import (
    _render_frames,
    _validate_capture_receipt,
)
from .contracts import AtlasMediaError, AtlasMediaPlan
from .encoding import (
    _encode_story,
    _encoding_profile,
    _execution_receipts,
    _tool_identity,
)
from .gallery import (
    build_gallery_manifest,
    sha256_file,
    write_gallery_manifest,
)
from .run_evidence import build_run_evidence_index, write_run_evidence_index
from .source_authority import load_source_chronology_authority
from .storyboards import load_storyboard_manifest, select_stories


def materialize_atlas_media(plan: AtlasMediaPlan) -> dict[str, object]:
    """Render, encode, reconcile, and checksum one immutable atlas candidate."""
    root = plan.artifact_root.resolve()
    if root.exists() and any(root.iterdir()):
        raise AtlasMediaError("artifact_root must be absent or empty")
    root.mkdir(parents=True, exist_ok=True)
    _require_candidate(plan)
    candidate_inputs = _materialize_candidate_inputs(plan)
    tool_identity_before = _tool_identity(plan, checkpoint="before")
    storyboard_path = candidate_inputs / plan.storyboard_manifest
    atlas_manifest_path = candidate_inputs / plan.atlas_manifest
    source_paths = (
        candidate_inputs / plan.atlas_document,
        atlas_manifest_path,
        storyboard_path,
    )
    input_digests = {str(path): sha256_file(path) for path in source_paths}
    storyboard = load_storyboard_manifest(storyboard_path, atlas_manifest_path)
    identity = cast(dict[str, object], storyboard["atlas_identity"])
    if identity["build_id"] != plan.candidate.build_id:
        raise AtlasMediaError("storyboard build does not match the candidate")
    scope = AtlasScope(
        name=cast(str, identity["scope_slug"]),
        document=plan.atlas_document,
        manifest=plan.atlas_manifest,
    )
    static_before = audit_static_atlas(plan.repository_root, scope, plan.candidate)
    source_authority = load_source_chronology_authority(
        candidate_inputs, atlas_manifest_path
    )
    if source_authority.build_id != plan.candidate.build_id:
        raise AtlasMediaError("source authority build differs from the candidate")
    stories = select_stories(
        storyboard,
        plan.selection,
        source_authority=source_authority,
    )
    succession = dict(cast(dict[str, object], storyboard["candidate_succession"]))
    receipt_path = _render_frames(
        plan,
        stories,
        candidate_succession=succession,
        static_root=candidate_inputs,
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    capture_frames = _validate_capture_receipt(
        receipt, plan=plan, stories=stories, candidate_succession=succession
    )
    assets = {
        story.story_id: _encode_story(plan, story, capture_frames[story.story_id])
        for story in stories
    }
    capture_frames = _validate_capture_receipt(
        receipt, plan=plan, stories=stories, candidate_succession=succession
    )
    _require_candidate(plan)
    static_after = audit_static_atlas(plan.repository_root, scope, plan.candidate)
    if static_before != static_after or input_digests != {
        str(path): sha256_file(path) for path in source_paths
    }:
        raise AtlasMediaError(
            "atlas or storyboard inputs changed during materialization"
        )
    tool_identity_after = _tool_identity(plan, checkpoint="after")
    if tool_identity_before != tool_identity_after:
        raise AtlasMediaError("media tool identity changed during materialization")
    capture_frames = _validate_capture_receipt(
        receipt, plan=plan, stories=stories, candidate_succession=succession
    )
    execution_receipts = _execution_receipts(root)
    gallery = build_gallery_manifest(
        atlas_identity=dict(identity),
        candidate_identity=plan.candidate.as_json(),
        storyboard_sha256=sha256_file(storyboard_path),
        stories=stories,
        assets_by_story=assets,
        capture_frames_by_story=capture_frames,
        tool_identity=tool_identity_after,
        encoding_profile=_encoding_profile(plan),
        execution_receipts=execution_receipts,
        candidate_succession=succession,
    )
    gallery_path, _ = write_gallery_manifest(root, gallery)
    run_evidence = build_run_evidence_index(
        root,
        gallery_manifest_path=gallery_path,
        capture_receipt_path=receipt_path,
        execution_receipts=execution_receipts,
    )
    write_run_evidence_index(root, run_evidence)
    return gallery
