"""Repository-location helpers shared by tests at arbitrary tree depths."""

from pathlib import Path


def _find_repository_root() -> Path:
    for candidate in Path(__file__).resolve().parents:
        if (candidate / ".git").exists() and (
            candidate / "packages" / "bijux-pollenomics"
        ).is_dir():
            return candidate
    raise RuntimeError("bijux-pollenomics repository root could not be located")


REPOSITORY_ROOT = _find_repository_root()

__all__ = ["REPOSITORY_ROOT"]
