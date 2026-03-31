from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..core.files import write_json
from ..core.text import slugify
from .contracts import BOUNDARY_COLLECTION


@dataclass(frozen=True)
class BoundariesDataReport:
    output_dir: Path
    country_names: tuple[str, ...]
    combined_path: Path
    manifest_path: Path


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


def write_boundary_archive(
    output_root: Path,
    *,
    country_boundaries: dict[str, dict[str, object]],
    source_manifest: dict[str, object],
) -> BoundariesDataReport:
    """Write raw and normalized boundary artifacts into one output root."""
    output_root = Path(output_root)
    raw_dir = output_root / "raw"
    normalized_dir = output_root / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    for country_name, payload in country_boundaries.items():
        write_json(raw_dir / f"{slugify(country_name)}.geojson", payload)
    manifest_path = raw_dir / "source_manifest.json"
    write_json(manifest_path, source_manifest)

    combined_path = BOUNDARY_COLLECTION.source_path_under(output_root)
    write_json(combined_path, build_combined_country_boundaries(country_boundaries))

    return BoundariesDataReport(
        output_dir=output_root,
        country_names=tuple(country_boundaries.keys()),
        combined_path=combined_path,
        manifest_path=manifest_path,
    )
