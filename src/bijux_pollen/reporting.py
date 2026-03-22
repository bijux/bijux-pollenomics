from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class SampleRecord:
    genetic_id: str
    master_id: str
    group_id: str
    locality: str
    political_entity: str
    latitude: float
    longitude: float
    latitude_text: str
    longitude_text: str
    publication: str
    year_first_published: str
    full_date: str
    date_mean_bp: str
    data_type: str
    molecular_sex: str
    datasets: tuple[str, ...]


@dataclass(frozen=True)
class LocalitySummary:
    locality: str
    latitude: float
    longitude: float
    latitude_text: str
    longitude_text: str
    sample_count: int
    sample_ids: tuple[str, ...]
    datasets: tuple[str, ...]


@dataclass(frozen=True)
class CountryReport:
    country: str
    version: str
    generated_on: str
    total_unique_samples: int
    total_unique_localities: int
    dataset_row_counts: dict[str, int]
    samples: tuple[SampleRecord, ...]
    localities: tuple[LocalitySummary, ...]
    output_dir: Path


class SchemaError(ValueError):
    """Raised when an AADR anno file does not contain expected columns."""


def generate_country_report(version_dir: Path, country: str, output_dir: Path) -> CountryReport:
    """Read all AADR anno files for a version, filter by country, and write report artifacts."""
    version_dir = Path(version_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    samples, dataset_counts = load_country_samples(version_dir=version_dir, country=country)
    localities = summarize_localities(samples)
    version = version_dir.name
    report = CountryReport(
        country=country,
        version=version,
        generated_on=str(date.today()),
        total_unique_samples=len(samples),
        total_unique_localities=len(localities),
        dataset_row_counts=dict(sorted(dataset_counts.items())),
        samples=tuple(samples),
        localities=tuple(localities),
        output_dir=output_dir,
    )

    slug = slugify(country)
    csv_path = output_dir / f"{slug}_aadr_{version}_samples.csv"
    locality_csv_path = output_dir / f"{slug}_aadr_{version}_localities.csv"
    geojson_path = output_dir / f"{slug}_aadr_{version}_samples.geojson"
    sample_markdown_path = output_dir / f"{slug}_aadr_{version}_samples.md"
    readme_path = output_dir / "README.md"

    write_samples_csv(csv_path, report.samples)
    write_localities_csv(locality_csv_path, report.localities)
    write_samples_geojson(geojson_path, report.samples)
    sample_markdown_path.write_text(render_sample_markdown(report), encoding="utf-8")
    readme_path.write_text(
        render_summary_markdown(
            report=report,
            samples_csv_name=csv_path.name,
            localities_csv_name=locality_csv_path.name,
            geojson_name=geojson_path.name,
            sample_markdown_name=sample_markdown_path.name,
        ),
        encoding="utf-8",
    )
    return report


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
                locality=clean_text(row.get(schema["locality"], "")),
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


def write_samples_csv(path: Path, samples: Iterable[SampleRecord]) -> None:
    """Write the full sample inventory as CSV."""
    fieldnames = [
        "genetic_id",
        "master_id",
        "group_id",
        "locality",
        "political_entity",
        "latitude",
        "longitude",
        "publication",
        "year_first_published",
        "full_date",
        "date_mean_bp",
        "data_type",
        "molecular_sex",
        "datasets",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for sample in samples:
            writer.writerow(
                {
                    "genetic_id": sample.genetic_id,
                    "master_id": sample.master_id,
                    "group_id": sample.group_id,
                    "locality": sample.locality,
                    "political_entity": sample.political_entity,
                    "latitude": sample.latitude_text,
                    "longitude": sample.longitude_text,
                    "publication": sample.publication,
                    "year_first_published": sample.year_first_published,
                    "full_date": sample.full_date,
                    "date_mean_bp": sample.date_mean_bp,
                    "data_type": sample.data_type,
                    "molecular_sex": sample.molecular_sex,
                    "datasets": ",".join(sample.datasets),
                }
            )


def write_localities_csv(path: Path, localities: Iterable[LocalitySummary]) -> None:
    """Write the locality-level aggregation as CSV."""
    fieldnames = [
        "locality",
        "latitude",
        "longitude",
        "sample_count",
        "datasets",
        "sample_ids",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for locality in localities:
            writer.writerow(
                {
                    "locality": locality.locality,
                    "latitude": locality.latitude_text,
                    "longitude": locality.longitude_text,
                    "sample_count": locality.sample_count,
                    "datasets": ",".join(locality.datasets),
                    "sample_ids": ";".join(locality.sample_ids),
                }
            )


def write_samples_geojson(path: Path, samples: Iterable[SampleRecord]) -> None:
    """Write map-ready sample points as GeoJSON."""
    features = []
    for sample in samples:
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [sample.longitude, sample.latitude],
                },
                "properties": {
                    "genetic_id": sample.genetic_id,
                    "master_id": sample.master_id,
                    "group_id": sample.group_id,
                    "locality": sample.locality,
                    "political_entity": sample.political_entity,
                    "publication": sample.publication,
                    "year_first_published": sample.year_first_published,
                    "full_date": sample.full_date,
                    "date_mean_bp": sample.date_mean_bp,
                    "data_type": sample.data_type,
                    "molecular_sex": sample.molecular_sex,
                    "datasets": list(sample.datasets),
                },
            }
        )
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}, indent=2), encoding="utf-8")


def render_summary_markdown(
    report: CountryReport,
    samples_csv_name: str,
    localities_csv_name: str,
    geojson_name: str,
    sample_markdown_name: str,
) -> str:
    """Render the country summary README."""
    latitude_values = [sample.latitude for sample in report.samples]
    longitude_values = [sample.longitude for sample in report.samples]

    dataset_lines = "\n".join(
        f"| `{dataset}` | {count} |"
        for dataset, count in sorted(report.dataset_row_counts.items())
    )
    top_locality_lines = "\n".join(
        f"| {escape_pipes(locality.locality)} | {locality.sample_count} | {locality.latitude_text} | {locality.longitude_text} | `{','.join(locality.datasets)}` |"
        for locality in report.localities[:15]
    )

    return f"""# {report.country} AADR {report.version} Report

This report was generated from the AADR `{report.version}` `.anno` files on `{report.generated_on}`.

## Summary

- Country filter: `{report.country}`
- Unique AADR samples: `{report.total_unique_samples}`
- Unique localities: `{report.total_unique_localities}`
- Latitude range: `{min(latitude_values):.6f}` to `{max(latitude_values):.6f}`
- Longitude range: `{min(longitude_values):.6f}` to `{max(longitude_values):.6f}`

## Dataset Coverage

| Dataset | Sweden rows |
| --- | ---: |
{dataset_lines}

The report deduplicates samples by `genetic_id` across datasets. In AADR `{report.version}`, the Sweden rows in `1240k` and `ho` resolve to the same `{report.total_unique_samples}` unique samples.

## Output Files

- Full sample inventory: [`{samples_csv_name}`](./{samples_csv_name})
- Locality summary: [`{localities_csv_name}`](./{localities_csv_name})
- Map-ready GeoJSON: [`{geojson_name}`](./{geojson_name})
- Full markdown sample table: [`{sample_markdown_name}`](./{sample_markdown_name})

## Top Localities

| Locality | Samples | Latitude | Longitude | Datasets |
| --- | ---: | ---: | ---: | --- |
{top_locality_lines}
"""


def render_sample_markdown(report: CountryReport) -> str:
    """Render the complete sample-level markdown table."""
    lines = [
        f"# {report.country} AADR {report.version} Sample Inventory",
        "",
        f"Generated on `{report.generated_on}`. Total samples: `{report.total_unique_samples}`.",
        "",
        "| Genetic ID | Master ID | Group ID | Locality | Latitude | Longitude | Publication | Full Date | Data Type | Sex | Datasets |",
        "| --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- | --- |",
    ]
    for sample in report.samples:
        lines.append(
            "| "
            + " | ".join(
                [
                    escape_pipes(sample.genetic_id),
                    escape_pipes(sample.master_id),
                    escape_pipes(sample.group_id),
                    escape_pipes(sample.locality),
                    sample.latitude_text,
                    sample.longitude_text,
                    escape_pipes(sample.publication),
                    escape_pipes(sample.full_date),
                    escape_pipes(sample.data_type),
                    escape_pipes(sample.molecular_sex),
                    ",".join(sample.datasets),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def pick_value(left: str, right: str) -> str:
    """Keep the first non-empty value when merging duplicate sample rows."""
    return left if left else right


def clean_text(value: str) -> str:
    """Normalize placeholder values from AADR."""
    value = value.strip()
    return "" if value in {"", ".", ".."} else value


def slugify(value: str) -> str:
    """Convert a human label into a stable directory/file slug."""
    slug = "".join(character.lower() if character.isalnum() else "-" for character in value)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def escape_pipes(value: str) -> str:
    """Escape markdown pipe characters in table cells."""
    return value.replace("|", "\\|")
