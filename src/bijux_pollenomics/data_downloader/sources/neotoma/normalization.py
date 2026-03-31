from __future__ import annotations

import copy
import json
from typing import Iterable

from ....core.bp_time import build_bp_interval_label, clamp_bp_year, midpoint_bp_year, normalize_bp_interval
from ....core.text import clean_optional_text
from ...geometry import classify_country, geometry_to_representative_point, point_in_bbox
from ...models import ContextPointRecord

__all__ = [
    "build_neotoma_site_rows_from_downloads",
    "build_neotoma_site_snapshot_rows",
    "classify_neotoma_site_country",
    "normalize_neotoma_rows",
]


def build_neotoma_site_rows_from_downloads(download_rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    """Aggregate full dataset downloads into one enriched site row per Neotoma site."""
    site_rows = []
    for item in download_rows:
        row = build_neotoma_site_row_from_download(item)
        if row is not None:
            site_rows.append(row)
    merged_rows = merge_neotoma_site_rows(site_rows)
    for row in merged_rows:
        populate_neotoma_site_summary_fields(row)
    return merged_rows


def build_neotoma_site_snapshot_rows(rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    """Build compact site-summary rows without duplicating full sample payloads."""
    snapshot_rows: list[dict[str, object]] = []
    for row in rows:
        snapshot = copy.deepcopy(row)
        snapshot_units = []
        for unit in normalize_collection_units(snapshot.get("collectionunits")):
            snapshot_unit = {key: copy.deepcopy(value) for key, value in unit.items() if key != "datasets"}
            snapshot_unit["datasets"] = [
                build_neotoma_dataset_snapshot(dataset)
                for dataset in normalize_datasets(unit.get("datasets"))
            ]
            snapshot_unit["datasets"] = sort_datasets(snapshot_unit["datasets"])
            snapshot_units.append(snapshot_unit)
        snapshot["collectionunits"] = sorted(snapshot_units, key=collection_unit_sort_key)
        snapshot_rows.append(snapshot)
    return snapshot_rows


def build_neotoma_dataset_snapshot(dataset: dict[str, object]) -> dict[str, object]:
    """Build a compact dataset summary without nested samples or chronologies."""
    snapshot = {
        key: copy.deepcopy(value)
        for key, value in dataset.items()
        if key not in {"samples", "chronologies", "defaultchronology"}
    }
    snapshot["sample_count"] = count_neotoma_dataset_samples(dataset)
    snapshot["analysis_unit_count"] = count_neotoma_dataset_analysis_units(dataset)
    snapshot["chronology_count"] = count_neotoma_dataset_chronologies(dataset)
    snapshot["taxon_count"] = count_neotoma_dataset_taxa(dataset)
    return snapshot


def build_neotoma_site_row_from_download(download_row: object) -> dict[str, object] | None:
    """Project one full dataset download into the site structure used downstream."""
    if not isinstance(download_row, dict):
        return None
    site = download_row.get("site")
    if not isinstance(site, dict):
        return None

    row = {
        key: copy.deepcopy(value)
        for key, value in site.items()
        if key not in {"dataset", "collectionunit", "chronologies", "defaultchronology"}
    }
    dataset = build_neotoma_dataset_from_download(site)
    collection_unit = build_neotoma_collection_unit_from_download(site, dataset)
    row["collectionunits"] = [collection_unit] if collection_unit is not None else []
    return row


def build_neotoma_collection_unit_from_download(
    site: dict[str, object],
    dataset: dict[str, object] | None,
) -> dict[str, object] | None:
    """Normalize one collection unit from the full dataset download response."""
    collection_unit = site.get("collectionunit")
    if not isinstance(collection_unit, dict):
        return None
    row = {
        "collectionunitid": copy.deepcopy(collection_unit.get("collectionunitid")),
        "collectionunit": copy.deepcopy(collection_unit.get("collectionunit")),
        "handle": copy.deepcopy(collection_unit.get("handle")),
        "collectionunittype": copy.deepcopy(collection_unit.get("collunittype")),
        "collectiondevice": copy.deepcopy(collection_unit.get("collectiondevice")),
        "depositionalenvironment": copy.deepcopy(collection_unit.get("depositionalenvironment")),
        "location": copy.deepcopy(collection_unit.get("location")),
        "notes": copy.deepcopy(collection_unit.get("notes")),
        "waterdepth": copy.deepcopy(collection_unit.get("waterdepth")),
        "datasets": [dataset] if dataset is not None else [],
    }
    gps_location = collection_unit.get("gpslocation")
    if isinstance(gps_location, dict):
        row["gpslocation"] = copy.deepcopy(gps_location)
    return row


def build_neotoma_dataset_from_download(site: dict[str, object]) -> dict[str, object] | None:
    """Normalize one dataset record from the full dataset download response."""
    collection_unit = site.get("collectionunit")
    if isinstance(collection_unit, dict) and isinstance(collection_unit.get("dataset"), dict):
        dataset = copy.deepcopy(collection_unit["dataset"])
    elif isinstance(site.get("dataset"), dict):
        dataset = copy.deepcopy(site["dataset"])
    else:
        return None
    dataset["chronologies"] = copy.deepcopy(site.get("chronologies", []))
    dataset["defaultchronology"] = copy.deepcopy(site.get("defaultchronology"))
    return dataset


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


def classify_neotoma_site_country(
    site: dict[str, object],
    bbox: tuple[float, float, float, float],
    country_boundaries: dict[str, dict[str, object]],
) -> str:
    """Resolve a Neotoma site payload to one tracked Nordic country, if any."""
    representative_point = neotoma_site_representative_point(site)
    if representative_point is None:
        return ""
    longitude, latitude, _ = representative_point
    if not point_in_bbox(longitude=longitude, latitude=latitude, bbox=bbox):
        return ""
    return classify_country(longitude, latitude, country_boundaries)


def neotoma_site_representative_point(site: dict[str, object]) -> tuple[float, float, str] | None:
    """Return one representative point for a Neotoma site payload."""
    geography_text = clean_optional_text(site.get("geography"))
    if not geography_text:
        return None
    try:
        geography = json.loads(geography_text)
    except json.JSONDecodeError:
        return None
    if not isinstance(geography, dict):
        return None
    return geometry_to_representative_point(geography)


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


def populate_neotoma_site_summary_fields(row: dict[str, object]) -> None:
    """Populate denormalized summary fields used by raw artifacts and map popups."""
    collection_units = normalize_collection_units(row.get("collectionunits"))
    datasets = [
        dataset
        for unit in collection_units
        for dataset in normalize_datasets(unit.get("datasets"))
    ]
    row["collectionunits"] = collection_units
    row["dataset_count"] = len({dataset_key(dataset) for dataset in datasets})
    row["dataset_ids"] = [
        clean_optional_text(dataset.get("datasetid"))
        for dataset in sort_datasets(datasets)
        if clean_optional_text(dataset.get("datasetid"))
    ]
    row["dataset_types"] = sorted(
        {
            clean_optional_text(dataset.get("datasettype"))
            for dataset in datasets
            if clean_optional_text(dataset.get("datasettype"))
        }
    )
    row["databases"] = sorted(
        {
            clean_optional_text(dataset.get("database"))
            for dataset in datasets
            if clean_optional_text(dataset.get("database"))
        }
    )

    sample_ids: set[str] = set()
    analysis_unit_ids: set[str] = set()
    chronology_ids: set[str] = set()
    taxon_keys: set[tuple[str, str]] = set()
    age_ranges_by_units: dict[str, dict[str, float | str]] = {}

    for dataset in datasets:
        for chronology in normalize_chronologies(dataset.get("chronologies")):
            chronology_id = chronology_key(chronology)
            if chronology_id:
                chronology_ids.add(chronology_id)

        merge_age_ranges(age_ranges_by_units, dataset.get("agerange"))

        samples = dataset.get("samples", [])
        if not isinstance(samples, list):
            continue
        for sample in samples:
            if not isinstance(sample, dict):
                continue
            sample_id = clean_optional_text(sample.get("sampleid"))
            if sample_id:
                sample_ids.add(sample_id)
            analysis_unit_id = clean_optional_text(sample.get("analysisunitid"))
            if analysis_unit_id:
                analysis_unit_ids.add(analysis_unit_id)
            merge_age_ranges(age_ranges_by_units, sample.get("ages"))
            datum = sample.get("datum", [])
            if not isinstance(datum, list):
                continue
            for item in datum:
                if not isinstance(item, dict):
                    continue
                taxon_id = clean_optional_text(item.get("taxonid"))
                variable_name = clean_optional_text(item.get("variablename"))
                if taxon_id or variable_name:
                    taxon_keys.add((taxon_id, variable_name))

    row["sample_count"] = len(sample_ids)
    row["analysis_unit_count"] = len(analysis_unit_ids)
    row["chronology_count"] = len(chronology_ids)
    row["taxon_count"] = len(taxon_keys)
    row["age_ranges"] = sorted(
        age_ranges_by_units.values(),
        key=lambda item: clean_optional_text(item.get("units")),
    )


def normalize_chronologies(value: object) -> list[dict[str, object]]:
    """Normalize chronology payloads to a mutable list of dictionaries."""
    if not isinstance(value, list):
        return []
    return [copy.deepcopy(item) for item in value if isinstance(item, dict)]


def count_neotoma_dataset_samples(dataset: dict[str, object]) -> int:
    """Count unique samples in one Neotoma dataset payload."""
    samples = dataset.get("samples", [])
    if not isinstance(samples, list):
        return 0
    return len(
        {
            clean_optional_text(sample.get("sampleid"))
            for sample in samples
            if isinstance(sample, dict) and clean_optional_text(sample.get("sampleid"))
        }
    )


def count_neotoma_dataset_analysis_units(dataset: dict[str, object]) -> int:
    """Count unique analysis units in one Neotoma dataset payload."""
    samples = dataset.get("samples", [])
    if not isinstance(samples, list):
        return 0
    return len(
        {
            clean_optional_text(sample.get("analysisunitid"))
            for sample in samples
            if isinstance(sample, dict) and clean_optional_text(sample.get("analysisunitid"))
        }
    )


def count_neotoma_dataset_chronologies(dataset: dict[str, object]) -> int:
    """Count unique chronologies in one Neotoma dataset payload."""
    return len(
        {
            chronology_key(chronology)
            for chronology in normalize_chronologies(dataset.get("chronologies"))
            if chronology_key(chronology)
        }
    )


def count_neotoma_dataset_taxa(dataset: dict[str, object]) -> int:
    """Count unique taxa in one Neotoma dataset payload."""
    samples = dataset.get("samples", [])
    if not isinstance(samples, list):
        return 0
    taxon_keys: set[tuple[str, str]] = set()
    for sample in samples:
        if not isinstance(sample, dict):
            continue
        datum = sample.get("datum", [])
        if not isinstance(datum, list):
            continue
        for item in datum:
            if not isinstance(item, dict):
                continue
            taxon_id = clean_optional_text(item.get("taxonid"))
            variable_name = clean_optional_text(item.get("variablename"))
            if taxon_id or variable_name:
                taxon_keys.add((taxon_id, variable_name))
    return len(taxon_keys)


def chronology_key(chronology: dict[str, object]) -> str:
    """Build a stable identity key for one chronology payload."""
    chronology_id = clean_optional_text(chronology.get("chronologyid"))
    if chronology_id:
        return chronology_id
    nested = chronology.get("chronology")
    if isinstance(nested, dict):
        return clean_optional_text(nested.get("chronologyid"))
    return ""


def merge_age_ranges(
    age_ranges_by_units: dict[str, dict[str, float | str]],
    values: object,
) -> None:
    """Aggregate Neotoma age ranges by units."""
    if not isinstance(values, list):
        return
    for item in values:
        if not isinstance(item, dict):
            continue
        units = clean_optional_text(item.get("units") or item.get("agetype"))
        if not units:
            continue
        target = age_ranges_by_units.setdefault(
            units,
            {"units": units, "ageold": None, "ageyoung": None},
        )
        age_old = numeric_age_value(item.get("ageold") or item.get("ageolder") or item.get("older"))
        age_young = numeric_age_value(item.get("ageyoung") or item.get("ageyounger") or item.get("younger"))
        if age_old is not None and (target["ageold"] is None or age_old > target["ageold"]):
            target["ageold"] = age_old
        if age_young is not None and (target["ageyoung"] is None or age_young < target["ageyoung"]):
            target["ageyoung"] = age_young


def numeric_age_value(value: object) -> float | None:
    """Return a numeric age value when a payload field is populated."""
    if isinstance(value, (int, float)):
        return float(value)
    text = clean_optional_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def format_neotoma_age_range(age_range: dict[str, object]) -> str:
    """Render one aggregated Neotoma age range for popup display."""
    younger = numeric_age_value(age_range.get("ageyoung"))
    older = numeric_age_value(age_range.get("ageold"))
    if younger is None and older is None:
        return ""
    if younger is None:
        return format_neotoma_age_value(older)
    if older is None:
        return format_neotoma_age_value(younger)
    return f"{format_neotoma_age_value(younger)} to {format_neotoma_age_value(older)}"


def format_neotoma_age_value(value: float | None) -> str:
    """Render a Neotoma numeric age without unnecessary decimal places."""
    if value is None:
        return ""
    rounded = round(value)
    if abs(value - rounded) < 1e-9:
        return str(int(rounded))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def neotoma_time_interval(age_ranges: list[dict[str, object]]) -> tuple[int, int] | None:
    """Choose a filterable BP interval from Neotoma site age coverage."""
    preferred_ranges = sorted(
        [
            age_range
            for age_range in age_ranges
            if neotoma_age_range_units_supported(clean_optional_text(age_range.get("units")))
        ],
        key=neotoma_age_range_priority,
    )
    intervals: list[tuple[int, int]] = []
    for age_range in preferred_ranges:
        older = clamp_bp_year(round_age_value(age_range.get("ageold")))
        younger = clamp_bp_year(round_age_value(age_range.get("ageyoung")))
        interval = normalize_bp_interval(younger, older)
        if interval is not None:
            intervals.append(interval)
    if not intervals:
        return None
    return (
        min(start for start, _ in intervals),
        max(end for _, end in intervals),
    )


def neotoma_time_label(
    age_ranges: list[dict[str, object]],
    interval: tuple[int, int] | None,
) -> str:
    """Render a human-readable Neotoma age-coverage label."""
    preferred_ranges = sorted(
        [
            age_range
            for age_range in age_ranges
            if neotoma_age_range_units_supported(clean_optional_text(age_range.get("units")))
        ],
        key=neotoma_age_range_priority,
    )
    if preferred_ranges:
        units = clean_optional_text(preferred_ranges[0].get("units"))
        older = clamp_bp_year(round_age_value(preferred_ranges[0].get("ageold")))
        younger = clamp_bp_year(round_age_value(preferred_ranges[0].get("ageyoung")))
        preferred_interval = normalize_bp_interval(younger, older)
        value = (
            build_bp_interval_label(preferred_interval[0], preferred_interval[1]).replace(" BP", "")
            if preferred_interval is not None
            else format_neotoma_age_range(preferred_ranges[0])
        )
        if units and value:
            return f"{value} {units}"
    if interval is None:
        return ""
    return build_bp_interval_label(interval[0], interval[1])


def neotoma_age_range_units_supported(units: str) -> bool:
    """Return whether a Neotoma age range is expressed in BP units."""
    return "bp" in units.casefold()


def neotoma_age_range_priority(age_range: dict[str, object]) -> tuple[int, str]:
    """Prefer calibrated BP ranges over uncalibrated BP ranges."""
    units = clean_optional_text(age_range.get("units"))
    normalized = units.casefold()
    if "cal" in normalized and "bp" in normalized:
        return (0, normalized)
    if "bp" in normalized:
        return (1, normalized)
    return (2, normalized)


def round_age_value(value: object) -> int | None:
    """Round one Neotoma numeric age value to an integer BP year."""
    numeric = numeric_age_value(value)
    if numeric is None:
        return None
    return int(round(numeric))


def normalize_neotoma_rows(
    rows: Iterable[dict[str, object]],
    bbox: tuple[float, float, float, float],
    country_boundaries: dict[str, dict[str, object]],
) -> list[ContextPointRecord]:
    """Convert raw Neotoma rows into compact Nordic pollen site records."""
    records: list[ContextPointRecord] = []
    for row in rows:
        representative_point = neotoma_site_representative_point(row)
        if representative_point is None:
            continue
        longitude, latitude, geometry_type = representative_point
        if not point_in_bbox(longitude=longitude, latitude=latitude, bbox=bbox):
            continue
        country = classify_country(longitude, latitude, country_boundaries)
        if not country:
            continue

        collection_units = normalize_collection_units(row.get("collectionunits"))
        datasets = [
            dataset
            for unit in collection_units
            for dataset in normalize_datasets(unit.get("datasets"))
        ]

        dataset_types = row.get("dataset_types")
        if not isinstance(dataset_types, list):
            dataset_types = sorted(
                {
                    clean_optional_text(dataset.get("datasettype"))
                    for dataset in datasets
                    if clean_optional_text(dataset.get("datasettype"))
                }
            )

        dataset_count = int(row.get("dataset_count") or len({dataset_key(dataset) for dataset in datasets}))
        collection_unit_count = len(collection_units)
        sample_count = int(row.get("sample_count") or 0)
        chronology_count = int(row.get("chronology_count") or 0)
        taxon_count = int(row.get("taxon_count") or 0)
        databases = row.get("databases")
        if not isinstance(databases, list):
            databases = sorted(
                {
                    clean_optional_text(dataset.get("database"))
                    for dataset in datasets
                    if clean_optional_text(dataset.get("database"))
                }
            )
        age_ranges = row.get("age_ranges")
        if not isinstance(age_ranges, list):
            age_ranges_by_units: dict[str, dict[str, float | str]] = {}
            for dataset in datasets:
                merge_age_ranges(age_ranges_by_units, dataset.get("agerange"))
                samples = dataset.get("samples", [])
                if not isinstance(samples, list):
                    continue
                for sample in samples:
                    if isinstance(sample, dict):
                        merge_age_ranges(age_ranges_by_units, sample.get("ages"))
            age_ranges = sorted(age_ranges_by_units.values(), key=lambda item: clean_optional_text(item.get("units")))
        time_interval = neotoma_time_interval(age_ranges)
        time_label = neotoma_time_label(age_ranges, time_interval)
        site_id = str(row.get("siteid", "")).strip()
        site_name = str(row.get("sitename", "")).strip() or f"Neotoma site {site_id}"
        source_url = f"https://apps.neotomadb.org/explorer/#/record/site/{site_id}"
        description = clean_optional_text(row.get("sitedescription")) or clean_optional_text(row.get("notes"))
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
        if sample_count:
            popup_rows.append(("Samples", str(sample_count)))
        if chronology_count:
            popup_rows.append(("Chronologies", str(chronology_count)))
        if taxon_count:
            popup_rows.append(("Taxa", str(taxon_count)))
        if dataset_types:
            popup_rows.append(("Dataset types", ", ".join(dataset_types)))
        if databases:
            popup_rows.append(("Databases", ", ".join(databases)))
        for age_range in age_ranges:
            if not isinstance(age_range, dict):
                continue
            units = clean_optional_text(age_range.get("units"))
            value = format_neotoma_age_range(age_range)
            if units and value:
                popup_rows.append((f"Age coverage ({units})", value))
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
                subtitle="Nordic pollen sites with samples and chronologies",
                description=description,
                source_url=source_url,
                record_count=dataset_count,
                popup_rows=tuple(popup_rows),
                time_start_bp=time_interval[0] if time_interval is not None else None,
                time_end_bp=time_interval[1] if time_interval is not None else None,
                time_mean_bp=midpoint_bp_year(time_interval[0], time_interval[1]) if time_interval is not None else None,
                time_label=time_label,
            )
        )

    return sorted(records, key=lambda item: (item.name.casefold(), item.record_id))


__all__ = [
    "build_neotoma_site_rows_from_downloads",
    "build_neotoma_site_snapshot_rows",
    "classify_neotoma_site_country",
    "normalize_neotoma_rows",
]
