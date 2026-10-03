"""Keep the author formatter's complete source stage and exact summary."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import hashlib
from pathlib import Path
import shutil
import subprocess

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.source_completion.pollen_taxonomy import (
    author_formatter_comparison as subject,
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
    script.write_bytes(b"original formatter")
    directory = tmp_path / "sources/landclim/author-reference"
    for name in subject.SOURCE_FILES:
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
    author_file = directory / subject.SOURCE_FILES[0]
    descriptor = repository / subject.DESCRIPTOR
    descriptor.parent.mkdir(parents=True)
    descriptor.write_bytes(b"qualified descriptor")
    inputs = {
        subject.DESCRIPTOR.as_posix(): descriptor,
        **{subject.SOURCE_ID + name: directory / name for name in subject.SOURCE_FILES},
        **{
            f"external/landclim/author-reference/source-{index:03d}": author_file
            for index in range(187)
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
        capture_output: bool,
        text: bool,
        check: bool,
        timeout: int,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        assert command[:4] == ["Rscript", "--vanilla", str(script), str(directory)]
        assert capture_output and text and check and timeout == 180
        assert all(
            env[key] == "1"
            for key in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
                "BLIS_NUM_THREADS",
            )
        )
        stage = Path(command[-1])
        work = stage / "work"
        work.mkdir(parents=True)
        rows = [
            "site,sample_rows,prepared_rows,prepared_columns,matched_cells,compared_cells,cell_equal,byte_equal"
        ]
        for index in range(17):
            site = f"SITE{index:02d}"
            site_dir = work / site
            site_dir.mkdir()
            for name in (*subject.STAGE_FILES, f"LRAready_{site}.csv"):
                (site_dir / name).write_bytes(b"stage")
            rows.append(f"{site},10,25,26,650,650,TRUE,TRUE")
        (stage / "sites.csv").write_text("\n".join(rows) + "\n")
        return subprocess.CompletedProcess(
            command, 0, "17 author sites replayed; 17 cell-equal; 17 byte-equal\n", ""
        )

    monkeypatch.setattr(subprocess, "run", writer)
    return Case(
        repository,
        tmp_path / "sources",
        repository / "artifacts/output/sites.csv",
        script,
        author_file,
    )


def invoke(case: Case) -> None:
    subject.run(case.repository, case.source_root, subject.DESCRIPTOR, case.output)


def _alter_writer(
    monkeypatch: pytest.MonkeyPatch, change: Callable[[Path], object]
) -> None:
    original = subprocess.run

    def changed(
        command: list[str],
        *,
        capture_output: bool,
        text: bool,
        check: bool,
        timeout: int,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        result = original(
            command,
            capture_output=capture_output,
            text=text,
            check=check,
            timeout=timeout,
            env=env,
        )
        change(Path(command[-1]))
        return result

    monkeypatch.setattr(subprocess, "run", changed)


def test_exact_summary_and_complete_retained_stage(case: Case) -> None:
    invoke(case)
    assert case.output.read_bytes().count(b"\n") == 18
    stages = list(
        (case.repository / "artifacts/jobs/report-preparation/author-formatter").glob(
            "*/complete-stage"
        )
    )
    assert len(stages) == 1
    assert len(list((stages[0] / "work").rglob("*.csv"))) == 68


def test_source_changed_during_r_refused(
    case: Case, monkeypatch: pytest.MonkeyPatch
) -> None:
    _alter_writer(monkeypatch, lambda _: case.author_file.write_bytes(b"changed"))
    with pytest.raises(ValueError, match="inputs changed"):
        invoke(case)
    assert not case.output.exists()


def test_extra_intermediate_refused(
    case: Case, monkeypatch: pytest.MonkeyPatch
) -> None:
    def add_extra(stage: Path) -> None:
        (stage / "work/SITE00/unclaimed.csv").write_bytes(b"extra")

    _alter_writer(monkeypatch, add_extra)
    with pytest.raises(ValueError, match="intermediate stage differs"):
        invoke(case)
    assert not case.output.exists()


def test_false_counter_refused(case: Case, monkeypatch: pytest.MonkeyPatch) -> None:
    def alter(stage: Path) -> None:
        path = stage / "sites.csv"
        path.write_bytes(path.read_bytes().replace(b"650,650,TRUE", b"650,649,TRUE", 1))

    _alter_writer(monkeypatch, alter)
    with pytest.raises(ValueError, match="comparison rows differ"):
        invoke(case)
    assert not case.output.exists()


def test_changed_r_script_refused(case: Case) -> None:
    case.script.write_bytes(b"changed")
    with pytest.raises(ValueError, match="R source differs"):
        invoke(case)
    assert not case.output.exists()


def test_wrong_descriptor_refused(case: Case) -> None:
    with pytest.raises(ValueError, match="descriptor differs"):
        subject.run(case.repository, case.source_root, Path("wrong.json"), case.output)


def test_outside_artifact_destination_refused(case: Case) -> None:
    with pytest.raises(ReportRebuildError, match="artifact"):
        subject.run(
            case.repository,
            case.source_root,
            subject.DESCRIPTOR,
            case.repository / "docs/report/sites.csv",
        )


def test_reused_complete_stage_refused(case: Case) -> None:
    invoke(case)
    case.output.unlink()
    with pytest.raises(ValueError, match="stage must be absent"):
        invoke(case)


def test_linked_stage_ancestor_refused(case: Case, tmp_path: Path) -> None:
    jobs = case.repository / "artifacts/jobs"
    jobs.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (jobs / "report-preparation").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ReportRebuildError, match="not a real regular path"):
        invoke(case)
    assert not case.output.exists()
    assert list(outside.iterdir()) == []


def test_changed_publish_copy_refused_without_target(
    case: Case, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = shutil.copyfile

    def changed(source: Path, destination: Path) -> Path:
        original(source, destination)
        destination.write_bytes(b"changed")
        return destination

    monkeypatch.setattr(shutil, "copyfile", changed)
    with pytest.raises(ValueError, match="staged copy changed"):
        invoke(case)
    assert not case.output.exists()
