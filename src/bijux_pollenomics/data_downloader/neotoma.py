from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from .common import clean_optional_text, fetch_json, write_json
from .contracts import NEOTOMA_POINT_CSV, NEOTOMA_POINT_GEOJSON
from .geometry import classify_country, geometry_to_representative_point, point_in_bbox
from .models import ContextPointRecord
from .writers import write_context_points_csv, write_context_points_geojson


NEOTOMA_LIMIT = 400
NEOTOMA_DATA_URL = "https://api.neotomadb.org/v2.0/data"


@dataclass(frozen=True)
class NeotomaDataReport:
    output_dir: Path
    point_count: int
    raw_path: Path
    normalized_csv_path: Path
    normalized_geojson_path: Path


def fetch_neotoma_pollen_rows() -> list[dict[str, object]]:
    """Download all Neotoma pollen site rows using the full pollen-aware API surface."""
    dataset_rows = fetch_neotoma_dataset_site_rows()
    site_rows = fetch_neotoma_site_rows()
    return merge_neotoma_site_rows((*dataset_rows, *site_rows))


def fetch_neotoma_dataset_site_rows() -> list[dict[str, object]]:
    """Fetch pollen dataset rows and reshape them into site rows with collection units."""
    rows: list[dict[str, object]] = []
    for item in fetch_neotoma_api_rows("datasets"):
        row = build_neotoma_site_row_from_dataset(item)
        if row is not None:
            rows.append(row)
    return rows


def fetch_neotoma_site_rows() -> list[dict[str, object]]:
    """Fetch pollen site rows from the site endpoint."""
    rows: list[dict[str, object]] = []
    for item in fetch_neotoma_api_rows("sites"):
        if isinstance(item, dict):
            rows.append(copy.deepcopy(item))
    return rows


def fetch_neotoma_api_rows(endpoint: str) -> list[object]:
    """Fetch all rows from one Neotoma data endpoint with stable chunked pagination."""
    rows: list[object] = []
    offset = 0
    while True:
        payload = fetch_json(
            f"{NEOTOMA_DATA_URL}/{endpoint}",
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
    return rows


def build_neotoma_site_row_from_dataset(dataset_row: object) -> dict[str, object] | None:
    """Project one dataset response row into the site-row structure used downstream."""
    if not isinstance(dataset_row, dict):
        return None
    site = dataset_row.get("site")
    if not isinstance(site, dict):
        return None

    row = {
        key: copy.deepcopy(value)
        for key, value in site.items()
        if key not in {"collectionunitid", "collectionunit", "handle", "unittype", "datasets"}
    }
    row["collectionunits"] = [
        {
            "collectionunitid": copy.deepcopy(site.get("collectionunitid")),
            "collectionunit": copy.deepcopy(site.get("collectionunit")),
            "handle": copy.deepcopy(site.get("handle")),
            "collectionunittype": copy.deepcopy(site.get("unittype")),
            "datasets": copy.deepcopy(site.get("datasets", [])),
        }
    ]
    return row


def merge_neotoma_site_rows(rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    """Merge site rows from multiple Neotoma endpoints into one deduplicated site inventory."""
    merged_rows: dict[str, dict[str, object]] = {}
    for row in rows:
        site_id = str(row.get("siteid", "")).strip()
        if not site_id:
            continue
        existing = merged_rows.get(site_id)
        if existing is None:
            merged_rows[site_id] = copy.deepcopy(row)
            merged_rows[site_id]["collectionunits"] = normalize_collection_units(row.get("collectionunits"))
            continue
        merge_neotoma_site_row(existing, row)

    return sorted(merged_rows.values(), key=lambda item: int(item.get("siteid", 0)))


def merge_neotoma_site_row(existing: dict[str, object], incoming: dict[str, object]) -> None:
    """Merge one incoming Neotoma site row into an existing deduplicated site row."""
    for key, value in incoming.items():
        if key == "collectionunits":
            continue
        if not clean_optional_text(existing.get(key)):
            existing[key] = copy.deepcopy(value)

    existing_units = normalize_collection_units(existing.get("collectionunits"))
    incoming_units = normalize_collection_units(incoming.get("collectionunits"))
    existing["collectionunits"] = merge_collection_units(existing_units, incoming_units)


def normalize_collection_units(value: object) -> list[dict[str, object]]:
    """Normalize collection-unit payloads to a mutable list of dictionaries."""
    if not isinstance(value, list):
        return []
    return [copy.deepcopy(unit) for unit in value if isinstance(unit, dict)]


def merge_collection_units(
    existing_units: list[dict[str, object]],
    incoming_units: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Merge collection units and deduplicate nested dataset rows."""
    merged_units = [copy.deepcopy(unit) for unit in existing_units]
    unit_positions = {collection_unit_key(unit): index for index, unit in enumerate(merged_units)}

    for incoming_unit in incoming_units:
        key = collection_unit_key(incoming_unit)
        if key not in unit_positions:
            merged_units.append(copy.deepcopy(incoming_unit))
            unit_positions[key] = len(merged_units) - 1
            continue

        existing_unit = merged_units[unit_positions[key]]
        for field in ("collectionunitid", "collectionunit", "handle", "collectionunittype"):
            if not clean_optional_text(existing_unit.get(field)):
                existing_unit[field] = copy.deepcopy(incoming_unit.get(field))

        merged_datasets = normalize_datasets(existing_unit.get("datasets"))
        dataset_positions = {dataset_key(dataset): index for index, dataset in enumerate(merged_datasets)}
        for incoming_dataset in normalize_datasets(incoming_unit.get("datasets")):
            key = dataset_key(incoming_dataset)
            if key in dataset_positions:
                existing_dataset = merged_datasets[dataset_positions[key]]
                for field, value in incoming_dataset.items():
                    if field not in existing_dataset or existing_dataset[field] in ("", None, [], {}):
                        existing_dataset[field] = copy.deepcopy(value)
                continue
            dataset_positions[key] = len(merged_datasets)
            merged_datasets.append(copy.deepcopy(incoming_dataset))
        existing_unit["datasets"] = sort_datasets(merged_datasets)

    for unit in merged_units:
        unit["datasets"] = sort_datasets(normalize_datasets(unit.get("datasets")))
    return sorted(merged_units, key=collection_unit_sort_key)


def normalize_datasets(value: object) -> list[dict[str, object]]:
    """Normalize dataset payloads to a mutable list of dictionaries."""
    if not isinstance(value, list):
        return []
    return [copy.deepcopy(dataset) for dataset in value if isinstance(dataset, dict)]


def collection_unit_key(unit: dict[str, object]) -> tuple[str, ...]:
    """Build a stable identity key for one Neotoma collection unit."""
    collection_unit_id = clean_optional_text(unit.get("collectionunitid"))
    handle = clean_optional_text(unit.get("handle"))
    collection_unit = clean_optional_text(unit.get("collectionunit"))
    collection_unit_type = clean_optional_text(unit.get("collectionunittype"))
    return (collection_unit_id, handle, collection_unit, collection_unit_type)


def collection_unit_sort_key(unit: dict[str, object]) -> tuple[str, ...]:
    """Sort collection units consistently for reproducible output."""
    return (
        clean_optional_text(unit.get("collectionunitid")).zfill(12),
        clean_optional_text(unit.get("handle")),
        clean_optional_text(unit.get("collectionunit")),
        clean_optional_text(unit.get("collectionunittype")),
    )


def dataset_key(dataset: dict[str, object]) -> tuple[str, str]:
    """Build a stable identity key for one Neotoma dataset row."""
    dataset_id = clean_optional_text(dataset.get("datasetid"))
    dataset_type = clean_optional_text(dataset.get("datasettype"))
    return (dataset_id, dataset_type)


def sort_datasets(datasets: list[dict[str, object]]) -> list[dict[str, object]]:
    """Sort datasets consistently for reproducible output."""
    return sorted(
        datasets,
        key=lambda dataset: (
            clean_optional_text(dataset.get("datasetid")).zfill(12),
            clean_optional_text(dataset.get("datasettype")),
        ),
    )


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


def collect_neotoma_data(
    output_root: Path,
    country_boundaries: dict[str, dict[str, object]],
    bbox: tuple[float, float, float, float],
) -> NeotomaDataReport:
    """Download and write the Neotoma dataset under data/neotoma."""
    output_root = Path(output_root)
    raw_dir = output_root / "raw"
    normalized_dir = output_root / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    rows = fetch_neotoma_pollen_rows()
    raw_path = raw_dir / "neotoma_pollen_sites.json"
    write_json(
        raw_path,
        {
            "generated_on": str(date.today()),
            "source": "Neotoma",
            "endpoints": [
                f"{NEOTOMA_DATA_URL}/datasets?datasettype=pollen",
                f"{NEOTOMA_DATA_URL}/sites?datasettype=pollen",
            ],
            "row_count": len(rows),
            "rows": rows,
        },
    )
    records = normalize_neotoma_rows(rows, bbox=bbox, country_boundaries=country_boundaries)
    normalized_csv_path = NEOTOMA_POINT_CSV.source_path_under(output_root)
    normalized_geojson_path = NEOTOMA_POINT_GEOJSON.source_path_under(output_root)
    write_context_points_csv(normalized_csv_path, records)
    write_context_points_geojson(normalized_geojson_path, records)

    return NeotomaDataReport(
        output_dir=output_root,
        point_count=len(records),
        raw_path=raw_path,
        normalized_csv_path=normalized_csv_path,
        normalized_geojson_path=normalized_geojson_path,
    )
