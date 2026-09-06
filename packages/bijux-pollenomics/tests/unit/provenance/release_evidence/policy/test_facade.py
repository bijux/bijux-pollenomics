"""Compatibility and patch-seam tests for policy loading."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from bijux_pollenomics.provenance.release_evidence import policy
from tests.unit.provenance.test_release_evidence.support.policy import (
    _write_fixture_policy,
)


def test_loader_signature_and_legacy_dependencies_remain_available() -> None:
    assert str(inspect.signature(policy._load_release_evidence_policy)) == (
        "(root: 'Path') -> '_ReleaseEvidencePolicy'"
    )
    assert policy.Path is Path
    assert policy.ArtifactRole is not None
    assert policy.ReleaseEvidenceError is not None
    assert policy._RELEASE_POLICY_PATH == "configs/release_evidence_policy.json"
    assert callable(policy._canonical_json)
    assert callable(policy._mapping)
    assert callable(policy._read_repository_file)


def test_loader_and_section_helpers_use_facade_patch_seams(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_fixture_policy(tmp_path)
    original_read = policy._read_repository_file
    original_identity = policy._require_identity
    calls = {"read": 0, "identity": 0}

    def read(repository_root: Path, relative_path: str) -> bytes:
        calls["read"] += 1
        return original_read(repository_root, relative_path)

    def require_identity(value: str, field_name: str) -> None:
        calls["identity"] += 1
        original_identity(value, field_name)

    monkeypatch.setattr(policy, "_read_repository_file", read)
    monkeypatch.setattr(policy, "_require_identity", require_identity)

    loaded = policy._load_release_evidence_policy(tmp_path)

    assert loaded.mode == "fixture"
    assert calls["read"] == 1
    assert calls["identity"] > 10
