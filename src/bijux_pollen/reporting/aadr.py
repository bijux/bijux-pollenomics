from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from .models import LocalitySummary, SampleRecord, SchemaError
from .utils import clean_text, pick_value


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
                data_type=pick_value(existing.data_type, sample.data_type),
                molecular_sex=pick_value(existing.molecular_sex, sample.molecular_sex),
                datasets=merged_datasets,
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
            latitude_text = clean_text(row.get(schema["latitude"], ""))
            longitude_text = clean_text(row.get(schema["longitude"], ""))
            if not latitude_text or not longitude_text:
                continue
            yield SampleRecord(
                genetic_id=clean_text(row.get(schema["genetic_id"], "")),
                master_id=clean_text(row.get(schema["master_id"], "")),
                group_id=clean_text(row.get(schema["group_id"], "")),
                locality=clean_text(row.get(schema["locality"], "")) or "Unspecified locality",
                political_entity=clean_text(row.get(schema["political_entity"], "")),
                latitude=float(latitude_text),
                longitude=float(longitude_text),
                latitude_text=latitude_text,
                longitude_text=longitude_text,
                publication=clean_text(row.get(schema["publication"], "")),
                year_first_published=clean_text(row.get(schema["year_first_published"], "")),
                full_date=clean_text(row.get(schema["full_date"], "")),
                date_mean_bp=clean_text(row.get(schema["date_mean_bp"], "")),
                data_type=clean_text(row.get(schema["data_type"], "")),
                molecular_sex=clean_text(row.get(schema["molecular_sex"], "")),
                datasets=(dataset_name,),
            )


def resolve_schema(fieldnames: list[str]) -> dict[str, str]:
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
