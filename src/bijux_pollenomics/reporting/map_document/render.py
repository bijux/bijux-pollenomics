from __future__ import annotations

from ..utils import escape_html
from .payload import build_map_document_payload
from .template import MAP_DOCUMENT_TEMPLATE


def render_multi_country_map_html(
    title: str,
    version: str,
    generated_on: str,
    countries: tuple[str, ...],
    point_layers: list[dict[str, object]],
    polygon_layers: list[dict[str, object]],
    asset_base_path: str,
) -> str:
    """Render the standalone interactive map document."""
    rendered_document = MAP_DOCUMENT_TEMPLATE
    for placeholder, value in build_map_document_payload(
        title=title,
        version=version,
        generated_on=generated_on,
        countries=countries,
        point_layers=point_layers,
        polygon_layers=polygon_layers,
        asset_base_path=asset_base_path,
        escape_html_fn=escape_html,
    ).items():
        rendered_document = rendered_document.replace(placeholder, value)
    return rendered_document
