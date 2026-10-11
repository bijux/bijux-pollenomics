"""Governed-edge CLI source confinement and native failure preservation."""

from __future__ import annotations

from pathlib import Path
import runpy
import sys

import pytest

from bijux_pollenomics_dev.source_completion.propagation import governed_edge_ledger


def _replay(root: Path) -> Path:
    replay = root / governed_edge_ledger.REPLAY
    replay.parent.mkdir(parents=True)
    replay.write_text("# governed replay\n", encoding="utf-8")
    return replay


def test_routes_exact_absent_output_and_restores_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    replay = _replay(tmp_path)
    calls: list[tuple[str, str, list[str]]] = []

    def invoke(path: str, *, run_name: str) -> None:
        calls.append((path, run_name, list(sys.argv)))

    monkeypatch.setattr(runpy, "run_path", invoke)
    original = sys.argv
    output = tmp_path / "artifacts/source-products"
    assert (
        governed_edge_ledger.main(
            ["--repository", str(tmp_path), "--output", str(output)]
        )
        == 0
    )
    assert calls == [
        (str(replay), "__main__", [str(replay), "--output-dir", str(output)])
    ]
    assert sys.argv is original
    assert not output.exists()


def test_native_refusal_remains_an_error_without_partial_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _replay(tmp_path)

    def refuse(*_args: object, **_kwargs: object) -> None:
        raise ValueError("native ledger refusal")

    monkeypatch.setattr(runpy, "run_path", refuse)
    original = sys.argv
    output = tmp_path / "artifacts/source-products"
    with pytest.raises(ValueError, match="native ledger refusal"):
        governed_edge_ledger.run(tmp_path, output)
    assert sys.argv is original
    assert not output.exists()


def test_missing_or_linked_replay_refused_before_loading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[object] = []
    monkeypatch.setattr(runpy, "run_path", lambda *_args, **_kwargs: calls.append(True))
    output = tmp_path / "artifacts/source-products"
    with pytest.raises(ValueError, match="regular repository file"):
        governed_edge_ledger.run(tmp_path, output)
    replay = _replay(tmp_path)
    replay.unlink()
    foreign = tmp_path / "foreign.py"
    foreign.write_text("# foreign", encoding="utf-8")
    replay.symlink_to(foreign)
    with pytest.raises(ValueError, match="regular repository file"):
        governed_edge_ledger.run(tmp_path, output)
    replay.unlink()
    replay.parent.rename(replay.parent.with_name("stored-ledger"))
    replay.parent.symlink_to(replay.parent.with_name("stored-ledger"))
    replay.write_text("# linked parent", encoding="utf-8")
    with pytest.raises(ValueError, match="regular repository file"):
        governed_edge_ledger.run(tmp_path, output)
    assert not calls


def test_existing_linked_and_external_destinations_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    artifacts = repository / "artifacts"
    artifacts.mkdir(parents=True)
    existing = artifacts / "existing"
    existing.mkdir()
    linked = artifacts / "linked"
    linked.symlink_to(tmp_path / "outside")
    parent = artifacts / "escape"
    parent.symlink_to(tmp_path, target_is_directory=True)
    calls: list[object] = []
    monkeypatch.setattr(runpy, "run_path", lambda *_args, **_kwargs: calls.append(True))
    for output in (artifacts, existing, linked, parent / "new", tmp_path / "outside"):
        with pytest.raises(ValueError, match="destination|symlink"):
            governed_edge_ledger.run(repository, output)
    assert not calls


def test_cli_rejects_missing_paths_and_source_overrides() -> None:
    for arguments in (
        ["--repository", "."],
        ["--output", "somewhere"],
        ["--repository", ".", "--output", "somewhere", "--output-dir", "other"],
    ):
        with pytest.raises(SystemExit, match="2"):
            governed_edge_ledger.main(arguments)
