"""Artifact producer ownership and identity tests."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.provenance import ArtifactInput, ReleaseEvidenceError
from bijux_pollenomics.provenance import validate_release_evidence_manifest

from ..support import _artifacts, _build, _digest


def test_artifacts_may_bind_distinct_governed_producers(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path, secondary_producer=True)
    second_digest = _digest(b"def render(): return 2\n")

    manifest = _build(tmp_path, artifacts=artifacts)

    producer_digests = {
        artifact["output_digest"]
        for artifact in cast(list[dict[str, object]], manifest["artifacts"])
        if artifact["role"] == "producer"
    }
    assert producer_digests == {
        _digest(b"def build(): return 1\n"),
        second_digest,
    }
    validate_release_evidence_manifest(tmp_path, manifest)


def test_coherent_producer_reassignment_is_refused_by_product_policy(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path, secondary_producer=True)
    output = next(item for item in artifacts if item.identity == "output")
    primary = next(item for item in artifacts if item.identity == "producer")
    artifacts[artifacts.index(output)] = ArtifactInput(
        **{**output.__dict__, "producer_digest": primary.output_digest}
    )

    with pytest.raises(ReleaseEvidenceError, match="producer ownership mismatch"):
        _build(tmp_path, artifacts=artifacts)


def test_duplicate_digest_and_unused_producer_artifacts_are_refused(
    tmp_path: Path,
) -> None:
    artifacts = _artifacts(tmp_path, secondary_producer=True)
    duplicate_path = tmp_path / "secondary-producer.py"
    duplicate_path.write_bytes(b"def build(): return 1\n")
    duplicate_digest = _digest(duplicate_path.read_bytes())
    secondary = next(
        item for item in artifacts if item.identity == "secondary-producer"
    )
    artifacts[artifacts.index(secondary)] = ArtifactInput(
        **{
            **secondary.__dict__,
            "producer_digest": duplicate_digest,
            "output_digest": duplicate_digest,
        }
    )
    output = next(item for item in artifacts if item.identity == "output")
    artifacts[artifacts.index(output)] = ArtifactInput(
        **{**output.__dict__, "producer_digest": duplicate_digest}
    )
    with pytest.raises(ReleaseEvidenceError, match="duplicate producer digest"):
        _build(tmp_path, artifacts=artifacts)

    unused = _artifacts(
        tmp_path,
        secondary_producer=True,
        output_uses_secondary=False,
    )
    with pytest.raises(ReleaseEvidenceError, match="unused producer artifacts"):
        _build(tmp_path, artifacts=unused)
