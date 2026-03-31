from __future__ import annotations

import csv
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

from .aadr_schema import resolve_schema, sample_time_interval, sample_time_label, sample_time_mean
from .models import SampleRecord
from .utils import clean_text, pick_value
from ..core.bp_time import build_bp_interval_label, midpoint_bp_year


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
            combined[sample.genetic_id] = merge_duplicate_samples(existing, sample)

    samples = sorted(
        combined.values(),
        key=lambda sample: (sample.locality.casefold(), sample.master_id.casefold(), sample.genetic_id.casefold()),
    )
    return samples, dataset_counts


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


def merge_duplicate_samples(existing: SampleRecord, sample: SampleRecord) -> SampleRecord:
    """Merge duplicate AADR sample rows across datasets."""
    merged_datasets = tuple(sorted(set(existing.datasets) | set(sample.datasets)))
    merged_interval = merge_sample_time_interval(existing, sample)
    return SampleRecord(
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


def merge_sample_time_interval(left: SampleRecord, right: SampleRecord) -> tuple[int, int] | None:
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
    return (min(start for start, _ in intervals), max(end for _, end in intervals))


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
