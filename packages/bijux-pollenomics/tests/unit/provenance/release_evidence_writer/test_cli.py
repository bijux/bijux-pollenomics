"""Release-evidence cli tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from bijux_pollenomics.provenance import (
    release_evidence_main,
    write_release_evidence_request,
)

from .support import (
    _arguments,
    _inputs,
    _write,
)


def test_callable_cli_writes_and_validates_for_a_local_gate(
    tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    _inputs(tmp_path)
    request_status = release_evidence_main(
        [
            "request",
            "--repository-root",
            str(tmp_path),
            "--output",
            "artifacts/requests/release.json",
        ]
    )
    request_summary = json.loads(capfd.readouterr().out)
    output_path = "artifacts/release/manifest.json"

    write_status = release_evidence_main(
        [
            "write",
            "--repository-root",
            str(tmp_path),
            "--request",
            "artifacts/requests/release.json",
            "--output",
            output_path,
        ]
    )
    write_output = json.loads(capfd.readouterr().out)
    validate_status = release_evidence_main(
        [
            "validate",
            "--repository-root",
            str(tmp_path),
            "--manifest",
            output_path,
        ]
    )
    validate_output = json.loads(capfd.readouterr().out)

    assert request_status == 0
    assert request_summary["schema_version"] == "release-evidence-request.v3"
    assert write_status == validate_status == 1
    assert write_output == validate_output
    assert write_output["release_ready"] is False
    assert write_output["status"] == "implemented_unverified"


def test_callable_cli_returns_nonzero_for_nonrelease_evidence(
    tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    _inputs(tmp_path, gate_status="FAIL")
    write_release_evidence_request(tmp_path, "artifacts/requests/release.json")

    result = release_evidence_main(
        [
            "write",
            "--repository-root",
            str(tmp_path),
            "--request",
            "artifacts/requests/release.json",
            "--output",
            "artifacts/release/manifest.json",
        ]
    )
    summary = json.loads(capfd.readouterr().out)

    assert result == 1
    assert summary["release_ready"] is False
    assert summary["status"] == "failed"
    assert (tmp_path / "artifacts/release/manifest.json").is_file()


def test_validate_cli_detects_changed_immutable_input(
    tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    arguments = _arguments(tmp_path)
    output_path = "artifacts/release/manifest.json"
    _write(tmp_path, output_path, arguments)
    (tmp_path / "inputs/output.json").write_text('{"records":2}\n', encoding="utf-8")

    result = release_evidence_main(
        [
            "validate",
            "--repository-root",
            str(tmp_path),
            "--manifest",
            output_path,
        ]
    )
    captured = capfd.readouterr()

    assert result == 2
    assert captured.out == ""
    assert "release evidence refused" in captured.err
