from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .common import slugify, write_json
from .common import fetch_json


BOUNDARY_URLS = {
    "Sweden": "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/SWE.geo.json",
    "Norway": "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/NOR.geo.json",
    "Finland": "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/FIN.geo.json",
    "Denmark": "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/DNK.geo.json",
}


@dataclass(frozen=True)
class BoundariesDataReport:
    output_dir: Path
    country_names: tuple[str, ...]
    combined_path: Path


def fetch_country_boundaries() -> dict[str, dict[str, object]]:
    """Download Nordic country boundaries used for country assignment and display."""
    return {country: fetch_json(url) for country, url in BOUNDARY_URLS.items()}


def load_country_boundaries(output_root: Path) -> dict[str, dict[str, object]] | None:
    """Load tracked Nordic country boundaries from a local boundaries directory when present."""
    raw_dir = Path(output_root) / "raw"
    country_boundaries: dict[str, dict[str, object]] = {}
    for country in BOUNDARY_URLS:
        path = raw_dir / f"{slugify(country)}.geojson"
        if not path.exists():
            return None
        country_boundaries[country] = json.loads(path.read_text(encoding="utf-8"))
    return country_boundaries


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


def collect_boundaries_data(output_root: Path) -> tuple[dict[str, dict[str, object]], BoundariesDataReport]:
    """Download and write the Nordic boundary dataset under data/boundaries."""
    output_root = Path(output_root)
    raw_dir = output_root / "raw"
    normalized_dir = output_root / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    country_boundaries = fetch_country_boundaries()
    for country_name, payload in country_boundaries.items():
        write_json(raw_dir / f"{slugify(country_name)}.geojson", payload)

    combined_path = normalized_dir / "nordic_country_boundaries.geojson"
    write_json(combined_path, build_combined_country_boundaries(country_boundaries))

    return country_boundaries, BoundariesDataReport(
        output_dir=output_root,
        country_names=tuple(country_boundaries.keys()),
        combined_path=combined_path,
    )
