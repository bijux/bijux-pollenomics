from __future__ import annotations

import hashlib
import json
from pathlib import Path
import socket

import pytest

from bijux_pollenomics.collection.sources.sead.acquisition.governed import (
    governed_sead_expected_identity,
)
from bijux_pollenomics.collection.sources.sead.evidence import rebuild


def _repository(tmp_path: Path) -> tuple[Path, Path]:
    (tmp_path / "data/boundaries").mkdir(parents=True)
    output_parent = tmp_path / "artifacts/fixed-point"
    output_parent.mkdir(parents=True)
    return tmp_path, output_parent / "candidate"


def _materializing_writer(
    acquisition_root: Path,
    output_root: Path,
    *,
    expected_identity: object,
) -> tuple[Path, ...]:
    del acquisition_root, expected_identity
    output_root.mkdir()
    for index in range(53):
        (output_root / f"part-{index:02d}.json").write_text(
            json.dumps({"index": index}) + "\n", encoding="utf-8"
        )
    return tuple(sorted(path for path in output_root.iterdir() if path.is_file()))


def test_rebuild_uses_pinned_identity_and_validates_offline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, output = _repository(tmp_path)
    calls: list[str] = []

    def validate_admission(acquisition_root: Path, *, data_root: Path) -> object:
        assert acquisition_root.name == rebuild.SEAD_GOVERNED_EVIDENCE_RUN_ID
        assert data_root == repository / "data"
        calls.append("admission")
        return object()

    def write_bundle(
        acquisition_root: Path,
        output_root: Path,
        *,
        expected_identity: object,
    ) -> tuple[Path, ...]:
        with pytest.raises(rebuild.NetworkAccessRefused):
            socket.getaddrinfo("example.invalid", 443)
        paths = _materializing_writer(
            acquisition_root,
            output_root,
            expected_identity=expected_identity,
        )
        manifest = output_root / "evidence_materialization_manifest.json"
        manifest.write_text('{"schema_version":"fixture"}\n', encoding="utf-8")
        calls.append("writer")
        return tuple(sorted((*paths, manifest)))

    def validate_bundle(candidate: Path) -> None:
        assert candidate == output
        calls.append("bundle")

    manifest_bytes = b'{"schema_version":"fixture"}\n'
    monkeypatch.setattr(
        rebuild,
        "SEAD_GOVERNED_EVIDENCE_MANIFEST_SHA256",
        hashlib.sha256(manifest_bytes).hexdigest(),
    )

    result = rebuild.rebuild_governed_sead_evidence(
        repository,
        output,
        admission_validator=validate_admission,
        bundle_writer=write_bundle,
        bundle_validator=validate_bundle,
    )

    assert calls == ["admission", "writer", "bundle"]
    assert result["status"] == "PASS"
    assert result["file_count"] == 54
    assert result["network_policy"] == "forbidden"
    identity = governed_sead_expected_identity(repository / "data")
    assert identity.run_id == rebuild.SEAD_GOVERNED_EVIDENCE_RUN_ID
    assert identity.country_authority_root == (repository / "data/boundaries").resolve()


def test_network_attempt_aborts_before_validation(
    tmp_path: Path,
) -> None:
    repository, output = _repository(tmp_path)
    validated = False

    def write_bundle(
        acquisition_root: Path,
        output_root: Path,
        *,
        expected_identity: object,
    ) -> tuple[Path, ...]:
        del acquisition_root, output_root, expected_identity
        socket.getaddrinfo("example.invalid", 443)
        raise AssertionError("network refusal did not stop the writer")

    def validate_bundle(candidate: Path) -> None:
        nonlocal validated
        del candidate
        validated = True

    with pytest.raises(rebuild.NetworkAccessRefused):
        rebuild.rebuild_governed_sead_evidence(
            repository,
            output,
            admission_validator=lambda *args, **kwargs: object(),
            bundle_writer=write_bundle,
            bundle_validator=validate_bundle,
        )
    assert validated is False


def test_command_audit_policy_refuses_socket_and_child_process_events() -> None:
    with pytest.raises(rebuild.NetworkAccessRefused, match="socket.connect"):
        rebuild._audit_offline_operation("socket.connect", ())
    with pytest.raises(rebuild.NetworkAccessRefused, match="subprocess.Popen"):
        rebuild._audit_offline_operation("subprocess.Popen", ())

    rebuild._audit_offline_operation("open", ())


def test_rebuild_rejects_outputs_outside_repository_artifacts(tmp_path: Path) -> None:
    repository, _ = _repository(tmp_path)

    with pytest.raises(ValueError, match="below repository artifacts"):
        rebuild.rebuild_governed_sead_evidence(
            repository,
            tmp_path / "candidate",
            admission_validator=lambda *args, **kwargs: object(),
            bundle_writer=_materializing_writer,
            bundle_validator=lambda path: None,
        )
