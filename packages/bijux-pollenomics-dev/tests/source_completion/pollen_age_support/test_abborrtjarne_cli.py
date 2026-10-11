"""Check the ABBO adapter's complete stage and declared-output boundary."""

from __future__ import annotations

import json
from pathlib import Path
import runpy
import sys

import pytest

from bijux_pollenomics_dev.source_completion.pollen_age_support import (
    abborrtjarne as adapter,
)


def _repository(tmp_path: Path) -> Path:
    repo = tmp_path / "repository"
    (repo / "artifacts").mkdir(parents=True)
    source = repo / adapter.PARENT
    source.mkdir(parents=True)
    for filename in ("dataset-53995.json", "dataset-54001.json"):
        (source / filename).write_text(f'{{"source":"{filename}"}}\n')
    return repo


def _writer(repository: Path, stage: Path, *, omit: str = "", alter: str = "") -> None:
    del repository
    stage.mkdir()
    for relative in adapter.STAGE_FILES - {omit}:
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if relative in adapter.COPIES:
            filename = Path(relative).name
            content = f'{{"source":"{filename}"}}\n'
        else:
            content = f"owned {relative}\n"
        target.write_text("changed\n" if relative == alter else content)


def test_complete_stage_exposes_only_owned_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _repository(tmp_path)
    monkeypatch.setattr(adapter, "_invoke_core", _writer)
    output = repo / "artifacts/owner/source-products"
    receipt = adapter.run(repo, output)
    actual = {
        p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()
    }
    assert actual == set(adapter.OWNED)
    assert set(receipt["complete_stage_sha256"]) == set(adapter.STAGE_FILES)
    assert json.loads(capsys.readouterr().out) == receipt
    stage = repo / receipt["complete_stage_path"]
    assert {
        p.relative_to(stage).as_posix() for p in stage.rglob("*") if p.is_file()
    } == set(adapter.STAGE_FILES)
    for relative in adapter.COPIES:
        assert (stage / relative).read_bytes() == (
            repo / adapter.PARENT / Path(relative).name
        ).read_bytes()


def test_missing_intermediate_refuses_complete_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repository(tmp_path)
    monkeypatch.setattr(
        adapter,
        "_invoke_core",
        lambda repository, stage: _writer(
            repository, stage, omit="prepared/dataset-54001.json"
        ),
    )
    output = repo / "artifacts/owner/source-products"
    with pytest.raises(ValueError, match="population differs"):
        adapter.run(repo, output)
    assert not output.exists()


def test_changed_intermediate_refuses_source_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repository(tmp_path)
    monkeypatch.setattr(
        adapter,
        "_invoke_core",
        lambda repository, stage: _writer(
            repository, stage, alter="prepared/dataset-53995.json"
        ),
    )
    with pytest.raises(ValueError, match="copied source profile differs"):
        adapter.run(repo, repo / "artifacts/owner/source-products")


def test_unrecognized_stage_file_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repository(tmp_path)

    def writer(repository: Path, stage: Path) -> None:
        _writer(repository, stage)
        (stage / "unexpected.json").write_text("{}\n")

    monkeypatch.setattr(adapter, "_invoke_core", writer)
    with pytest.raises(ValueError, match="population differs"):
        adapter.run(repo, repo / "artifacts/owner/source-products")


def test_existing_or_symlinked_output_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repository(tmp_path)
    monkeypatch.setattr(adapter, "_invoke_core", _writer)
    existing = repo / "artifacts/owner"
    existing.mkdir()
    with pytest.raises(ValueError, match="absent repository artifact output"):
        adapter.run(repo, existing)
    linked = repo / "artifacts/linked"
    linked.symlink_to(existing, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        adapter.run(repo, linked / "source-products")


@pytest.mark.parametrize("fails", (False, True))
def test_native_prepare_route_and_argument_restoration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fails: bool
) -> None:
    repo = _repository(tmp_path)
    replay = repo / adapter.REPLAY
    replay.parent.mkdir(parents=True)
    replay.write_text("# source-bound replay\n", encoding="utf-8")
    stage = repo / "artifacts/stage"
    calls: list[tuple[str, str, list[str]]] = []

    def invoke(path: str, *, run_name: str) -> None:
        calls.append((path, run_name, list(sys.argv)))
        if fails:
            raise ValueError("native preparation refusal")

    monkeypatch.setattr(runpy, "run_path", invoke)
    original = sys.argv
    if fails:
        with pytest.raises(ValueError, match="native preparation refusal"):
            adapter._invoke_core(repo, stage)
    else:
        adapter._invoke_core(repo, stage)
    assert calls == [
        (
            str(replay),
            "__main__",
            [str(replay), "prepare", "--repository", str(repo), "--output", str(stage)],
        )
    ]
    assert sys.argv is original
    assert not stage.exists()


def test_failed_stage_is_retained_and_cannot_be_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repository(tmp_path)
    calls: list[object] = []

    def refuse(repository: Path, stage: Path) -> None:
        calls.append(True)
        _writer(repository, stage)
        raise ValueError("native refusal after stage writes")

    monkeypatch.setattr(adapter, "_invoke_core", refuse)
    output = repo / "artifacts/owner/source-products"
    with pytest.raises(ValueError, match="native refusal after stage writes"):
        adapter.run(repo, output)
    stages = list(
        (repo / "artifacts/jobs/report-preparation/abborrtjarne").glob(
            "*/complete-stage"
        )
    )
    assert len(stages) == 1
    assert {
        p.relative_to(stages[0]).as_posix() for p in stages[0].rglob("*") if p.is_file()
    } == set(adapter.STAGE_FILES)
    with pytest.raises(ValueError, match="stage already exists"):
        adapter.run(repo, output)
    assert len(calls) == 1
    assert not output.exists()


@pytest.mark.parametrize("unsafe", ("stage-link", "file-link", "extra-directory"))
def test_unsafe_stage_refused_before_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, unsafe: str
) -> None:
    repo = _repository(tmp_path)

    def writer(repository: Path, stage: Path) -> None:
        if unsafe == "stage-link":
            outside = tmp_path / "outside"
            _writer(repository, outside)
            stage.symlink_to(outside, target_is_directory=True)
        else:
            _writer(repository, stage)
            if unsafe == "file-link":
                linked = stage / "age-bin-support.csv"
                linked.unlink()
                linked.symlink_to(repo / adapter.PARENT / "dataset-53995.json")
            else:
                (stage / "unrecognized").mkdir()

    monkeypatch.setattr(adapter, "_invoke_core", writer)
    output = repo / "artifacts/owner/source-products"
    with pytest.raises(
        ValueError, match="real directory|unsafe path|population differs"
    ):
        adapter.run(repo, output)
    assert not output.exists()


def test_staging_ancestor_link_refused_before_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repository(tmp_path)
    (repo / "artifacts/jobs").symlink_to(tmp_path, target_is_directory=True)
    calls: list[object] = []
    monkeypatch.setattr(adapter, "_invoke_core", lambda *_: calls.append(True))
    with pytest.raises(ValueError, match="stage ancestor"):
        adapter.run(repo, repo / "artifacts/owner/source-products")
    assert not calls


def test_cli_requires_paths_and_rejects_prediction_stage() -> None:
    for arguments in (
        ["--repository", "."],
        ["--output", "somewhere"],
        ["--repository", ".", "--output", "somewhere", "--stage", "predict"],
    ):
        with pytest.raises(SystemExit, match="2"):
            adapter.main(arguments)
