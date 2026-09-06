"""Artifact inventory, schema, and content integrity tests."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.provenance import (
    ArtifactInput,
    ArtifactReference,
    ReleaseEvidenceError,
    validate_release_evidence_manifest,
)

from ..support import (
    _artifacts,
    _build,
    _digest,
    _rewrite_fixture_policy,
)


def test_artifact_inventory_binds_metadata_and_rejects_cross_role_digest_alias(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)
    receipt = next(item for item in artifacts if item.identity == "receipt")
    artifacts[artifacts.index(receipt)] = ArtifactInput(
        **{**receipt.__dict__, "media_type": "text/plain"}
    )
    with pytest.raises(ReleaseEvidenceError, match="exact product inventory"):
        _build(tmp_path, artifacts=artifacts)

    artifacts = _artifacts(tmp_path)
    boundary = next(item for item in artifacts if item.identity == "boundary")
    (tmp_path / "receipt.json").write_bytes(
        (tmp_path / "boundary.geojson").read_bytes()
    )
    receipt = next(item for item in artifacts if item.identity == "receipt")
    artifacts[artifacts.index(receipt)] = ArtifactInput(
        **{**receipt.__dict__, "output_digest": boundary.output_digest}
    )
    snapshot = next(item for item in artifacts if item.identity == "snapshot")
    artifacts[artifacts.index(snapshot)] = ArtifactInput(
        **{
            **snapshot.__dict__,
            "parents": (ArtifactReference("receipt", boundary.output_digest),),
        }
    )
    with pytest.raises(ReleaseEvidenceError, match="cross-role digest alias"):
        _build(tmp_path, artifacts=artifacts)


def test_json_artifact_schema_identity_is_checked_against_content(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path)
    (tmp_path / "receipt.json").write_text('{"receipt":1}\n', encoding="utf-8")
    receipt_digest = _digest(b'{"receipt":1}\n')
    receipt = next(item for item in artifacts if item.identity == "receipt")
    artifacts[artifacts.index(receipt)] = ArtifactInput(
        **{**receipt.__dict__, "output_digest": receipt_digest}
    )
    snapshot = next(item for item in artifacts if item.identity == "snapshot")
    artifacts[artifacts.index(snapshot)] = ArtifactInput(
        **{
            **snapshot.__dict__,
            "parents": (ArtifactReference("receipt", receipt_digest),),
        }
    )

    def require_receipt_schema(policy: dict[str, object]) -> None:
        requirements = cast(list[dict[str, object]], policy["required_artifacts"])
        receipt = next(item for item in requirements if item["identity"] == "receipt")
        receipt["media_type"] = "application/json"
        receipt["schema_version"] = "fixture-receipt.v1"
        receipt["schema_identity_field"] = "schema_version"

    _rewrite_fixture_policy(tmp_path, artifacts, require_receipt_schema)
    receipt = next(item for item in artifacts if item.identity == "receipt")
    artifacts[artifacts.index(receipt)] = ArtifactInput(
        **{
            **receipt.__dict__,
            "media_type": "application/json",
            "schema_version": "fixture-receipt.v1",
        }
    )

    with pytest.raises(ReleaseEvidenceError, match="embedded schema identity mismatch"):
        _build(tmp_path, artifacts=artifacts)


def test_validation_detects_file_and_manifest_tampering(tmp_path: Path) -> None:
    manifest = _build(tmp_path)
    (tmp_path / "output.json").write_text('{"records":2}\n', encoding="utf-8")
    with pytest.raises(ReleaseEvidenceError, match="digest changed"):
        validate_release_evidence_manifest(tmp_path, manifest)

    (tmp_path / "output.json").write_text('{"records":1}\n', encoding="utf-8")
    altered = copy.deepcopy(manifest)
    altered["code_commit"] = "2" * 40
    with pytest.raises(
        ReleaseEvidenceError, match="content or an immutable input changed"
    ):
        validate_release_evidence_manifest(tmp_path, altered)
