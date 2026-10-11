"""Tests for repository-root discovery independent of module depth."""

from pathlib import Path

import pytest

from bijux_pollenomics.core.repository import (
    RepositoryRootNotFoundError,
    find_repository_root,
    repository_data_root,
)
from tests.support.repository import REPOSITORY_ROOT


def test_find_repository_root_from_nested_source() -> None:
    nested_source = (
        REPOSITORY_ROOT
        / "packages/bijux-pollenomics/src/bijux_pollenomics/adna/projects/evidence/sites.py"
    )

    assert find_repository_root(nested_source) == REPOSITORY_ROOT
    assert repository_data_root(nested_source) == REPOSITORY_ROOT / "data"


def test_find_repository_root_refuses_unowned_tree() -> None:
    unrelated_file = (
        REPOSITORY_ROOT.parent
        / f"{REPOSITORY_ROOT.name}-unowned"
        / "package"
        / "module.py"
    )

    with pytest.raises(RepositoryRootNotFoundError):
        find_repository_root(unrelated_file)


def _workspace(root: Path) -> Path:
    package = root / "packages/bijux-pollenomics"
    source = package / "src/bijux_pollenomics"
    source.mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        '[project]\nname = "bijux-pollenomics-repository"\n'
    )
    (package / "pyproject.toml").write_text('[project]\nname = "bijux-pollenomics"\n')
    (source / "__init__.py").write_text('"""Owned host package."""\n')
    module = source / "nested/module.py"
    module.parent.mkdir()
    module.write_text('"""Nested source."""\n')
    return module


def test_archive_owns_data_even_inside_another_workspace(tmp_path: Path) -> None:
    parent = tmp_path / "checkout"
    _workspace(parent)
    (parent / ".git").mkdir()
    archive = parent / "artifacts/snapshot"
    module = _workspace(archive)
    assert find_repository_root(module) == archive
    assert repository_data_root(module) == archive / "data"
    assert find_repository_root(archive) == archive
    assert not (archive / ".git").exists()


@pytest.mark.parametrize(
    "case",
    [
        "missing_root",
        "invalid_root",
        "wrong_root",
        "missing_package",
        "wrong_package",
        "missing_source",
        "indirect_descriptor",
    ],
)
def test_partial_workspace_never_borrows_parent_data(tmp_path: Path, case: str) -> None:
    parent = tmp_path / "checkout"
    _workspace(parent)
    archive = parent / "artifacts/snapshot"
    module = _workspace(archive)
    if case == "missing_root":
        (archive / "pyproject.toml").unlink()
    if case == "invalid_root":
        (archive / "pyproject.toml").write_text("[broken")
    if case == "wrong_root":
        (archive / "pyproject.toml").write_text('[project]\nname="unowned"\n')
    if case == "missing_package":
        (archive / "packages/bijux-pollenomics/pyproject.toml").unlink()
    if case == "wrong_package":
        (archive / "packages/bijux-pollenomics/pyproject.toml").write_text(
            '[project]\nname="different"\n'
        )
    if case == "missing_source":
        (
            archive / "packages/bijux-pollenomics/src/bijux_pollenomics/__init__.py"
        ).unlink()
    if case == "indirect_descriptor":
        (archive / "pyproject.toml").unlink()
        (archive / "pyproject.toml").symlink_to(parent / "pyproject.toml")
    with pytest.raises(RepositoryRootNotFoundError):
        find_repository_root(module)


@pytest.mark.parametrize(
    "relative",
    [
        "artifacts/installed/lib/python3.11/site-packages/bijux_pollenomics/module.py",
        "artifacts/unowned/module.py",
        ".venv/lib/python3.11/site-packages/bijux_pollenomics/module.py",
    ],
)
def test_installed_or_unowned_anchor_cannot_find_ancestor_workspace(
    tmp_path: Path, relative: str
) -> None:
    _workspace(tmp_path)
    module = tmp_path / relative
    module.parent.mkdir(parents=True)
    module.write_text('"""Unowned module."""\n')
    with pytest.raises(RepositoryRootNotFoundError):
        find_repository_root(module)


def test_nearer_unrelated_project_is_a_refusal_boundary(tmp_path: Path) -> None:
    source = _workspace(tmp_path)
    nested = source.parent / "other"
    nested.mkdir()
    (nested / "pyproject.toml").write_text('[project]\nname="unrelated"\n')
    with pytest.raises(RepositoryRootNotFoundError):
        find_repository_root(nested / "module.py")
