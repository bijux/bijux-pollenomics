from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from .common import clean_optional_text, fetch_json, write_json
from .contracts import SEAD_POINT_CSV, SEAD_POINT_GEOJSON
from .geometry import classify_country
from .models import ContextPointRecord
from .writers import write_context_points_csv, write_context_points_geojson


SEAD_LIMIT = 1000
SEAD_FILTER_BATCH_SIZE = 100
SEAD_POSTGREST_ROOT = "https://browser.sead.se/postgrest"


@dataclass(frozen=True)
class SeadDataReport:
    output_dir: Path
    point_count: int
    raw_path: Path
    normalized_csv_path: Path
    normalized_geojson_path: Path


def fetch_sead_site_rows(bbox: tuple[float, float, float, float]) -> list[dict[str, object]]:
    """Download SEAD site rows inside the Nordic bounding box."""
    min_longitude, min_latitude, max_longitude, max_latitude = bbox
    base_url = (
        f"{SEAD_POSTGREST_ROOT}/tbl_sites"
        "?select=site_id,site_name,national_site_identifier,latitude_dd,longitude_dd,"
        "altitude,site_description,site_uuid"
        f"&latitude_dd=gte.{min_latitude}"
        f"&latitude_dd=lte.{max_latitude}"
        f"&longitude_dd=gte.{min_longitude}"
        f"&longitude_dd=lte.{max_longitude}"
    )
    rows: list[dict[str, object]] = []
    start = 0
    while True:
        chunk = fetch_json(
            base_url,
            headers={
                "Range-Unit": "items",
                "Range": f"{start}-{start + SEAD_LIMIT - 1}",
            },
        )
        if not isinstance(chunk, list) or not chunk:
            break
        rows.extend(item for item in chunk if isinstance(item, dict))
        if len(chunk) < SEAD_LIMIT:
            break
        start += SEAD_LIMIT

    deduplicated: dict[str, dict[str, object]] = {}
    for row in rows:
        deduplicated[str(row.get("site_id", ""))] = row
    deduplicated_rows = sorted(deduplicated.values(), key=lambda item: int(item.get("site_id", 0)))
    populate_sead_site_inventory_fields(deduplicated_rows)
    return deduplicated_rows


def fetch_sead_rows(
    table_name: str,
    *,
    select: str,
    filters: dict[str, str] | None = None,
) -> list[dict[str, object]]:
    """Fetch every row from one SEAD PostgREST table for a selected projection."""
    rows: list[dict[str, object]] = []
    start = 0
    params = {"select": select}
    if filters:
        params.update(filters)
    while True:
        chunk = fetch_json(
            f"{SEAD_POSTGREST_ROOT}/{table_name}",
            params=params,
            headers={
                "Range-Unit": "items",
                "Range": f"{start}-{start + SEAD_LIMIT - 1}",
            },
        )
        if not isinstance(chunk, list) or not chunk:
            break
        rows.extend(item for item in chunk if isinstance(item, dict))
        if len(chunk) < SEAD_LIMIT:
            break
        start += SEAD_LIMIT
    return rows


def fetch_sead_rows_by_ids(
    table_name: str,
    *,
    select: str,
    filter_field: str,
    ids: Iterable[int],
) -> list[dict[str, object]]:
    """Fetch SEAD rows in manageable `in.(...)` batches."""
    unique_ids = sorted({int(value) for value in ids})
    rows: list[dict[str, object]] = []
    for start in range(0, len(unique_ids), SEAD_FILTER_BATCH_SIZE):
        batch = unique_ids[start:start + SEAD_FILTER_BATCH_SIZE]
        rows.extend(
            fetch_sead_rows(
                table_name,
                select=select,
                filters={filter_field: build_sead_in_filter(batch)},
            )
        )
    return rows


def build_sead_in_filter(values: list[int]) -> str:
    """Render a PostgREST `in.(...)` filter from integer identifiers."""
    return f"in.({','.join(str(value) for value in values)})"


def populate_sead_site_inventory_fields(rows: list[dict[str, object]]) -> None:
    """Attach linked sample, dataset, and reference counts to SEAD site rows."""
    site_ids = [int(row.get("site_id", 0)) for row in rows if row.get("site_id")]
    sample_groups = fetch_sead_rows_by_ids(
        "tbl_sample_groups",
        select="sample_group_id,site_id,sample_group_name",
        filter_field="site_id",
        ids=site_ids,
    )
    sample_group_by_id = {
        int(row["sample_group_id"]): int(row["site_id"])
        for row in sample_groups
        if row.get("sample_group_id") is not None and row.get("site_id") is not None
    }
    physical_samples = fetch_sead_rows_by_ids(
        "tbl_physical_samples",
        select="physical_sample_id,sample_group_id",
        filter_field="sample_group_id",
        ids=sample_group_by_id,
    ) if sample_group_by_id else []
    site_id_by_physical_sample_id = {
        int(row["physical_sample_id"]): sample_group_by_id.get(int(row["sample_group_id"]), 0)
        for row in physical_samples
        if row.get("physical_sample_id") is not None and row.get("sample_group_id") is not None
    }
    analysis_entities = fetch_sead_rows_by_ids(
        "tbl_analysis_entities",
        select="analysis_entity_id,physical_sample_id,dataset_id",
        filter_field="physical_sample_id",
        ids=site_id_by_physical_sample_id,
    ) if site_id_by_physical_sample_id else []
    dataset_ids = [
        int(row["dataset_id"])
        for row in analysis_entities
        if row.get("dataset_id") is not None
    ]
    datasets = fetch_sead_rows_by_ids(
        "tbl_datasets",
        select="dataset_id,dataset_name",
        filter_field="dataset_id",
        ids=dataset_ids,
    ) if dataset_ids else []
    dataset_name_by_id = {
        int(row["dataset_id"]): clean_optional_text(row.get("dataset_name"))
        for row in datasets
        if row.get("dataset_id") is not None
    }
    site_references = fetch_sead_rows_by_ids(
        "tbl_site_references",
        select="site_reference_id,site_id,biblio_id",
        filter_field="site_id",
        ids=site_ids,
    ) if site_ids else []

    sample_group_ids_by_site: dict[int, set[int]] = {}
    site_id_by_sample_group_id: dict[int, int] = {}
    physical_sample_ids_by_site: dict[int, set[int]] = {}
    analysis_entity_ids_by_site: dict[int, set[int]] = {}
    dataset_ids_by_site: dict[int, set[int]] = {}
    reference_ids_by_site: dict[int, set[int]] = {}

    for sample_group in sample_groups:
        site_id = int(sample_group.get("site_id") or 0)
        sample_group_id = int(sample_group.get("sample_group_id") or 0)
        if site_id and sample_group_id:
            sample_group_ids_by_site.setdefault(site_id, set()).add(sample_group_id)
            site_id_by_sample_group_id[sample_group_id] = site_id
    for physical_sample_id, site_id in site_id_by_physical_sample_id.items():
        if site_id:
            physical_sample_ids_by_site.setdefault(site_id, set()).add(physical_sample_id)
    for entity in analysis_entities:
        physical_sample_id = int(entity.get("physical_sample_id") or 0)
        analysis_entity_id = int(entity.get("analysis_entity_id") or 0)
        dataset_id = int(entity.get("dataset_id") or 0)
        site_id = site_id_by_physical_sample_id.get(physical_sample_id, 0)
        if not site_id:
            continue
        if analysis_entity_id:
            analysis_entity_ids_by_site.setdefault(site_id, set()).add(analysis_entity_id)
        if dataset_id:
            dataset_ids_by_site.setdefault(site_id, set()).add(dataset_id)
    for reference in site_references:
        site_id = int(reference.get("site_id") or 0)
        reference_id = int(reference.get("site_reference_id") or 0)
        if site_id and reference_id:
            reference_ids_by_site.setdefault(site_id, set()).add(reference_id)

    for row in rows:
        site_id = int(row.get("site_id") or 0)
        dataset_names = [
            name
            for name in sorted(
                {
                    dataset_name_by_id.get(dataset_id, "")
                    for dataset_id in dataset_ids_by_site.get(site_id, set())
                }
            )
            if name
        ]
        row["sample_group_count"] = len(sample_group_ids_by_site.get(site_id, set()))
        row["physical_sample_count"] = len(physical_sample_ids_by_site.get(site_id, set()))
        row["analysis_entity_count"] = len(analysis_entity_ids_by_site.get(site_id, set()))
        row["dataset_count"] = len(dataset_ids_by_site.get(site_id, set()))
        row["dataset_names"] = dataset_names
        row["reference_count"] = len(reference_ids_by_site.get(site_id, set()))


def normalize_sead_rows(
    rows: Iterable[dict[str, object]],
    country_boundaries: dict[str, dict[str, object]],
) -> list[ContextPointRecord]:
    """Convert SEAD site rows into compact environmental archaeology records."""
    records: list[ContextPointRecord] = []
    for row in rows:
        latitude = row.get("latitude_dd")
        longitude = row.get("longitude_dd")
        if latitude is None or longitude is None:
            continue
        country = classify_country(float(longitude), float(latitude), country_boundaries)
        if not country:
            continue
        site_id = str(row.get("site_id", "")).strip()
        site_name = str(row.get("site_name", "")).strip() or f"SEAD site {site_id}"
        national_identifier = str(row.get("national_site_identifier", "") or "").strip()
        altitude = clean_optional_text(row.get("altitude"))
        description = str(row.get("site_description", "") or "").strip()
        source_url = f"https://browser.sead.se/site/{site_id}"
        sample_group_count = int(row.get("sample_group_count") or 0)
        physical_sample_count = int(row.get("physical_sample_count") or 0)
        analysis_entity_count = int(row.get("analysis_entity_count") or 0)
        dataset_count = int(row.get("dataset_count") or 0)
        reference_count = int(row.get("reference_count") or 0)
        dataset_names = row.get("dataset_names")
        if not isinstance(dataset_names, list):
            dataset_names = []

        popup_rows = [
            ("Site ID", site_id),
            ("Category", "Environmental archaeology"),
            ("Source", "SEAD"),
            ("Country", country),
        ]
        if sample_group_count:
            popup_rows.append(("Sample groups", str(sample_group_count)))
        if physical_sample_count:
            popup_rows.append(("Physical samples", str(physical_sample_count)))
        if analysis_entity_count:
            popup_rows.append(("Analysis entities", str(analysis_entity_count)))
        if dataset_count:
            popup_rows.append(("Datasets", str(dataset_count)))
        if dataset_names:
            popup_rows.append(("Dataset names", ", ".join(dataset_names)))
        if reference_count:
            popup_rows.append(("References", str(reference_count)))
        if national_identifier:
            popup_rows.append(("National identifier", national_identifier))
        if altitude:
            popup_rows.append(("Altitude", altitude))
        if description:
            popup_rows.append(("Description", description))

        records.append(
            ContextPointRecord(
                source="SEAD",
                layer_key="sead-sites",
                layer_label="SEAD sites",
                category="Environmental archaeology",
                country=country,
                record_id=site_id,
                name=site_name,
                latitude=float(latitude),
                longitude=float(longitude),
                geometry_type="Point",
                subtitle="Nordic environmental archaeology sites",
                description=description,
                source_url=source_url,
                record_count=max(dataset_count, analysis_entity_count, 1),
                popup_rows=tuple(popup_rows),
            )
        )

    return sorted(records, key=lambda item: (item.name.casefold(), item.record_id))


def collect_sead_data(
    output_root: Path,
    country_boundaries: dict[str, dict[str, object]],
    bbox: tuple[float, float, float, float],
) -> SeadDataReport:
    """Download and write the SEAD dataset under data/sead."""
    output_root = Path(output_root)
    raw_dir = output_root / "raw"
    normalized_dir = output_root / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    rows = fetch_sead_site_rows(bbox=bbox)
    raw_path = raw_dir / "nordic_sites.json"
    write_json(
        raw_path,
        {
            "generated_on": str(date.today()),
            "source": "SEAD",
            "endpoint": "https://browser.sead.se/postgrest/tbl_sites",
            "row_count": len(rows),
            "rows": rows,
        },
    )
    records = normalize_sead_rows(rows, country_boundaries=country_boundaries)
    normalized_csv_path = SEAD_POINT_CSV.source_path_under(output_root)
    normalized_geojson_path = SEAD_POINT_GEOJSON.source_path_under(output_root)
    write_context_points_csv(normalized_csv_path, records)
    write_context_points_geojson(normalized_geojson_path, records)

    return SeadDataReport(
        output_dir=output_root,
        point_count=len(records),
        raw_path=raw_path,
        normalized_csv_path=normalized_csv_path,
        normalized_geojson_path=normalized_geojson_path,
    )
