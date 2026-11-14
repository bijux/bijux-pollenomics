"""Repository-root discovery for owned source archives and working checkouts."""

from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath
import tomllib
from typing import Any

__all__ = [
    "RepositoryRootNotFoundError",
    "find_repository_root",
    "repository_data_root",
]


class RepositoryRootNotFoundError(RuntimeError):
    """Raised when an anchor has no valid owning Pollenomics workspace."""


def _descriptor(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise RepositoryRootNotFoundError(
            f"missing or indirect project identity: {path}"
        )
    try:
        with path.open("rb") as stream:
            return tomllib.load(stream)
    except (OSError, ValueError) as error:
        raise RepositoryRootNotFoundError(
            f"invalid project identity: {path}"
        ) from error


def _project_name(path: Path) -> str:
    try:
        name = _descriptor(path)["project"]["name"]
    except (KeyError, TypeError) as error:
        raise RepositoryRootNotFoundError(
            f"invalid project identity: {path}"
        ) from error
    if not isinstance(name, str) or not name:
        raise RepositoryRootNotFoundError(f"invalid project name: {path}")
    return name


def _matches_workspace_glob(parts: tuple[str, ...], pattern: tuple[str, ...]) -> bool:
    """Match every path segment from the workspace root, including recursive globs."""
    if not pattern:
        return not parts
    if pattern[0] == "**":
        return (
            _matches_workspace_glob(parts, pattern[1:])
            or bool(parts)
            and (_matches_workspace_glob(parts[1:], pattern))
        )
    return (
        bool(parts)
        and fnmatchcase(parts[0], pattern[0])
        and (_matches_workspace_glob(parts[1:], pattern[1:]))
    )


def _workspace_owns_host(path: Path) -> bool:
    payload = _descriptor(path)
    try:
        owner = payload["tool"]["bijux_pollenomics"]["repository"]
        workspace = payload["tool"]["uv"]["workspace"]
        members = workspace["members"]
        excluded = workspace.get("exclude", [])
    except (KeyError, TypeError, AttributeError):
        return False
    if owner != "bijux-pollenomics" or not all(
        isinstance(items, list)
        and all(isinstance(item, str) and item for item in items)
        for items in (members, excluded)
    ):
        return False
    package = ("packages", "bijux-pollenomics")
    return any(
        _matches_workspace_glob(package, PurePosixPath(pattern).parts)
        for pattern in members
    ) and not any(
        _matches_workspace_glob(package, PurePosixPath(pattern).parts)
        for pattern in excluded
    )


def _owned_workspace(candidate: Path, anchor: Path) -> Path:
    package = candidate / "packages" / "bijux-pollenomics"
    source = package / "src" / "bijux_pollenomics"
    if (
        not _workspace_owns_host(candidate / "pyproject.toml")
        or _project_name(package / "pyproject.toml") != "bijux-pollenomics"
        or any(
            path.is_symlink()
            for path in (
                candidate / "packages",
                package,
                package / "src",
                source,
                source / "__init__.py",
            )
        )
        or not (source / "__init__.py").is_file()
    ):
        raise RepositoryRootNotFoundError(f"invalid Pollenomics workspace: {candidate}")
    if anchor != candidate and not anchor.is_relative_to(package):
        raise RepositoryRootNotFoundError(
            f"anchor is outside the workspace-owned host package: {anchor}"
        )
    return candidate


def find_repository_root(anchor: str | Path) -> Path:
    """Find the nearest identified host workspace without requiring Git metadata.

    Root anchors and anchors inside the owned host package are supported. A
    nearer partial, malformed or unrelated project is a refusal boundary; an
    installed package or incomplete archive cannot borrow an ancestor's data.
    """
    resolved_anchor = Path(anchor).resolve()
    start = resolved_anchor if resolved_anchor.is_dir() else resolved_anchor.parent
    for candidate in (start, *start.parents):
        descriptor = candidate / "pyproject.toml"
        package = candidate / "packages" / "bijux-pollenomics"
        if package.exists() or package.is_symlink():
            return _owned_workspace(candidate, resolved_anchor)
        if descriptor.exists() or descriptor.is_symlink():
            name = _project_name(descriptor)
            if not (
                name == "bijux-pollenomics"
                and candidate.name == "bijux-pollenomics"
                and candidate.parent.name == "packages"
            ):
                raise RepositoryRootNotFoundError(
                    f"anchor belongs to another or incomplete project: {candidate}"
                )
    raise RepositoryRootNotFoundError(
        f"cannot locate the Bijux Pollenomics workspace from {resolved_anchor}"
    )


def repository_data_root(anchor: str | Path) -> Path:
    """Resolve the data root belonging to the identified source workspace."""
    return find_repository_root(anchor) / "data"
