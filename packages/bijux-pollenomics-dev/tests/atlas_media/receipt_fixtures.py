"""Build exact capture and network receipts for atlas-media tests."""

from __future__ import annotations

import hashlib
import json

from bijux_pollenomics_dev.ci.atlas_media import admission
from bijux_pollenomics_dev.ci.atlas_media.contracts import AtlasMediaPlan, SelectedStory
from tests.atlas_media.fixtures import COUNTRIES, SUCCESSION


def make_story() -> SelectedStory:
    """Return one valid source-observation story."""
    return SelectedStory(
        story_id="source-sample",
        title="Source sample presence",
        evidence_role="observation_chronology",
        selector_kind="source_sample_presence",
        selector_value="all",
        node_count=10,
        observation_denominator=20,
        expected_visible_feature_counts=(1,),
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


def build_capture_frames(
    media_plan: AtlasMediaPlan, story: SelectedStory
) -> list[dict[str, object]]:
    """Describe the PNG frames already written for one story."""
    root = media_plan.artifact_root
    rows = []
    for ordinal in range(len(story.frames)):
        path = root / "frames" / story.story_id / f"{ordinal:06d}.png"
        payload = path.read_bytes()
        rows.append(
            {
                "ordinal": ordinal,
                "file": f"frames/{story.story_id}/{ordinal:06d}.png",
                "png_sha256": hashlib.sha256(payload).hexdigest(),
                "byte_count": len(payload),
            }
        )
    return rows


def network_receipt(media_plan: AtlasMediaPlan) -> dict[str, object]:
    """Return the governed loopback-only network receipt for a fixture plan."""
    document = f"/{media_plan.atlas_document}"
    port = 8123
    atlas_manifest = json.loads(
        (media_plan.repository_root / media_plan.atlas_manifest).read_text(
            encoding="utf-8"
        )
    )
    allowed_paths = sorted(
        f"/{path}"
        for path in admission._governed_input_paths(media_plan)
        if path != media_plan.storyboard_manifest
    )
    governed_static_assets = admission._governed_static_assets(media_plan)
    return {
        "atlas_identity": {
            field: atlas_manifest[field]
            for field in ("build_id", "scope_slug", "version")
        },
        "candidate_succession": dict(SUCCESSION),
        "network_policy": "deny-before-send-governed-origin-data-blob-only.v2",
        "governed_static_assets": governed_static_assets,
        "network_authority": {
            "scheme": "http",
            "host": "127.0.0.1",
            "port": port,
            "origin": f"http://127.0.0.1:{port}",
            "allowed_static_paths": allowed_paths,
        },
        "network_request_count": 1,
        "network_requests": [
            {
                "url": f"http://127.0.0.1:{port}{document}",
                "scheme": "http",
                "host": "127.0.0.1",
                "port": port,
                "path": document,
                "query": "",
                "method": "GET",
                "resource_type": "Document",
            }
        ],
        "navigation_evidence": {
            "request_count": 1,
            "method": "GET",
            "resource_type": "Document",
            "scheme": "http",
            "host": "127.0.0.1",
            "port": port,
            "path": document,
            "query": "",
        },
    }
