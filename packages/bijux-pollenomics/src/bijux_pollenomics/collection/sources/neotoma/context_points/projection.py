from __future__ import annotations

from collections.abc import Iterable, Mapping

from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.collection.spatial import classify_country, point_in_bbox
from bijux_pollenomics.core.bp_time import midpoint_bp_year
from bijux_pollenomics.core.text import clean_optional_text

from ..chronology import (
    AgeRangeAggregate,
    format_neotoma_age_range,
    merge_age_ranges,
    neotoma_time_interval,
    neotoma_time_label,
)
from ..chronology.semantics import _build_neotoma_temporal_semantics
from ..country import neotoma_site_representative_point
from ..site_inventory.merging import (
    dataset_key,
    normalize_collection_units,
    normalize_datasets,
    parse_int_or_default,
)


def normalize_neotoma_rows(
    rows: Iterable[dict[str, object]],
    bbox: tuple[float, float, float, float],
    country_boundaries: Mapping[str, Mapping[str, object]],
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

        dataset_count = parse_int_or_default(
            row.get("dataset_count"),
            default=len({dataset_key(dataset) for dataset in datasets}),
        )
        collection_unit_count = len(collection_units)
        sample_count = parse_int_or_default(row.get("sample_count"))
        chronology_count = parse_int_or_default(row.get("chronology_count"))
        taxon_count = parse_int_or_default(row.get("taxon_count"))
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
            age_ranges_by_units: dict[str, AgeRangeAggregate] = {}
            for dataset in datasets:
                merge_age_ranges(age_ranges_by_units, dataset.get("agerange"))
                samples = dataset.get("samples", [])
                if not isinstance(samples, list):
                    continue
                for sample in samples:
                    if isinstance(sample, dict):
                        merge_age_ranges(age_ranges_by_units, sample.get("ages"))
            age_ranges = sorted(
                age_ranges_by_units.values(),
                key=lambda item: clean_optional_text(item.get("units")),
            )
        age_ranges = [
            age_range for age_range in age_ranges if isinstance(age_range, dict)
        ]
        time_interval = neotoma_time_interval(age_ranges)
        time_label = neotoma_time_label(age_ranges, time_interval)
        temporal_semantics = _build_neotoma_temporal_semantics(
            age_ranges,
            time_interval=time_interval,
            time_label=time_label,
        )
        site_id = str(row.get("siteid", "")).strip()
        site_name = str(row.get("sitename", "")).strip() or f"Neotoma site {site_id}"
        source_url = f"https://apps.neotomadb.org/explorer/#/record/site/{site_id}"
        description = clean_optional_text(
            row.get("sitedescription")
        ) or clean_optional_text(row.get("notes"))
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
            units = clean_optional_text(age_range.get("units"))
            value = format_neotoma_age_range(age_range)
            if units and value:
                popup_rows.append((f"Age coverage ({units})", value))
        comparability_posture = str(
            temporal_semantics.get("comparability_posture", "")
        ).strip()
        if comparability_posture:
            popup_rows.append(
                (
                    "Temporal comparison posture",
                    comparability_posture.replace("_", " "),
                )
            )
        window_label = str(temporal_semantics.get("temporal_window_label", "")).strip()
        if window_label:
            popup_rows.append(("Temporal window", window_label))
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
                time_mean_bp=midpoint_bp_year(time_interval[0], time_interval[1])
                if time_interval is not None
                else None,
                time_label=time_label,
                temporal_semantics=temporal_semantics,
            )
        )

    return sorted(records, key=lambda item: (item.name.casefold(), item.record_id))
