"""The product release policy must bind projection payloads to their producer."""

from __future__ import annotations

import hashlib
import json

from bijux_pollenomics.analysis.propagation.outputs import (
    PROPAGATION_PRODUCER_SOURCE_PATHS,
)
from bijux_pollenomics.analysis.propagation.outputs.models import _OUTPUT_NAMES
from tests.support.repository import REPOSITORY_ROOT


def test_release_inventory_and_paths_follow_projection_producer() -> None:
    policy = json.loads(
        (REPOSITORY_ROOT / "configs/release_evidence_policy.json").read_bytes()
    )
    records = [
        {
            "path": relative,
            "sha256": hashlib.sha256(
                (REPOSITORY_ROOT / relative).read_bytes()
            ).hexdigest(),
        }
        for relative in PROPAGATION_PRODUCER_SOURCE_PATHS
    ]
    digest = hashlib.sha256(
        json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    producers = {
        row["artifact_identity"]: row for row in policy["embedded_producer_identities"]
    }
    assert producers["propagation"]["source_paths"] == list(
        PROPAGATION_PRODUCER_SOURCE_PATHS
    )
    assert producers["scenario"]["source_paths"] == list(
        PROPAGATION_PRODUCER_SOURCE_PATHS
    )
    inventory = next(
        row["filenames"]
        for row in policy["bundle_inventories"]
        if row["artifact_identity"] == "propagation"
    )
    assert inventory == sorted(_OUTPUT_NAMES)
    artifacts = {row["identity"]: row for row in policy["required_artifacts"]}
    expected = f"artifacts/release-verification/propagation/neotoma-audit-{digest[:8]}"
    assert artifacts["propagation"]["path"] == expected + "/manifest.json"
    assert artifacts["scenario"]["path"] == expected + "/sensitivity_summary.json"
