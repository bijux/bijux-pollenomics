"""Build exact capture and network receipts for atlas-media tests."""

from __future__ import annotations

import hashlib
import json

from bijux_pollenomics_dev.ci.atlas_media import admission
from bijux_pollenomics_dev.ci.atlas_media.contracts import AtlasMediaPlan, SelectedStory
from tests.atlas_media.fixtures import COUNTRIES, SUCCESSION


def capture_layers(
    evidence_layer_key: str = "neotoma-source-sample-pollen-context",
) -> dict[str, object]:
    """Return one exact capture-layer inventory with a geographic orientation layer."""
    orientation_keys = ["country-boundaries"]
    return {
        "active_keys": sorted([*orientation_keys, evidence_layer_key]),
        "evidence_layer_key": evidence_layer_key,
        "orientation_keys": orientation_keys,
    }


def capture_evidence_layer_key(selector_kind: str) -> str:
    """Resolve the fixture layer key from the governed story selector kind."""
    return {
        "source_sample_presence": "neotoma-source-sample-pollen-context",
        "source_ecological_code": "neotoma-source-ecological-code",
        "source_taxon": "neotoma-source-exact-taxon",
        "modeled_metric": "landclim-reveals-temporal-grid",
    }[selector_kind]


def capture_presentation(
    *,
    evidence_role: str,
    source_level: str = "source_sample_presence",
    title: str = "Source sample presence",
    younger_bp: int = 100,
    older_bp: int = 200,
    visible_source_count: int = 1,
    source_node_denominator: int = 10,
    visible_source_observations: int = 2,
    source_observation_denominator: int = 20,
    modeled_feature_count: int = 75,
    modeled_no_pollen_data_count: int = 4,
    source_window_label: str = "0-500 BP",
) -> dict[str, object]:
    """Return exact, semantics-bearing presentation evidence for one frame."""
    source = evidence_role == "observation_chronology"
    key_labels = (
        ["source record", "records grouped at current zoom", "country boundary"]
        if source
        else [
            "0–20%",
            ">20–40%",
            ">40–60%",
            ">60–80%",
            ">80–100%",
            "no pollen data · N/A, not 0",
            "country boundary",
        ]
    )
    cues = (
        ["point", "cluster-count", "line"]
        if source
        else ["area", "area", "area", "area", "area", "area", "line"]
    )
    source_colors = {
        "source_sample_presence": ("rgb(180, 83, 9)", "rgb(120, 53, 15)"),
        "source_ecological_code": ("rgb(15, 118, 110)", "rgb(19, 78, 74)"),
        "source_taxon": ("rgb(124, 58, 237)", "rgb(76, 29, 149)"),
    }
    styles = (
        [
            source_colors[source_level],
            ("rgba(255, 255, 255, 0.9)", "rgba(24, 37, 61, 0.35)"),
            ("rgba(0, 0, 0, 0)", "rgb(100, 116, 139)"),
        ]
        if source
        else [
            ("rgb(27, 67, 50)", "rgb(51, 65, 85)"),
            ("rgb(82, 121, 111)", "rgb(51, 65, 85)"),
            ("rgb(167, 201, 87)", "rgb(51, 65, 85)"),
            ("rgb(242, 204, 143)", "rgb(51, 65, 85)"),
            ("rgb(217, 119, 6)", "rgb(51, 65, 85)"),
            ("rgb(203, 213, 225)", "rgb(51, 65, 85)"),
            ("rgba(0, 0, 0, 0)", "rgb(100, 116, 139)"),
        ]
    )
    return {
        "schema_version": "atlas-capture-presentation.v1",
        "null_handling": "null_not_zero",
        "interpolation_allowed": False,
        "propagation_use_allowed": False,
        "evidence_role": evidence_role,
        "role_label": (
            "Observed source chronology"
            if source
            else "Modeled context · published source window"
        ),
        "title": title,
        "time_label": f"[{younger_bp}, {older_bp}] BP · oldest → present",
        "counts_label": (
            f"{visible_source_count}/{source_node_denominator} governed source nodes in this interval · "
            f"{visible_source_observations}/{source_observation_denominator} contributing observations"
            if source
            else f"{modeled_feature_count}/{modeled_feature_count} published cells visible · "
            f"{modeled_no_pollen_data_count} explicitly have no pollen data · {source_window_label}"
        ),
        "key_labels": key_labels,
        "key_items": [
            {
                "label": label,
                "cue": cue,
                "fill": fill,
                "stroke": stroke,
            }
            for label, cue, (fill, stroke) in zip(key_labels, cues, styles, strict=True)
        ],
        "caveat": (
            "Observed source records only · display clusters are not abundance · no interpolation, flow, or propagation inference."
            if source
            else "Published modeled cells are context only · no atlas interpolation, flow, or propagation inference."
        ),
    }


def capture_layout() -> dict[str, object]:
    """Return a clear, bounded 1440x900 capture-layout receipt."""
    return {
        "overlay_visible": True,
        "overlay_bounded": True,
        "overlay_overlaps_map": False,
        "map_width_px": 1110,
        "map_height_px": 900,
        "viewport_width_px": 1440,
        "viewport_height_px": 900,
    }


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
                "visible_source_chronology_point_count": (
                    story.expected_visible_feature_counts[ordinal]
                    if story.evidence_role == "observation_chronology"
                    and story.expected_visible_feature_counts is not None
                    else 0
                ),
                "visible_modeled_context_feature_count": (
                    story.frames[ordinal]["feature_count"]
                    if story.evidence_role == "modeled_context"
                    else 0
                ),
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
