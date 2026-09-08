from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from bijux_pollenomics.reporting.bundles.report_partitions import __main__ as command


def _invoke(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], payload: str
) -> tuple[int, str, str]:
    status = command.main([payload])
    captured = capsys.readouterr()
    return status, captured.out, captured.err


def test_plan_response_is_exact_and_keeps_producer_output_off_stdout(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    partition = SimpleNamespace(identity="world", required_partition_ids=())

    def build(*args: object, **kwargs: object) -> SimpleNamespace:
        print("producer diagnostic")
        return SimpleNamespace(partitions=(partition,), partition_ids=("world",))

    monkeypatch.setattr(command, "build_report_partition_plan", build)
    status, stdout, stderr = _invoke(
        monkeypatch,
        capsys,
        json.dumps(
            {
                "schema_version": "published-report-partition-command.v1",
                "operation": "plan",
                "country_group_size": 2,
            }
        ),
    )

    response = json.loads(stdout)
    assert status == 0
    assert set(response) == {"schema_version", "operation", "result"}
    assert response["operation"] == "plan"
    assert response["result"]["partition_ids"] == ["world"]
    assert stderr == "producer diagnostic\n"


@pytest.mark.parametrize(
    "payload",
    [
        "{}",
        (
            '{"schema_version":"published-report-partition-command.v1",'
            '"operation":"plan","operation":"plan","country_group_size":2}'
        ),
        (
            '{"schema_version":"published-report-partition-command.v1",'
            '"operation":"plan","country_group_size":NaN}'
        ),
        (
            '{"schema_version":"published-report-partition-command.v1",'
            '"operation":"plan","country_group_size":2,"extra":true}'
        ),
    ],
)
def test_command_refuses_malformed_or_nonexact_requests(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    payload: str,
) -> None:
    status, stdout, stderr = _invoke(monkeypatch, capsys, payload)

    assert status == 2
    assert stdout == ""
    assert stderr


def test_generate_decodes_exact_runtime_types(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, object] = {}

    def generate(partition_id: str, **kwargs: object) -> SimpleNamespace:
        observed.update(partition_id=partition_id, **kwargs)
        return SimpleNamespace(
            partition=SimpleNamespace(identity=partition_id),
            relative_paths=("world/report.html",),
        )

    monkeypatch.setattr(command, "generate_report_partition", generate)
    request = {
        "schema_version": "published-report-partition-command.v1",
        "operation": "generate",
        "partition_id": "world",
        "version_dir": str(tmp_path / "data/aadr/v66"),
        "countries": ["Sweden"],
        "output_root": str(tmp_path / "output"),
        "published_output_root": "docs/report",
        "title": "Title",
        "slug": "world",
        "context_root": str(tmp_path / "data"),
        "scope_input_root": None,
        "country_group_size": 2,
    }

    status, stdout, _ = _invoke(monkeypatch, capsys, json.dumps(request))

    assert status == 0
    assert json.loads(stdout)["result"] == {
        "partition_id": "world",
        "relative_paths": ["world/report.html"],
    }
    assert observed["version_dir"] == tmp_path / "data/aadr/v66"
    assert observed["countries"] == ("Sweden",)
    assert observed["published_output_root"] == Path("docs/report")
    assert observed["scope_input_root"] is None


def test_assemble_decodes_partition_roots_and_rejects_absolute_publication_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, object] = {}

    def assemble(**kwargs: object) -> SimpleNamespace:
        observed.update(kwargs)
        return SimpleNamespace(output_root=kwargs["output_root"])

    monkeypatch.setattr(command, "assemble_report_partitions", assemble)
    request = {
        "schema_version": "published-report-partition-command.v1",
        "operation": "assemble",
        "version_dir": str(tmp_path / "data/aadr/v66"),
        "countries": ["Sweden"],
        "output_root": str(tmp_path / "output"),
        "partition_roots": {"world": str(tmp_path / "world")},
        "published_output_root": "docs/report",
        "title": "Title",
        "slug": "world",
        "context_root": str(tmp_path / "data"),
        "country_group_size": 2,
    }

    status, stdout, _ = _invoke(monkeypatch, capsys, json.dumps(request))

    assert status == 0
    assert json.loads(stdout)["result"] == {"output_root": str(tmp_path / "output")}
    assert observed["partition_roots"] == {"world": tmp_path / "world"}

    request["published_output_root"] = str(tmp_path / "docs/report")
    status, stdout, stderr = _invoke(monkeypatch, capsys, json.dumps(request))
    assert status == 2
    assert stdout == ""
    assert "must be relative" in stderr
