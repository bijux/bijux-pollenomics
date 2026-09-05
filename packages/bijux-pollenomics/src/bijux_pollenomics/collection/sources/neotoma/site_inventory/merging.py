from __future__ import annotations

from collections.abc import Iterable
import copy

from bijux_pollenomics.core.text import clean_optional_text


def merge_neotoma_site_rows(
    rows: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    """Merge site rows from multiple Neotoma endpoints into one deduplicated site inventory."""
    merged_rows: dict[str, dict[str, object]] = {}
    for row in rows:
        site_id = str(row.get("siteid", "")).strip()
        if not site_id:
            continue
        existing = merged_rows.get(site_id)
        if existing is None:
            merged_rows[site_id] = copy.deepcopy(row)
            merged_rows[site_id]["collectionunits"] = normalize_collection_units(
                row.get("collectionunits")
            )
            continue
        merge_neotoma_site_row(existing, row)

    return sorted(
        merged_rows.values(),
        key=lambda item: parse_int_or_default(item.get("siteid")),
    )


def merge_neotoma_site_row(
    existing: dict[str, object], incoming: dict[str, object]
) -> None:
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
    unit_positions = {
        collection_unit_key(unit): index for index, unit in enumerate(merged_units)
    }

    for incoming_unit in incoming_units:
        key = collection_unit_key(incoming_unit)
        if key not in unit_positions:
            merged_units.append(copy.deepcopy(incoming_unit))
            unit_positions[key] = len(merged_units) - 1
            continue

        existing_unit = merged_units[unit_positions[key]]
        for field in (
            "collectionunitid",
            "collectionunit",
            "handle",
            "collectionunittype",
        ):
            if not clean_optional_text(existing_unit.get(field)):
                existing_unit[field] = copy.deepcopy(incoming_unit.get(field))

        merged_datasets = normalize_datasets(existing_unit.get("datasets"))
        dataset_positions = {
            dataset_key(dataset): index for index, dataset in enumerate(merged_datasets)
        }
        for incoming_dataset in normalize_datasets(incoming_unit.get("datasets")):
            key = dataset_key(incoming_dataset)
            if key in dataset_positions:
                existing_dataset = merged_datasets[dataset_positions[key]]
                for field, value in incoming_dataset.items():
                    if field not in existing_dataset or existing_dataset[field] in (
                        "",
                        None,
                        [],
                        {},
                    ):
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


def normalize_chronologies(value: object) -> list[dict[str, object]]:
    """Normalize chronology payloads to a mutable list of dictionaries."""
    if not isinstance(value, list):
        return []
    return [copy.deepcopy(item) for item in value if isinstance(item, dict)]


def parse_int_or_default(value: object, *, default: int = 0) -> int:
    """Parse one optional numeric field as integer with fallback."""
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = clean_optional_text(value)
    if not text:
        return default
    try:
        return int(text)
    except ValueError:
        return default
