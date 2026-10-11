"""Keep the WHH05 source-name witness tied to retained R inputs."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import subprocess

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.source_completion.pollen_taxonomy import (
    header_parity as subject,
)

CSV = (
    b"r_read_name,source_column_index,author_target,raw_column_sum,prepared_target_sum,sums_equal\n"
    b"Fagus,8,Fagus sylvatica,5,5,TRUE\n"
    b"Fraxinus,9,Fraxinus,1,1,TRUE\n"
    b"Juniperus,14,Juniperus,2,2,TRUE\n"
    b"Calluna,17,Calluna vulgaris,1364,1364,TRUE\n"
    b"Poaceae,18,Poaceae,138,138,TRUE\n"
)


@dataclass(frozen=True)
class Case:
    repository: Path
    source_root: Path
    output: Path
    script: Path
    author_file: Path


@pytest.fixture
def case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Case:
    repository = tmp_path / "repository"
    (repository / "artifacts/output").mkdir(parents=True)
    script = repository / "source.R"
    script.write_bytes(b"R original source")
    directory = tmp_path / "sources/landclim/author-reference"
    author_file = directory / subject.NEEDED[0]
    for name in subject.NEEDED:
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
    descriptor = repository / subject.DESCRIPTOR
    descriptor.parent.mkdir(parents=True)
    descriptor.write_bytes(b"qualified author descriptor")
    inputs = {
        subject.DESCRIPTOR.as_posix(): descriptor,
        **{subject.AUTHOR_SOURCE + name: directory / name for name in subject.NEEDED},
        **{
            f"external/landclim/author-reference/source-{index:03d}": author_file
            for index in range(190)
        },
    }
    qualified = QualifiedReportSources(directory, inputs, subject.DESCRIPTOR_SHA256)
    monkeypatch.setattr(
        subject, "validated_external_report_sources", lambda *_: qualified
    )
    monkeypatch.setattr(subject, "SCRIPT", Path("source.R"))
    monkeypatch.setattr(
        subject, "SCRIPT_SHA256", hashlib.sha256(script.read_bytes()).hexdigest()
    )

    def writer(
        command: list[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        assert command[:4] == ["Rscript", "--vanilla", str(script), str(directory)]
        assert check and capture_output and text and timeout == 60
        Path(command[-1]).write_bytes(CSV)
        return subprocess.CompletedProcess(command, 0, "five rows", "")

    monkeypatch.setattr(subprocess, "run", writer)
    return Case(
        repository,
        tmp_path / "sources",
        repository / "artifacts/output/whh05.csv",
        script,
        author_file,
    )


def invoke(case: Case) -> None:
    subject.run(case.repository, case.source_root, subject.DESCRIPTOR, case.output)


def test_original_route_and_exact_single_output(case: Case) -> None:
    invoke(case)
    assert case.output.read_bytes() == CSV


def test_changed_script_refused_before_r(case: Case) -> None:
    case.script.write_bytes(b"changed")
    with pytest.raises(ValueError, match="formatter identity differs"):
        invoke(case)
    assert not case.output.exists()


def test_author_source_mutation_during_r_refused(
    case: Case, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = subprocess.run

    def changed(
        command: list[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        result = original(
            command,
            check=check,
            capture_output=capture_output,
            text=text,
            timeout=timeout,
        )
        case.author_file.write_bytes(b"changed")
        return result

    monkeypatch.setattr(subprocess, "run", changed)
    with pytest.raises(ValueError, match="inputs changed during parsing"):
        invoke(case)
    assert not case.output.exists()


def test_unsupported_parser_rows_refused(
    case: Case, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = subprocess.run

    def changed(
        command: list[str],
        *,
        check: bool,
        capture_output: bool,
        text: bool,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        result = original(
            command,
            check=check,
            capture_output=capture_output,
            text=text,
            timeout=timeout,
        )
        Path(command[-1]).write_bytes(CSV.replace(b"Poaceae,18", b"Poaceae,19"))
        return result

    monkeypatch.setattr(subprocess, "run", changed)
    with pytest.raises(ValueError, match="witness differs"):
        invoke(case)
    assert not case.output.exists()


def test_wrong_descriptor_refused(case: Case) -> None:
    with pytest.raises(ValueError, match="descriptor differs"):
        subject.run(case.repository, case.source_root, Path("wrong.json"), case.output)
    assert not case.output.exists()


def test_outside_artifacts_refused(case: Case) -> None:
    with pytest.raises(ReportRebuildError, match="artifact"):
        subject.run(
            case.repository,
            case.source_root,
            subject.DESCRIPTOR,
            case.repository / "docs/report/whh05.csv",
        )


def test_existing_output_refused(case: Case) -> None:
    case.output.write_bytes(b"existing")
    with pytest.raises(ReportRebuildError, match="must be absent"):
        invoke(case)
    assert case.output.read_bytes() == b"existing"
