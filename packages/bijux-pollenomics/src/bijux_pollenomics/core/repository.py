"""Repository-root discovery for owned source archives and working checkouts."""

from __future__ import annotations

from pathlib import Path
import tomllib

__all__ = [
    "RepositoryRootNotFoundError",
    "find_repository_root",
    "repository_data_root",
]


class RepositoryRootNotFoundError(RuntimeError):
    """Raised when an anchor has no valid owning Pollenomics workspace."""


def _project_name(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise RepositoryRootNotFoundError(
            f"missing or indirect project identity: {path}"
        )
    try:
        with path.open("rb") as stream:
            payload = tomllib.load(stream)
        name = payload["project"]["name"]
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise RepositoryRootNotFoundError(
            f"invalid project identity: {path}"
        ) from error
    if not isinstance(name, str) or not name:
        raise RepositoryRootNotFoundError(f"invalid project name: {path}")
    return name


def _owned_workspace(candidate: Path, anchor: Path) -> Path:
    package = candidate / "packages" / "bijux-pollenomics"
    source = package / "src" / "bijux_pollenomics"
    if (
        _project_name(candidate / "pyproject.toml") != "bijux-pollenomics-repository"
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
            if name == "bijux-pollenomics-repository":
                return _owned_workspace(candidate, resolved_anchor)
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
