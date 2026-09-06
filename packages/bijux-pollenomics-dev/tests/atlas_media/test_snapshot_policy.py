"""Executable checks for exact browser snapshot admission."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

from bijux_pollenomics_dev.ci import atlas_media
from tests.atlas_media.fixtures import BUILD_ID, COUNTRIES


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
    story = {"node_count": 10, "observation_denominator": 20}
    snapshot = {
        "capture_api_version": "atlas-capture.v1",
        "ready": True,
        **atlas_identity,
        "basemap": "none",
        "countries": list(COUNTRIES),
        "visible_point_count": 1,
        "visible_polygon_layer_count": 0,
        "visible_source_chronology_point_count": 1,
        "visible_modeled_context_feature_count": 0,
        "visible_governed_candidate_count": 0,
        "time_window_bp": {"younger_bp": 100, "older_bp": 200},
        "source_chronology": {
            "level": "source_sample_presence",
            "source_code": None,
            "source_taxon": None,
            "facet_node_count": 10,
            "facet_observation_denominator": 20,
        },
        "modeled_context": None,
        "scientific_posture": {
            "classifications_status": "unavailable",
            "classifications_reason_code": (
                "accepted_scientific_classifications_not_available"
            ),
            "observation_chronology_is_propagation": False,
        },
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
