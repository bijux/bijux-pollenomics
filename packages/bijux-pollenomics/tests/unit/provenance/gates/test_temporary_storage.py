"""Temporary execution storage remains private, bounded and source-authenticated."""

from __future__ import annotations

import json
from pathlib import Path
import shlex
import subprocess
import sys

import pytest

from bijux_pollenomics.provenance.gate_runner import _environment, _parser
from bijux_pollenomics.provenance.gates import (
    build_product_gate_specification,
    run_recorded_gate,
)
from bijux_pollenomics.provenance.gates.temporary import (
    main,
    prepare_execution_temporary_directories,
    prepare_temporary_directory,
    temporary_paths,
)
from bijux_pollenomics.provenance.release_evidence import ReleaseEvidenceError
from tests.support.repository import REPOSITORY_ROOT


@pytest.mark.parametrize("gate", ["science", "data", "map", "provenance"])
def test_specification_describes_private_storage_without_writing(
    tmp_path: Path, gate: str
) -> None:
    specification = build_product_gate_specification(tmp_path, gate)
    temporary, basetemp = temporary_paths(
        tmp_path, specification.artifacts_directory, gate
    )

    assert dict(specification.environment)["TMPDIR"] == str(temporary)
    assert specification.argv[specification.argv.index("--basetemp") + 1] == str(
        basetemp
    )
    assert not (tmp_path / "artifacts").exists()


def test_private_shard_roots_are_disjoint_from_each_other(tmp_path: Path) -> None:
    roots = [
        path
        for identity in ("doc-count-plan", "doc-count-0", "doc-count-1", "doc-counts")
        for path in temporary_paths(
            tmp_path, "artifacts/release-verification/gates", identity
        )
    ]
    assert len(set(roots)) == 8
    assert not any(a.is_relative_to(b) for a in roots for b in roots if a != b)
    assert not (tmp_path / "artifacts").exists()


def test_doc_count_specification_is_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.provenance.gates import specification

    monkeypatch.setattr(specification, "_head_revision", lambda _root: "a" * 40)
    described = build_product_gate_specification(tmp_path, "doc-counts")
    temporary, _ = temporary_paths(
        tmp_path, described.artifacts_directory, "doc-counts"
    )
    assert dict(described.environment)["TMPDIR"] == str(temporary)
    assert "--basetemp" not in described.argv
    assert not (tmp_path / "artifacts").exists()


@pytest.mark.parametrize("form", ["relative", "outside", "traversal", "bare-artifacts"])
def test_writer_refuses_unowned_or_ambiguous_storage(tmp_path: Path, form: str) -> None:
    path = {
        "relative": Path("artifacts/private/tmp"),
        "outside": tmp_path.parent / "outside-tmp",
        "traversal": tmp_path / "artifacts/private/../tmp",
        "bare-artifacts": tmp_path / "artifacts",
    }[form]
    with pytest.raises(ReleaseEvidenceError):
        prepare_temporary_directory(tmp_path, path)
    assert not (tmp_path / "artifacts").exists()


@pytest.mark.parametrize("member", ["symlink", "file"])
def test_writer_refuses_unsafe_existing_ancestors(tmp_path: Path, member: str) -> None:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    blocked = artifacts / "blocked"
    if member == "symlink":
        target = tmp_path / "external"
        target.mkdir()
        blocked.symlink_to(target, target_is_directory=True)
    else:
        blocked.write_text("protected")
    with pytest.raises(ReleaseEvidenceError):
        prepare_temporary_directory(tmp_path, blocked / "tmp")
    assert not (tmp_path / "external/tmp").exists()


@pytest.mark.parametrize("form", ["duplicate", "ancestor", "descendant", "outside"])
def test_execution_preflight_refuses_aliasing_before_creating_any_root(
    tmp_path: Path, form: str
) -> None:
    temporary = tmp_path / "artifacts/private/tmp"
    base = {
        "duplicate": temporary,
        "ancestor": temporary.parent,
        "descendant": temporary / "pytest",
        "outside": tmp_path.parent / "outside-pytest",
    }[form]
    with pytest.raises(ReleaseEvidenceError):
        prepare_execution_temporary_directories(
            tmp_path, ["pytest", "--basetemp", str(base)], {"TMPDIR": str(temporary)}
        )
    assert not (tmp_path / "artifacts").exists()


@pytest.mark.parametrize("equal_form", [False, True])
def test_execution_writer_prepares_both_explicit_pytest_forms(
    tmp_path: Path, equal_form: bool
) -> None:
    temporary, base = temporary_paths(tmp_path, "artifacts/gates", "science")
    arguments = [f"--basetemp={base}"] if equal_form else ["--basetemp", str(base)]
    prepare_execution_temporary_directories(
        tmp_path, ["pytest", *arguments], {"TMPDIR": str(temporary)}
    )
    assert temporary.is_dir() and base.is_dir()


def test_nonpytest_literal_argument_does_not_become_a_directory(tmp_path: Path) -> None:
    path = tmp_path / "artifacts/literal"
    prepare_execution_temporary_directories(
        tmp_path, [sys.executable, "script.py", "--basetemp", str(path)], {}
    )
    assert not path.exists()


def test_missing_pytest_basetemp_argument_refuses(tmp_path: Path) -> None:
    with pytest.raises(ReleaseEvidenceError):
        prepare_execution_temporary_directories(tmp_path, ["pytest", "--basetemp"], {})


def test_direct_shard_writer_prepares_exact_directories(tmp_path: Path) -> None:
    temporary, base = temporary_paths(tmp_path, "artifacts/gates", "doc-count-1")
    assert (
        main(
            [
                "--repository-root",
                str(tmp_path),
                "--directory",
                str(temporary),
                "--directory",
                str(base),
            ]
        )
        == 0
    )
    assert temporary.is_dir() and base.is_dir()


def test_real_child_tempfile_uses_declared_owned_directory(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("protected")
    temporary = tmp_path / "artifacts/gates/temporary/science/tmp"
    junit = "artifacts/gates/science.junit.xml"
    script = (
        "import pathlib,tempfile; "
        "p=pathlib.Path(tempfile.mkdtemp()); print(p); "
        f"pathlib.Path({junit!r}).write_text('<testsuite/>')"
    )
    command = [sys.executable, "-c", script]
    environment = {"TMPDIR": str(temporary), "PYTHONIOENCODING": "utf-8"}
    record = run_recorded_gate(
        tmp_path,
        gate_id="science",
        argv=command,
        environment=environment,
        input_paths=["source.txt"],
        artifacts_directory="artifacts/gates",
        junit_path=junit,
    )
    child_path = Path(
        (tmp_path / "artifacts/gates/science.stdout.log").read_text().strip()
    )
    assert child_path.is_relative_to(temporary) and child_path.is_dir()
    assert record["status"] == "PASS"
    assert record["argv"] == command and record["environment"] == environment


@pytest.mark.parametrize("gate", ["science", "data", "map", "provenance"])
def test_make_exact_execution_contract_matches_current_specification(
    tmp_path: Path, gate: str
) -> None:
    prefix = {
        "science": "SCIENCE",
        "data": "DATA",
        "map": "MAP",
        "provenance": "PROVENANCE",
    }[gate]
    query = tmp_path / "inspect.mk"
    query.write_text(
        ".PHONY: inspect-recorded-gate\ninspect-recorded-gate:\n"
        f"\t$(call run_pollenomics_pytest_gate,{gate},$(POLLENOMICS_{prefix}_TESTS),$(POLLENOMICS_{prefix}_INPUTS))\n"
    )
    output = subprocess.check_output(
        [
            "make",
            "--no-print-directory",
            "-n",
            "-f",
            "makes/pollenomics-verification.mk",
            "-f",
            str(query),
            "inspect-recorded-gate",
            f"ROOT_CHECK_VENV={REPOSITORY_ROOT}/artifacts/root/check-venv",
        ],
        cwd=REPOSITORY_ROOT,
        text=True,
    )
    words = shlex.split(output.replace("\\\n", " "))
    arguments = _parser().parse_args(words[words.index("--repository-root") :])
    specification = build_product_gate_specification(REPOSITORY_ROOT, gate)
    assert arguments.command_argv[1:] == list(specification.argv)
    assert _environment(arguments.environment) == dict(specification.environment)
    assert sorted(arguments.input) == list(specification.input_paths)
    assert arguments.timeout_seconds == specification.timeout_seconds
    assert json.loads(json.dumps(dict(specification.environment)))["TMPDIR"]
