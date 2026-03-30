from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Iterable

from .models import LocalitySummary, SampleRecord


MAP_ASSET_SOURCE_DIR = Path(__file__).resolve().parents[3] / "docs" / "assets" / "vendor" / "map"
SAMPLE_EXPORT_FIELDS = (
    "genetic_id",
    "master_id",
    "group_id",
    "locality",
    "political_entity",
    "latitude",
    "longitude",
    "publication",
    "year_first_published",
    "full_date",
    "date_mean_bp",
    "data_type",
    "molecular_sex",
    "datasets",
)
LOCALITY_EXPORT_FIELDS = (
    "locality",
    "latitude",
    "longitude",
    "sample_count",
    "datasets",
    "sample_ids",
)


def serialize_sample_record(sample: SampleRecord) -> dict[str, object]:
    """Serialize one sample record into the shared export contract."""
    return {
        "genetic_id": sample.genetic_id,
        "master_id": sample.master_id,
        "group_id": sample.group_id,
        "locality": sample.locality,
        "political_entity": sample.political_entity,
        "latitude": sample.latitude_text,
        "longitude": sample.longitude_text,
        "publication": sample.publication,
        "year_first_published": sample.year_first_published,
        "full_date": sample.full_date,
        "date_mean_bp": sample.date_mean_bp,
        "data_type": sample.data_type,
        "molecular_sex": sample.molecular_sex,
        "datasets": list(sample.datasets),
    }


def serialize_locality_summary(locality: LocalitySummary) -> dict[str, object]:
    """Serialize one locality summary into the shared export contract."""
    return {
        "locality": locality.locality,
        "latitude": locality.latitude_text,
        "longitude": locality.longitude_text,
        "sample_count": locality.sample_count,
        "datasets": list(locality.datasets),
        "sample_ids": list(locality.sample_ids),
    }


def build_sample_geojson_feature(sample: SampleRecord) -> dict[str, object]:
    """Build one GeoJSON feature from a normalized sample record."""
    properties = serialize_sample_record(sample)
    properties["datasets"] = list(sample.datasets)
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [sample.longitude, sample.latitude],
        },
        "properties": properties,
    }


def write_samples_csv(path: Path, samples: Iterable[SampleRecord]) -> None:
    """Write the full sample inventory as CSV."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SAMPLE_EXPORT_FIELDS))
        writer.writeheader()
        for sample in samples:
            payload = serialize_sample_record(sample)
            payload["datasets"] = ",".join(sample.datasets)
            writer.writerow(payload)


def write_localities_csv(path: Path, localities: Iterable[LocalitySummary]) -> None:
    """Write the locality-level aggregation as CSV."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(LOCALITY_EXPORT_FIELDS))
        writer.writeheader()
        for locality in localities:
            payload = serialize_locality_summary(locality)
            payload["datasets"] = ",".join(locality.datasets)
            payload["sample_ids"] = ";".join(locality.sample_ids)
            writer.writerow(payload)


def write_samples_geojson(path: Path, samples: Iterable[SampleRecord]) -> None:
    """Write map-ready sample points as GeoJSON."""
    path.write_text(json.dumps(build_samples_geojson(samples), indent=2), encoding="utf-8")


def build_samples_geojson(samples: Iterable[SampleRecord]) -> dict[str, object]:
    """Build a GeoJSON feature collection from normalized sample records."""
    features = []
    for sample in samples:
        features.append(build_sample_geojson_feature(sample))
    return {"type": "FeatureCollection", "features": features}


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
