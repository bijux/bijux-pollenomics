"""The product release policy must bind projection payloads to their producer."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import pytest

from bijux_pollenomics.analysis.propagation.outputs import (
    PROPAGATION_PRODUCER_ID,
    PROPAGATION_PRODUCER_SOURCE_PATHS,
    PROPAGATION_PRODUCER_VERSION,
    PropagationOutputRefusalError,
    producer,
)
from bijux_pollenomics.analysis.propagation.outputs.inputs import _read_identity_file
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
    retained_source = "c9b2047155e999d6a6164b52ec73b5fd95cd31be"
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", retained_source, "HEAD"],
        cwd=REPOSITORY_ROOT,
        check=True,
    )
    retained_models = subprocess.check_output(
        [
            "git",
            "show",
            retained_source + ":packages/bijux-pollenomics/src/"
            "bijux_pollenomics/analysis/propagation/outputs/models.py",
        ],
        cwd=REPOSITORY_ROOT,
    ).decode()
    retained_paths = ast.literal_eval(
        next(
            node.value
            for node in ast.parse(retained_models).body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "PROPAGATION_PRODUCER_SOURCE_PATHS"
                for target in node.targets
            )
        )
    )
    assert isinstance(retained_paths, tuple)
    assert all(isinstance(path, str) for path in retained_paths)
    assert retained_paths == PROPAGATION_PRODUCER_SOURCE_PATHS
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
        for relative in retained_paths
    ]
    retained_digest = hashlib.sha256(
        json.dumps(retained_records, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert retained_digest == (
        "2072b0721285f9bcca07ade74f62affc7e57d6db3203aedb2d7da3d1809af661"
    )
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


def test_changed_relation_dependency_refuses_stale_producer_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
    identity = {
        "propagation_producer_id": PROPAGATION_PRODUCER_ID,
        "propagation_producer_version": PROPAGATION_PRODUCER_VERSION,
        "propagation_producer_digest": digest,
    }
    _validate_producer_identity(REPOSITORY_ROOT, **identity)
    relation = REPOSITORY_ROOT / (
        "packages/bijux-pollenomics/src/bijux_pollenomics/"
        "analysis/propagation/projection/relation.py"
    )

    def changed_dependency(path: Path, **kwargs: Any) -> bytes:
        body = _read_identity_file(path, **kwargs)
        return body + b"\n# changed relation semantics\n" if path == relation else body

    monkeypatch.setattr(producer, "_read_identity_file", changed_dependency)
    with pytest.raises(PropagationOutputRefusalError) as refusal:
        _validate_producer_identity(REPOSITORY_ROOT, **identity)
    assert refusal.value.reason_code == "invalid_propagation_identity"
