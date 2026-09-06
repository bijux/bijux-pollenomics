"""Capture receipt, visibility, and exact network reconciliation tests."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any
from urllib.parse import urlsplit

import pytest

from bijux_pollenomics_dev.ci.atlas_media import AtlasMediaError, admission, capture
from bijux_pollenomics_dev.ci.atlas_media.contracts import SelectedStory
from bijux_pollenomics_dev.ci.atlas_media.gallery import canonical_json_bytes

from tests.atlas_media.fixtures import COUNTRIES, plan
from tests.atlas_media.receipt_fixtures import make_story, network_receipt


def test_capture_receipt_must_reconcile_every_frame(tmp_path: Path) -> None:
    media_plan = plan(tmp_path)
    story = make_story()
    receipt: Any = {
        "schema_version": "atlas-media-capture-receipt.v2",
        "candidate": media_plan.candidate.as_json(),
        "capture_api_version": "atlas-capture.v1",
        "basemap": "none",
        "temporal_direction": "oldest_to_present",
        "interpolation_allowed": False,
        "frame_hash_contract": capture._FRAME_HASH_CONTRACT,
        **network_receipt(media_plan),
        "stories": [{"story_id": story.story_id, "frame_count": 0}],
    }

    with pytest.raises(AtlasMediaError, match="frames differ"):
        capture._validate_capture_receipt(receipt, plan=media_plan, stories=(story,))


def test_candidate_check_targets_governed_inputs_instead_of_unrelated_work(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    media_plan = plan(tmp_path)
    governed_paths = [
        media_plan.atlas_document,
        media_plan.atlas_manifest,
        media_plan.storyboard_manifest,
    ]
    calls: list[tuple[str, ...]] = []

    def fake_git(_root: Path, *arguments: str) -> str:
        calls.append(arguments)
        if arguments == ("rev-parse", "HEAD"):
            return media_plan.candidate.repository_head
        if arguments == ("rev-parse", "HEAD^{tree}"):
            return media_plan.candidate.repository_tree
        if arguments[:3] == ("log", "-1", "--format=%H"):
            return media_plan.candidate.atlas_output_commit
        if arguments[:3] == ("ls-files", "--error-unmatch", "--"):
            return "\n".join(arguments[3:])
        if arguments[:3] == ("ls-files", "-s", "--"):
            return "\n".join(f"100644 {'1' * 40} 0\t{path}" for path in arguments[3:])
        if arguments[:2] == ("hash-object", "--"):
            return "\n".join("1" * 40 for _path in arguments[2:])
        raise AssertionError(f"unexpected git arguments: {arguments}")

    monkeypatch.setattr(admission, "_git", fake_git)
    monkeypatch.setattr(
        admission, "_governed_input_paths", lambda _plan: governed_paths
    )

    admission._require_candidate(media_plan)

    assert not any(arguments[0] == "status" for arguments in calls)
    assert ("ls-files", "--error-unmatch", "--", *governed_paths) in calls


def test_candidate_refuses_untracked_governed_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    media_plan = plan(tmp_path)
    governed_paths = [
        media_plan.atlas_document,
        media_plan.atlas_manifest,
        media_plan.storyboard_manifest,
    ]

    def fake_git(_root: Path, *arguments: str) -> str:
        if arguments == ("rev-parse", "HEAD"):
            return media_plan.candidate.repository_head
        if arguments == ("rev-parse", "HEAD^{tree}"):
            return media_plan.candidate.repository_tree
        if arguments[:3] == ("log", "-1", "--format=%H"):
            return media_plan.candidate.atlas_output_commit
        if arguments[:3] == ("ls-files", "--error-unmatch", "--"):
            return "\n".join(arguments[3:-1])
        raise AssertionError(f"unexpected git arguments: {arguments}")

    monkeypatch.setattr(admission, "_git", fake_git)
    monkeypatch.setattr(
        admission, "_governed_input_paths", lambda _plan: governed_paths
    )

    with pytest.raises(AtlasMediaError, match="not fully tracked"):
        admission._require_candidate(media_plan)


def test_capture_receipt_refuses_zero_navigation_requests(tmp_path: Path) -> None:
    media_plan = plan(tmp_path)
    receipt = network_receipt(media_plan)
    receipt["network_request_count"] = 0
    receipt["network_requests"] = []

    with pytest.raises(AtlasMediaError, match="document navigation"):
        capture._validate_network_receipt(receipt, plan=media_plan)


def test_capture_receipt_refuses_stale_static_asset_authority(tmp_path: Path) -> None:
    media_plan = plan(tmp_path)
    receipt = network_receipt(media_plan)
    governed_assets = deepcopy(receipt["governed_static_assets"])
    assert isinstance(governed_assets, list)
    governed_assets[0]["sha256"] = "0" * 64
    receipt["governed_static_assets"] = governed_assets

    with pytest.raises(AtlasMediaError, match="network authority differs"):
        capture._validate_network_receipt(receipt, plan=media_plan)


def test_capture_receipt_binds_frame_selector_build_and_png(tmp_path: Path) -> None:
    media_plan = plan(tmp_path)
    story = make_story()
    frame = story.frames[0]
    frame_path = media_plan.artifact_root / "frames/source-sample/000000.png"
    frame_path.parent.mkdir(parents=True)
    frame_path.write_bytes(b"captured-png")
    receipt: Any = {
        "schema_version": "atlas-media-capture-receipt.v2",
        "candidate": media_plan.candidate.as_json(),
        "capture_api_version": "atlas-capture.v1",
        "basemap": "none",
        "temporal_direction": "oldest_to_present",
        "interpolation_allowed": False,
        "frame_hash_contract": capture._FRAME_HASH_CONTRACT,
        **network_receipt(media_plan),
        "stories": [
            {
                "story_id": story.story_id,
                "selector": {
                    "kind": story.selector_kind,
                    "value": story.selector_value,
                    "family": story.selector_family,
                },
                "node_count": story.node_count,
                "observation_denominator": story.observation_denominator,
                "frame_feature_denominators": None,
                "expected_visible_feature_counts": [1],
                "source_authority_sha256": "1" * 64,
                "frame_count": 1,
                "frames": [
                    {
                        "ordinal": 0,
                        "file": "frames/source-sample/000000.png",
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
                        "time_start_bp": 100,
                        "time_end_bp": 200,
                        "frame_sha256": hashlib.sha256(
                            canonical_json_bytes(frame)
                        ).hexdigest(),
                        "node_count": story.node_count,
                        "observation_denominator": story.observation_denominator,
                        "feature_count": None,
                        "source_level": "source_sample_presence",
                        "source_code": None,
                        "source_taxon": None,
                        "source_window_label": None,
                        "metric_family_key": None,
                        "metric_key": None,
                        "visible_point_count": 1,
                        "visible_polygon_layer_count": 0,
                        "visible_feature_count": 1,
                        "visible_source_chronology_point_count": 1,
                        "visible_modeled_context_feature_count": 0,
                        "png_sha256": hashlib.sha256(b"captured-png").hexdigest(),
                        "byte_count": len(b"captured-png"),
                    }
                ],
            }
        ],
    }

    capture._validate_capture_receipt(receipt, plan=media_plan, stories=(story,))

    for field, stale_value in (
        ("capture_api_version", "atlas-capture.v0"),
        ("ready", False),
        ("scope_slug", "europe-plus"),
        ("version", "v65"),
        ("classifications_status", "available"),
        ("classifications_reason_code", "stale_reason"),
        ("observation_chronology_is_propagation", True),
        ("visible_governed_candidate_count", 1),
    ):
        stale_snapshot = deepcopy(receipt)
        stale_snapshot["stories"][0]["frames"][0][field] = stale_value
        with pytest.raises(AtlasMediaError, match="frame identity"):
            capture._validate_capture_receipt(
                stale_snapshot,
                plan=media_plan,
                stories=(story,),
            )

    wrong_denominator = deepcopy(receipt)
    wrong_denominator["stories"][0]["frames"][0]["node_count"] = 11
    with pytest.raises(AtlasMediaError, match="frame identity"):
        capture._validate_capture_receipt(
            wrong_denominator,
            plan=media_plan,
            stories=(story,),
        )

    wrong_selector = deepcopy(receipt)
    wrong_selector["stories"][0]["selector"]["value"] = "TRSH"
    with pytest.raises(AtlasMediaError, match="story frames"):
        capture._validate_capture_receipt(
            wrong_selector,
            plan=media_plan,
            stories=(story,),
        )

    wrong_frame_selector = deepcopy(receipt)
    wrong_frame_selector["stories"][0]["frames"][0]["source_level"] = (
        "source_ecological_code"
    )
    with pytest.raises(AtlasMediaError, match="frame identity"):
        capture._validate_capture_receipt(
            wrong_frame_selector,
            plan=media_plan,
            stories=(story,),
        )

    empty_frame = deepcopy(receipt)
    empty_frame["stories"][0]["frames"][0]["visible_point_count"] = 0
    empty_frame["stories"][0]["frames"][0]["visible_feature_count"] = 0
    empty_frame["stories"][0]["frames"][0]["visible_source_chronology_point_count"] = 0
    with pytest.raises(AtlasMediaError, match="frame identity"):
        capture._validate_capture_receipt(
            empty_frame,
            plan=media_plan,
            stories=(story,),
        )

    external_request = deepcopy(receipt)
    external_request["network_request_count"] = 1
    external_request["network_requests"] = [
        {
            "url": "https://example.invalid/data.json",
            "method": "GET",
            "resource_type": "Fetch",
        }
    ]
    with pytest.raises(AtlasMediaError, match="non-local request"):
        capture._validate_capture_receipt(
            external_request,
            plan=media_plan,
            stories=(story,),
        )


def test_selected_layer_visibility_uses_role_specific_denominators() -> None:
    source = make_story()
    source_empty_frame: dict[str, object] = {
        "visible_point_count": 1,
        "visible_polygon_layer_count": 0,
        "visible_feature_count": 1,
        "visible_source_chronology_point_count": 0,
        "visible_modeled_context_feature_count": 0,
    }
    assert not capture._valid_visible_counts(
        source_empty_frame,
        story=source,
        frame=source.frames[0],
    )
    source_over_denominator = dict(source_empty_frame)
    source_over_denominator["visible_point_count"] = 11
    source_over_denominator["visible_feature_count"] = 11
    source_over_denominator["visible_source_chronology_point_count"] = 11
    assert not capture._valid_visible_counts(
        source_over_denominator,
        story=source,
        frame=source.frames[0],
    )
    modeled_frame: dict[str, object] = {
        "ordinal": 0,
        "story_kind": "modeled_context",
        "source_window_label": "0-500 BP",
        "metric_family_key": "land_cover",
        "metric_key": "OL",
        "time_start_bp": 0,
        "time_end_bp": 500,
        "feature_count": 75,
        "countries": list(COUNTRIES),
        "basemap": "none",
    }
    modeled = SelectedStory(
        story_id="open-land",
        title="Open land modeled context",
        evidence_role="modeled_context",
        selector_kind="modeled_metric",
        selector_value="OL",
        selector_family="land_cover",
        frame_feature_denominators=(75,),
        frames=(modeled_frame,),
    )
    modeled_receipt: dict[str, object] = {
        "visible_point_count": 0,
        "visible_polygon_layer_count": 75,
        "visible_feature_count": 75,
        "visible_source_chronology_point_count": 0,
        "visible_modeled_context_feature_count": 75,
    }
    assert capture._valid_visible_counts(
        modeled_receipt,
        story=modeled,
        frame=modeled_frame,
    )
    modeled_receipt["visible_modeled_context_feature_count"] = 74
    assert not capture._valid_visible_counts(
        modeled_receipt,
        story=modeled,
        frame=modeled_frame,
    )


@pytest.mark.parametrize(
    ("url", "allowed"),
    (
        ("http://127.0.0.1:8123/atlas.json", True),
        ("http://127.0.0.1:8124/atlas.json", False),
        ("http://127.0.0.2:8123/atlas.json", False),
        ("http://127.0.0.1:8123/unrelated.json", False),
        ("http://127.0.0.1:8123/atlas.json?cache=1", False),
        ("data:image/png;base64,AA==", True),
        ("blob:http://127.0.0.1:8123/identifier", True),
        ("blob:http://127.0.0.1:8124/identifier", False),
        ("https://tile.openstreetmap.org/1/2/3.png", False),
        ("https://127.0.0.1.example.invalid/", False),
        ("file:///private/source", False),
    ),
)
def test_capture_network_policy_is_fail_closed(url: str, allowed: bool) -> None:
    parsed = urlsplit(url)
    receipt: dict[str, object] = {
        "url": url,
        "scheme": parsed.scheme or None,
        "host": parsed.hostname,
        "port": parsed.port,
        "path": parsed.path,
        "query": f"?{parsed.query}" if parsed.query else "",
        "method": "GET",
        "resource_type": "Fetch",
    }
    assert (
        capture._network_request_allowed(
            receipt,
            origin="http://127.0.0.1:8123",
            allowed_paths={"/atlas.json"},
        )
        is allowed
    )


def test_node_network_receipts_round_trip_through_python_validation(
    tmp_path: Path,
) -> None:
    media_plan = plan(tmp_path)
    policy = Path(capture.__file__).with_name("network_policy.mjs")
    document = f"/{media_plan.atlas_document}"
    script = """
      import { classifyNetworkRequest } from %s;
      const authority = {
        origin: 'http://127.0.0.1:8123',
        allowedPaths: new Set([%s]),
      };
      const requests = [
        [%s, 'Document'],
        ['data:image/png;base64,AA==', 'Image'],
        ['blob:http://127.0.0.1:8123/identifier', 'Image'],
      ];
      process.stdout.write(JSON.stringify(requests.map(([url, type], index) =>
        classifyNetworkRequest(
          { requestId: String(index), type, request: { url, method: 'GET' } },
          authority,
        ).receipt
      )));
    """ % (
        json.dumps(policy.as_uri()),
        json.dumps(document),
        json.dumps(f"http://127.0.0.1:8123{document}"),
    )
    completed = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    receipt = network_receipt(media_plan)
    rows = json.loads(completed.stdout)
    receipt["network_requests"] = rows
    receipt["network_request_count"] = len(rows)

    capture._validate_network_receipt(receipt, plan=media_plan)

    assert rows[1]["host"] is None
    assert rows[2]["host"] is None
