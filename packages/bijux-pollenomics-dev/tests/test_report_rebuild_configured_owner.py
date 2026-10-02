"""Contract tests for the configured owner proposal; no producer is executed."""

from __future__ import annotations

from collections.abc import Callable
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild import configured_owner as proposal
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError

OWNER_ID = "domain/summary"
MODULE = "bijux_pollenomics_dev.source_completion.example"
MODULE_PATH = (
    "packages/bijux-pollenomics-dev/src/"
    "bijux_pollenomics_dev/source_completion/example.py"
)
PARENT = "docs/report/domain/report.json"
OUTPUT = "docs/report/domain/summary.json"


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
        "schema_version": proposal.SCHEMA,
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
        proposal, "check_report_ownership", lambda *_args, **_kwargs: None
    )
    return tmp_path


def _modify(
    repository: Path, file: str, modifier: Callable[[dict[str, Any]], None]
) -> None:
    path = repository / f"configs/ci/{file}"
    payload = json.loads(path.read_text(encoding="utf-8"))
    modifier(payload)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_exact_declared_code_and_data_inputs_resolve(repository: Path) -> None:
    resolved = proposal.resolve_configured_owner(repository, OWNER_ID)
    assert set(resolved.inputs) == {MODULE_PATH, PARENT}
    assert resolved.source_paths == {"summary.json": "domain/summary.json"}
    assert resolved.command == (
        sys.executable,
        "-c",
        proposal.SOURCE_RUNTIME,
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
        proposal.resolve_configured_owner(repository, "domain/other")


def test_absolute_confined_configuration_and_inventory_paths(repository: Path) -> None:
    resolved = proposal.resolve_configured_owner(
        repository,
        OWNER_ID,
        configuration_path=repository / "configs/ci/report-owner-execution.json",
        inventory_path=repository / "configs/ci/report-ownership.json",
    )
    assert resolved.owner_id == OWNER_ID


def test_external_configuration_is_refused(repository: Path) -> None:
    with pytest.raises(ReportRebuildError, match="outside the repository"):
        proposal.resolve_configured_owner(
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
        proposal.resolve_configured_owner(repository, OWNER_ID)


def test_changed_output_mapping_is_refused(repository: Path) -> None:
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(source_paths={"summary.json": PARENT}),
    )
    with pytest.raises(ReportRebuildError, match="output map differs"):
        proposal.resolve_configured_owner(repository, OWNER_ID)


def test_self_fed_output_is_refused(repository: Path) -> None:
    _modify(
        repository,
        "report-ownership.json",
        lambda p: p["owners"][0].update(producer_inputs=[OUTPUT]),
    )
    with pytest.raises(ReportRebuildError, match="feeds its output"):
        proposal.resolve_configured_owner(repository, OWNER_ID)


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
        proposal.resolve_configured_owner(repository, OWNER_ID)


def test_source_argument_must_be_declared_input(repository: Path) -> None:
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(
            source_arguments=[{"flag": "--screen", "path": OUTPUT}]
        ),
    )
    with pytest.raises(ReportRebuildError, match="differs from declared input"):
        proposal.resolve_configured_owner(repository, OWNER_ID)


def test_symlinked_input_ancestor_is_refused(repository: Path) -> None:
    original = repository / "docs/report/domain"
    original.rename(repository / "docs/report/real-domain")
    original.symlink_to("real-domain", target_is_directory=True)
    with pytest.raises(ReportRebuildError, match="non-real ancestor"):
        proposal.resolve_configured_owner(repository, OWNER_ID)


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

    monkeypatch.setattr(proposal, "build_owner_output", fake_build)
    result = proposal.build_configured_owner(
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

    monkeypatch.setattr(proposal, "build_owner_output", fake_build)
    with pytest.raises(ReportRebuildError, match="bytes differ"):
        proposal.build_configured_owner(
            repository=repository,
            plan_path=repository / "artifacts/plan.json",
            lane="reference",
            owner_id=OWNER_ID,
            evidence_root=repository / "artifacts/owner",
        )


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
        proposal.resolve_configured_owner(repository, OWNER_ID)


def test_unhashable_source_flag_is_refused(repository: Path) -> None:
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(
            source_arguments=[{"flag": [], "path": PARENT}]
        ),
    )
    with pytest.raises(ReportRebuildError, match="source argument differs"):
        proposal.resolve_configured_owner(repository, OWNER_ID)


def test_duplicate_configuration_key_is_refused(repository: Path) -> None:
    (repository / "configs/ci/report-owner-execution.json").write_text(
        '{"owners": [], "owners": [], "schema_version": "configured-report-owner-execution.v1"}'
    )
    with pytest.raises(ReportRebuildError, match="duplicate JSON key"):
        proposal.resolve_configured_owner(repository, OWNER_ID)


@pytest.mark.parametrize("source_missing", [False, True])
def test_child_process_selects_and_checks_candidate_module_origin(
    repository: Path, source_missing: bool
) -> None:
    package = Path(MODULE_PATH).parents[1]
    _write(repository, (package / "__init__.py").as_posix(), "")
    _write(repository, (package / "source_completion/__init__.py").as_posix(), "")
    _write(repository, MODULE_PATH, "print('candidate producer executed')\n")
    resolved = proposal.resolve_configured_owner(repository, OWNER_ID)
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
