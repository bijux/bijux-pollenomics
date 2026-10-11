"""Source routing and refusal preservation for metadata and parameter adapters."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys
from types import ModuleType

import pytest

NAMES = ("study_metadata.landclim", "love.parameter_correspondence")


def _module(name: str) -> ModuleType:
    return importlib.import_module(f"bijux_pollenomics_dev.source_completion.{name}")


def _verifier(module: ModuleType, repository: Path, content: str = "") -> Path:
    relative = module.VERIFIER
    assert isinstance(relative, Path)
    script = repository / relative
    script.parent.mkdir(parents=True)
    script.write_text(content)
    return script


def test_landclim_uses_fixed_workbook_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _module(NAMES[0])
    calls: list[tuple[Path, Path]] = []
    monkeypatch.setattr(
        module,
        "publish_study_input_products",
        lambda source, output: calls.append((source, output)),
    )
    output = tmp_path / "artifacts/source-products"
    assert module.main(["--repository", str(tmp_path), "--output", str(output)]) == 0
    assert calls == [(tmp_path / "data/landclim/raw", output)]
    assert not output.exists()


def test_love_runs_fixed_verifier_with_original_arguments_restored(
    tmp_path: Path,
) -> None:
    module = _module(NAMES[1])
    _verifier(
        module,
        tmp_path,
        "import json, sys\nfrom pathlib import Path\nPath(sys.argv[-1]).write_text(json.dumps(sys.argv))\n",
    )
    output = tmp_path / "artifacts/report.json"
    output.parent.mkdir()
    original = sys.argv
    assert module.main(["--repository", str(tmp_path), "--output", str(output)]) == 0

    assert json.loads(output.read_bytes()) == [
        str(tmp_path / module.VERIFIER),
        "--repository",
        str(tmp_path),
        "--output",
        str(output),
    ]
    assert sys.argv is original


@pytest.mark.parametrize("name", NAMES)
def test_output_guards_run_before_source_writer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    module = _module(name)
    repository = tmp_path / "repository"
    artifacts = repository / "artifacts"
    artifacts.mkdir(parents=True)
    existing = artifacts / "existing"
    existing.mkdir()
    linked = artifacts / "linked"
    linked.symlink_to(tmp_path / "absent")
    parent = artifacts / "escape"
    parent.symlink_to(tmp_path, target_is_directory=True)
    calls: list[object] = []
    if name == NAMES[0]:
        monkeypatch.setattr(
            module, "publish_study_input_products", lambda *_: calls.append(True)
        )
    else:
        _verifier(module, repository)
        monkeypatch.setattr(
            module.runpy, "run_path", lambda *_args, **_kwargs: calls.append(True)
        )
    for output in (existing, artifacts, linked, parent / "new", tmp_path / "outside"):
        with pytest.raises(ValueError, match="destination|symlink"):
            module.run(repository, output)
    assert not calls


@pytest.mark.parametrize("name", NAMES)
def test_native_failure_is_preserved_without_output_or_argument_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    module = _module(name)

    def refuse(*_args: object, **_kwargs: object) -> None:
        raise ValueError("native source refused")

    if name == NAMES[0]:
        monkeypatch.setattr(module, "publish_study_input_products", refuse)
    else:
        _verifier(module, tmp_path)
        monkeypatch.setattr(module.runpy, "run_path", refuse)
    output = tmp_path / "artifacts/report"
    original = sys.argv
    with pytest.raises(ValueError, match="native source refused"):
        module.run(tmp_path, output)
    assert sys.argv is original
    assert not output.exists()


def test_love_refuses_missing_and_linked_verifier_before_running(
    tmp_path: Path,
) -> None:
    module = _module(NAMES[1])
    output = tmp_path / "artifacts/report.json"
    with pytest.raises(ValueError, match="regular repository file"):
        module.run(tmp_path, output)
    verifier = _verifier(module, tmp_path)
    verifier.unlink()
    external = tmp_path / "outside.py"
    external.write_text("raise AssertionError('must not execute')")
    verifier.symlink_to(external)
    with pytest.raises(ValueError, match="regular repository file"):
        module.run(tmp_path, output)
    assert not output.exists()


@pytest.mark.parametrize("name", NAMES)
def test_cli_requires_fixed_repository_and_output_flags(name: str) -> None:
    module = _module(name)
    with pytest.raises(SystemExit, match="2"):
        module.main(["--repository", "."])
    with pytest.raises(SystemExit, match="2"):
        module.main(["--output", "somewhere"])
    with pytest.raises(SystemExit, match="2"):
        module.main(["--repository", ".", "--output", "somewhere", "--capture", "x"])
