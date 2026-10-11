"""Synchronize badge blocks through the shared catalog-driven renderer."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tomllib
from types import ModuleType
from typing import Any, cast


def _repository_root() -> Path:
    """Bind this repository-only writer to the invoking repository."""
    root = Path.cwd().resolve()
    project = root / "pyproject.toml"
    if not project.is_file() or project.is_symlink():
        raise RuntimeError(
            f"Badge synchronization requires the repository root: {root}"
        )
    with project.open("rb") as stream:
        metadata = tomllib.load(stream)
    if (
        metadata.get("tool", {}).get("bijux_pollenomics", {}).get("repository")
        != "bijux-pollenomics"
    ):
        raise RuntimeError(f"Not a bijux-pollenomics repository root: {root}")
    return root


REPO_ROOT = _repository_root()
SHARED_RENDERER = (
    REPO_ROOT / ".bijux/shared/bijux-makes-py/repository/badge_renderer.py"
)


def _load_shared_renderer() -> ModuleType:
    relative = SHARED_RENDERER.relative_to(REPO_ROOT)
    current = REPO_ROOT
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise RuntimeError(f"Shared badge renderer path is a symlink: {current}")
    if not SHARED_RENDERER.is_file():
        raise RuntimeError(f"Shared badge renderer is unavailable: {SHARED_RENDERER}")
    module_name = "bijux_shared_badge_renderer"
    spec = importlib.util.spec_from_file_location(module_name, SHARED_RENDERER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load shared badge renderer: {SHARED_RENDERER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_shared = _load_shared_renderer()
_renderer = _shared.BadgeRenderer(REPO_ROOT, "bijux_pollenomics")
BadgeTarget = _shared.BadgeTarget
PackageBadgeRecord = _shared.PackageBadgeRecord


def load_badge_catalog() -> dict[str, str]:
    """Load the shared badge template catalog."""
    return cast(dict[str, str], _renderer.load_badge_catalog())


def public_package_records() -> tuple[Any, ...]:
    """Return badge metadata for public workspace packages."""
    return cast(tuple[Any, ...], _renderer.public_package_records())


def iter_badge_targets() -> tuple[Any, ...]:
    """Return every repository surface governed by badge synchronization."""
    return cast(tuple[Any, ...], _renderer.iter_badge_targets())


def render_badge_block(target: Any) -> str:
    """Render the governed badge block for one target."""
    return cast(str, _renderer.render_badge_block(target))


def render_target_text(target: Any, current_text: str) -> str:
    """Render a target document with its governed badge block."""
    return cast(str, _renderer.render_target_text(target, current_text))


def synchronize_badges(*, check: bool) -> list[Path]:
    """Check or synchronize all governed badge targets."""
    return cast(list[Path], _renderer.synchronize_badges(check=check))


def main(argv: list[str] | None = None) -> int:
    """Run the shared badge synchronization command."""
    return cast(int, _renderer.main(argv))


if __name__ == "__main__":
    raise SystemExit(main())
