from __future__ import annotations

from pathlib import Path

from .rendering import artifacts as _artifacts
from .rendering.record_exports import (
    build_sample_geojson_feature,
    build_samples_geojson,
    serialize_locality_summary,
    serialize_sample_record,
    write_localities_csv,
    write_samples_csv,
    write_samples_geojson,
)

MAP_ASSET_SOURCE_DIR = _artifacts.MAP_ASSET_SOURCE_DIR


def write_summary_json(path: Path, payload: dict[str, object]) -> None:
    """Write a machine-readable summary alongside generated report artifacts."""
    _artifacts.write_summary_json(path, payload)


def resolve_map_asset_source_dir() -> Path:
    """Validate the vendored map asset bundle before copying it."""
    _artifacts.MAP_ASSET_SOURCE_DIR = MAP_ASSET_SOURCE_DIR
    return _artifacts.resolve_map_asset_source_dir()


def copy_map_assets(output_dir: Path) -> Path:
    """Copy bundled map UI assets into a report bundle directory."""
    _artifacts.MAP_ASSET_SOURCE_DIR = MAP_ASSET_SOURCE_DIR
    return _artifacts.copy_map_assets(output_dir)


__all__ = [
    "MAP_ASSET_SOURCE_DIR",
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
