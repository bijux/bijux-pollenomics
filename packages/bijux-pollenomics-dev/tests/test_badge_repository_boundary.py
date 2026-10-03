"""Repository-bound badge renderer behavior from a foreign installed module path."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import sys
from types import ModuleType

import pytest

SOURCE = (
    Path(__file__).resolve().parents[1] / "src/bijux_pollenomics_dev/docs/badge_sync.py"
)
REPOSITORY = Path.cwd().resolve()


def _load_from_foreign_origin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, root: Path
) -> ModuleType:
    installed = tmp_path / "site-packages/bijux_pollenomics_dev/docs/badge_sync.py"
    installed.parent.mkdir(parents=True)
    shutil.copyfile(SOURCE, installed)
    monkeypatch.chdir(root)
    name = "installed_badge_boundary"
    spec = importlib.util.spec_from_file_location(name, installed)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


def test_installed_module_uses_invoking_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _load_from_foreign_origin(tmp_path, monkeypatch, REPOSITORY)
    assert module.__file__ is not None
    assert Path(module.__file__).is_relative_to(tmp_path)
    assert module.REPO_ROOT == REPOSITORY
    assert module.SHARED_RENDERER == (
        REPOSITORY / ".bijux/shared/bijux-makes-py/repository/badge_renderer.py"
    )
    assert len(module.iter_badge_targets()) == 5
    assert module.synchronize_badges(check=True) == []


def test_installed_module_refuses_nonrepository_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(RuntimeError, match="requires the repository root"):
        _load_from_foreign_origin(tmp_path, monkeypatch, tmp_path)


def test_installed_module_refuses_other_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "pyproject.toml").write_text('[tool.other]\nrepository = "other"\n')
    with pytest.raises(RuntimeError, match="Not a bijux-pollenomics"):
        _load_from_foreign_origin(tmp_path, monkeypatch, tmp_path)


def test_shared_renderer_symlink_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.bijux_pollenomics]\nrepository = "bijux-pollenomics"\n'
    )
    renderer = tmp_path / ".bijux/shared/bijux-makes-py/repository/badge_renderer.py"
    renderer.parent.mkdir(parents=True)
    renderer.symlink_to(
        REPOSITORY / ".bijux/shared/bijux-makes-py/repository/badge_renderer.py"
    )
    with pytest.raises(RuntimeError, match="symlink"):
        _load_from_foreign_origin(tmp_path, monkeypatch, tmp_path)
