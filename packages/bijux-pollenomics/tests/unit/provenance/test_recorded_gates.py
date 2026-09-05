from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from tests.support.repository import REPOSITORY_ROOT
import re
import subprocess
import sys

import pytest

from bijux_pollenomics.governance.country_coverage import INPUT_PATHS
from bijux_pollenomics.provenance import gates as gate_module
from bijux_pollenomics.provenance.gates import (
    build_product_gate_specification,
    run_recorded_gate,
)
from bijux_pollenomics.provenance.release_evidence import ReleaseEvidenceError


def _digest(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def _json_digest(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _digest(payload)


def _gate_producer_source_files() -> list[dict[str, object]]:
    package_root = Path(gate_module.__file__).parent
    source_files: list[dict[str, object]] = []
    for path in sorted(
        package_root.rglob("*.py"),
        key=lambda item: item.relative_to(package_root).as_posix(),
    ):
        relative = path.relative_to(package_root)
        components = list(relative.parts)
        if components[-1] == "__init__.py":
            components.pop()
        else:
            components[-1] = path.stem
        payload = path.read_bytes()
        source_files.append(
            {
                "module": ".".join(("bijux_pollenomics.provenance.gates", *components)),
                "sha256": _digest(payload),
                "byte_count": len(payload),
            }
        )
    return source_files


def _input(root: Path) -> None:
    path = root / "inputs/source.txt"
    path.parent.mkdir(parents=True)
    path.write_text("immutable input\n", encoding="utf-8")


def test_product_map_gate_binds_generated_report_tree() -> None:
    repository_root = REPOSITORY_ROOT

    specification = build_product_gate_specification(repository_root, "map")

    assert "docs/report" in specification.input_paths
    assert specification.timeout_seconds == 900.0
    runtime_identity = dict(specification.runtime_identity)
    assert runtime_identity["command_executable_path"].endswith("/pytest")
    assert runtime_identity["command_executable_sha256"].startswith("sha256:")
    assert runtime_identity["runner_python"]
    assert runtime_identity["python_implementation"]
    assert runtime_identity["python_version"]


def test_make_gate_inputs_and_timeout_match_product_specifications() -> None:
    repository_root = REPOSITORY_ROOT
    environment = {
        key: value
        for key, value in os.environ.items()
        if key != "POLLENOMICS_GATE_TIMEOUT_SECONDS"
    }
    completed = subprocess.run(
        ["make", "-pn"],
        cwd=repository_root,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )

    prefixes = {
        "science": "SCIENCE",
        "data": "DATA",
        "map": "MAP",
        "provenance": "PROVENANCE",
        "doc-counts": "DOC_COUNT",
    }
    for gate_id, prefix in prefixes.items():
        match = re.search(
            rf"^POLLENOMICS_{prefix}_INPUTS := (.*)$",
            completed.stdout,
            flags=re.MULTILINE,
        )
        assert match is not None
        make_inputs = tuple(sorted(match.group(1).split()))
        specification = build_product_gate_specification(repository_root, gate_id)
        assert make_inputs == specification.input_paths
        assert specification.timeout_seconds == 900.0
        assert {
            "Makefile",
            "makes/pollenomics-verification.mk",
            "packages/bijux-pollenomics/pyproject.toml",
            "pyproject.toml",
            "uv.lock",
        } <= set(specification.input_paths)
        if gate_id == "doc-counts":
            assert set(INPUT_PATHS) <= set(specification.input_paths)

        for test_name in gate_module._GATE_TESTS[gate_id]:
            test_path = (
                repository_root
                / "packages/bijux-pollenomics/tests/regression/test_docs_breadth.py"
                if test_name.startswith("../regression/")
                else repository_root
                / "packages/bijux-pollenomics/tests/unit"
                / test_name
            )
            assert test_path.exists(), test_path

    assert re.search(
        r"^POLLENOMICS_GATE_TIMEOUT_SECONDS = 900$",
        completed.stdout,
        flags=re.MULTILINE,
    )


def test_gate_inputs_recursively_bind_owned_python_sources() -> None:
    source_root = REPOSITORY_ROOT / "packages/bijux-pollenomics/src/bijux_pollenomics"
    owned_roots = {
        "science": ("analysis", "core", "evidence"),
        "data": ("adna", "collection"),
        "map": ("evidence", "reporting"),
        "provenance": ("provenance",),
        "doc-counts": ("governance", "reporting/review"),
    }

    for gate_id, relative_roots in owned_roots.items():
        specification = build_product_gate_specification(REPOSITORY_ROOT, gate_id)
        expected = {
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for relative_root in relative_roots
            for path in (source_root / relative_root).rglob("*.py")
        }
        assert expected <= set(specification.input_paths)


def test_make_release_evidence_does_not_rerun_recorded_gates() -> None:
    repository_root = REPOSITORY_ROOT

    completed = subprocess.run(
        ["make", "-n", "release-evidence"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert " -m pytest" not in completed.stdout
    assert "provenance.gates" not in completed.stdout
    assert "provenance request" in completed.stdout
    assert "provenance write" in completed.stdout


def test_make_has_explicit_gate_refresh_and_candidate_addressed_outputs() -> None:
    repository_root = REPOSITORY_ROOT
    makefile = (repository_root / "makes/pollenomics-verification.mk").read_text(
        encoding="utf-8"
    )

    assert (
        "refresh-release-gates: verify-science verify-data verify-map "
        "verify-provenance verify-doc-counts"
    ) in makefile
    assert "release-evidence: release-evidence-request" in makefile
    assert "release-evidence: verify-science" not in makefile
    assert "release-evidence/$(POLLENOMICS_RELEASE_CANDIDATE_ID)" in makefile


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
