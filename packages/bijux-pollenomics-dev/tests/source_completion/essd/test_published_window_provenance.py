"""Bind the three-file ESSD provenance writer to qualified correspondence inputs."""

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
    published_window_provenance as subject,
)


@dataclass(frozen=True)
class Case:
    repository: Path
    source_root: Path
    output: Path
    core: Path
    crosswalk: Path
    inputs: tuple[Path, ...]


@pytest.fixture
def case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Case:
    repository = tmp_path / "repository"
    (repository / "artifacts/output").mkdir(parents=True)
    core = repository / "core.py"
    core.write_bytes(b"retained provenance writer")
    inputs = tuple(repository / path for path in subject.INPUTS)
    for path in inputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(path.name.encode())
    source_root = tmp_path / "source"
    directory = source_root / subject.SOURCE_ID
    crosswalk = directory / subject.CROSSWALK
    crosswalk.parent.mkdir(parents=True)
    crosswalk.write_bytes(b"source,prepared\n")
    qualified_inputs = {
        f"external/{subject.SOURCE_ID}/{subject.CROSSWALK}": crosswalk,
        **{f"external/source-{n:03d}": crosswalk for n in range(194)},
    }
    qualified = QualifiedReportSources(
        directory, qualified_inputs, subject.DESCRIPTOR_SHA256
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
        assert sys.argv[1:3] == ["--author-csv", str(inputs[0])]
        assert sys.argv[3:5] == ["--author-report", str(inputs[1])]
        assert sys.argv[5:7] == ["--published-csv", str(inputs[2])]
        assert sys.argv[7:9] == ["--published-report", str(inputs[3])]
        assert sys.argv[9:11] == ["--crosswalk-csv", str(crosswalk)]
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
        crosswalk,
        inputs,
    )


def invoke(case: Case, *, output: Path | None = None) -> None:
    subject.run(
        case.repository,
        case.source_root,
        subject.DESCRIPTOR,
        case.output if output is None else output,
    )


def test_three_outputs_and_all_inputs_unchanged(case: Case) -> None:
    before = tuple(path.read_bytes() for path in (*case.inputs, case.crosswalk))
    original_argv = sys.argv
    invoke(case)
    assert {path.name for path in case.output.iterdir()} == set(subject.OUTPUTS)
    assert tuple(path.read_bytes() for path in (*case.inputs, case.crosswalk)) == before
    assert sys.argv is original_argv


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
    with pytest.raises(ValueError, match="writer identity differs"):
        invoke(case)
    assert not case.output.exists()


def test_changed_input_during_writer_refused(
    case: Case, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = runpy.run_module

    def writer(module: str, *, run_name: str) -> None:
        original(module, run_name=run_name)
        case.inputs[1].write_bytes(b"changed report")

    monkeypatch.setattr(runpy, "run_module", writer)
    with pytest.raises(ValueError, match="inputs changed"):
        invoke(case)
    assert not case.output.exists()


def test_qualified_crosswalk_mutation_refused(
    case: Case, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = runpy.run_module

    def writer(module: str, *, run_name: str) -> None:
        original(module, run_name=run_name)
        case.crosswalk.write_bytes(b"changed crosswalk")

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
