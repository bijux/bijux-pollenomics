from __future__ import annotations

from collections.abc import Iterable
from copy import deepcopy
import csv
import json
from pathlib import Path
from typing import cast

from ...core.files import write_json
from ..contracts.models import ContextPointRecord


def _normalize_csv_text(value: str) -> str:
    """Remove source formatting whitespace without flattening meaningful lines."""
    return "\n".join(line.rstrip() for line in value.splitlines()).strip()


def write_context_points_csv(path: Path, records: Iterable[ContextPointRecord]) -> None:
    """Write normalized context point records as CSV."""
    records = tuple(records)
    include_source = any(
        record.source_record is not None or record.occurrence_supports is not None
        for record in records
    )
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
        "time_start_bp",
        "time_end_bp",
        "time_mean_bp",
        "time_label",
        "temporal_semantics_json",
        "popup_rows_json",
        "site_uuid",
    ]
    if include_source:
        fieldnames.extend(("occurrence_supports_json", "source_record_json"))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
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
                    "description": _normalize_csv_text(record.description),
                    "source_url": record.source_url,
                    "record_count": record.record_count,
                    "time_start_bp": record.time_start_bp
                    if record.time_start_bp is not None
                    else "",
                    "time_end_bp": record.time_end_bp
                    if record.time_end_bp is not None
                    else "",
                    "time_mean_bp": record.time_mean_bp
                    if record.time_mean_bp is not None
                    else "",
                    "time_label": record.time_label,
                    "temporal_semantics_json": json.dumps(
                        record.temporal_semantics or {}, ensure_ascii=False
                    ),
                    "popup_rows_json": json.dumps(
                        record.popup_rows, ensure_ascii=False
                    ),
                    "site_uuid": record.site_uuid or "",
                    **(
                        {
                            "occurrence_supports_json": json.dumps(
                                [
                                    support.as_dict()
                                    for support in record.occurrence_supports
                                ],
                                ensure_ascii=False,
                                allow_nan=False,
                            )
                            if record.occurrence_supports is not None
                            else "",
                            "source_record_json": json.dumps(
                                record.source_record,
                                ensure_ascii=False,
                                allow_nan=False,
                            )
                            if record.source_record is not None
                            else "",
                        }
                        if include_source
                        else {}
                    ),
                }
            )


def write_context_points_geojson(
    path: Path, records: Iterable[ContextPointRecord]
) -> None:
    """Write normalized context point records as GeoJSON."""
    features = []
    for record in records:
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [record.longitude, record.latitude],
                },
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
                    "time_start_bp": record.time_start_bp,
                    "time_end_bp": record.time_end_bp,
                    "time_mean_bp": record.time_mean_bp,
                    "time_label": record.time_label,
                    "temporal_semantics": record.temporal_semantics or {},
                    "popup_rows": [
                        {"label": label, "value": value}
                        for label, value in record.popup_rows
                    ],
                    "site_uuid": record.site_uuid,
                },
            }
        )
        properties = cast(dict[str, object], features[-1]["properties"])
        if record.source_record is not None:
            properties.update(deepcopy(record.source_record))
            properties["source_record"] = deepcopy(record.source_record)
            if (
                "temporal_semantics" not in record.source_record
                and record.temporal_semantics is None
            ):
                properties.pop("temporal_semantics", None)
        if record.occurrence_supports is not None:
            properties["occurrence_supports"] = [
                support.as_dict() for support in record.occurrence_supports
            ]
    write_json(path, {"type": "FeatureCollection", "features": features})


__all__ = ["write_context_points_csv", "write_context_points_geojson"]
