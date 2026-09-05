"""Scientific and deterministic contract tests for policy loading."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics.provenance import ReleaseEvidenceError
from bijux_pollenomics.provenance.release_evidence import policy
from tests.unit.provenance.test_release_evidence.support.codec import _canonical_json
from tests.unit.provenance.test_release_evidence.support.policy import (
    _write_fixture_policy,
)


def test_fixture_policy_preserves_order_values_and_content_identity(
    tmp_path: Path,
) -> None:
    payload = _write_fixture_policy(tmp_path)

    loaded = policy._load_release_evidence_policy(tmp_path)

    assert loaded.output_digest == f"sha256:{hashlib.sha256(payload).hexdigest()}"
    assert tuple(item.identity for item in loaded.required_artifacts) == tuple(
        sorted(item.identity for item in loaded.required_artifacts)
    )
    assert tuple(
        (item.source, item.entity) for item in loaded.required_reconciliations
    ) == (("neotoma", "samples"),)
    assert loaded.propagation_contract.maximum_distance_km == 1.0
    assert loaded.propagation_contract.maximum_lag_years == 1.0
    assert loaded.governed_request_artifact_ids == frozenset({"receipt"})


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda record: record["propagation_contract"]["default_scenario"].update(
                maximum_distance_km=True
            ),
            "default propagation thresholds are invalid",
        ),
        (
            lambda record: record.update(required_gate_ids=[]),
            "required gate IDs must be non-empty and sorted",
        ),
        (
            lambda record: record.update(governed_request_artifact_ids=["unknown"]),
            "governed request artifact IDs must be known",
        ),
    ],
)
def test_policy_refusals_remain_fail_closed_and_exact(
    tmp_path: Path,
    mutate: object,
    message: str,
) -> None:
    payload = _write_fixture_policy(tmp_path)
    record = json.loads(payload)
    assert isinstance(record, dict)
    assert callable(mutate)
    mutate(record)
    policy_path = tmp_path / "configs/release_evidence_policy.json"
    policy_path.write_bytes(_canonical_json(record) + b"\n")

    with pytest.raises(ReleaseEvidenceError, match=f"^{message}$"):
        policy._load_release_evidence_policy(tmp_path)
