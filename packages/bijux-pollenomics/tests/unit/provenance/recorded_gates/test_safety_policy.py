from __future__ import annotations

import sys
from pathlib import Path

import pytest
from bijux_pollenomics.provenance.gates import run_recorded_gate
from bijux_pollenomics.provenance.release_evidence import ReleaseEvidenceError

from .support import _input


@pytest.mark.parametrize(
    ("payload", "reason_code"),
    [
        ('<testsuite failures="1"/>', "junit_failed"),
        ('<testsuite errors="1"/>', "junit_failed"),
        ('<testsuite skipped="1"/>', "junit_failed"),
        ("not XML", "junit_invalid"),
    ],
)
def test_nonpassing_or_invalid_junit_overrides_zero_exit(
    tmp_path: Path, payload: str, reason_code: str
) -> None:
    _input(tmp_path)
    junit = "artifacts/gates/result.xml"
    script = (
        "from pathlib import Path; import sys; "
        f"Path(sys.argv[1]).write_text({payload!r})"
    )

    record = run_recorded_gate(
        tmp_path,
        gate_id="junit-semantics",
        argv=[sys.executable, "-c", script, junit],
        environment={"PYTHONIOENCODING": "utf-8"},
        input_paths=["inputs/source.txt"],
        artifacts_directory="artifacts/gates",
        junit_path=junit,
    )

    assert record["exit_code"] == 0
    assert record["status"] == "FAIL"
    assert record["reason_code"] == reason_code


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


def test_gate_refuses_empty_input_inventory(tmp_path: Path) -> None:
    with pytest.raises(ReleaseEvidenceError, match="at least one gate input"):
        run_recorded_gate(
            tmp_path,
            gate_id="empty-inputs",
            argv=[sys.executable, "-c", "raise SystemExit(0)"],
            environment={},
            input_paths=[],
            artifacts_directory="artifacts/gates",
        )
