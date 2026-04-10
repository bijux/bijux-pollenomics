"""Helpers for copying root-level site icon assets into the built site."""

from __future__ import annotations

from pathlib import Path
import shutil

ROOT_ICON_FILENAMES = (
    "favicon.ico",
    "apple-touch-icon.png",
    "apple-touch-icon-precomposed.png",
)


def publish_root_site_icons(*, docs_dir: Path, site_dir: Path) -> None:
    """Publish browser-probed site icons into the built site root."""
    icon_source_dir = docs_dir / "assets" / "site-icons"

    for filename in ROOT_ICON_FILENAMES:
        source_path = icon_source_dir / filename
        if not source_path.exists():
            raise FileNotFoundError(f"Missing site icon source: {source_path}")
        destination_path = site_dir / filename
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, destination_path)
