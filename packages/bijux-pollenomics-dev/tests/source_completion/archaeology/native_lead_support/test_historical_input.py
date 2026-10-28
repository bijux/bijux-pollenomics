"""Keep historical lead context opaque and outside current decision authority."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.archaeology.native_lead_support import (
    producer,
)


def context_pin() -> dict[str, object]:
    witness = producer._HISTORICAL_LEAD_CONTEXT
    return {"path": witness.member, "sha256": witness.sha256, "bytes": witness.bytes}


def test_context_reads_only_declared_git_witness(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[Path, object]] = []

    def read(root: Path, member: object) -> bytes:
        calls.append((root, member))
        return b"opaque, deliberately not JSON"

    monkeypatch.setattr(producer, "read_blob", read)
    assert not (tmp_path / str(context_pin()["path"])).exists()
    assert (
        producer._lead_input_bytes(tmp_path, context_pin())
        == b"opaque, deliberately not JSON"
    )
    assert calls == [(tmp_path, producer._HISTORICAL_LEAD_CONTEXT)]


@pytest.mark.parametrize(
    "field,value",
    [("sha256", "0" * 64), ("bytes", 64526), ("bytes", 64527.0), ("extra", False)],
)
def test_changed_context_pin_refuses_before_git_or_native_io(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> bytes:
        pytest.fail("no Git or native input may open after a context pin mismatch")

    monkeypatch.setattr(producer, "read_blob", forbidden)
    monkeypatch.setattr(producer, "read_only_database", forbidden)
    pinned = context_pin()
    pinned[field] = value
    with pytest.raises(ValueError, match="historical lead context pin differs"):
        producer._lead_input_bytes(tmp_path, pinned)


@pytest.mark.parametrize(
    "reason", ["unreachable revision", "wrong blob", "wrong size", "wrong SHA256"]
)
def test_git_admission_failure_never_uses_current_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, reason: str
) -> None:
    current = tmp_path / str(context_pin()["path"])
    current.parent.mkdir(parents=True)
    current.write_bytes(b"current content cannot override historical custody")

    def refuse(*args: Any, **kwargs: Any) -> bytes:
        raise ReportRebuildError(reason)

    monkeypatch.setattr(producer, "read_blob", refuse)
    with pytest.raises(ReportRebuildError, match=reason):
        producer._lead_input_bytes(tmp_path, context_pin())


def test_other_lead_input_remains_physical(tmp_path: Path) -> None:
    path = tmp_path / "data/raa/raw/national_geopackage_source.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"small metadata fixture")
    pinned = {
        "path": path.relative_to(tmp_path).as_posix(),
        "sha256": sha256(path.read_bytes()).hexdigest(),
    }
    assert producer._lead_input_bytes(tmp_path, pinned) == b"small metadata fixture"
    alias = path.parent / "alias.json"
    alias.symlink_to(path)
    with pytest.raises(ValueError, match="lead input symlink ancestor"):
        producer._lead_input_bytes(
            tmp_path, {"path": alias.relative_to(tmp_path).as_posix()}
        )


@pytest.mark.parametrize("alteration", ["missing", "duplicate", "wrong_path"])
def test_protocol_population_refuses_before_native_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, alteration: str
) -> None:
    inputs = [
        context_pin(),
        {"path": "data/raa/raw/national_geopackage_source.json"},
        {"path": "docs/report/countries/sweden/sweden_land_use_synthesis_v66.json"},
    ]
    if alteration == "missing":
        inputs.pop()
    elif alteration == "duplicate":
        inputs.append(context_pin())
    else:
        inputs[0] = {"path": "reports/needed/other.json"}
    path = tmp_path / "reports/science/archaeology-native-lead-support/protocol.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"inputs": inputs}))

    def forbidden(*args: Any, **kwargs: Any) -> bytes:
        pytest.fail(
            "invalid protocol population cannot reach Git or national source IO"
        )

    monkeypatch.setattr(producer, "read_blob", forbidden)
    monkeypatch.setattr(producer, "read_only_database", forbidden)
    with pytest.raises(ValueError, match="finite lead input population differs"):
        producer.build_private(
            tmp_path, tmp_path / "source", tmp_path / "artifacts/candidate"
        )
