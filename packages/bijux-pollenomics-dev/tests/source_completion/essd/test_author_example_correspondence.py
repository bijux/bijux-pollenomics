"""Route retained two-grid correspondence through qualified source custody."""

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
from bijux_pollenomics_dev.source_completion.essd import (
    author_example_correspondence as subject,
)


@dataclass(frozen=True)
class Case:
    repository: Path
    source_root: Path
    output: Path
    core: Path
    candidate: Path
    author: Path
    repository_input: Path


@pytest.fixture
def case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Case:
    repository = tmp_path / "repository"
    (repository / "artifacts/output").mkdir(parents=True)
    core = repository / "core.py"
    core.write_bytes(b"retained correspondence writer")
    inputs = [repository / path for path in subject.REPOSITORY_INPUTS]
    for path in inputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(path.name.encode())
    source_root = tmp_path / "source"
    candidate = source_root / subject.RUN / "report.json"
    author = source_root / subject.REFERENCE / "receipt.json"
    for path in (candidate, author):
        path.parent.mkdir(parents=True)
        path.write_bytes(path.name.encode())
    source_inputs = {
        "external/landclim/two-grid-process/run/run001/report.json": candidate,
        "external/landclim/author-reference/reference/receipt.json": author,
        **{f"external/source-{n:03d}": candidate for n in range(263)},
    }
    qualified = QualifiedReportSources(
        source_root, source_inputs, subject.DESCRIPTOR_SHA256
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
        assert sys.argv[1:3] == ["--run", str(source_root / subject.RUN)]
        assert sys.argv[3:5] == ["--reference", str(source_root / subject.REFERENCE)]
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
        candidate,
        author,
        inputs[0],
    )


def invoke(case: Case, *, output: Path | None = None) -> None:
    subject.run(
        case.repository,
        case.source_root,
        subject.DESCRIPTOR,
        case.output if output is None else output,
    )


def test_exact_outputs_and_restored_argv(case: Case) -> None:
    original_argv = sys.argv
    invoke(case)
    assert {path.name for path in case.output.iterdir()} == set(subject.OUTPUTS)
    assert sys.argv is original_argv


def test_wrong_descriptor_refused(case: Case) -> None:
    with pytest.raises(ValueError, match="descriptor differs"):
        subject.run(
            case.repository,
            case.source_root,
            Path("configs/ci/other.json"),
            case.output,
        )
    assert not case.output.exists()


def test_outside_artifact_destination_refused(case: Case) -> None:
    with pytest.raises(ReportRebuildError, match="artifact"):
        invoke(case, output=case.repository / "docs/report/result")
    assert not case.output.exists()


def test_changed_writer_refused(case: Case) -> None:
    case.core.write_bytes(b"changed writer")
    with pytest.raises(ValueError, match="writer identity differs"):
        invoke(case)
    assert not case.output.exists()


def test_changed_candidate_during_writer_refused(
    case: Case, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = runpy.run_module

    def writer(module: str, *, run_name: str) -> None:
        original(module, run_name=run_name)
        case.candidate.write_bytes(b"changed candidate")

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
