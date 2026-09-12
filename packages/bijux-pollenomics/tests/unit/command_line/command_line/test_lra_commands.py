"""Installed-command contracts for structured exploratory LRA operations."""

from __future__ import annotations

from importlib import metadata
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.cli import main

from ...analysis.lra.support import request_fixture


def test_valid_request_reports_missing_extra_without_creating_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request = tmp_path / "request.json"
    request.write_text(json.dumps(request_fixture(tmp_path)))
    destination = tmp_path / "product"
    with patch.object(
        metadata, "distribution", side_effect=metadata.PackageNotFoundError
    ):
        code = main(
            [
                "run-lra",
                str(request),
                "--input-root",
                str(tmp_path),
                "--output",
                str(destination),
            ]
        )
    result = json.loads(capsys.readouterr().out)
    assert code == 2
    assert result["reason_code"] == "lra_extension_missing"
    assert not destination.exists()


def test_duplicate_json_key_is_not_silently_overwritten(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request = tmp_path / "request.json"
    request.write_text('{"operation":"reveals","operation":"love"}')
    code = main(["validate-lra-input", str(request), "--input-root", str(tmp_path)])
    result = json.loads(capsys.readouterr().out)
    assert code == 2
    assert result["reason_code"] == "lra_request_io_or_encoding"
    assert "Duplicate JSON key" in result["detail"]


def test_nonobject_request_is_a_structured_refusal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    request = tmp_path / "request.json"
    request.write_text("[]")
    code = main(["validate-lra-input", str(request), "--input-root", str(tmp_path)])
    assert code == 2
    assert json.loads(capsys.readouterr().out)["reason_code"] == "invalid_lra_json"


def test_optimizer_diagnostics_survive_command_boundary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
    from bijux_pollenomics.command_line.runtime import lra

    request = tmp_path / "request.json"
    request.write_text(json.dumps(request_fixture(tmp_path)))
    diagnostics = [
        {"reason": "maximum_iterations", "evaluations": 5, "best_objective": 0.125}
    ]
    refusal = LRARefusal(
        "optimizer_nonconvergence",
        "Iteration budget exhausted",
        diagnostics=diagnostics,
    )
    with patch.object(lra, "run_lra_request", side_effect=refusal):
        code = main(
            [
                "run-lra",
                str(request),
                "--input-root",
                str(tmp_path),
                "--output",
                str(tmp_path / "product"),
            ]
        )
    envelope = json.loads(capsys.readouterr().out)
    assert code == 2
    assert envelope["reason_code"] == "optimizer_nonconvergence"
    assert envelope["diagnostics"] == diagnostics
