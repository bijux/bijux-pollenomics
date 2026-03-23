from __future__ import annotations

import json
from typing import Iterable

from .common import clean_optional_text, fetch_json
from .geometry import classify_country, geometry_to_representative_point, point_in_bbox
from .models import ContextPointRecord


NEOTOMA_LIMIT = 400


def fetch_neotoma_pollen_rows() -> list[dict[str, object]]:
    """Download all Neotoma pollen site rows using stable chunked pagination."""
    rows: list[dict[str, object]] = []
    offset = 0
    while True:
        payload = fetch_json(
            "https://api.neotomadb.org/v2.0/data/sites",
            params={
                "datasettype": "pollen",
                "limit": str(NEOTOMA_LIMIT),
                "offset": str(offset),
            },
            insecure=True,
        )
        chunk = payload.get("data", [])
        if not isinstance(chunk, list) or not chunk:
            break
        rows.extend(chunk)
        if len(chunk) < NEOTOMA_LIMIT:
            break
        offset += NEOTOMA_LIMIT

    deduplicated: dict[str, dict[str, object]] = {}
    for row in rows:
        deduplicated[str(row.get("siteid", ""))] = row
    return sorted(deduplicated.values(), key=lambda item: int(item.get("siteid", 0)))


def normalize_neotoma_rows(
    rows: Iterable[dict[str, object]],
    bbox: tuple[float, float, float, float],
    country_boundaries: dict[str, dict[str, object]],
) -> list[ContextPointRecord]:
    """Convert raw Neotoma rows into compact Nordic pollen site records."""
    records: list[ContextPointRecord] = []
    for row in rows:
        geography_text = str(row.get("geography", "")).strip()
        if not geography_text:
            continue
        representative_point = geometry_to_representative_point(json.loads(geography_text))
        if representative_point is None:
            continue
        longitude, latitude, geometry_type = representative_point
        if not point_in_bbox(longitude=longitude, latitude=latitude, bbox=bbox):
            continue
        country = classify_country(longitude, latitude, country_boundaries)
        if not country:
            continue

        collection_units = row.get("collectionunits", [])
        if not isinstance(collection_units, list):
            collection_units = []

        dataset_types = sorted(
            {
                str(dataset.get("datasettype", "")).strip()
                for unit in collection_units
                if isinstance(unit, dict)
                for dataset in unit.get("datasets", [])
                if isinstance(dataset, dict) and str(dataset.get("datasettype", "")).strip()
            }
        )
        dataset_count = sum(
            len(unit.get("datasets", []))
            for unit in collection_units
            if isinstance(unit, dict) and isinstance(unit.get("datasets", []), list)
        )
        collection_unit_count = len(collection_units)
        site_id = str(row.get("siteid", "")).strip()
        site_name = str(row.get("sitename", "")).strip() or f"Neotoma site {site_id}"
        source_url = f"https://apps.neotomadb.org/explorer/#/record/site/{site_id}"
        description = str(row.get("sitedescription", "") or "").strip()
        altitude = clean_optional_text(row.get("altitude"))

        popup_rows = [
            ("Site ID", site_id),
            ("Category", "Pollen"),
            ("Source", "Neotoma"),
            ("Country", country),
            ("Geometry", geometry_type),
            ("Collection units", str(collection_unit_count)),
            ("Datasets", str(dataset_count)),
        ]
        if dataset_types:
            popup_rows.append(("Dataset types", ", ".join(dataset_types)))
        if altitude:
            popup_rows.append(("Altitude", altitude))
        if description:
            popup_rows.append(("Description", description))

        records.append(
            ContextPointRecord(
                source="Neotoma",
                layer_key="neotoma-pollen",
                layer_label="Neotoma pollen sites",
                category="Pollen",
                country=country,
                record_id=site_id,
                name=site_name,
                latitude=latitude,
                longitude=longitude,
                geometry_type=geometry_type,
                subtitle="Nordic pollen and paleoecology sites",
                description=description,
                source_url=source_url,
                record_count=dataset_count,
                popup_rows=tuple(popup_rows),
            )
        )

    return sorted(records, key=lambda item: (item.name.casefold(), item.record_id))
