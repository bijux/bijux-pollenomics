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
        .replace(
            "__EDGE_DISPLAY_CONTROLLER__",
            package_root.joinpath("assets/edge-display.js").read_text(encoding="utf-8"),
        )
        .replace(
            "__RELATION_SUMMARY_CONTROLLER__",
            package_root.joinpath("assets/relation-summary.js").read_text(
                encoding="utf-8"
            ),
        )
        .replace(
            "__RELATION_TIME_SUMMARY_CONTROLLER__",
            package_root.joinpath("assets/relation-time-summary.js").read_text(
                encoding="utf-8"
            ),
        )
        .replace(
            "__SELECTION_LOADING_CONTROLLER__",
            package_root.joinpath("assets/selection-loading.js").read_text(
                encoding="utf-8"
            ),
        )
        .replace(
            "__SEARCH_INDEX_CONTROLLER__",
            package_root.joinpath("assets/search-index.js").read_text(encoding="utf-8"),
        )
        .replace(
            "__CHRONOLOGY_DIAGRAM_CONTROLLER__",
            package_root.joinpath("assets/chronology-diagram.js").read_text(
                encoding="utf-8"
            ),
        )
        .replace(
            "__POLLEN_DIAGRAM_CONTROLLER__",
            package_root.joinpath("assets/pollen-diagram.js").read_text(
                encoding="utf-8"
            ),
        )
        .replace(
            "__POLLEN_AGE_AXIS_CONTROLLER__",
            package_root.joinpath("assets/pollen-age-axis.js").read_text(
                encoding="utf-8"
            ),
        )
        .replace(
            "__POLLEN_SMALL_MULTIPLES_CONTROLLER__",
            package_root.joinpath("assets/pollen-small-multiples.js").read_text(
                encoding="utf-8"
            ),
        )
        .replace(
            "__POLLEN_FOCUSED_SIGNAL_CONTROLLER__",
            package_root.joinpath("assets/focused-source-signal.js").read_text(
                encoding="utf-8"
            ),
        )
        .replace(
            "__SOURCE_RECORD_DETAILS_CONTROLLER__",
            package_root.joinpath("assets/source-record-details.js").read_text(
                encoding="utf-8"
            ),
        )
    )


MAP_DOCUMENT_TEMPLATE: Final = load_map_document_template()
NATIVE_LRA_CONTROLLER: Final = (
    files(__package__)
    .joinpath("assets")
    .joinpath("native-lra.js")
    .read_text(encoding="utf-8")
)
URL_STATE_CONTROLLER: Final = (
    files(__package__).joinpath("assets/url-state.js").read_text(encoding="utf-8")
)
SOURCE_RECORD_EXPORT_CONTROLLER: Final = (
    files(__package__)
    .joinpath("assets")
    .joinpath("source-record-export.js")
    .read_text(encoding="utf-8")
)

__all__ = [
    "MAP_DOCUMENT_TEMPLATE",
    "SOURCE_RECORD_EXPORT_CONTROLLER",
    "URL_STATE_CONTROLLER",
    "load_map_document_template",
]
