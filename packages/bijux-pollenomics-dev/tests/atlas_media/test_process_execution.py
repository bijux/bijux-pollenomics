from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest
from bijux_pollenomics_dev.ci.atlas_media import AtlasMediaError, process_execution


def test_logged_command_timeout_is_bounded_and_receipted(tmp_path: Path) -> None:
    root = tmp_path / "artifacts/media"
    root.mkdir(parents=True)
    stdout_path = root / "bounded.stdout.log"
    stderr_path = root / "bounded.stderr.log"

    with pytest.raises(AtlasMediaError, match="exceeded"):
        process_execution._run_logged(
            (sys.executable, "-c", "import time; time.sleep(2)"),
            cwd=tmp_path,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            timeout_seconds=0.05,
        )

    receipt = json.loads((root / "bounded.execution.json").read_text(encoding="utf-8"))
    assert receipt["command"] == [
        sys.executable,
        "-c",
        "import time; time.sleep(2)",
    ]
    assert receipt["timed_out"] is True
    assert receipt["exit_status"] is None
    assert receipt["duration_seconds"] < 1


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group contract")
def test_logged_timeout_terminates_descendant_process_group(tmp_path: Path) -> None:
    root = tmp_path / "artifacts/media"
    root.mkdir(parents=True)
    child_pid = root / "child.pid"
    command = (
        sys.executable,
        "-c",
        (
            "import pathlib,subprocess,sys,time; "
            "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']); "
            f"pathlib.Path({str(child_pid)!r}).write_text(str(child.pid)); "
            "time.sleep(60)"
        ),
    )

    with pytest.raises(AtlasMediaError, match="exceeded"):
        process_execution._run_logged(
            command,
            cwd=tmp_path,
            stdout_path=root / "tree.stdout.log",
            stderr_path=root / "tree.stderr.log",
            timeout_seconds=0.2,
        )

    pid = int(child_pid.read_text(encoding="utf-8"))
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group contract")
def test_timeout_kills_term_resistant_descendant_holding_output_pipes(
    tmp_path: Path,
) -> None:
    root = tmp_path / "artifacts/media"
    root.mkdir(parents=True)
    child_pid = root / "resistant-child.pid"
    child_program = (
        "import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(60)"
    )
    command = (
        sys.executable,
        "-c",
        (
            "import pathlib,subprocess,sys,time;"
            f"child=subprocess.Popen([sys.executable,'-c',{child_program!r}]);"
            f"pathlib.Path({str(child_pid)!r}).write_text(str(child.pid));"
            "time.sleep(60)"
        ),
    )
    started = time.perf_counter()

    with pytest.raises(AtlasMediaError, match="exceeded"):
        process_execution._run_logged(
            command,
            cwd=tmp_path,
            stdout_path=root / "resistant.stdout.log",
            stderr_path=root / "resistant.stderr.log",
            timeout_seconds=0.2,
        )

    assert time.perf_counter() - started < 2
    receipt = json.loads(
        (root / "resistant.execution.json").read_text(encoding="utf-8")
    )
    assert receipt["termination"] == "killed_process_group"
    pid = int(child_pid.read_text(encoding="utf-8"))
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)
