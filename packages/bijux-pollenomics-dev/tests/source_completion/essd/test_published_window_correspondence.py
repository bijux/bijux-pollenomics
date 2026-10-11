"""Bind the ESSD window writer to the qualified two-grid source packet."""

from __future__ import annotations

from collections.abc import Callable
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
    published_window_correspondence as subject,
)


@dataclass(frozen=True)
class Case:
    repository: Path
    source_root: Path
    output: Path
    core: Path
    candidate: Path
    raw: Path


@pytest.fixture
def case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Case:
    """Provide case for the retained source contract."""
    repository = tmp_path / "repository"
    (repository / "artifacts/output").mkdir(parents=True)
    core = repository / "core.py"
    core.write_bytes(b"retained ESSD writer")
    for relative in subject.REPOSITORY_INPUTS:
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(relative.name.encode())
    source_root = tmp_path / "source"
    candidate = source_root / subject.RUN / "report.json"
    author = source_root / subject.AUTHOR / "bins.csv"
    for path in (candidate, author):
        path.parent.mkdir(parents=True)
        path.write_bytes(path.name.encode())
    inputs = {
        "external/landclim/two-grid-process/run/run001/report.json": candidate,
        "external/landclim/author-reference/author/bins.csv": author,
        **{f"external/source-{n:03d}": candidate for n in range(263)},
    }
    qualified = QualifiedReportSources(source_root, inputs, subject.DESCRIPTOR_SHA256)
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
        assert sys.argv[1:] == [
            "--raw",
            str(repository / subject.RAW),
            "--author",
            str(source_root / subject.AUTHOR),
            "--run",
            str(source_root / subject.RUN),
            "--reference",
            str(source_root / subject.REFERENCE),
            "--output",
            sys.argv[-1],
        ]
        produced = Path(sys.argv[-1])
        produced.mkdir()
        (produced / "REPORT.md").write_bytes(b"retained narrative")
        (produced / "report.json").write_bytes(b"{}")
        (produced / "paper-correspondence.csv").write_bytes(b"x\r\n" * 63)

    monkeypatch.setattr(runpy, "run_module", writer)
    return Case(
        repository,
        source_root,
        repository / "artifacts/output/source-products",
        core,
        candidate,
        repository / subject.REPOSITORY_INPUTS[0],
    )


def invoke(case: Case, *, output: Path | None = None) -> None:
    """Provide invoke for the retained source contract."""
    subject.run(
        case.repository,
        case.source_root,
        subject.DESCRIPTOR,
        case.output if output is None else output,
    )


def change_writer(monkeypatch: pytest.MonkeyPatch, mutate: Callable[[], int]) -> None:
    """Provide change writer for the retained source contract."""
    original = runpy.run_module

    def changed(module: str, *, run_name: str) -> None:
        original(module, run_name=run_name)
        mutate()

    monkeypatch.setattr(runpy, "run_module", changed)


def test_original_flags_output_population_and_lf_serialization(case: Case) -> None:
    """Verify original flags output population and lf serialization."""
    original_argv = sys.argv
    invoke(case)
    assert {path.name for path in case.output.iterdir()} == set(subject.OUTPUTS)
    assert (case.output / "paper-correspondence.csv").read_bytes() == b"x\n" * 63
    assert sys.argv is original_argv


def test_changed_original_writer_refused(case: Case) -> None:
    """Verify changed original writer refused."""
    case.core.write_bytes(b"changed writer")
    with pytest.raises(ValueError, match="writer identity differs"):
        invoke(case)
    assert not case.output.exists()


@pytest.mark.parametrize("changed", ["raw", "candidate"])
def test_changed_source_during_writer_refused(
    case: Case, monkeypatch: pytest.MonkeyPatch, changed: str
) -> None:
    """Verify changed source during writer refused."""
    path = case.raw if changed == "raw" else case.candidate
    change_writer(monkeypatch, lambda: path.write_bytes(b"changed"))
    with pytest.raises(ValueError, match="inputs changed during publication"):
        invoke(case)
    assert not case.output.exists()


def test_mixed_csv_line_endings_refused(
    case: Case, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify mixed csv line endings refused."""
    change_writer(
        monkeypatch,
        lambda: (Path(sys.argv[-1]) / "paper-correspondence.csv").write_bytes(
            b"x\r\n" * 62 + b"x\n"
        ),
    )
    with pytest.raises(ValueError, match="serialization differs"):
        invoke(case)
    assert not case.output.exists()


def test_extra_output_refused(case: Case, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify extra output refused."""
    change_writer(
        monkeypatch, lambda: (Path(sys.argv[-1]) / "extra.json").write_bytes(b"x")
    )
    with pytest.raises(ValueError, match="output population differs"):
        invoke(case)
    assert not case.output.exists()


def test_wrong_descriptor_refused(case: Case) -> None:
    """Verify wrong descriptor refused."""
    with pytest.raises(ValueError, match="descriptor differs"):
        subject.run(
            case.repository,
            case.source_root,
            Path("configs/ci/other.json"),
            case.output,
        )
    assert not case.output.exists()


def test_outside_artifact_destination_refused(case: Case) -> None:
    """Verify outside artifact destination refused."""
    with pytest.raises(ReportRebuildError, match="artifact"):
        invoke(case, output=case.repository / "docs/report/result")
    assert not case.output.exists()


def test_declared_window_writer_matches_packaged_source() -> None:
    """Verify declared window writer matches packaged source."""
    spec = importlib.util.find_spec(subject.CORE)
    assert spec is not None and spec.origin is not None
    assert (
        hashlib.sha256(Path(spec.origin).read_bytes()).hexdigest()
        == subject.CORE_SHA256
    )
