from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

from bijux_pollenomics.provenance.gate_runner import main


def _arguments(root: Path, command: list[str]) -> list[str]:
    source = root / "inputs/source.txt"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("stable\n", encoding="utf-8")
    return [
        "--repository-root",
        str(root),
        "--gate-id",
        "science",
        "--artifacts-directory",
        "artifacts/execution-control/gates",
        "--junit-path",
        "artifacts/execution-control/gates/science.junit.xml",
        "--input",
        "inputs/source.txt",
        "--environment",
        "PYTHONIOENCODING=utf-8",
        "--",
        *command,
    ]


def test_runner_preserves_exact_command_and_returns_success(
    tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    junit = "artifacts/execution-control/gates/science.junit.xml"
    command = [
        sys.executable,
        "-c",
        (
            "from pathlib import Path; import sys; "
            "Path(sys.argv[1]).write_text('<testsuite/>\\n'); print(sys.argv[2])"
        ),
        junit,
        "literal argument with spaces",
    ]

    result = main(_arguments(tmp_path, command))
    summary = json.loads(capfd.readouterr().out)
    record = json.loads(
        (tmp_path / "artifacts/execution-control/gates/science.json").read_text(
            encoding="utf-8"
        )
    )

    assert result == 0
    assert summary["status"] == "PASS"
    assert record["argv"] == command
    assert record["environment"] == {"PYTHONIOENCODING": "utf-8"}
    assert (
        tmp_path / "artifacts/execution-control/gates/science.stdout.log"
    ).read_text(encoding="utf-8") == "literal argument with spaces\n"


def test_runner_replaces_only_its_previous_regular_junit(
    tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    junit = tmp_path / "artifacts/execution-control/gates/science.junit.xml"
    junit.parent.mkdir(parents=True)
    junit.write_text("stale\n", encoding="utf-8")
    command = [
        sys.executable,
        "-c",
        "from pathlib import Path; Path('artifacts/execution-control/gates/science.junit.xml').write_text('<testsuite/>\\n')",
    ]

    first = main(_arguments(tmp_path, command))
    capfd.readouterr()
    second = main(_arguments(tmp_path, command))
    capfd.readouterr()

    assert first == second == 0
    assert junit.read_text(encoding="utf-8") == "<testsuite/>\n"


def test_runner_returns_failure_status_without_hiding_record(
    tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    command = [
        sys.executable,
        "-c",
        "from pathlib import Path; Path('artifacts/execution-control/gates/science.junit.xml').write_text('<testsuite failures=\"1\"/>\\n'); raise SystemExit(5)",
    ]

    result = main(_arguments(tmp_path, command))
    summary = json.loads(capfd.readouterr().out)

    assert result == 1
    assert summary["status"] == "FAIL"
    assert (tmp_path / "artifacts/execution-control/gates/science.json").is_file()


def test_runner_refuses_duplicate_environment_and_unsafe_junit(
    tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    command = [sys.executable, "-c", "raise SystemExit(0)"]
    arguments = _arguments(tmp_path, command)
    separator = arguments.index("--")
    arguments[separator:separator] = ["--environment", "PYTHONIOENCODING=ascii"]

    duplicate_result = main(arguments)
    duplicate_error = capfd.readouterr().err

    unsafe = _arguments(tmp_path, command)
    unsafe[unsafe.index("artifacts/execution-control/gates/science.junit.xml")] = (
        "artifacts/outside.xml"
    )
    unsafe_result = main(unsafe)
    unsafe_error = capfd.readouterr().err

    assert duplicate_result == unsafe_result == 2
    assert "duplicate environment" in duplicate_error
    assert "JUnit path" in unsafe_error
