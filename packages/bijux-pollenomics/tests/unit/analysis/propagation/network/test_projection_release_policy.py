"""The product release policy must bind projection payloads to their producer."""

from __future__ import annotations

import hashlib
import json
import subprocess

import pytest

from bijux_pollenomics.analysis.propagation.outputs import (
    PROPAGATION_PRODUCER_ID,
    PROPAGATION_PRODUCER_SOURCE_PATHS,
    PROPAGATION_PRODUCER_VERSION,
    PropagationOutputRefusalError,
)
from bijux_pollenomics.analysis.propagation.outputs.models import _OUTPUT_NAMES
from bijux_pollenomics.analysis.propagation.outputs.producer import (
    _validate_producer_identity,
)
from tests.support.repository import REPOSITORY_ROOT


def test_release_inventory_preserves_producer_contract_and_retained_source_paths() -> (
    None
):
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
    # The configured location retains its recorded producer source identity.
    # execution still authenticates current raw source bytes independently.
    retained_source = "f530ef2e7aea4dea15758350729cacc152f74e01"
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", retained_source, "HEAD"],
        cwd=REPOSITORY_ROOT,
        check=True,
    )
    retained_records = [
        {
            "path": relative,
            "sha256": hashlib.sha256(
                subprocess.check_output(
                    ["git", "show", retained_source + ":" + relative],
                    cwd=REPOSITORY_ROOT,
                )
            ).hexdigest(),
        }
        for relative in PROPAGATION_PRODUCER_SOURCE_PATHS
    ]
    retained_digest = hashlib.sha256(
        json.dumps(retained_records, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    expected = (
        "artifacts/release-verification/propagation/"
        f"neotoma-audit-{retained_digest[:8]}"
    )
    _validate_producer_identity(
        REPOSITORY_ROOT,
        propagation_producer_id=PROPAGATION_PRODUCER_ID,
        propagation_producer_version=PROPAGATION_PRODUCER_VERSION,
        propagation_producer_digest=digest,
    )
    if retained_digest != digest:
        with pytest.raises(
            PropagationOutputRefusalError, match="governed source bytes"
        ):
            _validate_producer_identity(
                REPOSITORY_ROOT,
                propagation_producer_id=PROPAGATION_PRODUCER_ID,
                propagation_producer_version=PROPAGATION_PRODUCER_VERSION,
                propagation_producer_digest=retained_digest,
            )
    assert artifacts["propagation"]["path"] == expected + "/manifest.json"
    assert artifacts["scenario"]["path"] == expected + "/sensitivity_summary.json"
