"""Installed-command contracts for structured exploratory LRA operations."""

from __future__ import annotations

from importlib import metadata
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from bijux_pollenomics.cli import main

from ...analysis.lra.support import request_fixture


@pytest.mark.parametrize(
    "interrupted,completed,expected_code",
    [(False, True, 0), (False, False, 2), (True, False, 130)],
)
def test_batch_cli_preserves_item_outcomes_and_exit_status(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    interrupted: bool,
    completed: bool,
    expected_code: int,
) -> None:
    from bijux_pollenomics.analysis.lra.api import LRABatchItemResult, LRABatchResult
    from bijux_pollenomics.command_line.runtime import lra

    path = tmp_path / "batch.json"
    request = request_fixture(tmp_path)
    path.write_text(
        json.dumps(
            {
                "schema_version": "lra-batch-request.v1",
                "items": [{"item_id": "one", "request": request}],
            }
        )
    )
    result = LRABatchResult(
        "0" * 64,
        tmp_path / "attempt",
        (
            LRABatchItemResult(
                0, "one", "1" * 64, "completed" if completed else "not_run"
            ),
        ),
        interrupted,
    )
    with patch.object(lra, "run_lra_batch", return_value=result) as run:
        code = main(
            [
                "run-lra-batch",
                str(path),
                "--input-root",
                str(tmp_path),
                "--cache-root",
                str(tmp_path / "cache"),
                "--report-root",
                str(tmp_path / "attempt"),
                "--max-workers",
                "2",
            ]
        )
    assert code == expected_code
    output = json.loads(capsys.readouterr().out)
    assert output == result.as_dict()
    assert run.call_args.args[0][0].payload() == request
    assert run.call_args.kwargs["limits"].max_workers == 2


@pytest.mark.parametrize(
    "payload",
    [
        {"schema_version": "lra-batch-request.v1", "items": "invalid"},
        {
            "schema_version": "lra-batch-request.v1",
            "items": [{"item_id": "one", "request": None}],
        },
        {"schema_version": "unversioned", "items": []},
    ],
)
def test_batch_cli_refuses_invalid_envelope_before_spawning(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    payload: object,
) -> None:
    from bijux_pollenomics.command_line.runtime import lra

    path = tmp_path / "batch.json"
    path.write_text(json.dumps(payload))
    with patch.object(lra, "run_lra_batch") as run:
        code = main(
            [
                "run-lra-batch",
                str(path),
                "--input-root",
                str(tmp_path),
                "--cache-root",
                str(tmp_path / "cache"),
                "--report-root",
                str(tmp_path / "attempt"),
            ]
        )
    assert code == 2 and not run.called
    assert (
        json.loads(capsys.readouterr().out)["reason_code"] == "invalid_lra_batch_json"
    )


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
