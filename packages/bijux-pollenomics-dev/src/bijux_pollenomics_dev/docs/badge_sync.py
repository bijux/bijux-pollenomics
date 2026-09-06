"""Synchronize badge blocks through the shared catalog-driven renderer."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[5]
SHARED_RENDERER = (
    REPO_ROOT / ".bijux/shared/bijux-makes-py/repository/badge_renderer.py"
)


def _load_shared_renderer() -> ModuleType:
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
