"""Neotoma ownership CLI capture, source confinement and failure semantics."""

from __future__ import annotations

from pathlib import Path
import runpy
import sys

import pytest

from bijux_pollenomics_dev.source_completion.neotoma import relational_summary


def _verifier(repository: Path) -> Path:
    verifier = repository / relational_summary.VERIFIER
    verifier.parent.mkdir(parents=True)
    verifier.write_text("# governed verifier\n", encoding="utf-8")
    return verifier


def test_captures_exact_verifier_output_with_fixed_source_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    verifier = _verifier(tmp_path)
    calls: list[tuple[str, str, list[str]]] = []
    payload = '{\n  "label": "Åland",\n  "count": 18\n}\n'

    def invoke(path: str, *, run_name: str) -> dict[str, object]:
        calls.append((path, run_name, list(sys.argv)))

        def publish() -> None:
            print(payload, end="")

        return {"main": publish}

    monkeypatch.setattr(runpy, "run_path", invoke)
    original = sys.argv
    output = tmp_path / "artifacts/summary/report.json"
    assert (
        relational_summary.main(
            ["--repository", str(tmp_path), "--output", str(output)]
        )
        == 0
    )
    assert calls == [
        (
            str(verifier),
            "_neotoma_ownership_verifier",
            [str(verifier), "--source-root", str(tmp_path / "data/neotoma/relational")],
        )
    ]
    assert output.read_bytes() == payload.encode("utf-8")
    assert sys.argv is original


@pytest.mark.parametrize("during_load", (False, True))
def test_native_failure_restores_arguments_without_partial_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, during_load: bool
) -> None:
    _verifier(tmp_path)

    def refuse() -> None:
        print("partial output")
        raise ValueError("native ownership refusal")

    def invoke(*_args: object, **_kwargs: object) -> dict[str, object]:
        if during_load:
            refuse()
        return {"main": refuse}

    monkeypatch.setattr(runpy, "run_path", invoke)
    original = sys.argv
    output = tmp_path / "artifacts/summary/report.json"
    with pytest.raises(ValueError, match="native ownership refusal"):
        relational_summary.run(tmp_path, output)
    assert sys.argv is original
    assert not output.parent.exists()


def test_invalid_destinations_refused_before_loading_verifier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    artifacts = repository / "artifacts"
    artifacts.mkdir(parents=True)
    existing = artifacts / "existing.json"
    existing.write_text("original", encoding="utf-8")
    linked = artifacts / "linked.json"
    linked.symlink_to(tmp_path / "outside.json")
    parent = artifacts / "escape"
    parent.symlink_to(tmp_path, target_is_directory=True)
    calls: list[object] = []
    monkeypatch.setattr(
        runpy,
        "run_path",
        lambda *_args, **_kwargs: calls.append(True),
    )
    for output in (existing, artifacts, linked, parent / "new.json", tmp_path / "out"):
        with pytest.raises(ValueError, match="destination|symlink"):
            relational_summary.run(repository, output)
    assert not calls
    assert existing.read_text(encoding="utf-8") == "original"


def test_missing_and_linked_verifier_refused_before_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[object] = []
    monkeypatch.setattr(
        runpy,
        "run_path",
        lambda *_args, **_kwargs: calls.append(True),
    )
    output = tmp_path / "artifacts/report.json"
    with pytest.raises(ValueError, match="regular repository file"):
        relational_summary.run(tmp_path, output)
    verifier = _verifier(tmp_path)
    verifier.unlink()
    foreign = tmp_path / "foreign.py"
    foreign.write_text("# foreign", encoding="utf-8")
    verifier.symlink_to(foreign)
    with pytest.raises(ValueError, match="regular repository file"):
        relational_summary.run(tmp_path, output)
    verifier.unlink()
    verifier.parent.rename(verifier.parent.with_name("stored-neotoma"))
    verifier.parent.symlink_to(verifier.parent.with_name("stored-neotoma"))
    (verifier.parent / verifier.name).write_text("# linked parent", encoding="utf-8")
    with pytest.raises(ValueError, match="regular repository file"):
        relational_summary.run(tmp_path, output)
    assert not calls
    assert not output.exists()


def test_cli_requires_repository_and_output_and_rejects_source_override() -> None:
    for arguments in (
        ["--repository", "."],
        ["--output", "somewhere"],
        ["--repository", ".", "--output", "somewhere", "--source-root", "x"],
    ):
        with pytest.raises(SystemExit, match="2"):
            relational_summary.main(arguments)
