from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from ....core.files import write_json
from ....core.geojson import CountryBoundaryCollection, feature_list
from ....core.text import slugify
from ...contracts.artifacts import BOUNDARY_COLLECTION

__all__ = [
    "BoundariesDataReport",
    "build_combined_country_boundaries",
    "write_boundary_archive",
]


@dataclass(frozen=True)
class BoundariesDataReport:
    output_dir: Path
    country_names: tuple[str, ...]
    combined_path: Path
    manifest_path: Path


def build_combined_country_boundaries(
    country_boundaries: CountryBoundaryCollection,
) -> dict[str, object]:
    """Combine individual Nordic country files into one GeoJSON collection."""
    features = []
    for country, payload in country_boundaries.items():
        for feature in feature_list(payload):
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
    country_boundaries: CountryBoundaryCollection,
    source_manifest: dict[str, object],
) -> BoundariesDataReport:
    """Write raw and normalized boundary artifacts into one output root."""
    output_root = Path(output_root)
    raw_dir = output_root / "raw"
    normalized_dir = output_root / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    country_artifacts: dict[str, dict[str, object]] = {}
    for country_name, payload in country_boundaries.items():
        country_path = raw_dir / f"{slugify(country_name)}.geojson"
        write_json(country_path, payload)
        country_artifacts[country_name] = {
            "path": country_path.name,
            "sha256": _file_sha256(country_path),
            "feature_count": len(feature_list(payload)),
        }

    combined_path = BOUNDARY_COLLECTION.source_path_under(output_root)
    write_json(combined_path, build_combined_country_boundaries(country_boundaries))
    manifest_payload = {
        **source_manifest,
        "country_artifacts": country_artifacts,
        "normalized_artifact": {
            "path": str(combined_path.relative_to(output_root)),
            "sha256": _file_sha256(combined_path),
            "feature_count": len(country_boundaries),
        },
    }
    manifest_path = raw_dir / "source_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return BoundariesDataReport(
        output_dir=output_root,
        country_names=tuple(country_boundaries.keys()),
        combined_path=combined_path,
        manifest_path=manifest_path,
    )


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
