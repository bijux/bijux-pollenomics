"""Repository-root discovery for runtime access to governed local data."""

from __future__ import annotations

from pathlib import Path

__all__ = [
    "RepositoryRootNotFoundError",
    "find_repository_root",
    "repository_data_root",
]


class RepositoryRootNotFoundError(RuntimeError):
    """Raised when an anchor is not inside a Bijux Pollenomics checkout."""


def find_repository_root(anchor: str | Path) -> Path:
    """Find the checkout root containing the package and Git repository."""
    resolved_anchor = Path(anchor).resolve()
    start = resolved_anchor if resolved_anchor.is_dir() else resolved_anchor.parent
    for candidate in (start, *start.parents):
        package_root = candidate / "packages" / "bijux-pollenomics"
        if (candidate / ".git").exists() and package_root.is_dir():
            return candidate
    raise RepositoryRootNotFoundError(
        f"cannot locate the Bijux Pollenomics repository from {resolved_anchor}"
    )


def repository_data_root(anchor: str | Path) -> Path:
    """Resolve the governed repository data root from a runtime source path."""
    return find_repository_root(anchor) / "data"
