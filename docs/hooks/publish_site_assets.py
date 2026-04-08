from __future__ import annotations

from pathlib import Path

from bijux_pollenomics_dev.site_assets import publish_root_site_icons


def on_post_build(config) -> None:
    """Publish browser-probed site icons into the built site root."""
    publish_root_site_icons(
        docs_dir=Path(config.docs_dir),
        site_dir=Path(config.site_dir),
    )
