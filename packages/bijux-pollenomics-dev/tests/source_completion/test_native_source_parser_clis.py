"""Fixed native-parser and published-window report routes preserve refusals."""

from __future__ import annotations

import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest

NAMES = ("neotoma.swedish_native_sequences", "essd.published_window_uncertainty")


def _module(name: str) -> ModuleType:
    return importlib.import_module(f"bijux_pollenomics_dev.source_completion.{name}")


@pytest.mark.parametrize("name", NAMES)
def test_fixed_source_route_and_argument_restoration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    module = _module(name)
    monkeypatch.setattr(
        module.importlib.util,
        "find_spec",
        lambda *_: SimpleNamespace(origin=str(tmp_path / module.CORE_PATH)),
    )
    calls: list[tuple[str, str, list[str]]] = []

    def invoke(core: str, *, run_name: str) -> None:
        calls.append((core, run_name, list(sys.argv)))

    monkeypatch.setattr(module.runpy, "run_module", invoke)
    original = sys.argv
    output = tmp_path / "artifacts/source-products"
    assert module.main(["--repository", str(tmp_path), "--output", str(output)]) == 0
    if name.startswith("neotoma."):
        arguments = [
            module.CORE,
            "--data-root",
            str(tmp_path / "data/neotoma/raw/neotoma_pollen_dataset_downloads"),
            "--destination",
            str(output),
        ]
    else:
        source = (
            tmp_path
            / "docs/report/publication-replay/landclim-published-window-provenance"
        )
        arguments = [
            module.CORE,
            "--correspondence-csv",
            str(source / "paper-correspondence.csv"),
            "--provenance-report",
            str(source / "report.json"),
            "--output",
            str(output),
        ]
    assert calls == [(module.CORE, "__main__", arguments)]
    assert sys.argv is original
    assert not output.exists()


@pytest.mark.parametrize("name", NAMES)
def test_native_failure_preserves_error_and_process_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    module = _module(name)
    monkeypatch.setattr(
        module.importlib.util,
        "find_spec",
        lambda *_: SimpleNamespace(origin=str(tmp_path / module.CORE_PATH)),
    )

    def refuse(*_args: object, **_kwargs: object) -> None:
        raise ValueError("native source mismatch")

    monkeypatch.setattr(module.runpy, "run_module", refuse)
    original = sys.argv
    output = tmp_path / "artifacts/source-products"
    with pytest.raises(ValueError, match="native source mismatch"):
        module.run(tmp_path, output)
    assert sys.argv is original
    assert not output.exists()


@pytest.mark.parametrize("name", NAMES)
def test_missing_or_foreign_writer_refused_before_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    module = _module(name)
    calls: list[object] = []
    monkeypatch.setattr(
        module.runpy, "run_module", lambda *_args, **_kwargs: calls.append(True)
    )
    original = sys.argv
    for spec in (
        None,
        SimpleNamespace(origin=None),
        SimpleNamespace(origin=str(tmp_path / "foreign.py")),
    ):
        monkeypatch.setattr(
            module.importlib.util, "find_spec", lambda *_, result=spec: result
        )
        with pytest.raises(ValueError, match="origin"):
            module.run(tmp_path, tmp_path / "artifacts/source-products")
    assert not calls
    assert sys.argv is original


@pytest.mark.parametrize("name", NAMES)
def test_existing_linked_and_external_outputs_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    module = _module(name)
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
    monkeypatch.setattr(
        module.runpy, "run_module", lambda *_args, **_kwargs: calls.append(True)
    )
    for output in (artifacts, existing, linked, parent / "new", tmp_path / "outside"):
        with pytest.raises(ValueError, match="destination|symlink"):
            module.run(repository, output)
    assert not calls


@pytest.mark.parametrize("name", NAMES)
def test_cli_requires_paths_and_refuses_source_override(name: str) -> None:
    module = _module(name)
    for arguments in (
        ["--repository", "."],
        ["--output", "somewhere"],
        ["--repository", ".", "--output", "somewhere", "--data-root", "other"],
    ):
        with pytest.raises(SystemExit, match="2"):
            module.main(arguments)
