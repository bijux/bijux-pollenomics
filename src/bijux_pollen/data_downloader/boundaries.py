from __future__ import annotations

from .common import fetch_json


BOUNDARY_URLS = {
    "Sweden": "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/SWE.geo.json",
    "Norway": "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/NOR.geo.json",
    "Finland": "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/FIN.geo.json",
    "Denmark": "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/DNK.geo.json",
}


def fetch_country_boundaries() -> dict[str, dict[str, object]]:
    """Download Nordic country boundaries used for country assignment and display."""
    return {country: fetch_json(url) for country, url in BOUNDARY_URLS.items()}


def build_combined_country_boundaries(
    country_boundaries: dict[str, dict[str, object]],
) -> dict[str, object]:
    """Combine individual Nordic country files into one GeoJSON collection."""
    features = []
    for country, payload in country_boundaries.items():
        for feature in payload.get("features", []):
            features.append(
                {
                    "type": "Feature",
                    "geometry": feature["geometry"],
                    "properties": {
                        "country": country,
                        "name": country,
                        "layer_key": "country-boundaries",
                        "layer_label": "Country boundaries",
                    },
                }
            )
    return {"type": "FeatureCollection", "features": features}
