"""Governed browser capture planning and receipt reconciliation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast
from urllib.parse import SplitResult, urlsplit

from .admission import (
    _atlas_manifest_identity,
    _governed_input_paths,
    _governed_static_assets,
    _require_governed_inputs_at_head,
)
from .capture_evidence import capture_frame_evidence_valid, expected_capture_layer_key
from .contracts import AtlasMediaError, AtlasMediaPlan, SelectedStory
from .gallery import canonical_json_bytes, sha256_file
from .process_execution import _run_logged, _write_json

_FRAME_HASH_CONTRACT = "python-json-sort-keys-utf8-newline.v1"


def _frame_sha256(frame: dict[str, object]) -> str:
    return hashlib.sha256(canonical_json_bytes(frame)).hexdigest()


def _render_frames(
    plan: AtlasMediaPlan,
    stories: tuple[SelectedStory, ...],
    *,
    candidate_succession: dict[str, object],
    static_root: Path,
) -> Path:
    _require_governed_inputs_at_head(plan)
    try:
        atlas_manifest = json.loads(
            (plan.repository_root / plan.atlas_manifest).read_text(encoding="utf-8")
        )
        atlas_identity = {
            field: atlas_manifest[field]
            for field in ("build_id", "scope_slug", "version")
        }
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError) as error:
        raise AtlasMediaError("cannot bind render plan to atlas identity") from error
    if any(
        not isinstance(value, str) or not value for value in atlas_identity.values()
    ):
        raise AtlasMediaError("render plan atlas identity is invalid")
    governed_static_assets = _governed_static_assets(plan)
    allowed_static_paths = [
        cast(str, asset["path"]) for asset in governed_static_assets
    ]
    render_plan = {
        "schema_version": "atlas-media-render-plan.v2",
        "repository_root": str(plan.repository_root.resolve()),
        "static_root": str(static_root.resolve()),
        "artifact_root": str(plan.artifact_root.resolve()),
        "browser_binary": str(plan.browser_binary.resolve()),
        "atlas_document": plan.atlas_document,
        "timeout_seconds": plan.timeout_seconds,
        "viewport": {"width": plan.width, "height": plan.height},
        "candidate": plan.candidate.as_json(),
        "atlas_identity": atlas_identity,
        "frame_hash_contract": _FRAME_HASH_CONTRACT,
        "candidate_succession": candidate_succession,
        "allowed_static_paths": allowed_static_paths,
        "governed_static_assets": governed_static_assets,
        "stories": [
            {
                "story_id": story.story_id,
                "title": story.title,
                "evidence_role": story.evidence_role,
                "selector": {
                    "kind": story.selector_kind,
                    "value": story.selector_value,
                    "family": story.selector_family,
                },
                "node_count": story.node_count,
                "observation_denominator": story.observation_denominator,
                "frame_feature_denominators": story.frame_feature_denominators,
                "frame_no_pollen_data_counts": story.frame_no_pollen_data_counts,
                "expected_visible_feature_counts": story.expected_visible_feature_counts,
                "source_authority_sha256": story.source_authority_sha256,
                "frames": [
                    {
                        "capture": frame,
                        "canonical_sha256": _frame_sha256(frame),
                    }
                    for frame in story.frames
                ],
            }
            for story in stories
        ],
    }
    render_plan_path = plan.artifact_root / "render-plan.json"
    _write_json(render_plan_path, render_plan)
    script = Path(__file__).with_name("render.mjs")
    _run_logged(
        (str(plan.node_binary.resolve()), str(script), str(render_plan_path)),
        cwd=plan.repository_root,
        stdout_path=plan.artifact_root / "renderer.stdout.log",
        stderr_path=plan.artifact_root / "renderer.stderr.log",
        timeout_seconds=min(
            3600,
            max(
                120,
                (plan.timeout_seconds * 2)
                + (5 * sum(len(story.frames) for story in stories)),
            ),
        ),
    )
    receipt = plan.artifact_root / "capture-receipt.json"
    if not receipt.is_file():
        raise AtlasMediaError("browser renderer produced no capture receipt")
    return receipt


def _validate_capture_receipt(
    value: object,
    *,
    plan: AtlasMediaPlan,
    stories: tuple[SelectedStory, ...],
    candidate_succession: dict[str, object] | None = None,
) -> dict[str, list[dict[str, object]]]:
    if not isinstance(value, dict):
        raise AtlasMediaError("capture receipt must be an object")
    receipt = cast(dict[str, object], value)
    if candidate_succession is None:
        receipt_succession = receipt.get("candidate_succession")
        if not isinstance(receipt_succession, dict):
            raise AtlasMediaError("capture receipt candidate succession is absent")
        candidate_succession = cast(dict[str, object], receipt_succession)
    if (
        candidate_succession.get("product_key") != "candidate_succession"
        or candidate_succession.get("status") != "refused"
        or candidate_succession.get("reason_code")
        != "accepted_scientific_classifications_not_available"
        or candidate_succession.get("story_count") != 0
        or candidate_succession.get("edge_count") != 0
    ):
        raise AtlasMediaError("capture receipt candidate succession posture differs")
    expected_atlas_identity = _atlas_manifest_identity(plan)
    if (
        receipt.get("schema_version") != "atlas-media-capture-receipt.v2"
        or receipt.get("candidate") != plan.candidate.as_json()
        or receipt.get("atlas_identity") != expected_atlas_identity
        or expected_atlas_identity["build_id"] != plan.candidate.build_id
        or receipt.get("capture_api_version") != "atlas-capture.v1"
        or receipt.get("basemap") != "none"
        or receipt.get("temporal_direction") != "oldest_to_present"
        or receipt.get("interpolation_allowed") is not False
        or receipt.get("frame_hash_contract") != _FRAME_HASH_CONTRACT
        or receipt.get("candidate_succession") != candidate_succession
    ):
        raise AtlasMediaError("capture receipt candidate identity differs")
    _validate_network_receipt(receipt, plan=plan)
    rows = receipt.get("stories")
    if not isinstance(rows, list) or len(rows) != len(stories):
        raise AtlasMediaError("capture receipt story inventory differs")
    expected = {story.story_id: len(story.frames) for story in stories}
    observed: dict[object, object] = {}
    capture_frames: dict[str, list[dict[str, object]]] = {}
    for row_value in rows:
        if not isinstance(row_value, dict):
            raise AtlasMediaError("capture receipt story row is invalid")
        row = cast(dict[str, object], row_value)
        story_id = row.get("story_id")
        observed[story_id] = row.get("frame_count")
        story = next(
            (candidate for candidate in stories if candidate.story_id == story_id),
            None,
        )
        frames = row.get("frames")
        if (
            story is None
            or not isinstance(frames, list)
            or len(frames) != len(story.frames)
            or row.get("selector")
            != {
                "kind": story.selector_kind,
                "value": story.selector_value,
                "family": story.selector_family,
            }
            or row.get("node_count") != story.node_count
            or row.get("observation_denominator") != story.observation_denominator
            or row.get("frame_feature_denominators")
            != (
                list(story.frame_feature_denominators)
                if story.frame_feature_denominators is not None
                else None
            )
            or row.get("frame_no_pollen_data_counts")
            != (
                list(story.frame_no_pollen_data_counts)
                if story.frame_no_pollen_data_counts is not None
                else None
            )
            or row.get("expected_visible_feature_counts")
            != (
                list(story.expected_visible_feature_counts)
                if story.expected_visible_feature_counts is not None
                else None
            )
            or row.get("source_authority_sha256") != story.source_authority_sha256
        ):
            raise AtlasMediaError("capture receipt story frames differ")
        capture_frames[cast(str, story_id)] = [
            cast(dict[str, object], frame) for frame in frames
        ]
        for ordinal, (frame_receipt, frame) in enumerate(
            zip(frames, story.frames, strict=True)
        ):
            if not isinstance(frame_receipt, dict):
                raise AtlasMediaError("capture receipt frame row is invalid")
            expected_file = f"frames/{story.story_id}/{ordinal:06d}.png"
            captured_path = plan.artifact_root / expected_file
            if (
                frame_receipt.get("ordinal") != ordinal
                or frame_receipt.get("file") != expected_file
                or frame_receipt.get("capture_api_version") != "atlas-capture.v1"
                or frame_receipt.get("ready") is not True
                or frame_receipt.get("build_id") != plan.candidate.build_id
                or frame_receipt.get("scope_slug")
                != expected_atlas_identity["scope_slug"]
                or frame_receipt.get("version") != expected_atlas_identity["version"]
                or frame_receipt.get("classifications_status") != "unavailable"
                or frame_receipt.get("classifications_reason_code")
                != "accepted_scientific_classifications_not_available"
                or frame_receipt.get("observation_chronology_is_propagation")
                is not False
                or frame_receipt.get("visible_governed_candidate_count") != 0
                or frame_receipt.get("time_start_bp") != frame["time_start_bp"]
                or frame_receipt.get("time_end_bp") != frame["time_end_bp"]
                or frame_receipt.get("frame_sha256") != _frame_sha256(frame)
                or frame_receipt.get("node_count") != story.node_count
                or frame_receipt.get("observation_denominator")
                != story.observation_denominator
                or frame_receipt.get("feature_count") != frame.get("feature_count")
                or frame_receipt.get("no_pollen_data_count")
                != frame.get("no_pollen_data_count")
                or frame_receipt.get("source_level") != frame.get("source_level")
                or frame_receipt.get("source_code") != frame.get("source_code")
                or frame_receipt.get("source_taxon") != frame.get("source_taxon")
                or frame_receipt.get("source_window_label")
                != frame.get("source_window_label")
                or frame_receipt.get("metric_family_key")
                != frame.get("metric_family_key")
                or frame_receipt.get("metric_key") != frame.get("metric_key")
                or not _valid_visible_counts(
                    frame_receipt,
                    story=story,
                    frame=frame,
                )
                or not captured_path.is_file()
                or frame_receipt.get("png_sha256") != sha256_file(captured_path)
                or frame_receipt.get("byte_count") != captured_path.stat().st_size
            ):
                raise AtlasMediaError("capture receipt frame identity differs")
    if observed != expected:
        raise AtlasMediaError("capture receipt frame inventory differs")
    return capture_frames


def _valid_visible_counts(
    frame_receipt: dict[str, object],
    *,
    story: SelectedStory,
    frame: dict[str, object],
) -> bool:
    ordinal = frame.get("ordinal")
    expected_source_count = (
        story.expected_visible_feature_counts[ordinal]
        if story.expected_visible_feature_counts is not None
        and isinstance(ordinal, int)
        else None
    )
    return capture_frame_evidence_valid(
        frame_receipt,
        evidence_role=story.evidence_role,
        source_level=frame.get("source_level"),
        expected_evidence_layer_key=expected_capture_layer_key(
            story_kind=frame.get("story_kind"), source_level=frame.get("source_level")
        ),
        expected_title=story.title,
        expected_source_count=expected_source_count,
        source_node_denominator=story.node_count,
        source_observation_denominator=story.observation_denominator,
        expected_modeled_count=frame.get("feature_count"),
        expected_modeled_no_pollen_data_count=frame.get("no_pollen_data_count"),
        source_window_label=frame.get("source_window_label"),
        time_start_bp=frame.get("time_start_bp"),
        time_end_bp=frame.get("time_end_bp"),
    )


def _validate_network_receipt(
    receipt: dict[str, object], *, plan: AtlasMediaPlan
) -> None:
    rows = receipt.get("network_requests")
    if (
        receipt.get("network_policy")
        != "deny-before-send-governed-origin-data-blob-only.v2"
        or not isinstance(rows, list)
        or receipt.get("network_request_count") != len(rows)
    ):
        raise AtlasMediaError("capture receipt network inventory differs")
    authority = receipt.get("network_authority")
    allowed_paths = sorted(
        f"/{path}"
        for path in _governed_input_paths(plan)
        if path != plan.storyboard_manifest
    )
    governed_static_assets = _governed_static_assets(plan)
    if not isinstance(authority, dict):
        raise AtlasMediaError("capture receipt network authority is absent")
    port = authority.get("port")
    if (
        authority.get("scheme") != "http"
        or authority.get("host") != "127.0.0.1"
        or isinstance(port, bool)
        or not isinstance(port, int)
        or not 1 <= port <= 65535
        or authority.get("origin") != f"http://127.0.0.1:{port}"
        or authority.get("allowed_static_paths") != allowed_paths
        or receipt.get("governed_static_assets") != governed_static_assets
    ):
        raise AtlasMediaError("capture receipt network authority differs")
    document_requests: list[dict[str, object]] = []
    for value in rows:
        if not isinstance(value, dict):
            raise AtlasMediaError("capture receipt network row is invalid")
        url = value.get("url")
        if (
            not isinstance(url, str)
            or not isinstance(value.get("method"), str)
            or not value["method"]
            or not isinstance(value.get("resource_type"), str)
            or not value["resource_type"]
            or not _network_request_allowed(
                value,
                origin=cast(str, authority["origin"]),
                allowed_paths=set(allowed_paths),
            )
        ):
            raise AtlasMediaError("capture receipt contains a non-local request")
        if value.get("resource_type") == "Document":
            document_requests.append(value)
    expected_navigation = {
        "request_count": 1,
        "method": "GET",
        "resource_type": "Document",
        "scheme": "http",
        "host": "127.0.0.1",
        "port": port,
        "path": f"/{plan.atlas_document}",
        "query": "",
    }
    if receipt.get("navigation_evidence") != expected_navigation:
        raise AtlasMediaError("capture receipt navigation evidence differs")
    if len(document_requests) != 1:
        raise AtlasMediaError(
            "capture receipt requires exactly one document navigation"
        )
    try:
        parsed = urlsplit(cast(str, document_requests[0]["url"]))
    except ValueError as error:
        raise AtlasMediaError(
            "capture receipt document navigation is invalid"
        ) from error
    if (
        document_requests[0].get("method") != "GET"
        or parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or parsed.port != port
        or parsed.path != f"/{plan.atlas_document}"
        or parsed.query
    ):
        raise AtlasMediaError("capture receipt document navigation differs")


def _network_request_allowed(
    value: dict[str, object], *, origin: str, allowed_paths: set[str]
) -> bool:
    url = value.get("url")
    if not isinstance(url, str) or value.get("method") != "GET":
        return False
    try:
        parsed = urlsplit(url)
    except ValueError:
        return False
    expected_fields = {
        "scheme": parsed.scheme or None,
        "host": parsed.hostname,
        "port": parsed.port,
        "path": parsed.path,
        "query": f"?{parsed.query}" if parsed.query else "",
    }
    if any(value.get(field) != expected for field, expected in expected_fields.items()):
        return False
    if parsed.scheme == "data":
        return True
    if parsed.scheme == "blob":
        try:
            return _origin(urlsplit(parsed.path)) == origin
        except ValueError:
            return False
    return (
        _origin(parsed) == origin
        and parsed.path in allowed_paths
        and not parsed.query
        and parsed.username is None
        and parsed.password is None
    )


def _origin(parsed: SplitResult) -> str:
    scheme = parsed.scheme
    hostname = parsed.hostname
    port = parsed.port
    if not scheme or hostname is None:
        return ""
    return f"{scheme}://{hostname}{f':{port}' if port is not None else ''}"
