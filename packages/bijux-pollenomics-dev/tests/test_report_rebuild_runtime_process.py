from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from bijux_pollenomics_dev.ci.atlas_media.process_execution import BoundedProcessError
from bijux_pollenomics_dev.ci.report_rebuild import runtime_process
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.runtime_process import (
    run_runtime_command,
)


def _plan_request() -> dict[str, object]:
    return {
        "schema_version": "published-report-partition-command.v1",
        "operation": "plan",
        "country_group_size": 2,
    }


def test_runtime_plan_executes_through_package_process_boundary() -> None:
    result = run_runtime_command(_plan_request())

    assert result["partition_ids"] == [
        "world",
        "regions",
        "countries-000",
        "countries-001",
        "foundation",
    ]
    assert result["dependent_partition_ids"] == ["foundation"]
    assert result["countries"] == ["Sweden", "Norway", "Finland", "Denmark"]
    assert result["version"] == "v66"
    assert result["title"] == "World Evidence Surface"
    assert result["slug"] == "world"


@pytest.mark.parametrize(
    ("stdout", "message"),
    [
        ("not-json", "strict JSON"),
        (
            (
                '{"schema_version":"published-report-partition-response.v1",'
                '"operation":"plan","operation":"plan","result":{}}'
            ),
            "strict JSON",
        ),
        (
            (
                '{"schema_version":"published-report-partition-response.v1",'
                '"operation":"plan","result":{"value":NaN}}'
            ),
            "strict JSON",
        ),
        (
            (
                '{"schema_version":"published-report-partition-response.v1",'
                '"operation":"plan","result":{},"extra":true}'
            ),
            "fields are not exact",
        ),
        (
            (
                '{"schema_version":"published-report-partition-response.v1",'
                '"operation":"assemble","result":{}}'
            ),
            "does not match",
        ),
    ],
)
def test_runtime_process_rejects_untrusted_responses(
    monkeypatch: pytest.MonkeyPatch, stdout: str, message: str
) -> None:
    def run(*args: object, **kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(
            returncode=0,
            stdout=stdout.encode(),
            stderr=b"",
            timed_out=False,
        )

    monkeypatch.setattr(
        runtime_process,
        "run_bounded_argv",
        run,
    )

    with pytest.raises(ReportRebuildError, match=message):
        run_runtime_command(_plan_request())


def test_runtime_process_bounds_failed_command_diagnostic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def run(*args: object, **kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(
            returncode=2,
            stdout=b"",
            stderr=b"x" * 5000,
            timed_out=False,
        )

    monkeypatch.setattr(
        runtime_process,
        "run_bounded_argv",
        run,
    )

    with pytest.raises(ReportRebuildError) as raised:
        run_runtime_command(_plan_request())

    assert len(str(raised.value)) < 4_100


def test_runtime_process_uses_exact_argv_and_bounds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, object] = {}

    def run(command: tuple[str, ...], **kwargs: object) -> SimpleNamespace:
        observed.update(command=command, **kwargs)
        response = {
            "schema_version": "published-report-partition-response.v1",
            "operation": "plan",
            "result": {},
        }
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(response).encode(),
            stderr=b"",
            timed_out=False,
        )

    monkeypatch.setattr(runtime_process, "run_bounded_argv", run)

    run_runtime_command(_plan_request())

    command = observed["command"]
    assert isinstance(command, tuple)
    assert command[:3] == (
        runtime_process._ENV_EXECUTABLE,
        runtime_process.sys.executable,
        "-m",
    )
    assert command[3] == "bijux_pollenomics.reporting.bundles.report_partitions"
    assert json.loads(command[4]) == _plan_request()
    assert observed["timeout_seconds"] == 480
    assert observed["max_output_bytes"] == 1024 * 1024


@pytest.mark.parametrize("invalid", [object(), float("nan")])
def test_runtime_process_translates_unserializable_requests(invalid: object) -> None:
    request = _plan_request()
    request["invalid"] = invalid

    with pytest.raises(ReportRebuildError, match="not strict JSON"):
        run_runtime_command(request)


def test_runtime_process_translates_timeout_or_executor_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        runtime_process,
        "run_bounded_argv",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=-1, stdout=b"", stderr=b"", timed_out=True
        ),
    )
    with pytest.raises(ReportRebuildError, match="timed out"):
        run_runtime_command(_plan_request())

    def unavailable(*args: object, **kwargs: object) -> object:
        raise BoundedProcessError("unavailable")

    monkeypatch.setattr(runtime_process, "run_bounded_argv", unavailable)
    with pytest.raises(ReportRebuildError, match="cannot execute"):
        run_runtime_command(_plan_request())
