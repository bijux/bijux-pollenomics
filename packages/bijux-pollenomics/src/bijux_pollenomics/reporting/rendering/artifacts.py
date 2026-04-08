from __future__ import annotations

import json
import shutil
from pathlib import Path

from .record_exports import (
    build_sample_geojson_feature,
    build_samples_geojson,
    serialize_locality_summary,
    serialize_sample_record,
    write_localities_csv,
    write_samples_csv,
    write_samples_geojson,
)

def resolve_repository_root() -> Path:
    """Locate the repository root from the installed or editable runtime package path."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "docs" / "assets" / "vendor" / "map"
        if candidate.exists():
            return parent
    raise FileNotFoundError("Unable to locate the repository root for vendored map assets")


MAP_ASSET_SOURCE_DIR = resolve_repository_root() / "docs" / "assets" / "vendor" / "map"


def write_summary_json(path: Path, payload: dict[str, object]) -> None:
    """Write a machine-readable summary alongside generated report artifacts."""
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def resolve_map_asset_source_dir() -> Path:
    """Validate the vendored map asset bundle before copying it."""
    required_paths = (
        MAP_ASSET_SOURCE_DIR,
        MAP_ASSET_SOURCE_DIR / "leaflet" / "leaflet.css",
        MAP_ASSET_SOURCE_DIR / "leaflet" / "leaflet.js",
        MAP_ASSET_SOURCE_DIR / "markercluster" / "MarkerCluster.css",
        MAP_ASSET_SOURCE_DIR / "markercluster" / "leaflet.markercluster.js",
    )
    missing = [path for path in required_paths if not path.exists()]
    if missing:
        missing_text = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(f"Vendored map asset bundle is incomplete: {missing_text}")
    return MAP_ASSET_SOURCE_DIR


def copy_map_assets(output_dir: Path) -> Path:
    """Copy bundled map UI assets into a report bundle directory."""
    source_dir = resolve_map_asset_source_dir()
    destination = Path(output_dir) / "_map_assets"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source_dir, destination)
    return destination


__all__ = [
    "build_sample_geojson_feature",
    "build_samples_geojson",
    "copy_map_assets",
    "resolve_map_asset_source_dir",
    "serialize_locality_summary",
    "serialize_sample_record",
    "write_localities_csv",
    "write_samples_csv",
    "write_samples_geojson",
    "write_summary_json",
]
