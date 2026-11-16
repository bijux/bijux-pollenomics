"""Private recovery follows the destination owner without borrowing other projects."""

from hashlib import sha256
from pathlib import Path

import pytest
from bijux_pollenomics.core.filesystem.recovery_storage import (
    resolve_publication_workspace_parent,
)


def _workspace(root: Path) -> Path:
    package = root / "packages/bijux-pollenomics"
    source = package / "src/bijux_pollenomics"
    source.mkdir(parents=True)
    (source / "__init__.py").write_text('"""Synthetic host."""\n')
    (root / "pyproject.toml").write_text(
        '[tool.bijux_pollenomics]\nrepository="bijux-pollenomics"\n'
        '[tool.uv.workspace]\nmembers=["packages/*"]\n'
    )
    (package / "pyproject.toml").write_text('[project]\nname="bijux-pollenomics"\n')
    return package


def test_identified_destination_uses_its_own_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "checkout"
    _workspace(root)
    public = root / "reports/nordic"
    public.mkdir(parents=True)
    result = resolve_publication_workspace_parent(public, namespace="raa-publication")
    assert (
        result
        == root / "artifacts/raa-publication" / sha256(str(public).encode()).hexdigest()
    )
    assert not result.exists()
    assert not result.is_relative_to(public)


def test_canonical_host_package_is_owned_without_using_source_location(
    tmp_path: Path,
) -> None:
    root = tmp_path / "checkout"
    package = _workspace(root)
    public = package / "exports/report"
    public.mkdir(parents=True)
    assert resolve_publication_workspace_parent(
        public, namespace="neotoma-publication"
    ).is_relative_to(root / "artifacts/neotoma-publication")


@pytest.mark.parametrize("marker", ["unrelated", "malformed", "git_only", "partial"])
def test_nearer_project_boundary_never_borrows_outer_owner(
    tmp_path: Path, marker: str
) -> None:
    root = tmp_path / "checkout"
    package = _workspace(root)
    nested = package / "nested"
    public = nested / "report"
    public.mkdir(parents=True)
    if marker == "unrelated":
        (nested / "pyproject.toml").write_text('[project]\nname="another"\n')
    elif marker == "malformed":
        (nested / "pyproject.toml").write_text("[broken")
    elif marker == "git_only":
        (nested / ".git").mkdir()
    else:
        (nested / "packages/bijux-pollenomics").mkdir(parents=True)
    result = resolve_publication_workspace_parent(public, namespace="raa-publication")
    assert result.is_relative_to(nested / ".bijux-publication-recovery/raa-publication")
    assert not result.is_relative_to(root / "artifacts")
    assert not result.is_relative_to(public)


def test_publishing_artifacts_itself_uses_external_sibling(tmp_path: Path) -> None:
    root = tmp_path / "checkout"
    _workspace(root)
    public = root / "artifacts"
    public.mkdir()
    result = resolve_publication_workspace_parent(public, namespace="raa-publication")
    assert result.is_relative_to(root / ".bijux-publication-recovery/raa-publication")
    assert not result.is_relative_to(public)


def test_different_device_preferred_storage_uses_destination_sibling(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.core.filesystem import recovery_storage

    root = tmp_path / "checkout"
    _workspace(root)
    public = root / "reports/nordic"
    public.mkdir(parents=True)
    original = recovery_storage._directory_device

    def device(path: Path) -> int:
        return original(path) + (1 if path.is_relative_to(root / "artifacts") else 0)

    monkeypatch.setattr(recovery_storage, "_directory_device", device)
    result = resolve_publication_workspace_parent(public, namespace="raa-publication")
    assert result.is_relative_to(
        public.parent / ".bijux-publication-recovery/raa-publication"
    )


@pytest.mark.parametrize(
    "namespace", ["", "../escape", "nested/path", "/absolute", "has space"]
)
def test_invalid_storage_namespace_refuses(tmp_path: Path, namespace: str) -> None:
    with pytest.raises(ValueError):
        resolve_publication_workspace_parent(tmp_path, namespace=namespace)


def test_physical_alias_and_root_publication_refuse(tmp_path: Path) -> None:
    physical = tmp_path / "physical"
    physical.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(physical, target_is_directory=True)
    with pytest.raises(ValueError):
        resolve_publication_workspace_parent(alias, namespace="raa-publication")
    with pytest.raises(ValueError):
        resolve_publication_workspace_parent(Path("/"), namespace="raa-publication")


def test_absolute_destination_is_independent_of_current_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "checkout"
    _workspace(root)
    public = root / "reports/nordic"
    public.mkdir(parents=True)
    before = resolve_publication_workspace_parent(public, namespace="raa-publication")
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    monkeypatch.chdir(unrelated)
    assert (
        resolve_publication_workspace_parent(public, namespace="raa-publication")
        == before
    )
