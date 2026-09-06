"""Compatibility tests for the release-evidence request facade."""

from __future__ import annotations

from pathlib import Path

import pytest
from bijux_pollenomics.provenance import ReleaseEvidenceError
from bijux_pollenomics.provenance import request as request_module
from bijux_pollenomics.provenance.request import (
    derive_release_evidence_request,
    validate_release_evidence_request,
)

from tests.unit.provenance.release_evidence_writer.support import _inputs


def test_public_facade_exports_only_stable_request_operations() -> None:
    assert request_module.__all__ == [
        "derive_release_evidence_request",
        "validate_release_evidence_request",
    ]
    assert request_module.derive_release_evidence_request is (
        derive_release_evidence_request
    )
    assert request_module.validate_release_evidence_request is (
        validate_release_evidence_request
    )


def test_repository_state_override_remains_compatible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _inputs(tmp_path)
    observed = request_module._repository_state(tmp_path, "fixture")
    dirty_state = {**observed, "dirty": True}
    monkeypatch.setattr(
        request_module,
        "_repository_state",
        lambda _root, _mode: dict(dirty_state),
    )

    request = derive_release_evidence_request(tmp_path)

    assert request["dirty"] is True


def test_exact_validation_rejects_a_mutated_request(tmp_path: Path) -> None:
    _inputs(tmp_path)
    request = derive_release_evidence_request(tmp_path)
    request["dependency_lock_digest"] = "sha256:" + "0" * 64

    with pytest.raises(
        ReleaseEvidenceError,
        match="differs from current product derivation",
    ):
        validate_release_evidence_request(tmp_path, request)
