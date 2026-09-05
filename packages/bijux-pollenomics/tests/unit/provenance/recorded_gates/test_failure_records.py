from __future__ import annotations

from pathlib import Path
import sys

from bijux_pollenomics.provenance.gates import run_recorded_gate

from .support import _input


def test_gate_timeout_is_a_recorded_failure(tmp_path: Path) -> None:
    _input(tmp_path)

    record = run_recorded_gate(
        tmp_path,
        gate_id="timeout",
        argv=[sys.executable, "-c", "import time; time.sleep(1)"],
        environment={},
        input_paths=["inputs/source.txt"],
        artifacts_directory="artifacts/gates",
        timeout_seconds=0.01,
    )

    assert record["exit_code"] is None
    assert record["status"] == "FAIL"
    assert record["reason_code"] == "command_timed_out"


def test_gate_records_command_launch_failure(tmp_path: Path) -> None:
    _input(tmp_path)

    record = run_recorded_gate(
        tmp_path,
        gate_id="missing-command",
        argv=[str(tmp_path / "does-not-exist")],
        environment={},
        input_paths=["inputs/source.txt"],
        artifacts_directory="artifacts/gates",
    )

    assert record["exit_code"] is None
    assert record["status"] == "FAIL"
    assert record["reason_code"] == "command_launch_failed"
    assert "FileNotFoundError" in (
        tmp_path / "artifacts/gates/missing-command.stderr.log"
    ).read_text(encoding="utf-8")


def test_missing_junit_and_changed_input_force_failure(tmp_path: Path) -> None:
    _input(tmp_path)
    missing_junit = run_recorded_gate(
        tmp_path,
        gate_id="missing-junit",
        argv=[sys.executable, "-c", "raise SystemExit(0)"],
        environment={},
        input_paths=["inputs/source.txt"],
        artifacts_directory="artifacts/gates",
        junit_path="artifacts/gates/missing.xml",
    )
    assert missing_junit["status"] == "FAIL"
    assert missing_junit["reason_code"] == "junit_missing"
    assert missing_junit["junit"] == {
        "path": "artifacts/gates/missing.xml",
        "status": "MISSING",
    }

    changed_input = run_recorded_gate(
        tmp_path,
        gate_id="changed-input",
        argv=[
            sys.executable,
            "-c",
            "from pathlib import Path; Path('inputs/source.txt').write_text('changed')",
        ],
        environment={},
        input_paths=["inputs/source.txt"],
        artifacts_directory="artifacts/gates",
    )
    assert changed_input["status"] == "FAIL"
    assert changed_input["reason_code"] == "input_changed_during_gate"

    deleted_input = run_recorded_gate(
        tmp_path,
        gate_id="deleted-input",
        argv=[
            sys.executable,
            "-c",
            "from pathlib import Path; Path('inputs/source.txt').unlink()",
        ],
        environment={},
        input_paths=["inputs/source.txt"],
        artifacts_directory="artifacts/gates",
    )
    assert deleted_input["status"] == "FAIL"
    assert deleted_input["reason_code"] == "input_changed_during_gate"
