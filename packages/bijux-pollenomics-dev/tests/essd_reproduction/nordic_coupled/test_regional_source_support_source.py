"""Synthetic publication proves stable-source and absent-output requirements."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled import (
    regional_source_support as audit,
)
from tests.essd_reproduction.nordic_coupled.test_regional_source_support import (
    artificial,
)


def stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], dict[str, Any], list[tuple[Path, str, int, int]]]:
    source, protocol = artificial()
    (tmp_path / "artifacts").mkdir()
    path = tmp_path / audit.PROTOCOL
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(protocol))
    calls: list[tuple[Path, str, int, int]] = []

    def retained(path: Path, checksum: str, size: int, maximum: int) -> bytes:
        calls.append((path, checksum, size, maximum))
        return json.dumps(source).encode()

    monkeypatch.setattr(audit, "buffer", retained)
    monkeypatch.setattr(audit, "source_revision", lambda repository: "a" * 40)
    return source, protocol, calls


def test_only_two_stable_reads_one_absent_owned_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _, calls = stage(tmp_path, monkeypatch)
    output = tmp_path / "artifacts/native-run"
    result = audit.publish(tmp_path, output)
    assert len(calls) == 2 and calls[0] == calls[1]
    assert calls[0] == (
        tmp_path / audit.SOURCE["path"],
        audit.SOURCE["sha256"],
        audit.SOURCE["bytes"],
        32 * 1024**2,
    )
    assert result["source_commit"] == "a" * 40 and len(result["samples"]) == 96
    assert json.loads((output / "result.json").read_bytes()) == result
    assert {path.name for path in output.iterdir()} == {"result.json"}
    with pytest.raises(ReportRebuildError, match="must be absent"):
        audit.publish(tmp_path, output)
    assert len(calls) == 2


def test_source_change_prevents_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, _, _ = stage(tmp_path, monkeypatch)
    native = json.dumps(source).encode()
    calls: list[tuple[object, ...]] = []

    def changing(*args: object) -> bytes:
        calls.append(args)
        return native if len(calls) == 1 else native + b" "

    monkeypatch.setattr(audit, "buffer", changing)
    output = tmp_path / "artifacts/native-run"
    with pytest.raises(ValueError, match="Consumed source changed"):
        audit.publish(tmp_path, output)
    assert not output.exists()


def test_source_revision_change_prevents_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    stage(tmp_path, monkeypatch)
    revisions = iter(["a" * 40, "b" * 40])
    monkeypatch.setattr(audit, "source_revision", lambda repository: next(revisions))
    output = tmp_path / "artifacts/native-run"
    with pytest.raises(ValueError, match="Consumed source changed"):
        audit.publish(tmp_path, output)
    assert not output.exists()


def test_output_budget_is_checked_before_creating_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, protocol, _ = stage(tmp_path, monkeypatch)
    protocol["resource_budget"]["output_bytes"] = 100
    (tmp_path / audit.PROTOCOL).write_text(json.dumps(protocol))
    output = tmp_path / "artifacts/native-run"
    with pytest.raises(ValueError, match="runtime/output budget"):
        audit.publish(tmp_path, output)
    assert not output.exists()


def test_outside_artifact_path_refused_before_native_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _, calls = stage(tmp_path, monkeypatch)
    with pytest.raises(ReportRebuildError, match="below repository artifacts"):
        audit.publish(tmp_path, tmp_path / "result")
    assert calls == []
