"""Fixed-source CLI routing and refusal preservation for SEAD owner adapters."""

from __future__ import annotations

import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest

NAMES = ("numerical_values", "pollen_dataset_screen", "integer_values", "relations")


def _module(name: str) -> ModuleType:
    return importlib.import_module(
        f"bijux_pollenomics_dev.source_completion.sead.{name}"
    )


def _bind_origin(
    module: ModuleType, root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        module.importlib.util,
        "find_spec",
        lambda *_: SimpleNamespace(origin=str(root / module.CORE_PATH)),
    )


@pytest.mark.parametrize("name", NAMES)
def test_routes_fixed_source_arguments_and_restores_process_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    module = _module(name)
    _bind_origin(module, tmp_path, monkeypatch)
    calls: list[tuple[str, str, list[str]]] = []

    def invoke(core: str, *, run_name: str) -> None:
        calls.append((core, run_name, list(sys.argv)))

    monkeypatch.setattr(module.runpy, "run_module", invoke)
    original = sys.argv
    output = tmp_path / "artifacts/source-products"
    assert module.main(["--repository", str(tmp_path), "--output", str(output)]) == 0
    assert calls == [
        (
            module.CORE,
            "__main__",
            [
                module.CORE,
                "--data-root",
                str(tmp_path / "data"),
                "--output",
                str(output),
            ],
        )
    ]
    assert sys.argv is original
    assert not output.exists()


@pytest.mark.parametrize("name", NAMES)
def test_source_failure_preserves_error_and_restores_process_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    module = _module(name)
    _bind_origin(module, tmp_path, monkeypatch)

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
def test_missing_or_foreign_core_origin_refused_before_execution(
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
def test_existing_linked_and_external_destinations_refused_before_core(
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
    for output in (existing, artifacts, linked, parent / "new", tmp_path / "outside"):
        with pytest.raises(ValueError, match="destination|symlink"):
            module.run(repository, output)
    assert not calls


@pytest.mark.parametrize("name", NAMES)
def test_cli_requires_fixed_repository_and_output_arguments(name: str) -> None:
    module = _module(name)
    with pytest.raises(SystemExit, match="2"):
        module.main(["--repository", "."])
    with pytest.raises(SystemExit, match="2"):
        module.main(["--output", "somewhere"])
    with pytest.raises(SystemExit, match="2"):
        module.main(["--repository", ".", "--output", "somewhere", "--data-root", "x"])
