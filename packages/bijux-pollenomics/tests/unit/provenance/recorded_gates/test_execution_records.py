from __future__ import annotations

import json
from pathlib import Path
import sys

from bijux_pollenomics.provenance.gates import run_recorded_gate

from .support import _digest, _gate_producer_source_files, _input, _json_digest


def test_gate_runs_exact_argv_and_records_canonical_logs(tmp_path: Path) -> None:
    _input(tmp_path)
    junit = "artifacts/gates/unit.junit.xml"
    argv = [
        sys.executable,
        "-c",
        (
            "from pathlib import Path; import sys; "
            "Path(sys.argv[1]).write_text('<testsuite/>\\n'); "
            "print('out'); print('err', file=sys.stderr)"
        ),
        junit,
    ]

    record = run_recorded_gate(
        tmp_path,
        gate_id="unit",
        argv=argv,
        environment={"PYTHONIOENCODING": "utf-8"},
        input_paths=["inputs/source.txt"],
        artifacts_directory="artifacts/gates",
        junit_path=junit,
    )

    directory = tmp_path / "artifacts/gates"
    assert record["argv"] == argv
    assert record["exit_code"] == 0
    assert record["status"] == "PASS"
    assert record["reason_code"] == "command_passed"
    assert record["schema_version"] == "recorded-gate.v4"
    assert record["attestation"] == {
        "class": "local_self_attestation",
        "independent_execution_attested": False,
        "external_authority_id": None,
    }
    producer = record["producer"]
    assert isinstance(producer, dict)
    source_files = producer["source_files"]
    assert isinstance(source_files, list)
    expected_source_files = _gate_producer_source_files()
    producer_content = {
        "identity": "bijux-pollenomics.recorded-gate",
        "version": "4",
        "source_files": expected_source_files,
        "source_digest": _json_digest(expected_source_files),
    }
    assert source_files == expected_source_files
    assert producer == {**producer_content, "digest": _json_digest(producer_content)}
    assert isinstance(record["duration_monotonic_ns"], int)
    assert record["timeout_seconds"] is None
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
    assert first["environment"] == {"A": "first", "Z": "last"}


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
