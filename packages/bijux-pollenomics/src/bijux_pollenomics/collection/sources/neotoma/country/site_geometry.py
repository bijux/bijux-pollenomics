from __future__ import annotations

import json
from collections.abc import Mapping

from bijux_pollenomics.collection.spatial import (
    classify_country,
    geometry_to_representative_point,
    point_in_bbox,
)
from bijux_pollenomics.core.text import clean_optional_text


def classify_neotoma_site_country(
    site: dict[str, object],
    bbox: tuple[float, float, float, float],
    country_boundaries: Mapping[str, Mapping[str, object]],
) -> str:
    """Resolve a Neotoma site payload to one tracked Nordic country, if any."""
    representative_point = neotoma_site_representative_point(site)
    if representative_point is None:
        return ""
    longitude, latitude, _ = representative_point
    if not point_in_bbox(longitude=longitude, latitude=latitude, bbox=bbox):
        return ""
    return classify_country(longitude, latitude, country_boundaries)


def neotoma_site_representative_point(
    site: Mapping[str, object],
) -> tuple[float, float, str] | None:
    """Return one representative point for a Neotoma site payload."""
    geography_text = clean_optional_text(site.get("geography"))
    if not geography_text:
        return None
    try:
        geography = json.loads(geography_text)
    except json.JSONDecodeError:
        return None
    if not isinstance(geography, dict):
        return None
    return geometry_to_representative_point(geography)
