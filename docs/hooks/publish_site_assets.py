from __future__ import annotations

from pathlib import Path
from typing import Protocol

from bijux_pollenomics_dev.docs.site_assets import publish_root_site_icons


class MkDocsBuildConfig(Protocol):
    docs_dir: str
    site_dir: str


def on_post_build(config: MkDocsBuildConfig) -> None:
    """Publish browser-probed site icons into the built site root."""
    publish_root_site_icons(
        docs_dir=Path(config.docs_dir),
        site_dir=Path(config.site_dir),
    )
