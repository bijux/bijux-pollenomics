from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

from bijux_pollenomics_dev.ci.atlas_media.process_execution import (
    BoundedProcessError,
    CompletedCommand,
)
from bijux_pollenomics_dev.ci.report_rebuild import owner_process
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    ReportRebuildError,
    sha256_bytes,
)


def _run(root: Path, command: tuple[str, ...]) -> None:
    owner_process.run_owner_command(
        command=command,
        repo_root=root,
        evidence_root=root,
        owner_id="science/example",
        lane="reference",
        binding={"candidate": "fixed"},
        producer_inputs={"source": {"sha256": "source-identity"}},
        timeout_seconds=5,
    )


@pytest.mark.parametrize("exit_code", [0, 17])
def test_owner_command_retains_real_stdout_and_failure(
    tmp_path: Path, exit_code: int
) -> None:
    command = (
        sys.executable,
        "-c",
        f"import sys; print('producer output'); print('diagnostic', file=sys.stderr); sys.exit({exit_code})",
    )
    if exit_code:
        with pytest.raises(ReportRebuildError, match="exit=17"):
            _run(tmp_path, command)
    else:
        _run(tmp_path, command)
    request = json.loads((tmp_path / "producer-command.json").read_text())
    receipt = json.loads((tmp_path / "producer-execution.json").read_text())
    assert request["command"] == list(command)
    assert request["binding"] == {"candidate": "fixed"}
    assert request["producer_inputs"] == {"source": {"sha256": "source-identity"}}
    assert receipt["command_receipt_sha256"] == sha256_bytes(
        (tmp_path / "producer-command.json").read_bytes()
    )
    assert receipt["exit_code"] == exit_code
    assert receipt["status"] == "exited"
    assert receipt["timed_out"] is False
    for name, expected in (
        ("stdout", b"producer output\n"),
        ("stderr", b"diagnostic\n"),
    ):
        log = tmp_path / receipt[name]["path"]
        assert log.read_bytes() == expected
        assert receipt[name]["sha256"] == sha256_bytes(expected)
        assert receipt[name]["bytes"] == len(expected)


def test_owner_command_retains_timeout_diagnostics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    command = (sys.executable, "-c", "pass")

    def timeout(*_args: object, **_kwargs: object) -> CompletedCommand:
        return CompletedCommand(
            command,
            -15,
            b"partial result",
            b"timeout detail",
            5.1,
            True,
            "terminated_process_group",
        )

    monkeypatch.setattr(owner_process, "run_bounded_argv", timeout)
    with pytest.raises(ReportRebuildError, match="timed_out=True"):
        _run(tmp_path, command)
    receipt = json.loads((tmp_path / "producer-execution.json").read_text())
    assert receipt["status"] == "timed_out"
    assert receipt["exit_code"] == -15
    assert receipt["termination"] == "terminated_process_group"
    assert (tmp_path / "producer.stderr.log").read_bytes() == b"timeout detail"


def test_owner_command_records_unavailable_execution_without_invented_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unavailable(*_args: object, **_kwargs: object) -> CompletedCommand:
        raise BoundedProcessError("unavailable executable")

    monkeypatch.setattr(owner_process, "run_bounded_argv", unavailable)
    with pytest.raises(ReportRebuildError, match="executed safely"):
        _run(tmp_path, ("unavailable",))
    receipt = json.loads((tmp_path / "producer-execution.json").read_text())
    assert receipt["status"] == "execution_error"
    assert receipt["exit_code"] is None
    assert receipt["error"] == "unavailable executable"
    assert "stdout" not in receipt
    assert not (tmp_path / "producer.stdout.log").exists()
