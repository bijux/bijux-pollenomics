"""Bind the retained BP-axis writer to qualified source and three outputs."""

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
from bijux_pollenomics_dev.source_completion.essd import window_alignment as subject


@dataclass(frozen=True)
class Case:
    repository: Path
    source_root: Path
    output: Path
    core: Path
    bins: Path
    lookup: Path


@pytest.fixture
def case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Case:
    repository = tmp_path / "repository"
    (repository / "artifacts/output").mkdir(parents=True)
    core = repository / "core.py"
    core.write_bytes(b"retained writer")
    author = repository / subject.AUTHOR_REPORT
    published = repository / subject.PUBLISHED_REPORT
    author.parent.mkdir(parents=True)
    published.parent.mkdir(parents=True)
    author.write_bytes(b"author receipt")
    published.write_bytes(b"published receipt")
    source_root = tmp_path / "source"
    directory = source_root / subject.SOURCE_ID
    bins, lookup = (directory / name for name in subject.AXES)
    bins.parent.mkdir(parents=True)
    bins.write_bytes(b"bins")
    lookup.write_bytes(b"lookup")
    inputs = {
        f"external/{subject.SOURCE_ID}/{subject.AXES[0]}": bins,
        f"external/{subject.SOURCE_ID}/{subject.AXES[1]}": lookup,
    }
    inputs.update({f"external/source-{n:03d}": bins for n in range(193)})
    qualified = QualifiedReportSources(directory, inputs, subject.DESCRIPTOR_SHA256)
    monkeypatch.setattr(
        subject, "validated_external_report_sources", lambda *_: qualified
    )
    monkeypatch.setattr(subject, "CORE_PATH", Path("core.py"))
    monkeypatch.setattr(
        subject, "CORE_SHA256", hashlib.sha256(core.read_bytes()).hexdigest()
    )
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda _: SimpleNamespace(origin=str(core)),
    )

    def writer(module: str, *, run_name: str) -> None:
        assert module == subject.CORE and run_name == "__main__"
        assert sys.argv[1:3] == ["--bins", str(bins)]
        assert sys.argv[3:5] == ["--lookup", str(lookup)]
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
        bins,
        lookup,
    )


def invoke(case: Case, *, output: Path | None = None) -> None:
    subject.run(
        case.repository,
        case.source_root,
        subject.DESCRIPTOR,
        case.output if output is None else output,
    )


def test_exact_three_outputs_and_source_unchanged(case: Case) -> None:
    before = (case.bins.read_bytes(), case.lookup.read_bytes())
    invoke(case)
    assert {p.name for p in case.output.iterdir()} == set(subject.OUTPUTS)
    assert (case.bins.read_bytes(), case.lookup.read_bytes()) == before


def test_outside_artifact_destination_refused(case: Case) -> None:
    with pytest.raises(ReportRebuildError, match="artifact"):
        invoke(case, output=case.repository / "docs/report/result")
    assert not case.output.exists()


def test_wrong_source_descriptor_refused(case: Case) -> None:
    with pytest.raises(ValueError, match="descriptor differs"):
        subject.run(
            case.repository,
            case.source_root,
            Path("configs/ci/unqualified.json"),
            case.output,
        )
    assert not case.output.exists()


def test_changed_writer_refused(case: Case) -> None:
    case.core.write_bytes(b"changed writer")
    with pytest.raises(ValueError, match="producer identity differs"):
        invoke(case)
    assert not case.output.exists()


def test_linked_writer_refused(case: Case) -> None:
    original = case.core.with_name("original.py")
    case.core.rename(original)
    case.core.symlink_to(original.name)
    with pytest.raises(ReportRebuildError, match="regular"):
        invoke(case)
    assert not case.output.exists()


def test_qualified_axis_mutation_refused(
    case: Case, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = runpy.run_module

    def writer(module: str, *, run_name: str) -> None:
        original(module, run_name=run_name)
        case.bins.write_bytes(b"changed bins")

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
