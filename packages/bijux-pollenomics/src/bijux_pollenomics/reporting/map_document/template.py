"""Packaged HTML template for published multi-country map documents."""

from __future__ import annotations

from importlib.resources import files
from typing import Final

_TEMPLATE_RESOURCE: Final = "assets/document.html"


def load_map_document_template() -> str:
    """Load the atlas document from its distribution-owned resource."""
    package_root = files(__package__)
    return (
        package_root.joinpath("assets")
        .joinpath("document.html")
        .read_text(encoding="utf-8")
    )


MAP_DOCUMENT_TEMPLATE: Final = load_map_document_template()

__all__ = ["MAP_DOCUMENT_TEMPLATE", "load_map_document_template"]
