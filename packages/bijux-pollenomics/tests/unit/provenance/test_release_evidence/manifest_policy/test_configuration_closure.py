"""Output configuration closure and policy invalidation tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.provenance import (
    ArtifactInput,
    ReleaseEvidenceError,
    validate_release_evidence_manifest,
)

from ..support import _artifacts, _build, _canonical_json, _rewrite_fixture_policy


def test_outputs_must_bind_the_product_policy_digest(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    output = next(item for item in artifacts if item.identity == "output")
    policy = next(
        item for item in artifacts if item.identity == "release-evidence-policy"
    )
    artifacts[artifacts.index(output)] = ArtifactInput(
        **{
            **output.__dict__,
            "config_digests": tuple(
                digest
                for digest in output.config_digests
                if digest != policy.output_digest
            ),
        }
    )

    with pytest.raises(ReleaseEvidenceError, match="lacks release policy digest"):
        _build(tmp_path, artifacts=artifacts)


def test_output_configuration_closure_is_exact(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    output = next(item for item in artifacts if item.identity == "output")
    boundary = next(item for item in artifacts if item.identity == "boundary")
    artifacts[artifacts.index(output)] = ArtifactInput(
        **{
            **output.__dict__,
            "config_digests": tuple(
                digest
                for digest in output.config_digests
                if digest != boundary.output_digest
            ),
        }
    )

    with pytest.raises(ReleaseEvidenceError, match="configuration closure mismatch"):
        _build(tmp_path, artifacts=artifacts)

    artifacts = _artifacts(tmp_path)

    def narrow_only_generated_output(policy: dict[str, object]) -> None:
        requirements = cast(list[dict[str, object]], policy["required_artifacts"])
        output_requirement = next(
            item for item in requirements if item["identity"] == "output"
        )
        output_requirement["required_config_identities"] = [
            identity
            for identity in cast(
                list[str], output_requirement["required_config_identities"]
            )
            if identity != "boundary"
        ]

    _rewrite_fixture_policy(tmp_path, artifacts, narrow_only_generated_output)
    with pytest.raises(ReleaseEvidenceError, match="configuration closure mismatch"):
        _build(tmp_path, artifacts=artifacts)


def test_policy_change_invalidates_existing_manifest(tmp_path: Path) -> None:
    manifest = _build(tmp_path)
    path = tmp_path / "configs/release_evidence_policy.json"
    policy = json.loads(path.read_text(encoding="utf-8"))
    policy["required_reconciliations"].append(
        {
            "source": "sead",
            "entity": "sites",
            "dimension": "country",
            "scope_values": {},
            "derivation_adapter": "unavailable",
            "derivation_metric": "sites",
            "unavailable_status": "unavailable",
            "unavailable_reason_code": "fixture_count_not_materialized",
        }
    )
    path.write_bytes(_canonical_json(policy) + b"\n")

    with pytest.raises(ReleaseEvidenceError, match="digest changed"):
        validate_release_evidence_manifest(tmp_path, manifest)
