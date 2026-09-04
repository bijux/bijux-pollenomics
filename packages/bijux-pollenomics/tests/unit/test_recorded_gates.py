from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

from bijux_pollenomics.provenance.gates import run_recorded_gate
from bijux_pollenomics.provenance.release_evidence import ReleaseEvidenceError


def _digest(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def _input(root: Path) -> None:
    path = root / "inputs/source.txt"
    path.parent.mkdir(parents=True)
    path.write_text("immutable input\n", encoding="utf-8")


def test_gate_runs_exact_argv_and_records_canonical_logs(tmp_path: Path) -> None:
    _input(tmp_path)
    argv = [
        sys.executable,
        "-c",
        "import sys; print('out'); print('err', file=sys.stderr)",
    ]

    record = run_recorded_gate(
        tmp_path,
        gate_id="unit",
        argv=argv,
        environment={"PYTHONIOENCODING": "utf-8"},
        input_paths=["inputs/source.txt"],
        artifacts_directory="artifacts/gates",
    )

    directory = tmp_path / "artifacts/gates"
    assert record["argv"] == argv
    assert record["exit_code"] == 0
    assert record["status"] == "PASS"
    assert record["reason_code"] == "command_passed"
    assert isinstance(record["duration_monotonic_ns"], int)
    assert record["duration_monotonic_ns"] >= 0
    assert (directory / "unit.stdout.log").read_text(encoding="utf-8") == "out\n"
    assert (directory / "unit.stderr.log").read_text(encoding="utf-8") == "err\n"
    assert not list(directory.glob("*.writing"))
    stored = json.loads((directory / "unit.json").read_text(encoding="utf-8"))
    assert stored == record
    expected = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
    assert (directory / "unit.json").read_text(encoding="utf-8") == expected


def test_gate_records_failure_and_junit_passthrough(tmp_path: Path) -> None:
    _input(tmp_path)
    junit = "artifacts/gates/results.xml"
    script = (
        "from pathlib import Path; import sys; "
        "Path(sys.argv[1]).write_text('<testsuite failures=\"1\"/>\\n'); "
        "raise SystemExit(7)"
    )
    argv = [sys.executable, "-c", script, junit]

    record = run_recorded_gate(
        tmp_path,
        gate_id="failing",
        argv=argv,
        environment={"PYTHONIOENCODING": "utf-8"},
        input_paths=["inputs/source.txt"],
        artifacts_directory="artifacts/gates",
        junit_path=junit,
    )

    assert record["exit_code"] == 7
    assert record["status"] == "FAIL"
    assert record["reason_code"] == "command_failed"
    assert record["junit"] == {
        "path": junit,
        "object_type": "file",
        "output_digest": _digest(b'<testsuite failures="1"/>\n'),
        "byte_size": 26,
        "file_count": 1,
    }


def test_command_environment_and_input_digests_are_reproducible(tmp_path: Path) -> None:
    _input(tmp_path)
    argv = [sys.executable, "-c", "raise SystemExit(0)"]
    first = run_recorded_gate(
        tmp_path,
        gate_id="first",
        argv=argv,
        environment={"Z": "last", "A": "first"},
        input_paths=["inputs/source.txt"],
        artifacts_directory="artifacts/gates",
    )
    second = run_recorded_gate(
        tmp_path,
        gate_id="second",
        argv=argv,
        environment={"A": "first", "Z": "last"},
        input_paths=["inputs/source.txt"],
        artifacts_directory="artifacts/gates",
    )

    assert first["command_digest"] == second["command_digest"]
    assert first["environment_digest"] == second["environment_digest"]
    assert first["input_digest"] == second["input_digest"]
    assert first["environment_keys"] == ["A", "Z"]


def test_gate_uses_only_the_explicit_environment(tmp_path: Path) -> None:
    _input(tmp_path)
    script = "import os; print(os.environ.get('GATE_SENTINEL')); print(os.environ.get('HOME'))"

    run_recorded_gate(
        tmp_path,
        gate_id="environment",
        argv=[sys.executable, "-c", script],
        environment={"GATE_SENTINEL": "present", "PYTHONIOENCODING": "utf-8"},
        input_paths=["inputs/source.txt"],
        artifacts_directory="artifacts/gates",
    )

    assert (tmp_path / "artifacts/gates/environment.stdout.log").read_text(
        encoding="utf-8"
    ) == "present\nNone\n"


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


@pytest.mark.parametrize(
    "artifacts_directory",
    ["gate-output", "../artifacts/gates", "artifacts/../gates"],
)
def test_gate_refuses_output_outside_artifacts(
    tmp_path: Path, artifacts_directory: str
) -> None:
    _input(tmp_path)

    with pytest.raises(ReleaseEvidenceError):
        run_recorded_gate(
            tmp_path,
            gate_id="unsafe",
            argv=[sys.executable, "-c", "raise SystemExit(0)"],
            environment={},
            input_paths=["inputs/source.txt"],
            artifacts_directory=artifacts_directory,
        )


def test_gate_refuses_junit_outside_its_artifacts_directory(tmp_path: Path) -> None:
    _input(tmp_path)

    with pytest.raises(ReleaseEvidenceError, match="JUnit path"):
        run_recorded_gate(
            tmp_path,
            gate_id="unsafe-junit",
            argv=[sys.executable, "-c", "raise SystemExit(0)"],
            environment={},
            input_paths=["inputs/source.txt"],
            artifacts_directory="artifacts/gates",
            junit_path="artifacts/other/results.xml",
        )
