from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from .models import LocalitySummary, SampleRecord, SchemaError
from .utils import clean_text, pick_value
from ..temporal import build_bp_interval_label, derive_bp_interval_from_mean_and_stddev, midpoint_bp_year


def load_country_samples(version_dir: Path, country: str) -> tuple[list[SampleRecord], Counter[str]]:
    """Load and deduplicate all samples for a country across every anno file in a version directory."""
    combined: dict[str, SampleRecord] = {}
    dataset_counts: Counter[str] = Counter()
    country_key = country.strip().casefold()

    for anno_path in discover_anno_files(version_dir):
        dataset_name = anno_path.parent.name
        for sample in iter_samples_from_anno(anno_path, dataset_name):
            if sample.political_entity.casefold() != country_key:
                continue
            dataset_counts[dataset_name] += 1
            existing = combined.get(sample.genetic_id)
            if existing is None:
                combined[sample.genetic_id] = sample
                continue

            merged_datasets = tuple(sorted(set(existing.datasets) | set(sample.datasets)))
            merged_interval = merge_sample_time_interval(existing, sample)
            combined[sample.genetic_id] = SampleRecord(
                genetic_id=existing.genetic_id,
                master_id=pick_value(existing.master_id, sample.master_id),
                group_id=pick_value(existing.group_id, sample.group_id),
                locality=pick_value(existing.locality, sample.locality),
                political_entity=pick_value(existing.political_entity, sample.political_entity),
                latitude=existing.latitude,
                longitude=existing.longitude,
                latitude_text=pick_value(existing.latitude_text, sample.latitude_text),
                longitude_text=pick_value(existing.longitude_text, sample.longitude_text),
                publication=pick_value(existing.publication, sample.publication),
                year_first_published=pick_value(existing.year_first_published, sample.year_first_published),
                full_date=pick_value(existing.full_date, sample.full_date),
                date_mean_bp=pick_value(existing.date_mean_bp, sample.date_mean_bp),
                date_stddev_bp=pick_value(existing.date_stddev_bp, sample.date_stddev_bp),
                data_type=pick_value(existing.data_type, sample.data_type),
                molecular_sex=pick_value(existing.molecular_sex, sample.molecular_sex),
                datasets=merged_datasets,
                time_start_bp=merged_interval[0] if merged_interval is not None else None,
                time_end_bp=merged_interval[1] if merged_interval is not None else None,
                time_mean_bp=mean_bp_from_samples(existing, sample, merged_interval),
                time_label=pick_time_label(existing, sample, merged_interval),
            )

    samples = sorted(
        combined.values(),
        key=lambda sample: (
            sample.locality.casefold(),
            sample.master_id.casefold(),
            sample.genetic_id.casefold(),
        ),
    )
    return samples, dataset_counts


def summarize_localities(samples: Iterable[SampleRecord]) -> list[LocalitySummary]:
    """Aggregate samples into unique locality coordinates."""
    grouped: dict[tuple[str, str, str], list[SampleRecord]] = defaultdict(list)
    for sample in samples:
        key = (sample.locality, sample.latitude_text, sample.longitude_text)
        grouped[key].append(sample)

    summaries: list[LocalitySummary] = []
    for (locality, latitude_text, longitude_text), records in grouped.items():
        datasets = tuple(sorted({dataset for record in records for dataset in record.datasets}))
        sample_ids = tuple(record.genetic_id for record in sorted(records, key=lambda item: item.genetic_id))
        summaries.append(
            LocalitySummary(
                locality=locality,
                latitude=records[0].latitude,
                longitude=records[0].longitude,
                latitude_text=latitude_text,
                longitude_text=longitude_text,
                sample_count=len(records),
                sample_ids=sample_ids,
                datasets=datasets,
            )
        )

    summaries.sort(key=lambda item: (-item.sample_count, item.locality.casefold()))
    return summaries


def discover_anno_files(version_dir: Path) -> list[Path]:
    """Find all public anno files for a given AADR version directory."""
    files = sorted(path for path in version_dir.glob("*/*.anno") if path.is_file())
    if not files:
        raise FileNotFoundError(f"No .anno files found under {version_dir}")
    return files


def iter_samples_from_anno(path: Path, dataset_name: str) -> Iterable[SampleRecord]:
    """Yield normalized sample records from a single AADR anno file."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        schema = resolve_schema(reader.fieldnames or [])
        for row in reader:
            genetic_id = clean_text(row.get(schema["genetic_id"], ""))
            latitude_text = clean_text(row.get(schema["latitude"], ""))
            longitude_text = clean_text(row.get(schema["longitude"], ""))
            if not genetic_id or not latitude_text or not longitude_text:
                continue
            try:
                latitude = float(latitude_text)
                longitude = float(longitude_text)
            except ValueError:
                continue
            time_interval = sample_time_interval(row, schema)
            yield SampleRecord(
                genetic_id=genetic_id,
                master_id=clean_text(row.get(schema["master_id"], "")),
                group_id=clean_text(row.get(schema["group_id"], "")),
                locality=clean_text(row.get(schema["locality"], "")) or "Unspecified locality",
                political_entity=clean_text(row.get(schema["political_entity"], "")),
                latitude=latitude,
                longitude=longitude,
                latitude_text=latitude_text,
                longitude_text=longitude_text,
                publication=clean_text(row.get(schema["publication"], "")),
                year_first_published=clean_text(row.get(schema["year_first_published"], "")),
                full_date=clean_text(row.get(schema["full_date"], "")),
                date_mean_bp=clean_text(row.get(schema["date_mean_bp"], "")),
                date_stddev_bp=clean_text(row.get(schema["date_stddev_bp"], "")),
                data_type=clean_text(row.get(schema["data_type"], "")),
                molecular_sex=clean_text(row.get(schema["molecular_sex"], "")),
                datasets=(dataset_name,),
                time_start_bp=time_interval[0] if time_interval is not None else None,
                time_end_bp=time_interval[1] if time_interval is not None else None,
                time_mean_bp=sample_time_mean(row, schema),
                time_label=sample_time_label(row, schema),
            )


def resolve_schema(fieldnames: list[str]) -> dict[str, str | None]:
    """Map expected logical fields to raw AADR column names."""
    return {
        "genetic_id": find_column(fieldnames, "Genetic ID"),
        "master_id": find_column(fieldnames, "Master ID"),
        "group_id": find_column(fieldnames, "Group ID"),
        "locality": find_column(fieldnames, "Locality"),
        "political_entity": find_column(fieldnames, "Political Entity"),
        "latitude": find_column(fieldnames, "Lat.", "Latitude"),
        "longitude": find_column(fieldnames, "Long.", "Longitude"),
        "publication": find_column(fieldnames, "Publication abbreviation"),
        "year_first_published": find_column(
            fieldnames,
            "Year data from this individual was first published",
            "Year first published",
        ),
        "full_date": find_column(fieldnames, "Full Date"),
        "date_mean_bp": find_column(fieldnames, "Date mean in BP"),
        "date_stddev_bp": find_optional_column(fieldnames, "Date standard deviation in BP"),
        "data_type": find_column(fieldnames, "Data type"),
        "molecular_sex": find_column(fieldnames, "Molecular Sex"),
    }


def find_column(fieldnames: list[str], *prefixes: str) -> str:
    """Find a column by exact name or a stable prefix."""
    lowered = {field.casefold(): field for field in fieldnames}
    for prefix in prefixes:
        exact = lowered.get(prefix.casefold())
        if exact:
            return exact
    for prefix in prefixes:
        prefix_key = prefix.casefold()
        for field in fieldnames:
            if field.casefold().startswith(prefix_key):
                return field
    raise SchemaError(f"Could not find any of {prefixes!r} in anno columns")


def find_optional_column(fieldnames: list[str], *prefixes: str) -> str | None:
    """Find a column by exact name or prefix when present."""
    try:
        return find_column(fieldnames, *prefixes)
    except SchemaError:
        return None


def sample_time_interval(row: dict[str, str], schema: dict[str, str | None]) -> tuple[int, int] | None:
    """Derive one AADR BP interval from the row's mean and standard deviation."""
    return derive_bp_interval_from_mean_and_stddev(
        row.get(schema["date_mean_bp"], ""),
        row.get(schema["date_stddev_bp"], ""),
    )


def sample_time_mean(row: dict[str, str], schema: dict[str, str | None]) -> int | None:
    """Return the sample mean BP year used for time filtering summaries."""
    interval = sample_time_interval(row, schema)
    return midpoint_bp_year(interval[0], interval[1]) if interval is not None else None


def sample_time_label(row: dict[str, str], schema: dict[str, str | None]) -> str:
    """Return the best available human-readable AADR time label."""
    full_date = clean_text(row.get(schema["full_date"], ""))
    if full_date:
        return full_date
    interval = sample_time_interval(row, schema)
    if interval is None:
        return ""
    return build_bp_interval_label(interval[0], interval[1])


def merge_sample_time_interval(
    left: SampleRecord,
    right: SampleRecord,
) -> tuple[int, int] | None:
    """Merge two sample intervals into a single BP span."""
    intervals = [
        interval
        for interval in (
            (left.time_start_bp, left.time_end_bp) if left.time_start_bp is not None and left.time_end_bp is not None else None,
            (right.time_start_bp, right.time_end_bp) if right.time_start_bp is not None and right.time_end_bp is not None else None,
        )
        if interval is not None
    ]
    if not intervals:
        return None
    return (
        min(start for start, _ in intervals),
        max(end for _, end in intervals),
    )


def mean_bp_from_samples(
    left: SampleRecord,
    right: SampleRecord,
    merged_interval: tuple[int, int] | None,
) -> int | None:
    """Choose the best AADR midpoint for merged duplicate samples."""
    for value in (left.time_mean_bp, right.time_mean_bp):
        if value is not None:
            return value
    if merged_interval is None:
        return None
    return midpoint_bp_year(merged_interval[0], merged_interval[1])


def pick_time_label(
    left: SampleRecord,
    right: SampleRecord,
    merged_interval: tuple[int, int] | None,
) -> str:
    """Prefer explicit AADR date labels before falling back to a BP interval label."""
    for value in (left.time_label, right.time_label, left.full_date, right.full_date):
        if clean_text(value):
            return clean_text(value)
    if merged_interval is None:
        return ""
    return build_bp_interval_label(merged_interval[0], merged_interval[1])
