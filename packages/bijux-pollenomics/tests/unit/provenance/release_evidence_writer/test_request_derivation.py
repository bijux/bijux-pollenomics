"""Release-evidence request derivation tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.provenance import (
    ReleaseEvidenceError,
    derive_release_evidence_request,
    write_release_evidence_request,
)
from bijux_pollenomics.provenance import request as request_module
from bijux_pollenomics.provenance.release_evidence import (
    repository as release_repository,
)
from bijux_pollenomics.provenance.request import service as request_service

from .support import (
    _canonical_json,
    _inputs,
    _write_request_document,
)


def test_request_derivation_is_deterministic_and_locally_unverified(
    tmp_path: Path,
) -> None:
    _inputs(tmp_path)

    first = derive_release_evidence_request(tmp_path)
    second = derive_release_evidence_request(tmp_path)

    assert first == second
    assert first["schema_version"] == "release-evidence-request.v3"
    assert len(cast(list[object], first["artifacts"])) == 11
    assert len(cast(list[object], first["gates"])) == 1
    assert len(cast(list[object], first["reconciliations"])) == 7
    assert first["blockers"] == []
    manifest = _write_request_document(tmp_path, first)
    decision = cast(dict[str, object], manifest["release_decision"])
    assert decision["status"] == "implemented_unverified"
    assert decision["release_ready"] is False


@pytest.mark.parametrize("failure", ["missing", "stale", "old_schema"])
def test_request_derivation_rejects_invalid_recorded_gate(
    tmp_path: Path, failure: str
) -> None:
    _inputs(tmp_path)
    gate = tmp_path / "artifacts/gate-evidence/quality.json"
    if failure == "missing":
        gate.unlink()
    elif failure == "stale":
        (tmp_path / "inputs/gate-input.txt").write_text(
            "changed after gate\n", encoding="utf-8"
        )
    else:
        record = json.loads(gate.read_text(encoding="utf-8"))
        record["schema_version"] = "recorded-gate.v1"
        gate.write_bytes(_canonical_json(record) + b"\n")

    with pytest.raises(ReleaseEvidenceError):
        derive_release_evidence_request(tmp_path)


def test_request_writer_is_idempotent_and_refuses_different_bytes(
    tmp_path: Path,
) -> None:
    _inputs(tmp_path)
    relative = "artifacts/release-candidate/request.json"
    first = write_release_evidence_request(tmp_path, relative)
    output = tmp_path / relative
    before = output.stat()

    second = write_release_evidence_request(tmp_path, relative)
    after = output.stat()
    assert first == second
    assert (after.st_ino, after.st_mtime_ns) == (before.st_ino, before.st_mtime_ns)

    (tmp_path / "inputs/output.json").write_text('{"records":2}\n', encoding="utf-8")
    with pytest.raises(ReleaseEvidenceError, match="different bytes"):
        write_release_evidence_request(tmp_path, relative)


def test_request_writer_rejects_symlinked_output_parent(tmp_path: Path) -> None:
    _inputs(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "artifacts/release-candidate").symlink_to(
        outside, target_is_directory=True
    )

    with pytest.raises(ReleaseEvidenceError, match="unsafe output directory"):
        write_release_evidence_request(
            tmp_path, "artifacts/release-candidate/request.json"
        )


def test_request_derivation_rejects_concurrent_input_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _inputs(tmp_path)
    original = release_repository._hash_repository_object
    mutated = False

    def mutating_hash(
        root: Path, relative_path: str, *, exclude_python_cache: bool = False
    ) -> dict[str, object]:
        nonlocal mutated
        result = original(
            root,
            relative_path,
            exclude_python_cache=exclude_python_cache,
        )
        if relative_path == "inputs/config.json" and not mutated:
            (root / relative_path).write_text('{"changed":true}\n', encoding="utf-8")
            mutated = True
        return result

    monkeypatch.setattr(request_service, "_hash_repository_object", mutating_hash)

    with pytest.raises(ReleaseEvidenceError, match="digest changed"):
        derive_release_evidence_request(tmp_path)
    assert mutated is True


def test_request_derivation_records_observed_dirty_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _inputs(tmp_path)
    state: dict[str, object] = {
        "mode": "fixture",
        "head_commit": None,
        "head_tree": None,
        "dirty": True,
        "status_digest": "sha256:" + "1" * 64,
        "tracked_paths_digest": None,
        "tracked_diff_digest": None,
        "untracked_objects": [],
    }
    monkeypatch.setattr(
        request_service,
        "_repository_state",
        lambda _root, _mode: dict(state),
    )

    request = derive_release_evidence_request(tmp_path)

    assert request["dirty"] is True


def test_exact_request_validation_rejects_hand_authored_change(tmp_path: Path) -> None:
    _inputs(tmp_path)
    request = derive_release_evidence_request(tmp_path)
    request["dirty"] = True

    with pytest.raises(ReleaseEvidenceError, match="differs from current"):
        request_module.validate_release_evidence_request(tmp_path, request)
