"""Resolve private publication recovery from the destination's project ownership."""

from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
import re
import stat

from ..repository import RepositoryRootNotFoundError, find_repository_root
from .anchors import DirectoryAnchor


def _directory_device(path: Path) -> int:
    """Inspect the nearest existing ordinary ancestor without following aliases."""
    for candidate in (path, *path.parents):
        try:
            node = candidate.lstat()
        except FileNotFoundError:
            continue
        if not stat.S_ISDIR(node.st_mode):
            raise ValueError("Recovery storage requires ordinary directory ancestry")
        with DirectoryAnchor(candidate) as anchor:
            device = os.fstat(anchor.fd).st_dev
            anchor.check()
            return device
    raise ValueError("Recovery storage has no physical directory ancestor")


def _present(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def _destination_repository(publication_root: Path) -> Path | None:
    for candidate in (publication_root, *publication_root.parents):
        descriptor = candidate / "pyproject.toml"
        git_boundary = _present(candidate / ".git")
        if not (
            _present(descriptor)
            or git_boundary
            or _present(candidate / "packages/bijux-pollenomics")
        ):
            continue
        try:
            owner = find_repository_root(candidate)
        except RepositoryRootNotFoundError:
            return None
        if owner == candidate:
            return owner
        if (
            not git_boundary
            and _present(descriptor)
            and candidate == owner / "packages/bijux-pollenomics"
        ):
            return owner
        # A nearer Git or partial project cannot borrow an outer host workspace.
        return None
    return None


def resolve_publication_workspace_parent(
    publication_root: Path, *, namespace: str
) -> Path:
    """Choose external same-volume storage without creating any directory.

    Identified destination workspaces use their own artifacts/namespace. Other
    destinations use a private sibling of the publication root. The caller must
    retain physical anchors and recheck the actual filesystem before writes.
    """
    if not isinstance(namespace, str):
        raise TypeError("Recovery storage namespace must be a string")
    if re.fullmatch(r"[a-z][a-z0-9-]{0,63}", namespace) is None:
        raise ValueError("Recovery storage namespace must be one literal name")
    root = Path(publication_root).absolute()
    if ".." in root.parts or root == root.parent:
        raise ValueError("Publication root requires an external physical parent")
    device = _directory_device(root)
    owner = _destination_repository(root)
    key = sha256(str(root).encode("utf-8")).hexdigest()
    if owner is not None:
        preferred = owner / "artifacts" / namespace / key
        if (
            not preferred.is_relative_to(root)
            and _directory_device(preferred) == device
        ):
            return preferred
    sibling = root.parent / ".bijux-publication-recovery" / namespace / key
    if sibling.is_relative_to(root) or _directory_device(sibling) != device:
        raise ValueError("No external same-volume publication recovery storage exists")
    return sibling
