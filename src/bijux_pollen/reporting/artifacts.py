from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from .models import LocalitySummary, SampleRecord


def write_samples_csv(path: Path, samples: Iterable[SampleRecord]) -> None:
    """Write the full sample inventory as CSV."""
    fieldnames = [
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
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for sample in samples:
            writer.writerow(
                {
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
                    "datasets": ",".join(sample.datasets),
                }
            )


def write_localities_csv(path: Path, localities: Iterable[LocalitySummary]) -> None:
    """Write the locality-level aggregation as CSV."""
    fieldnames = [
        "locality",
        "latitude",
        "longitude",
        "sample_count",
        "datasets",
        "sample_ids",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for locality in localities:
            writer.writerow(
                {
                    "locality": locality.locality,
                    "latitude": locality.latitude_text,
                    "longitude": locality.longitude_text,
                    "sample_count": locality.sample_count,
                    "datasets": ",".join(locality.datasets),
                    "sample_ids": ";".join(locality.sample_ids),
                }
            )


def write_samples_geojson(path: Path, samples: Iterable[SampleRecord]) -> None:
    """Write map-ready sample points as GeoJSON."""
    path.write_text(json.dumps(build_samples_geojson(samples), indent=2), encoding="utf-8")


def build_samples_geojson(samples: Iterable[SampleRecord]) -> dict[str, object]:
    """Build a GeoJSON feature collection from normalized sample records."""
    features = []
    for sample in samples:
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [sample.longitude, sample.latitude],
                },
                "properties": {
                    "genetic_id": sample.genetic_id,
                    "master_id": sample.master_id,
                    "group_id": sample.group_id,
                    "locality": sample.locality,
                    "political_entity": sample.political_entity,
                    "publication": sample.publication,
                    "year_first_published": sample.year_first_published,
                    "full_date": sample.full_date,
                    "date_mean_bp": sample.date_mean_bp,
                    "data_type": sample.data_type,
                    "molecular_sex": sample.molecular_sex,
                    "datasets": list(sample.datasets),
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}

