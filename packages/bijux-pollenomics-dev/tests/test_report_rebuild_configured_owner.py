"""Contract tests for configured report-owner command and output binding."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild import configured_owner as owner_runner
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError

OWNER_ID = "domain/summary"
MODULE = "bijux_pollenomics_dev.source_completion.example"
MODULE_PATH = (
    "packages/bijux-pollenomics-dev/src/"
    "bijux_pollenomics_dev/source_completion/example.py"
)
PARENT = "docs/report/domain/report.json"
OUTPUT = "docs/report/domain/summary.json"
SECOND_OUTPUT = "docs/report/domain/details.json"


def _write(repository: Path, name: str, content: str) -> None:
    path = repository / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    _write(tmp_path, MODULE_PATH, "# maintained producer\n")
    _write(tmp_path, PARENT, '{"source": 1}\n')
    _write(tmp_path, OUTPUT, '{"summary": 1}\n')
    inventory = {
        "owners": [
            {
                "owner_id": OWNER_ID,
                "role": "generated_owner",
                "paths": [OUTPUT],
                "producer_paths": [MODULE_PATH],
                "producer_inputs": [PARENT],
            }
        ]
    }
    configuration = {
        "schema_version": owner_runner.SCHEMA,
        "owners": [
            {
                "owner_id": OWNER_ID,
                "module": MODULE,
                "source_paths": {"summary.json": OUTPUT},
                "source_arguments": [{"flag": "--screen", "path": PARENT}],
                "output_mode": "single_file",
                "timeout_seconds": 120,
            }
        ],
    }
    _write(tmp_path, "configs/ci/report-ownership.json", json.dumps(inventory))
    _write(
        tmp_path, "configs/ci/report-owner-execution.json", json.dumps(configuration)
    )
    _write(tmp_path, "configs/ci/reproducible-report-build.json", "{}\n")
    monkeypatch.setattr(
        owner_runner, "check_report_ownership", lambda *_args, **_kwargs: None
    )
    return tmp_path


def _modify(
    repository: Path, file: str, modifier: Callable[[dict[str, Any]], None]
) -> None:
    path = repository / f"configs/ci/{file}"
    payload = json.loads(path.read_text(encoding="utf-8"))
    modifier(payload)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _two_outputs(repository: Path) -> None:
    _write(repository, SECOND_OUTPUT, '{"details": 2}\n')
    _modify(
        repository,
        "report-ownership.json",
        lambda p: p["owners"][0].update(paths=sorted([OUTPUT, SECOND_OUTPUT])),
    )
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(
            source_paths={"summary.json": OUTPUT, "details.json": SECOND_OUTPUT},
            output_mode="directory",
        ),
    )


def _copy_output(repository: Path, relative: str) -> None:
    target = (
        repository / "artifacts/owner/output" / relative.removeprefix("docs/report/")
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((repository / relative).read_bytes())


def test_exact_declared_code_and_data_inputs_resolve(repository: Path) -> None:
    resolved = owner_runner.resolve_configured_owner(repository, OWNER_ID)
    assert set(resolved.inputs) == {MODULE_PATH, PARENT}
    assert resolved.source_paths == {"summary.json": "domain/summary.json"}
    assert resolved.expected_outputs == {
        OUTPUT: hashlib.sha256((repository / OUTPUT).read_bytes()).hexdigest()
    }
    assert resolved.command == (
        sys.executable,
        "-c",
        owner_runner.SOURCE_RUNTIME,
        str(repository),
        MODULE,
        "--repository",
        str(repository),
        "--screen",
        str(repository / PARENT),
        "--output",
        "{output_root}/summary.json",
    )
    assert resolved.timeout_seconds == 120


def test_unknown_owner_is_refused(repository: Path) -> None:
    with pytest.raises(ReportRebuildError, match="unknown configured owner"):
        owner_runner.resolve_configured_owner(repository, "domain/other")


def test_absolute_confined_configuration_and_inventory_paths(repository: Path) -> None:
    resolved = owner_runner.resolve_configured_owner(
        repository,
        OWNER_ID,
        configuration_path=repository / "configs/ci/report-owner-execution.json",
        inventory_path=repository / "configs/ci/report-ownership.json",
    )
    assert resolved.owner_id == OWNER_ID


def test_external_configuration_is_refused(repository: Path) -> None:
    with pytest.raises(ReportRebuildError, match="outside the repository"):
        owner_runner.resolve_configured_owner(
            repository,
            OWNER_ID,
            configuration_path=repository.parent / "other-configuration.json",
        )


def test_changed_role_is_refused(repository: Path) -> None:
    _modify(
        repository,
        "report-ownership.json",
        lambda p: p["owners"][0].update(role="unresolved"),
    )
    with pytest.raises(ReportRebuildError, match="not declared generated"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)


def test_changed_output_mapping_is_refused(repository: Path) -> None:
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(source_paths={"summary.json": PARENT}),
    )
    with pytest.raises(ReportRebuildError, match="output map differs"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)


def test_self_fed_output_is_refused(repository: Path) -> None:
    _modify(
        repository,
        "report-ownership.json",
        lambda p: p["owners"][0].update(producer_inputs=[OUTPUT]),
    )
    with pytest.raises(ReportRebuildError, match="feeds its output"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)


def test_module_must_be_declared_producer(repository: Path) -> None:
    _write(
        repository,
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/other.py",
        "\n",
    )
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(
            module="bijux_pollenomics_dev.source_completion.other"
        ),
    )
    with pytest.raises(ReportRebuildError, match="absent from producer paths"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)


def test_source_argument_must_be_declared_input(repository: Path) -> None:
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(
            source_arguments=[{"flag": "--screen", "path": OUTPUT}]
        ),
    )
    with pytest.raises(ReportRebuildError, match="differs from declared input"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)


def test_symlinked_input_ancestor_is_refused(repository: Path) -> None:
    original = repository / "docs/report/domain"
    original.rename(repository / "docs/report/real-domain")
    original.symlink_to("real-domain", target_is_directory=True)
    with pytest.raises(ReportRebuildError, match="non-real ancestor"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)


def test_build_compares_fresh_bytes_without_running_producer(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed: dict[str, object] = {}

    def fake_build(**kwargs: object) -> dict[str, object]:
        observed.update(kwargs)
        target = repository / "artifacts/owner/output/domain/summary.json"
        target.parent.mkdir(parents=True)
        target.write_bytes((repository / OUTPUT).read_bytes())
        return {"owner_id": OWNER_ID, "lane": "reference"}

    monkeypatch.setattr(owner_runner, "build_owner_output", fake_build)
    result = owner_runner.build_configured_owner(
        repository=repository,
        plan_path=repository / "artifacts/plan.json",
        lane="reference",
        owner_id=OWNER_ID,
        evidence_root=repository / "artifacts/owner",
    )
    assert result["owner_id"] == OWNER_ID
    inputs = observed["producer_inputs"]
    assert isinstance(inputs, dict)
    assert set(inputs) == {MODULE_PATH, PARENT}
    assert observed["source_paths"] == {"summary.json": "domain/summary.json"}
    assert observed["timeout_seconds"] == 120


def test_changed_fresh_bytes_are_refused(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_build(**_kwargs: object) -> dict[str, object]:
        target = repository / "artifacts/owner/output/domain/summary.json"
        target.parent.mkdir(parents=True)
        target.write_text("changed\n", encoding="utf-8")
        return {"owner_id": OWNER_ID, "lane": "reference"}

    monkeypatch.setattr(owner_runner, "build_owner_output", fake_build)
    with pytest.raises(ReportRebuildError, match="bytes differ"):
        owner_runner.build_configured_owner(
            repository=repository,
            plan_path=repository / "artifacts/plan.json",
            lane="reference",
            owner_id=OWNER_ID,
            evidence_root=repository / "artifacts/owner",
        )


def test_directory_owner_binds_and_checks_both_outputs(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _two_outputs(repository)
    selected = owner_runner.resolve_configured_owner(repository, OWNER_ID)
    assert selected.source_paths == {
        "summary.json": "domain/summary.json",
        "details.json": "domain/details.json",
    }
    assert list(selected.expected_outputs) == sorted([OUTPUT, SECOND_OUTPUT])
    assert selected.command[-1] == "{output_root}"

    observed: dict[str, object] = {}

    def fake_build(**kwargs: object) -> dict[str, object]:
        observed.update(kwargs)
        for target in (OUTPUT, SECOND_OUTPUT):
            _copy_output(repository, target)
        return {"owner_id": OWNER_ID, "lane": "reference"}

    monkeypatch.setattr(owner_runner, "build_owner_output", fake_build)
    result = owner_runner.build_configured_owner(
        repository=repository,
        plan_path=repository / "artifacts/plan.json",
        lane="reference",
        owner_id=OWNER_ID,
        evidence_root=repository / "artifacts/owner",
    )
    assert result["owner_id"] == OWNER_ID
    assert observed["source_paths"] == selected.source_paths


def test_changed_second_fresh_output_is_refused(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _two_outputs(repository)

    def fake_build(**_kwargs: object) -> dict[str, object]:
        _copy_output(repository, OUTPUT)
        _copy_output(repository, SECOND_OUTPUT)
        (repository / "artifacts/owner/output/domain/details.json").write_text(
            "changed\n", encoding="utf-8"
        )
        return {"owner_id": OWNER_ID, "lane": "reference"}

    monkeypatch.setattr(owner_runner, "build_owner_output", fake_build)
    with pytest.raises(ReportRebuildError, match="bytes differ.*details.json"):
        owner_runner.build_configured_owner(
            repository=repository,
            plan_path=repository / "artifacts/plan.json",
            lane="reference",
            owner_id=OWNER_ID,
            evidence_root=repository / "artifacts/owner",
        )


def test_changed_second_tracked_oracle_is_refused(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _two_outputs(repository)
    original = (repository / SECOND_OUTPUT).read_bytes()

    def fake_build(**_kwargs: object) -> dict[str, object]:
        _copy_output(repository, OUTPUT)
        _copy_output(repository, SECOND_OUTPUT)
        (repository / SECOND_OUTPUT).write_text("changed\n", encoding="utf-8")
        assert (
            repository / "artifacts/owner/output/domain/details.json"
        ).read_bytes() == original
        return {"owner_id": OWNER_ID, "lane": "reference"}

    monkeypatch.setattr(owner_runner, "build_owner_output", fake_build)
    with pytest.raises(ReportRebuildError, match="bytes differ.*details.json"):
        owner_runner.build_configured_owner(
            repository=repository,
            plan_path=repository / "artifacts/plan.json",
            lane="reference",
            owner_id=OWNER_ID,
            evidence_root=repository / "artifacts/owner",
        )


def test_partial_directory_mapping_is_refused(repository: Path) -> None:
    _two_outputs(repository)
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(source_paths={"summary.json": OUTPUT}),
    )
    with pytest.raises(ReportRebuildError, match="output map differs"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)


def test_duplicate_directory_target_is_refused(repository: Path) -> None:
    _two_outputs(repository)
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(
            source_paths={"summary.json": OUTPUT, "details.json": OUTPUT}
        ),
    )
    with pytest.raises(ReportRebuildError, match="duplicate output targets"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)


def test_single_file_owner_refuses_two_outputs(repository: Path) -> None:
    _two_outputs(repository)
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(output_mode="single_file"),
    )
    with pytest.raises(ReportRebuildError, match="single-file.*one output"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)


@pytest.mark.parametrize(
    "field,value",
    [
        ("timeout_seconds", 0),
        ("timeout_seconds", True),
        ("timeout_seconds", 601),
        ("output_mode", []),
        ("module", "other.module"),
    ],
)
def test_malformed_execution_settings_are_refused(
    repository: Path, field: str, value: object
) -> None:
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update({field: value}),
    )
    with pytest.raises(ReportRebuildError):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)


def test_unhashable_source_flag_is_refused(repository: Path) -> None:
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(
            source_arguments=[{"flag": [], "path": PARENT}]
        ),
    )
    with pytest.raises(ReportRebuildError, match="source argument differs"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)


def test_duplicate_configuration_key_is_refused(repository: Path) -> None:
    (repository / "configs/ci/report-owner-execution.json").write_text(
        '{"owners": [], "owners": [], "schema_version": "configured-report-owner-execution.v1"}'
    )
    with pytest.raises(ReportRebuildError, match="duplicate JSON key"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)


@pytest.mark.parametrize("source_missing", [False, True])
def test_child_process_selects_and_checks_candidate_module_origin(
    repository: Path, source_missing: bool
) -> None:
    package = Path(MODULE_PATH).parents[1]
    _write(repository, (package / "__init__.py").as_posix(), "")
    _write(repository, (package / "source_completion/__init__.py").as_posix(), "")
    _write(repository, MODULE_PATH, "print('candidate producer executed')\n")
    resolved = owner_runner.resolve_configured_owner(repository, OWNER_ID)
    foreign = repository / "artifacts/foreign"
    _write(
        foreign,
        (
            package.relative_to("packages/bijux-pollenomics-dev/src") / "__init__.py"
        ).as_posix(),
        "",
    )
    _write(foreign, "bijux_pollenomics_dev/source_completion/__init__.py", "")
    _write(
        foreign,
        "bijux_pollenomics_dev/source_completion/example.py",
        "print('foreign producer executed')\n",
    )
    if source_missing:
        (repository / MODULE_PATH).unlink()
    completed = subprocess.run(
        resolved.command,
        cwd=foreign,
        env=dict(os.environ, PYTHONPATH=str(foreign)),
        capture_output=True,
        timeout=5,
    )
    if source_missing:
        assert completed.returncode != 0
        assert b"foreign producer executed" not in completed.stdout
    else:
        assert completed.returncode == 0
        assert completed.stdout == b"candidate producer executed\n"
        assert str(repository / MODULE_PATH).encode() in completed.stderr
