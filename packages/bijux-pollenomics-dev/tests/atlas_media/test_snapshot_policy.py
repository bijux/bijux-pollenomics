"""Executable checks for exact browser snapshot admission."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

from bijux_pollenomics_dev.ci import atlas_media
from tests.atlas_media.fixtures import BUILD_ID, COUNTRIES
from tests.atlas_media.receipt_fixtures import (
    capture_layers,
    capture_layout,
    capture_presentation,
)


def test_snapshot_policy_rejects_stale_readiness_and_scientific_posture() -> None:
    policy = Path(atlas_media.__file__).with_name("snapshot_policy.mjs")
    atlas_identity = {
        "build_id": BUILD_ID,
        "scope_slug": "nordic",
        "version": "v66",
    }
    frame = {
        "story_kind": "source_chronology",
        "source_level": "source_sample_presence",
        "time_start_bp": 100,
        "time_end_bp": 200,
        "countries": list(COUNTRIES),
    }
    story = {
        "title": "Source sample presence",
        "node_count": 10,
        "observation_denominator": 20,
    }
    snapshot = {
        "capture_api_version": "atlas-capture.v1",
        "ready": True,
        **atlas_identity,
        "basemap": "none",
        "countries": list(COUNTRIES),
        "visible_point_count": 1,
        "visible_polygon_layer_count": 0,
        "visible_polygon_feature_count": 0,
        "visible_source_chronology_point_count": 1,
        "visible_modeled_context_feature_count": 0,
        "visible_modeled_no_pollen_data_count": None,
        "visible_governed_candidate_count": 0,
        "time_window_bp": {"younger_bp": 100, "older_bp": 200},
        "source_chronology": {
            "level": "source_sample_presence",
            "source_code": None,
            "source_taxon": None,
            "facet_node_count": 10,
            "facet_observation_denominator": 20,
            "visible_node_count": 1,
            "visible_observation_denominator": 2,
        },
        "modeled_context": None,
        "scientific_posture": {
            "classifications_status": "unavailable",
            "classifications_reason_code": (
                "accepted_scientific_classifications_not_available"
            ),
            "observation_chronology_is_propagation": False,
        },
        "capture_layers": capture_layers(),
        "capture_presentation": capture_presentation(
            evidence_role="observation_chronology"
        ),
        "capture_layout": capture_layout(),
    }
    mutations = [
        ["ready", False],
        ["capture_api_version", "atlas-capture.v0"],
        ["scope_slug", "europe-plus"],
        ["version", "v65"],
        ["scientific_posture.classifications_status", "available"],
        ["scientific_posture.classifications_reason_code", "stale_reason"],
        ["scientific_posture.observation_chronology_is_propagation", True],
        ["visible_governed_candidate_count", 1],
        ["visible_polygon_feature_count", -1],
        ["capture_layers.active_keys", ["country-boundaries", "unrelated"]],
        ["capture_presentation.null_handling", "null_as_zero"],
        ["capture_presentation.key_items.1.fill", "rgb(255, 255, 255)"],
        ["capture_presentation.key_items.1.stroke", "rgb(24, 37, 61)"],
        ["capture_layout.overlay_content_bounded", False],
        ["capture_layout.overlay_content_overflow", True],
        ["capture_layout.overlay_overlaps_map", True],
        ["capture_layout.map_bounded", False],
        ["capture_layout.scroll_y_px", 1],
    ]
    script = """
      import { validateSnapshot } from __POLICY__;
      const baseline = __SNAPSHOT__;
      const frame = __FRAME__;
      const story = __STORY__;
      const identity = __IDENTITY__;
      const mutations = __MUTATIONS__;
      const results = [];
      validateSnapshot(structuredClone(baseline), frame, story, identity);
      for (const [path, value] of mutations) {
        const snapshot = structuredClone(baseline);
        const parts = path.split('.');
        let target = snapshot;
        for (const part of parts.slice(0, -1)) target = target[part];
        target[parts.at(-1)] = value;
        try {
          validateSnapshot(snapshot, frame, story, identity);
          results.push(false);
        } catch {
          results.push(true);
        }
      }
      process.stdout.write(JSON.stringify(results));
    """
    for placeholder, value in (
        ("__POLICY__", policy.as_uri()),
        ("__SNAPSHOT__", snapshot),
        ("__FRAME__", frame),
        ("__STORY__", story),
        ("__IDENTITY__", atlas_identity),
        ("__MUTATIONS__", mutations),
    ):
        script = script.replace(placeholder, json.dumps(value))

    completed = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == [True] * len(mutations)


def test_snapshot_policy_binds_modeled_no_pollen_count_to_governed_frame() -> None:
    policy = Path(atlas_media.__file__).with_name("snapshot_policy.mjs")
    identity = {"build_id": BUILD_ID, "scope_slug": "nordic", "version": "v66"}
    frame = {
        "story_kind": "modeled_context",
        "time_start_bp": 0,
        "time_end_bp": 500,
        "source_window_label": "0-500 BP",
        "metric_family_key": "land_cover",
        "metric_key": "OL",
        "feature_count": 75,
        "no_pollen_data_count": 4,
        "countries": list(COUNTRIES),
    }
    story = {"title": "Open land modeled context"}
    snapshot = {
        "capture_api_version": "atlas-capture.v1",
        "ready": True,
        **identity,
        "basemap": "none",
        "countries": list(COUNTRIES),
        "visible_point_count": 0,
        "visible_polygon_layer_count": 2,
        "visible_polygon_feature_count": 75,
        "visible_source_chronology_point_count": 0,
        "visible_modeled_context_feature_count": 75,
        "visible_modeled_no_pollen_data_count": 4,
        "visible_governed_candidate_count": 0,
        "source_chronology": None,
        "modeled_context": {
            "window_label": "0-500 BP",
            "metric_family_key": "land_cover",
            "metric_key": "OL",
            "feature_count": 75,
            "no_pollen_data_count": 4,
            "interpolation_allowed": False,
            "propagation_use_allowed": False,
        },
        "scientific_posture": {
            "classifications_status": "unavailable",
            "classifications_reason_code": "accepted_scientific_classifications_not_available",
            "observation_chronology_is_propagation": False,
        },
        "capture_layers": capture_layers("landclim-reveals-temporal-grid"),
        "capture_presentation": capture_presentation(
            evidence_role="modeled_context",
            title="Open land modeled context",
            younger_bp=0,
            older_bp=500,
        ),
        "capture_layout": capture_layout(),
    }
    script = f"""
      import {{ validateSnapshot }} from {json.dumps(policy.as_uri())};
      const frame = {json.dumps(frame)};
      const story = {json.dumps(story)};
      const identity = {json.dumps(identity)};
      const baseline = {json.dumps(snapshot)};
      validateSnapshot(structuredClone(baseline), frame, story, identity);
      const mutations = [
        (value) => {{ value.visible_modeled_no_pollen_data_count = 5; value.capture_presentation.counts_label = '75/75 published cells visible · 5 explicitly have no pollen data · 0-500 BP'; }},
        (value) => {{ value.modeled_context.no_pollen_data_count = 5; value.visible_modeled_no_pollen_data_count = 5; value.capture_presentation.counts_label = '75/75 published cells visible · 5 explicitly have no pollen data · 0-500 BP'; }},
      ];
      const rejected = mutations.map((mutate) => {{
        const value = structuredClone(baseline); mutate(value);
        try {{ validateSnapshot(value, frame, story, identity); return false; }}
        catch {{ return true; }}
      }});
      process.stdout.write(JSON.stringify(rejected));
    """
    completed = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == [True, True]
