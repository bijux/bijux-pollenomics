"""Contract tests for configured report-owner command and output binding."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild import configured_owner as owner_runner
from bijux_pollenomics_dev.ci.report_rebuild import scheduling
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.evidence import producer_input_identity
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.ci.report_rebuild.verification import (
    _require_current_owner_inputs,
)

OWNER_ID = "domain/summary"
MODULE = "bijux_pollenomics_dev.source_completion.example"
MODULE_PATH = (
    "packages/bijux-pollenomics-dev/src/"
    "bijux_pollenomics_dev/source_completion/example.py"
)
PARENT = "docs/report/domain/report.json"
SECOND_INPUT = "docs/report/domain/source.json"
OUTPUT = "docs/report/domain/summary.json"
SECOND_OUTPUT = "docs/report/domain/details.json"
EXTERNAL_DESCRIPTOR = "configs/ci/qualified-report-sources/legacyage.json"


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


def _fresh_output_subdirectory(repository: Path, subdirectory: str) -> None:
    _two_outputs(repository)
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(
            source_paths={
                f"{subdirectory}/summary.json": OUTPUT,
                f"{subdirectory}/details.json": SECOND_OUTPUT,
            },
            output_subdirectory=subdirectory,
        ),
    )


def _copy_output(repository: Path, relative: str) -> None:
    target = (
        repository / "artifacts/owner/output" / relative.removeprefix("docs/report/")
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((repository / relative).read_bytes())


def test_analysis_value_components_use_absent_child_output() -> None:
    repository = Path(__file__).resolve().parents[3]
    selected = owner_runner.resolve_configured_owner(
        repository, "source-relations/sead/analysis-value-components/report-products"
    )
    assert selected.command[-1] == "{output_root}/source-products"
    assert selected.source_paths == {
        "source-products/report.json": "source-relations/sead/analysis-value-components/report.json",
        "source-products/rows.csv": "source-relations/sead/analysis-value-components/rows.csv",
    }
    assert len(selected.inputs) == 1042


def test_neotoma_entity_map_assets_resolve_as_code_only() -> None:
    repository = Path(__file__).resolve().parents[3]
    owner_id = "regions/nordic/source-capability/neotoma-entities/derived-products"
    inventory = json.loads(
        (repository / "configs/ci/report-ownership.json").read_text()
    )
    declaration = next(
        row for row in inventory["owners"] if row["owner_id"] == owner_id
    )
    assets = {
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/"
        + name
        for name in (
            "document.html",
            "native-lra.js",
            "source-record-export.js",
            "url-state.js",
        )
    }
    assert assets <= set(declaration["producer_paths"])
    assert assets.isdisjoint(declaration["producer_inputs"])
    resolved = owner_runner.resolve_configured_owner(repository, owner_id)
    assert assets <= set(resolved.inputs)
    assert set(resolved.inputs) == set(declaration["producer_paths"]) | set(
        declaration["producer_inputs"]
    )


def test_owner_schedule_refuses_overlapping_code_and_data(repository: Path) -> None:
    _modify(
        repository,
        "report-ownership.json",
        lambda payload: payload["owners"][0].update(
            producer_inputs=[MODULE_PATH, PARENT]
        ),
    )
    with pytest.raises(
        ReportRebuildError, match="owner producer and data paths overlap"
    ):
        scheduling.configured_owner_schedule(repository)


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


@pytest.mark.parametrize("include_repository_argument", [None, True])
def test_existing_producer_repository_argument_is_preserved(
    repository: Path, include_repository_argument: bool | None
) -> None:
    if include_repository_argument is not None:
        _modify(
            repository,
            "report-owner-execution.json",
            lambda p: p["owners"][0].update(include_repository_argument=True),
        )
    command = owner_runner.resolve_configured_owner(repository, OWNER_ID).command
    assert command[3:7] == (
        str(repository),
        MODULE,
        "--repository",
        str(repository),
    )


def test_explicit_false_omits_only_producer_repository_argument(
    repository: Path,
) -> None:
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(include_repository_argument=False),
    )
    command = owner_runner.resolve_configured_owner(repository, OWNER_ID).command
    assert command[3:5] == (str(repository), MODULE)
    assert "--repository" not in command
    assert command[5:] == (
        "--screen",
        str(repository / PARENT),
        "--output",
        "{output_root}/summary.json",
    )


@pytest.mark.parametrize("value", [None, 0, 1, "false", [], {}])
def test_repository_argument_option_requires_exact_boolean(
    repository: Path, value: object
) -> None:
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(include_repository_argument=value),
    )
    with pytest.raises(ReportRebuildError, match="must be a boolean"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)


def test_unknown_configuration_field_is_refused(repository: Path) -> None:
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(arbitrary_argv=["--anything"]),
    )
    with pytest.raises(ReportRebuildError, match="fields differ"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)


@pytest.mark.parametrize(
    "flag",
    [
        "--raw-part",
        "--raw-manifest",
        "--workbook",
        "--workbook-receipt",
        "--count-mass",
        "--projection",
        "--receipt",
        "--sites",
    ],
)
def test_native_source_flags_accept_only_declared_source_paths(
    repository: Path, flag: str
) -> None:
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(
            include_repository_argument=False,
            source_arguments=[{"flag": flag, "path": PARENT}],
        ),
    )
    command = owner_runner.resolve_configured_owner(repository, OWNER_ID).command
    assert command[5:7] == (flag, str(repository / PARENT))
    assert "--repository" not in command


@pytest.mark.parametrize("flag", ["--output", "--repository", "--arbitrary"])
def test_undeclared_source_flag_is_refused(repository: Path, flag: str) -> None:
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(
            source_arguments=[{"flag": flag, "path": PARENT}]
        ),
    )
    with pytest.raises(ReportRebuildError, match="source argument differs"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)


def test_native_flag_cannot_name_undeclared_source(repository: Path) -> None:
    _write(repository, SECOND_INPUT, '{"source": 2}\n')
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(
            source_arguments=[{"flag": "--sites", "path": SECOND_INPUT}]
        ),
    )
    with pytest.raises(ReportRebuildError, match="source argument differs"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)


def test_two_distinct_native_flags_bind_two_declared_inputs(repository: Path) -> None:
    _write(repository, SECOND_INPUT, '{"source": 2}\n')
    _modify(
        repository,
        "report-ownership.json",
        lambda p: p["owners"][0].update(producer_inputs=sorted([PARENT, SECOND_INPUT])),
    )
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(
            include_repository_argument=False,
            source_arguments=[
                {"flag": "--raw-part", "path": PARENT},
                {"flag": "--raw-manifest", "path": SECOND_INPUT},
            ],
        ),
    )
    selected = owner_runner.resolve_configured_owner(repository, OWNER_ID)
    assert set(selected.inputs) == {MODULE_PATH, PARENT, SECOND_INPUT}
    assert selected.command[5:] == (
        "--raw-part",
        str(repository / PARENT),
        "--raw-manifest",
        str(repository / SECOND_INPUT),
        "--output",
        "{output_root}/summary.json",
    )


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


@pytest.mark.parametrize("subdirectory", ["source-products", "nested/source-products"])
def test_fresh_subdirectory_binds_two_outputs(
    repository: Path, monkeypatch: pytest.MonkeyPatch, subdirectory: str
) -> None:
    _fresh_output_subdirectory(repository, subdirectory)
    selected = owner_runner.resolve_configured_owner(repository, OWNER_ID)
    assert selected.command[-1] == f"{{output_root}}/{subdirectory}"
    assert selected.source_paths == {
        f"{subdirectory}/summary.json": "domain/summary.json",
        f"{subdirectory}/details.json": "domain/details.json",
    }
    observed: dict[str, object] = {}

    def fake_build(**kwargs: object) -> dict[str, object]:
        observed.update(kwargs)
        _copy_output(repository, OUTPUT)
        _copy_output(repository, SECOND_OUTPUT)
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
    assert observed["producer_command"] == selected.command


def test_fixture_producer_requires_absent_child_directory(repository: Path) -> None:
    _fresh_output_subdirectory(repository, "source-products")
    package = Path(MODULE_PATH).parents[1]
    _write(repository, (package / "__init__.py").as_posix(), "")
    _write(repository, (package / "source_completion/__init__.py").as_posix(), "")
    _write(
        repository,
        MODULE_PATH,
        "from pathlib import Path\n"
        "import argparse\n"
        "parser = argparse.ArgumentParser()\n"
        "parser.add_argument('--repository', required=True)\n"
        "parser.add_argument('--screen', required=True)\n"
        "parser.add_argument('--output', type=Path, required=True)\n"
        "args = parser.parse_args()\n"
        "if args.output.exists():\n"
        "    raise SystemExit('output directory already exists')\n"
        "args.output.mkdir(parents=True)\n"
        "(args.output / 'summary.json').write_text('{\"summary\": 1}\\n')\n"
        "(args.output / 'details.json').write_text('{\"details\": 2}\\n')\n",
    )
    selected = owner_runner.resolve_configured_owner(repository, OWNER_ID)
    producer_root = repository / "artifacts/producer-output"
    producer_root.mkdir(parents=True)
    assert not (producer_root / "source-products").exists()
    command = tuple(
        arg.replace("{output_root}", str(producer_root)) for arg in selected.command
    )
    completed = subprocess.run(
        command,
        cwd=repository,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert str(repository / MODULE_PATH) in completed.stderr
    for output in (OUTPUT, SECOND_OUTPUT):
        produced = producer_root / "source-products" / Path(output).name
        assert produced.read_bytes() == (repository / output).read_bytes()


@pytest.mark.parametrize(
    "subdirectory",
    [
        "",
        None,
        False,
        "../outside",
        "/absolute",
        ".",
        "a//b",
        "a/./b",
        "a/../b",
        "a\\b",
    ],
)
def test_output_subdirectory_must_be_canonical(
    repository: Path, subdirectory: object
) -> None:
    _two_outputs(repository)
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(output_subdirectory=subdirectory),
    )
    with pytest.raises(ReportRebuildError, match="output subdirectory"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)


def test_single_file_rejects_output_subdirectory(repository: Path) -> None:
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(output_subdirectory="source-products"),
    )
    with pytest.raises(ReportRebuildError, match="requires directory output mode"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)


def test_produced_map_must_stay_within_output_subdirectory(repository: Path) -> None:
    _two_outputs(repository)
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(output_subdirectory="source-products"),
    )
    with pytest.raises(
        ReportRebuildError, match="outside configured output subdirectory"
    ):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)


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


def test_schedule_cli_appends_exact_owner_outputs_without_running_producer(
    repository: Path,
) -> None:
    output = repository / "artifacts/schedule.json"
    github = repository / "artifacts/github-output"
    github.parent.mkdir(parents=True)
    github.write_text("scope_partitions=[]\n")
    assert (
        scheduling.main(
            [
                "--repository",
                str(repository),
                "--output",
                str(output),
                "--github-output",
                str(github),
            ]
        )
        == 0
    )
    report = json.loads(output.read_text())
    lines = dict(line.split("=", 1) for line in github.read_text().splitlines())
    assert lines["scope_partitions"] == "[]"
    assert json.loads(lines["owners"]) == report["owners"]
    assert lines["owner_ids"] == OWNER_ID
    assert report["owners"] == [
        {
            "id": OWNER_ID,
            "artifact": hashlib.sha256(OWNER_ID.encode()).hexdigest(),
        }
    ]
    assert (
        report["configuration_sha256"]
        == hashlib.sha256(
            (repository / "configs/ci/report-owner-execution.json").read_bytes()
        ).hexdigest()
    )
    assert not (repository / "artifacts/producer-output").exists()


@pytest.mark.parametrize(
    "identity",
    [
        "domain/with space",
        "domain/quote'",
        "domain/$value",
        "domain/with\nline",
        "domain/.hidden/report",
    ],
)
def test_schedule_refuses_owner_identity_that_cannot_cross_make_arguments(
    repository: Path,
    identity: str,
) -> None:
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(owner_id=identity),
    )
    with pytest.raises(ReportRebuildError, match="scheduled safely"):
        scheduling.configured_owner_schedule(repository)


def test_schedule_validates_owner_output_set_before_export(repository: Path) -> None:
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(
            source_paths={"unexpected.json": SECOND_OUTPUT}
        ),
    )
    with pytest.raises(ReportRebuildError):
        scheduling.configured_owner_schedule(repository)


def test_schedule_sorts_full_ids_and_separates_duplicate_leaf_names(
    repository: Path,
) -> None:
    _write(repository, SECOND_OUTPUT, '{"details": 2}\n')
    for file in ("report-owner-execution.json", "report-ownership.json"):
        path = repository / "configs/ci" / file
        payload = json.loads(path.read_text())
        first = payload["owners"][0]
        first["owner_id"] = "second/summary"
        other = json.loads(json.dumps(first))
        other["owner_id"] = "first/summary"
        if file == "report-owner-execution.json":
            other["source_paths"] = {"details.json": SECOND_OUTPUT}
        else:
            other["paths"] = [SECOND_OUTPUT]
        payload["owners"].append(other)
        path.write_text(json.dumps(payload))
    report = scheduling.configured_owner_schedule(repository)
    rows = report["owners"]
    assert isinstance(rows, list)
    assert [row["id"] for row in rows] == ["first/summary", "second/summary"]
    assert len({row["artifact"] for row in rows}) == 2
    assert report["owner_ids"] == "first/summary second/summary"
    assert set(report) == {
        "schema_version",
        "configuration_sha256",
        "owners",
        "owner_ids",
    }


def test_schedule_refuses_omitted_generated_owner_before_any_export(
    repository: Path,
) -> None:
    _write(repository, SECOND_OUTPUT, '{"details": 2}\n')
    _modify(
        repository,
        "report-ownership.json",
        lambda p: p["owners"].append(
            dict(
                p["owners"][0],
                owner_id="domain/other",
                paths=[SECOND_OUTPUT],
            )
        ),
    )
    output = repository / "artifacts/owner-schedule.json"
    github = repository / "artifacts/github-output"
    github.parent.mkdir()
    github.write_text("retained\n", encoding="utf-8")
    assert (
        scheduling.main(
            [
                "--repository",
                str(repository),
                "--output",
                str(output),
                "--github-output",
                str(github),
            ]
        )
        == 2
    )
    assert not output.exists()
    assert github.read_text(encoding="utf-8") == "retained\n"


def test_schedule_refuses_configured_owner_after_role_change(repository: Path) -> None:
    _modify(
        repository,
        "report-ownership.json",
        lambda p: p["owners"][0].update(role="maintained_editorial"),
    )
    with pytest.raises(ReportRebuildError, match="not declared generated"):
        scheduling.configured_owner_schedule(repository)


def test_schedule_refuses_ownership_mutation_during_resolution(
    repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = owner_runner.resolve_configured_owner

    def change_after_resolution(root: Path, identity: str) -> None:
        original(root, identity)
        _modify(
            root,
            "report-ownership.json",
            lambda p: p["owners"][0].update(verification="changed"),
        )

    monkeypatch.setattr(scheduling, "resolve_configured_owner", change_after_resolution)
    with pytest.raises(ReportRebuildError, match="ownership changed during scheduling"):
        scheduling.configured_owner_schedule(repository)


def test_schedule_cli_preserves_existing_artifact(repository: Path) -> None:
    output = repository / "artifacts/schedule.json"
    output.parent.mkdir()
    output.write_text("retained\n")
    assert (
        scheduling.main(["--repository", str(repository), "--output", str(output)]) == 2
    )
    assert output.read_text() == "retained\n"


@pytest.mark.parametrize(
    "count", [128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142]
)
def test_two_lane_schedule_capacity(
    repository: Path,
    monkeypatch: pytest.MonkeyPatch,
    count: int,
) -> None:
    path = repository / "configs/ci/report-owner-execution.json"
    payload = json.loads(path.read_text())
    base = payload["owners"][0]
    payload["owners"] = [
        dict(base, owner_id=f"domain/owner-{index}") for index in range(count)
    ]
    path.write_text(json.dumps(payload))
    inventory_path = repository / "configs/ci/report-ownership.json"
    inventory = json.loads(inventory_path.read_text())
    base_declaration = inventory["owners"][0]
    inventory["owners"] = [
        dict(base_declaration, owner_id=f"domain/owner-{index}")
        for index in range(count)
    ]
    inventory_path.write_text(json.dumps(inventory))
    monkeypatch.setattr(scheduling, "resolve_configured_owner", lambda *_args: None)
    if count == 142:
        with pytest.raises(ReportRebuildError, match="exceeds 141 owners"):
            scheduling.configured_owner_schedule(repository)
    else:
        report = scheduling.configured_owner_schedule(repository)
        assert isinstance(report["owners"], list)
        assert len(report["owners"]) == count


def test_schedule_refuses_ancestor_owner_namespace(repository: Path) -> None:
    inventory_path = repository / "configs/ci/report-ownership.json"
    configuration_path = repository / "configs/ci/report-owner-execution.json"
    inventory = json.loads(inventory_path.read_text())
    configuration = json.loads(configuration_path.read_text())
    for index, identity in enumerate(
        ("domain/summary-between", "domain/summary/detail")
    ):
        output = f"docs/report/domain/extra-{index}.json"
        _write(repository, output, '{"extra": 1}\n')
        inventory["owners"].append(
            dict(inventory["owners"][0], owner_id=identity, paths=[output])
        )
        configuration["owners"].append(
            dict(
                configuration["owners"][0],
                owner_id=identity,
                source_paths={f"extra-{index}.json": output},
            )
        )
    inventory_path.write_text(json.dumps(inventory))
    configuration_path.write_text(json.dumps(configuration))
    with pytest.raises(ReportRebuildError, match="ancestor namespaces"):
        scheduling.configured_owner_schedule(repository)


def test_schedule_preflight_does_not_write_outputs(repository: Path) -> None:
    output = repository / "artifacts/plan/owner-schedule.json"
    github = repository / "artifacts/github-output"
    github.parent.mkdir()
    github.write_text("retained\n")
    assert (
        scheduling.main(
            [
                "--repository",
                str(repository),
                "--output",
                str(output),
                "--github-output",
                str(github),
                "--check-only",
            ]
        )
        == 0
    )
    assert not output.parent.exists()
    assert github.read_text() == "retained\n"


def _qualified_fixture(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, Path]]:
    """Add a configured external owner with a synthetic qualified packet."""
    _write(repository, EXTERNAL_DESCRIPTOR, '{"packet": 1}\n')
    _modify(
        repository,
        "report-ownership.json",
        lambda p: p["owners"][0].update(
            producer_inputs=sorted([PARENT, EXTERNAL_DESCRIPTOR])
        ),
    )
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(external_source_descriptor=EXTERNAL_DESCRIPTOR),
    )
    root = repository.parent / f"{repository.name}-qualified-sources"
    root.mkdir()
    custody = root / "source-manifest.json"
    source = root / "table-s5.csv"
    custody.write_text('{"custody": 1}\n', encoding="utf-8")
    source.write_text("qualified source\n", encoding="utf-8")
    inputs = {
        EXTERNAL_DESCRIPTOR: repository / EXTERNAL_DESCRIPTOR,
        "external/legacyage/source-manifest.json": custody,
        "external/legacyage/table-s5.csv": source,
    }

    def qualify(*_args: object) -> QualifiedReportSources:
        return QualifiedReportSources(root, inputs, "a" * 64)

    monkeypatch.setattr(owner_runner, "validated_external_report_sources", qualify)
    monkeypatch.setattr(
        "bijux_pollenomics_dev.ci.report_rebuild.qualified_sources.validated_external_report_sources",
        qualify,
    )
    return root, inputs


def test_qualified_owner_requires_root_and_exact_declared_inputs(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, external = _qualified_fixture(repository, monkeypatch)
    with pytest.raises(ReportRebuildError, match="requires --source-root"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)
    selected = owner_runner.resolve_configured_owner(
        repository, OWNER_ID, source_root=root
    )
    assert selected.inputs == {
        MODULE_PATH: repository / MODULE_PATH,
        PARENT: repository / PARENT,
        **external,
    }
    assert selected.command[-4:-2] == ("--source-root", str(root))
    assert selected.command[-6:-4] == ("--source-descriptor", EXTERNAL_DESCRIPTOR)
    with pytest.raises(ReportRebuildError, match="requires --source-root"):
        scheduling.configured_owner_schedule(repository)
    assert (
        scheduling.configured_owner_schedule(repository, source_root=root)["owner_ids"]
        == OWNER_ID
    )


def test_qualified_owner_rejects_undeclared_descriptor_and_label_collision(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, external = _qualified_fixture(repository, monkeypatch)
    _modify(
        repository,
        "report-ownership.json",
        lambda p: p["owners"][0].update(producer_inputs=[PARENT]),
    )
    with pytest.raises(ReportRebuildError, match="not a declared repository input"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID, source_root=root)
    _modify(
        repository,
        "report-ownership.json",
        lambda p: p["owners"][0].update(
            producer_inputs=sorted([PARENT, EXTERNAL_DESCRIPTOR])
        ),
    )
    external[PARENT] = repository / PARENT
    with pytest.raises(ReportRebuildError, match="overlaps repository declaration"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID, source_root=root)


def test_qualified_owner_verifier_rejects_extra_input_and_missing_root(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _qualified_fixture(repository, monkeypatch)
    selected = owner_runner.resolve_configured_owner(
        repository, OWNER_ID, source_root=root
    )
    policy: dict[str, object] = {"tracked_report_root": "docs/report"}
    manifest: dict[str, object] = {
        "producer_inputs": producer_input_identity(selected.inputs, repository),
        "source_paths": selected.source_paths,
        "producer_command": list(selected.command),
    }

    _require_current_owner_inputs(
        manifest, repository, OWNER_ID, policy, source_root=root
    )
    with pytest.raises(ReportRebuildError, match="requires --source-root"):
        _require_current_owner_inputs(manifest, repository, OWNER_ID, policy)
    extra = repository / "extra.txt"
    extra.write_text("undeclared\n", encoding="utf-8")
    manifest["producer_inputs"] = producer_input_identity(
        {**selected.inputs, "external/legacyage/extra.txt": extra}, repository
    )
    with pytest.raises(ReportRebuildError, match="declaration differs"):
        _require_current_owner_inputs(
            manifest, repository, OWNER_ID, policy, source_root=root
        )
    producer_inputs = producer_input_identity(selected.inputs, repository)
    manifest["producer_inputs"] = producer_inputs
    producer_inputs["external/legacyage/undeclared.csv"] = {
        "path": str(repository / "unreadable-undeclared.csv"),
        "sha256": "0" * 64,
        "size": 1,
    }
    with pytest.raises(ReportRebuildError, match="declaration differs"):
        _require_current_owner_inputs(
            manifest, repository, OWNER_ID, policy, source_root=root
        )
    manifest["producer_inputs"] = producer_input_identity(selected.inputs, repository)
    manifest["producer_command"] = ["python", "-c", "print('forged')"]
    with pytest.raises(ReportRebuildError, match="invocation or input declaration"):
        _require_current_owner_inputs(
            manifest, repository, OWNER_ID, policy, source_root=root
        )


def test_qualified_owner_rechecks_source_identity_after_build(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, inputs = _qualified_fixture(repository, monkeypatch)
    calls = 0

    def changed_packet(*_args: object) -> QualifiedReportSources:
        nonlocal calls
        calls += 1
        return QualifiedReportSources(root, inputs, ("a" if calls == 1 else "b") * 64)

    monkeypatch.setattr(
        owner_runner, "validated_external_report_sources", changed_packet
    )
    monkeypatch.setattr(
        owner_runner,
        "build_owner_output",
        lambda **_kwargs: {"owner_id": OWNER_ID, "lane": "reference"},
    )
    with pytest.raises(ReportRebuildError, match="changed during owner build"):
        owner_runner.build_configured_owner(
            repository=repository,
            plan_path=repository / "plan.json",
            lane="reference",
            owner_id=OWNER_ID,
            evidence_root=repository / "artifacts" / "qualified-owner",
            source_root=root,
        )


def test_legacyage_wrapper_requires_absent_real_artifact_output(
    repository: Path,
) -> None:
    from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
        require_absent_artifact_output as _absent_artifact_output,
    )

    artifacts = repository / "artifacts"
    parent = artifacts / "owner" / "producer-output"
    parent.mkdir(parents=True)
    output = parent / "source-products"
    assert _absent_artifact_output(repository, output) == output
    with pytest.raises(ReportRebuildError, match="below repository artifacts"):
        _absent_artifact_output(repository, repository / "docs" / "result")
    traversal = artifacts / ".." / "docs" / "report" / "new-output"
    with pytest.raises(ReportRebuildError, match="not canonical"):
        _absent_artifact_output(repository, traversal)
    assert not (repository / "docs" / "report" / "new-output").exists()
    output.mkdir()
    with pytest.raises(ReportRebuildError, match="must be absent"):
        _absent_artifact_output(repository, output)
    output.rmdir()
    (artifacts / "linked").symlink_to(parent, target_is_directory=True)
    with pytest.raises(ReportRebuildError, match="non-real ancestor"):
        _absent_artifact_output(repository, artifacts / "linked" / "result")


def test_legacyage_wrapper_refuses_changed_replay_before_execution(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics_dev.source_completion.neotoma import legacyage_depth_join

    root = repository.parent / f"{repository.name}-qualified-replay"
    root.mkdir()
    _write(
        repository,
        EXTERNAL_DESCRIPTOR,
        json.dumps(
            {
                "files": [
                    {"path": "table-s5-legacyage-chronology.csv", "sha256": "a" * 64},
                    {"path": "table-s6-chronology-comparison.csv", "sha256": "b" * 64},
                ]
            }
        ),
    )
    _write(repository, legacyage_depth_join.REPLAY, "raise AssertionError('changed')\n")
    output = repository / "artifacts" / "source-products"
    output.parent.mkdir()
    monkeypatch.setattr(
        legacyage_depth_join,
        "validated_external_report_sources",
        lambda *_args: QualifiedReportSources(root, {}, "a" * 64),
    )
    with pytest.raises(ReportRebuildError, match="read set changed"):
        legacyage_depth_join.main(
            [
                "--repository",
                str(repository),
                "--source-root",
                str(root),
                "--output",
                str(output),
            ]
        )
    assert not output.exists()


def test_legacyage_wrapper_reads_the_forwarded_descriptor(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics_dev.source_completion.neotoma import legacyage_depth_join

    alternate = Path("configs/ci/qualified-report-sources/alternative.json")
    _write(
        repository,
        alternate.as_posix(),
        json.dumps({"files": [{"path": "source.csv", "sha256": "a" * 64}]}),
    )
    assert not (repository / legacyage_depth_join.DESCRIPTOR).exists()
    _write(repository, legacyage_depth_join.REPLAY, "# changed replay\n")
    output = repository / "artifacts" / "source-products"
    output.parent.mkdir()
    supplied: list[Path] = []

    def qualify(repo: Path, root: Path, descriptor: Path) -> QualifiedReportSources:
        assert repo == repository
        supplied.append(descriptor)
        return QualifiedReportSources(root, {}, "a" * 64)

    monkeypatch.setattr(
        legacyage_depth_join, "validated_external_report_sources", qualify
    )
    with pytest.raises(ReportRebuildError, match="read set changed"):
        legacyage_depth_join.main(
            [
                "--repository",
                str(repository),
                "--source-root",
                str(repository.parent),
                "--source-descriptor",
                alternate.as_posix(),
                "--output",
                str(output),
            ]
        )
    assert supplied == [alternate]
    assert not output.exists()


@pytest.mark.parametrize(
    ("target", "arguments"),
    [
        (
            "build-report-rebuild-owner",
            [
                "REBUILD_LANE=reference",
                "REBUILD_OWNER_ID=source-relations/neotoma/legacyage-chronology/report-products",
                "REBUILD_EVIDENCE_ROOT=artifacts/owner",
            ],
        ),
        (
            "assemble-report-rebuild",
            [
                "REBUILD_LANE=reference",
                "REBUILD_PARTITION_ARTIFACTS_ROOT=artifacts/partitions",
                "REBUILD_EVIDENCE_ROOT=artifacts/assembly",
            ],
        ),
        (
            "verify-partitioned-report-rebuild",
            [
                "REBUILD_REFERENCE_MANIFEST=artifacts/reference/manifest.json",
                "REBUILD_REPLAY_MANIFEST=artifacts/replay/manifest.json",
                "REBUILD_EVIDENCE_ROOT=artifacts/final",
            ],
        ),
    ],
)
def test_canonical_make_passes_explicit_qualified_source_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    target: str,
    arguments: list[str],
) -> None:
    fragment = Path(__file__).resolve().parents[3] / "makes/pollenomics-verification.mk"
    recorder = tmp_path / "record_argv.py"
    recorder.write_text(
        "import json\n"
        "import os\n"
        "from pathlib import Path\n"
        "import sys\n"
        "Path(os.environ['REBUILD_ARGV_LOG']).write_text(json.dumps(sys.argv[1:]))\n",
        encoding="utf-8",
    )
    wrapper = tmp_path / "Makefile"
    wrapper.write_text(
        f"DEV_RUN := {shlex.quote(sys.executable)} {shlex.quote(str(recorder))}\n"
        "root-check-env:\n\t@:\n"
        f"include {fragment}\n",
        encoding="utf-8",
    )
    argv_log = tmp_path / "argv.json"
    monkeypatch.setenv("REBUILD_ARGV_LOG", str(argv_log))
    root = tmp_path / "qualified-sources"
    result = subprocess.run(
        [
            "make",
            "-f",
            str(wrapper),
            target,
            f"REBUILD_SOURCE_ROOT={root}",
            *arguments,
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    argv = json.loads(argv_log.read_text(encoding="utf-8"))
    assert argv.count("--source-root") == 1
    assert argv[argv.index("--source-root") + 1] == str(root)


def test_retained_artifact_argument_binds_distinct_owner_namespace(
    repository: Path,
) -> None:
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(
            artifact_output_flag="--retained-artifacts-root"
        ),
    )
    selected = owner_runner.resolve_configured_owner(repository, OWNER_ID)
    offset = selected.command.index("--retained-artifacts-root")
    assert selected.command[offset + 1] == "{artifact_root}"
    assert selected.command[-1] == "{output_root}/summary.json"


@pytest.mark.parametrize("flag", ["--output", "--screen", "", None, True])
def test_unmaintained_artifact_output_flag_refuses(
    repository: Path, flag: object
) -> None:
    _modify(
        repository,
        "report-owner-execution.json",
        lambda p: p["owners"][0].update(artifact_output_flag=flag),
    )
    with pytest.raises(ReportRebuildError, match="artifact output flag"):
        owner_runner.resolve_configured_owner(repository, OWNER_ID)


_NATIVE_CAPTURE_OWNER = "method-certification/current-r-oracle/report-products"
_NATIVE_CAPTURE_MODULE = (
    "bijux_pollenomics_dev.source_completion.method_certification.native_r_comparison"
)


def _native_capture_configuration(profile: object) -> dict[str, Any]:
    return {
        "schema_version": owner_runner.SCHEMA,
        "owners": [
            {
                "owner_id": _NATIVE_CAPTURE_OWNER,
                "module": _NATIVE_CAPTURE_MODULE,
                "source_paths": {},
                "source_arguments": [],
                "output_mode": "directory",
                "timeout_seconds": 300,
                "native_capture_profile": profile,
            }
        ],
    }


@pytest.mark.parametrize("profile", ["annulus", "count-domain", "finite-covariance"])
def test_native_capture_configuration_accepts_finite_profile(profile: str) -> None:
    row = owner_runner._configuration_owner(
        _native_capture_configuration(profile), _NATIVE_CAPTURE_OWNER
    )
    assert row["native_capture_profile"] == profile


@pytest.mark.parametrize("profile", [None, False, [], {}, "arbitrary"])
def test_native_capture_configuration_refuses_invalid_profile(profile: object) -> None:
    with pytest.raises(ReportRebuildError, match="native capture profile"):
        owner_runner._configuration_owner(
            _native_capture_configuration(profile), _NATIVE_CAPTURE_OWNER
        )


@pytest.mark.parametrize(
    "change", [{"owner_id": "other/report-products"}, {"module": MODULE}]
)
def test_native_capture_configuration_stays_with_named_owner(
    change: dict[str, str],
) -> None:
    configuration = _native_capture_configuration("count-domain")
    configuration["owners"][0].update(change)
    with pytest.raises(ReportRebuildError, match="native capture profile"):
        owner_runner._configuration_owner(
            configuration, configuration["owners"][0]["owner_id"]
        )


def test_actual_native_capture_owner_emits_explicit_finite_covariance_profile() -> None:
    repository = Path(__file__).resolve().parents[3]
    selected = owner_runner.resolve_configured_owner(repository, _NATIVE_CAPTURE_OWNER)
    offset = selected.command.index("--capture-profile")
    assert selected.command[offset + 1] == "finite-covariance"
    assert len(selected.inputs) == 386
    assert selected.source_paths == {
        "source-products/report.json": "method-certification/current-r-oracle/report.json",
        "source-products/source-replay.json": "method-certification/current-r-oracle/source-replay.json",
    }
