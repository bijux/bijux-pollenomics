"""Preserve source custody and prepublication identity refusal."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.source_completion.landclim_taxonomy_mass import LOOKUP
from bijux_pollenomics_dev.source_completion.nordic import (
    author_target_preparation as account,
)

from .fixtures import Packet, _run, _unpublished
from .fixtures import packet as packet


@pytest.mark.parametrize("index", range(36))
@pytest.mark.parametrize("failure", ["missing", "symlink"])
def test_every_source_dependency_refuses_missing_or_linked(
    packet: Packet, index: int, failure: str
) -> None:
    path = packet.repository / account.REPOSITORY_INPUTS[index]
    path.unlink()
    if failure == "symlink":
        path.symlink_to(packet.qualified.directory / LOOKUP)
    with pytest.raises(ReportRebuildError):
        _run(packet)
    assert packet.calls == ["qualify"]
    _unpublished(packet)


def test_full_qualifier_refusal_never_runs_prepare(
    packet: Packet, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(*_args: object) -> QualifiedReportSources:
        raise ReportRebuildError("original snapshot differs")

    monkeypatch.setattr(account, "validated_external_report_sources", refuse)
    with pytest.raises(ReportRebuildError, match="original snapshot differs"):
        _run(packet)
    assert packet.calls == []
    _unpublished(packet)


@pytest.mark.parametrize("index", [0, 1, *range(32, 38)])
def test_source_descriptor_and_swedish_dependency_mutations_refuse_publication(
    packet: Packet, monkeypatch: pytest.MonkeyPatch, index: int
) -> None:
    inputs = [
        *packet.qualified.inputs.values(),
        *(packet.repository / relative for relative in account.REPOSITORY_INPUTS),
    ]

    def mutate(repo: Path, directory: Path, output: Path) -> None:
        packet.prepare(repo, directory, output)
        with inputs[index].open("ab") as stream:
            stream.write(b" ")

    monkeypatch.setattr(account, "prepare", mutate)
    with pytest.raises(ReportRebuildError, match="upstream identity|inputs changed"):
        _run(packet)
    _unpublished(packet)


@pytest.mark.parametrize("field", ["directory", "inputs", "descriptor_sha256"])
def test_qualified_declaration_drift_refuses_publication(
    packet: Packet, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    calls = 0

    def qualify(*_args: object) -> QualifiedReportSources:
        nonlocal calls
        calls += 1
        if calls == 1:
            return packet.qualified
        if field == "directory":
            return replace(packet.qualified, directory=packet.root)
        if field == "inputs":
            return replace(packet.qualified, inputs={})
        return replace(packet.qualified, descriptor_sha256="0" * 64)

    monkeypatch.setattr(account, "validated_external_report_sources", qualify)
    with pytest.raises(ReportRebuildError, match="inputs changed"):
        _run(packet)
    _unpublished(packet)
