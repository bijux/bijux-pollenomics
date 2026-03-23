from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from .common import write_json
from .models import ContextPointRecord


def write_context_points_csv(path: Path, records: Iterable[ContextPointRecord]) -> None:
    """Write normalized context point records as CSV."""
    fieldnames = [
        "source",
        "layer_key",
        "layer_label",
        "category",
        "country",
        "record_id",
        "name",
        "latitude",
        "longitude",
        "geometry_type",
        "subtitle",
        "description",
        "source_url",
        "record_count",
        "popup_rows_json",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "source": record.source,
                    "layer_key": record.layer_key,
                    "layer_label": record.layer_label,
                    "category": record.category,
                    "country": record.country,
                    "record_id": record.record_id,
                    "name": record.name,
                    "latitude": f"{record.latitude:.6f}",
                    "longitude": f"{record.longitude:.6f}",
                    "geometry_type": record.geometry_type,
                    "subtitle": record.subtitle,
                    "description": record.description,
                    "source_url": record.source_url,
                    "record_count": record.record_count,
                    "popup_rows_json": json.dumps(record.popup_rows, ensure_ascii=False),
                }
            )


def write_context_points_geojson(path: Path, records: Iterable[ContextPointRecord]) -> None:
    """Write normalized context point records as GeoJSON."""
    features = []
    for record in records:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [record.longitude, record.latitude]},
                "properties": {
                    "source": record.source,
                    "layer_key": record.layer_key,
                    "layer_label": record.layer_label,
                    "category": record.category,
                    "country": record.country,
                    "record_id": record.record_id,
                    "name": record.name,
                    "geometry_type": record.geometry_type,
                    "subtitle": record.subtitle,
                    "description": record.description,
                    "source_url": record.source_url,
                    "record_count": record.record_count,
                    "popup_rows": [
                        {"label": label, "value": value}
                        for label, value in record.popup_rows
                    ],
                },
            }
        )
    write_json(path, {"type": "FeatureCollection", "features": features})
