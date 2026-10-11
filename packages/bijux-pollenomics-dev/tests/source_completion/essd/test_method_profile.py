"""Bind the retained LandClim method profile to qualified author source bytes."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.source_completion.essd import method_profile as subject


@dataclass(frozen=True)
class Case:
    repository: Path
    source_root: Path
    output: Path
    core: Path
    private_manifest: Path
    repository_input: Path


@pytest.fixture
def case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Case:
    repository = tmp_path / "repository"
    (repository / "artifacts/output").mkdir(parents=True)
    core = repository / "core.py"
    core.write_bytes(b"retained profile writer")
    repository_inputs = [repository / name for name in subject.REPOSITORY_INPUTS]
    for path in repository_inputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(path.name.encode())
    source_root = tmp_path / "source"
    directory = source_root / subject.SOURCE_ID
    manifest = directory / "snapshot-manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_bytes(b"retained snapshot")
    source_inputs = {
        f"external/{subject.SOURCE_ID}/snapshot-manifest.json": manifest,
        **{f"external/source-{n:03d}": manifest for n in range(194)},
    }
    qualified = QualifiedReportSources(
        directory, source_inputs, subject.DESCRIPTOR_SHA256
    )
    monkeypatch.setattr(
        subject, "validated_external_report_sources", lambda *_: qualified
    )
    monkeypatch.setattr(subject, "CORE_PATH", Path("core.py"))
    monkeypatch.setattr(
        subject, "CORE_SHA256", hashlib.sha256(core.read_bytes()).hexdigest()
    )
    monkeypatch.setattr(
        importlib.util, "find_spec", lambda _: SimpleNamespace(origin=str(core))
    )

    def writer(module: str, *, run_name: str) -> None:
        assert module == subject.CORE and run_name == "__main__"
        assert sys.argv[1:3] == ["--repository", str(repository)]
        assert sys.argv[3:5] == ["--private-root", str(directory)]
        produced = Path(sys.argv[-1])
        produced.mkdir()
        for name in subject.OUTPUTS:
            (produced / name).write_bytes(name.encode())

    monkeypatch.setattr(runpy, "run_module", writer)
    return Case(
        repository,
        source_root,
        repository / "artifacts/output/source-products",
        core,
        manifest,
        repository_inputs[0],
    )


def invoke(case: Case, *, output: Path | None = None) -> None:
    subject.run(
        case.repository,
        case.source_root,
        subject.DESCRIPTOR,
        case.output if output is None else output,
    )


def test_exact_three_outputs_and_restored_argv(case: Case) -> None:
    original_argv = sys.argv
    invoke(case)
    assert {path.name for path in case.output.iterdir()} == set(subject.OUTPUTS)
    assert sys.argv is original_argv
    assert case.private_manifest.read_bytes() == b"retained snapshot"


def test_unqualified_descriptor_refused(case: Case) -> None:
    with pytest.raises(ValueError, match="descriptor differs"):
        subject.run(
            case.repository,
            case.source_root,
            Path("configs/ci/other-source.json"),
            case.output,
        )
    assert not case.output.exists()


def test_changed_core_refused(case: Case) -> None:
    case.core.write_bytes(b"changed writer")
    with pytest.raises(ValueError, match="writer identity differs"):
        invoke(case)
    assert not case.output.exists()


def test_outside_artifact_destination_refused(case: Case) -> None:
    with pytest.raises(ReportRebuildError, match="artifact"):
        invoke(case, output=case.repository / "docs/report/profile")
    assert not case.output.exists()


def test_changed_repository_input_refused(
    case: Case, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = runpy.run_module

    def writer(module: str, *, run_name: str) -> None:
        original(module, run_name=run_name)
        case.repository_input.write_bytes(b"changed source receipt")

    monkeypatch.setattr(runpy, "run_module", writer)
    with pytest.raises(ValueError, match="inputs changed"):
        invoke(case)
    assert not case.output.exists()


def test_private_snapshot_mutation_refused(
    case: Case, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = runpy.run_module

    def writer(module: str, *, run_name: str) -> None:
        original(module, run_name=run_name)
        case.private_manifest.write_bytes(b"changed private manifest")

    monkeypatch.setattr(runpy, "run_module", writer)
    with pytest.raises(ValueError, match="inputs changed"):
        invoke(case)
    assert not case.output.exists()


def test_extra_output_refused(case: Case, monkeypatch: pytest.MonkeyPatch) -> None:
    original = runpy.run_module

    def writer(module: str, *, run_name: str) -> None:
        original(module, run_name=run_name)
        (Path(sys.argv[-1]) / "extra.json").write_bytes(b"extra")

    monkeypatch.setattr(runpy, "run_module", writer)
    with pytest.raises(ValueError, match="output population differs"):
        invoke(case)
    assert not case.output.exists()
