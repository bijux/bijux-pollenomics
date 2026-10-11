"""Stage-specific Nordic input routes avoid prediction fitting and scoring."""

from __future__ import annotations

import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest

NAMES = ("swedish_author_inputs", "dalmutladdo_prediction_freeze")


def _module(name: str) -> ModuleType:
    return importlib.import_module(
        f"bijux_pollenomics_dev.source_completion.nordic.{name}"
    )


def _bind(module: ModuleType, root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if hasattr(module, "CORE"):
        monkeypatch.setattr(
            module.importlib.util,
            "find_spec",
            lambda *_: SimpleNamespace(origin=str(root / module.CORE_PATH)),
        )
    else:
        relative = module.REPLAY
        assert isinstance(relative, Path)
        path = root / relative
        path.parent.mkdir(parents=True)
        path.write_text("# source-bound replay\n", encoding="utf-8")


@pytest.mark.parametrize("name", NAMES)
def test_routes_only_preparation_or_saved_prediction_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    module = _module(name)
    _bind(module, tmp_path, monkeypatch)
    calls: list[tuple[str, str, list[str]]] = []

    def invoke(path: str, *, run_name: str) -> None:
        calls.append((path, run_name, list(sys.argv)))

    target = "run_module" if name == "swedish_author_inputs" else "run_path"
    monkeypatch.setattr(module.runpy, target, invoke)
    original = sys.argv
    output = tmp_path / "artifacts/source-products"
    assert module.main(["--repository", str(tmp_path), "--output", str(output)]) == 0
    source = (
        "bijux_pollenomics_dev.source_completion.swedish_author_target_pollen"
        if name == "swedish_author_inputs"
        else str(
            tmp_path
            / "docs/report/regions/nordic/dalmutladdo-author-target-age-interval/replay.py"
        )
    )
    stage = "prepare" if name == "swedish_author_inputs" else "freeze"
    assert calls == [
        (
            source,
            "__main__",
            [source, stage, "--repository", str(tmp_path), "--output", str(output)],
        )
    ]
    assert sys.argv is original
    assert not output.exists()


@pytest.mark.parametrize("name", NAMES)
def test_native_error_preserves_failure_and_process_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    module = _module(name)
    _bind(module, tmp_path, monkeypatch)

    def refuse(*_args: object, **_kwargs: object) -> None:
        raise ValueError("native source refusal")

    monkeypatch.setattr(
        module.runpy,
        "run_module" if name == "swedish_author_inputs" else "run_path",
        refuse,
    )
    original = sys.argv
    output = tmp_path / "artifacts/source-products"
    with pytest.raises(ValueError, match="native source refusal"):
        module.run(tmp_path, output)
    assert sys.argv is original
    assert not output.exists()


@pytest.mark.parametrize("name", NAMES)
def test_output_confinement_precedes_source_loading(
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
        module.runpy,
        "run_module" if name == "swedish_author_inputs" else "run_path",
        lambda *_args, **_kwargs: calls.append(True),
    )
    for output in (artifacts, existing, linked, parent / "new", tmp_path / "outside"):
        with pytest.raises(ValueError, match="destination|symlink"):
            module.run(repository, output)
    assert not calls


def test_swedish_writer_origin_must_match_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module("swedish_author_inputs")
    calls: list[object] = []
    monkeypatch.setattr(
        module.runpy, "run_module", lambda *_args, **_kwargs: calls.append(True)
    )
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


def test_missing_and_linked_dalmutladdo_replay_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module("dalmutladdo_prediction_freeze")
    output = tmp_path / "artifacts/source-products"
    with pytest.raises(ValueError, match="regular repository file"):
        module.run(tmp_path, output)
    _bind(module, tmp_path, monkeypatch)
    relative = module.REPLAY
    assert isinstance(relative, Path)
    replay = tmp_path / relative
    replay.unlink()
    foreign = tmp_path / "foreign.py"
    foreign.write_text("# foreign", encoding="utf-8")
    replay.symlink_to(foreign)
    with pytest.raises(ValueError, match="regular repository file"):
        module.run(tmp_path, output)
    replay.unlink()
    replay.parent.rename(replay.parent.with_name("stored-replay"))
    replay.parent.symlink_to(replay.parent.with_name("stored-replay"))
    replay.write_text("# linked parent", encoding="utf-8")
    with pytest.raises(ValueError, match="regular repository file"):
        module.run(tmp_path, output)
    assert not output.exists()


@pytest.mark.parametrize("name", NAMES)
def test_cli_requires_paths_and_rejects_stage_override(name: str) -> None:
    module = _module(name)
    for arguments in (
        ["--repository", "."],
        ["--output", "somewhere"],
        ["--repository", ".", "--output", "somewhere", "--stage", "score"],
    ):
        with pytest.raises(SystemExit, match="2"):
            module.main(arguments)
