"""Exact artifact parent-lineage policy tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.provenance import (
    ArtifactInput,
    ArtifactReference,
    ReleaseEvidenceError,
)

from ..support import _artifacts, _build


@pytest.mark.parametrize(
    ("target_identity", "attack", "expected_message"),
    [
        ("output", "reparent", "parent inventory mismatch"),
        ("output", "remove", "parent inventory mismatch"),
        ("output", "add", "parent inventory mismatch"),
        ("output", "stale", "parent digest mismatch"),
        ("validation", "unrelated-gate-ancestry", "parent inventory mismatch"),
    ],
)
def test_exact_parent_inventory_refuses_coherent_ancestry_attacks(
    tmp_path: Path, target_identity: str, attack: str, expected_message: str
) -> None:
    artifacts = _artifacts(tmp_path)
    target = next(item for item in artifacts if item.identity == target_identity)
    by_identity = {item.identity: item for item in artifacts}
    parents: tuple[ArtifactReference, ...]
    if attack == "reparent":
        parents = (ArtifactReference("receipt", by_identity["receipt"].output_digest),)
    elif attack == "remove":
        parents = ()
    elif attack == "add":
        parents = (
            *target.parents,
            ArtifactReference("receipt", by_identity["receipt"].output_digest),
        )
    elif attack == "stale":
        parents = (ArtifactReference("snapshot", "sha256:" + "0" * 64),)
    else:
        parents = (ArtifactReference("receipt", by_identity["receipt"].output_digest),)
    artifacts[artifacts.index(target)] = ArtifactInput(
        **{**target.__dict__, "parents": parents}
    )

    with pytest.raises(ReleaseEvidenceError, match=expected_message):
        _build(tmp_path, artifacts=artifacts)
