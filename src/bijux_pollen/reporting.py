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


@dataclass(frozen=True)
class MultiCountryMapReport:
    title: str
    slug: str
    version: str
    generated_on: str
    countries: tuple[str, ...]
    country_sample_counts: dict[str, int]
    total_unique_samples: int
    output_dir: Path


class SchemaError(ValueError):
    """Raised when an AADR anno file does not contain expected columns."""


def generate_country_report(
    version_dir: Path,
    country: str,
    output_dir: Path,
    map_reference: tuple[str, str] | None = None,
) -> CountryReport:
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
            map_reference=map_reference,
        ),
        encoding="utf-8",
    )
    return report


def generate_multi_country_map(
    version_dir: Path,
    countries: Iterable[str],
    output_dir: Path,
    title: str,
    slug: str,
) -> MultiCountryMapReport:
    """Write a shared interactive map for multiple countries with country toggles."""
    version_dir = Path(version_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    normalized_countries = tuple(dict.fromkeys(country.strip() for country in countries if country.strip()))
    if not normalized_countries:
        raise ValueError("At least one country is required to build a multi-country map")

    country_samples: dict[str, tuple[SampleRecord, ...]] = {}
    country_sample_counts: dict[str, int] = {}
    for country in normalized_countries:
        samples, _ = load_country_samples(version_dir=version_dir, country=country)
        country_samples[country] = tuple(samples)
        country_sample_counts[country] = len(samples)

    all_samples = tuple(
        sample
        for country in normalized_countries
        for sample in country_samples[country]
    )
    version = version_dir.name
    generated_on = str(date.today())

    map_geojson_path = output_dir / f"{slug}_aadr_{version}_samples.geojson"
    map_html_path = output_dir / f"{slug}_aadr_{version}_map.html"
    readme_path = output_dir / "README.md"

    map_geojson = build_samples_geojson(all_samples)
    map_geojson_path.write_text(json.dumps(map_geojson, indent=2), encoding="utf-8")
    map_html_path.write_text(
        render_multi_country_map_html(
            title=title,
            version=version,
            generated_on=generated_on,
            countries=normalized_countries,
            country_samples=country_samples,
            geojson=map_geojson,
        ),
        encoding="utf-8",
    )
    readme_path.write_text(
        render_multi_country_map_markdown(
            title=title,
            version=version,
            generated_on=generated_on,
            countries=normalized_countries,
            country_sample_counts=country_sample_counts,
            map_html_name=map_html_path.name,
            geojson_name=map_geojson_path.name,
        ),
        encoding="utf-8",
    )

    return MultiCountryMapReport(
        title=title,
        slug=slug,
        version=version,
        generated_on=generated_on,
        countries=normalized_countries,
        country_sample_counts=country_sample_counts,
        total_unique_samples=len(all_samples),
        output_dir=output_dir,
    )


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
    path.write_text(json.dumps(build_samples_geojson(samples), indent=2), encoding="utf-8")


def build_samples_geojson(samples: Iterable[SampleRecord]) -> dict[str, object]:
    """Build a GeoJSON feature collection from normalized sample records."""
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
    return {"type": "FeatureCollection", "features": features}


def render_summary_markdown(
    report: CountryReport,
    samples_csv_name: str,
    localities_csv_name: str,
    geojson_name: str,
    sample_markdown_name: str,
    map_reference: tuple[str, str] | None,
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

    map_line = ""
    if map_reference is not None:
        label, href = map_reference
        map_line = f"- Shared interactive map: [`{label}`]({href})\n"

    return f"""# {report.country} AADR {report.version} Report

This report was generated from the AADR `{report.version}` `.anno` files on `{report.generated_on}`.

## Summary

- Country filter: `{report.country}`
- Unique AADR samples: `{report.total_unique_samples}`
- Unique localities: `{report.total_unique_localities}`
- Latitude range: `{min(latitude_values):.6f}` to `{max(latitude_values):.6f}`
- Longitude range: `{min(longitude_values):.6f}` to `{max(longitude_values):.6f}`

## Dataset Coverage

| Dataset | {report.country} rows |
| --- | ---: |
{dataset_lines}

The report deduplicates samples by `genetic_id` across datasets. Dataset row counts can differ by coverage, but the combined inventory for `{report.country}` contains `{report.total_unique_samples}` unique samples in AADR `{report.version}`.

## Output Files

{map_line}- Full sample inventory: [`{samples_csv_name}`](./{samples_csv_name})
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


def render_multi_country_map_markdown(
    title: str,
    version: str,
    generated_on: str,
    countries: tuple[str, ...],
    country_sample_counts: dict[str, int],
    map_html_name: str,
    geojson_name: str,
) -> str:
    """Render a README for a shared multi-country map bundle."""
    rows = "\n".join(
        f"| {country} | {country_sample_counts[country]} |"
        for country in countries
    )
    return f"""# {title} AADR {version} Map

This shared interactive map was generated from the AADR `{version}` `.anno` files on `{generated_on}`.

## Included Countries

| Country | Unique samples |
| --- | ---: |
{rows}

## Output Files

- Interactive map: [`{map_html_name}`](./{map_html_name})
- Combined GeoJSON: [`{geojson_name}`](./{geojson_name})
"""


def render_multi_country_map_html(
    title: str,
    version: str,
    generated_on: str,
    countries: tuple[str, ...],
    country_samples: dict[str, tuple[SampleRecord, ...]],
    geojson: dict[str, object],
) -> str:
    """Render a standalone interactive HTML map with country toggles."""
    geojson_json = json.dumps(geojson, ensure_ascii=False)
    initial_diameter_km = 20
    all_samples = [sample for samples in country_samples.values() for sample in samples]
    latitude_values = [sample.latitude for sample in all_samples]
    longitude_values = [sample.longitude for sample in all_samples]
    bounds = [
        [min(latitude_values), min(longitude_values)],
        [max(latitude_values), max(longitude_values)],
    ]
    bounds_json = json.dumps(bounds)
    country_sample_counts = {country: len(country_samples[country]) for country in countries}
    stats_cards = [
        ("Samples", str(len(all_samples))),
        ("Countries", str(len(countries))),
        ("Version", version),
        ("Generated", generated_on),
    ]
    stats_html = "\n".join(
        f'<div class="stat-card"><span class="stat-label">{label}</span><strong class="stat-value">{value}</strong></div>'
        for label, value in stats_cards
    )
    country_toggle_html = "\n".join(
        (
            '<label class="country-toggle">'
            f'<input class="country-checkbox" type="checkbox" value="{escape_html(country)}" checked>'
            f'<span class="country-swatch country-{index % 4}"></span>'
            f'<span class="country-name">{escape_html(country)}</span>'
            f'<span class="country-count">{country_sample_counts[country]} samples</span>'
            "</label>"
        )
        for index, country in enumerate(countries)
    )
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title} AADR {version} Map</title>
    <link
      rel="stylesheet"
      href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
      crossorigin=""
    >
    <style>
      :root {{
        --bg: #f4f1ea;
        --panel: rgba(255, 252, 245, 0.92);
        --panel-border: rgba(94, 82, 64, 0.16);
        --ink: #1f2937;
        --muted: #5f6c7b;
        --accent: #1d4ed8;
        --accent-soft: rgba(37, 99, 235, 0.16);
        --circle-stroke: rgba(185, 28, 28, 0.55);
        --circle-fill: rgba(239, 68, 68, 0.12);
        --shadow: 0 18px 40px rgba(31, 41, 55, 0.16);
      }}

      html, body {{
        margin: 0;
        height: 100%;
        font-family: "Avenir Next", "Segoe UI", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(29, 78, 216, 0.08), transparent 28%),
          radial-gradient(circle at bottom right, rgba(185, 28, 28, 0.08), transparent 24%),
          var(--bg);
      }}

      body {{
        display: grid;
        grid-template-columns: minmax(320px, 420px) 1fr;
      }}

      aside {{
        position: relative;
        z-index: 900;
        padding: 24px;
        background: linear-gradient(180deg, rgba(250, 248, 242, 0.98), rgba(244, 241, 234, 0.95));
        border-right: 1px solid var(--panel-border);
        box-shadow: var(--shadow);
        overflow-y: auto;
      }}

      main {{
        position: relative;
        min-height: 100vh;
      }}

      #map {{
        width: 100%;
        height: 100vh;
      }}

      .eyebrow {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 10px;
        border-radius: 999px;
        background: var(--accent-soft);
        color: var(--accent);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
      }}

      h1 {{
        margin: 14px 0 10px;
        font-size: clamp(28px, 4vw, 40px);
        line-height: 1.05;
      }}

      .lede {{
        margin: 0 0 20px;
        color: var(--muted);
        font-size: 15px;
        line-height: 1.6;
      }}

      .stats-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
        margin-bottom: 22px;
      }}

      .stat-card {{
        padding: 14px 15px;
        border: 1px solid var(--panel-border);
        border-radius: 18px;
        background: var(--panel);
        backdrop-filter: blur(10px);
      }}

      .stat-label {{
        display: block;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--muted);
        margin-bottom: 8px;
      }}

      .stat-value {{
        font-size: 22px;
        line-height: 1;
      }}

      .control-panel {{
        padding: 18px;
        border-radius: 22px;
        background: var(--panel);
        border: 1px solid var(--panel-border);
        backdrop-filter: blur(14px);
      }}

      .control-panel h2 {{
        margin: 0 0 8px;
        font-size: 18px;
      }}

      .control-panel p {{
        margin: 0 0 16px;
        color: var(--muted);
        font-size: 14px;
        line-height: 1.55;
      }}

      .slider-wrap {{
        margin: 20px 0 10px;
      }}

      .slider-label {{
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: baseline;
        margin-bottom: 8px;
        font-size: 14px;
        font-weight: 700;
      }}

      .slider-value {{
        color: var(--accent);
      }}

      input[type="range"] {{
        width: 100%;
        accent-color: #b91c1c;
      }}

      .legend {{
        display: grid;
        gap: 10px;
        margin-top: 18px;
        font-size: 13px;
      }}

      .legend-item {{
        display: flex;
        align-items: center;
        gap: 10px;
        color: var(--muted);
      }}

      .country-toggles {{
        display: grid;
        gap: 10px;
        margin: 18px 0 0;
      }}

      .country-toggle {{
        display: grid;
        grid-template-columns: auto auto 1fr auto;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        border: 1px solid var(--panel-border);
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.72);
      }}

      .country-checkbox {{
        margin: 0;
      }}

      .country-swatch {{
        width: 12px;
        height: 12px;
        border-radius: 999px;
      }}

      .country-0 {{ background: #2563eb; }}
      .country-1 {{ background: #0f766e; }}
      .country-2 {{ background: #ca8a04; }}
      .country-3 {{ background: #9333ea; }}

      .country-name {{
        font-size: 14px;
        font-weight: 700;
      }}

      .country-count {{
        font-size: 12px;
        color: var(--muted);
      }}

      .toggle-actions {{
        display: flex;
        gap: 10px;
        margin-top: 12px;
      }}

      .toggle-actions button {{
        appearance: none;
        border: 0;
        border-radius: 999px;
        padding: 10px 14px;
        background: #e5e7eb;
        color: var(--ink);
        font-weight: 700;
        cursor: pointer;
      }}

      .toggle-actions button.primary {{
        background: #1d4ed8;
        color: white;
      }}

      .legend-dot,
      .legend-circle {{
        flex: 0 0 auto;
      }}

      .legend-dot {{
        width: 12px;
        height: 12px;
        border-radius: 999px;
        background: #2563eb;
        border: 1px solid #0f172a;
      }}

      .legend-circle {{
        width: 16px;
        height: 16px;
        border-radius: 999px;
        border: 2px solid rgba(185, 28, 28, 0.6);
        background: rgba(239, 68, 68, 0.16);
      }}

      .footnote {{
        margin-top: 20px;
        color: var(--muted);
        font-size: 12px;
        line-height: 1.6;
      }}

      .leaflet-popup-content-wrapper {{
        border-radius: 18px;
      }}

      .popup-grid {{
        display: grid;
        gap: 6px;
        font-size: 13px;
      }}

      .popup-grid strong {{
        display: inline-block;
        min-width: 92px;
      }}

      @media (max-width: 960px) {{
        body {{
          grid-template-columns: 1fr;
          grid-template-rows: auto 1fr;
        }}

        aside {{
          border-right: 0;
          border-bottom: 1px solid var(--panel-border);
        }}

        #map {{
          height: 70vh;
          min-height: 540px;
        }}
      }}
    </style>
  </head>
  <body>
    <aside>
      <span class="eyebrow">Interactive AADR Map</span>
      <h1>{title}</h1>
      <p class="lede">
        Explore one shared AADR map across the selected countries, toggle countries on and off,
        zoom across the region, and adjust the acceptance diameter around each sample point.
      </p>

      <section class="stats-grid">
        {stats_html}
      </section>

      <section class="control-panel">
        <h2>Country Selection</h2>
        <p>
          Use the country controls to show or hide sample layers without leaving the map.
        </p>
        <div class="country-toggles">
          {country_toggle_html}
        </div>
        <div class="toggle-actions">
          <button id="select-all" class="primary" type="button">Show all</button>
          <button id="clear-all" type="button">Hide all</button>
        </div>
      </section>

      <section class="control-panel" style="margin-top: 16px;">
        <h2>Acceptance Range</h2>
        <p>
          Use the slider to set the circle diameter around every sample point.
          The displayed radius is half of the selected diameter.
        </p>
        <div class="slider-wrap">
          <div class="slider-label">
            <span>Diameter</span>
            <span class="slider-value" id="diameter-value">{initial_diameter_km} km</span>
          </div>
          <input id="diameter-slider" type="range" min="0" max="100" step="5" value="{initial_diameter_km}">
        </div>
        <div class="slider-label">
          <span>Radius</span>
          <span class="slider-value" id="radius-value">{initial_diameter_km / 2:.1f} km</span>
        </div>

        <div class="legend">
          <div class="legend-item">
            <span class="legend-dot"></span>
            <span>Blue points show all available AADR samples.</span>
          </div>
          <div class="legend-item">
            <span class="legend-circle"></span>
            <span>Transparent red circles show the current acceptance range.</span>
          </div>
        </div>

        <p class="footnote">
          Tip: set the diameter to 0 km to hide the circles and inspect only the sample points.
          Popups show sample metadata, coordinates, publication, and datasets.
        </p>
      </section>
    </aside>

    <main>
      <div id="map" aria-label="{title} AADR sample map"></div>
    </main>

    <script
      src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
      integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
      crossorigin=""
    ></script>
    <script>
      const sampleData = {geojson_json};
      const initialBounds = {bounds_json};
      const countries = {json.dumps(list(countries), ensure_ascii=False)};
      const map = L.map('map', {{ preferCanvas: true, zoomControl: true }});

      const positron = L.tileLayer(
        'https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png',
        {{
          attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
          subdomains: 'abcd',
          maxZoom: 20
        }}
      );
      const voyager = L.tileLayer(
        'https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png',
        {{
          attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
          subdomains: 'abcd',
          maxZoom: 20
        }}
      );

      positron.addTo(map);
      L.control.layers({{ 'Light': positron, 'Voyager': voyager }}, {{}}, {{ position: 'topright' }}).addTo(map);
      L.control.scale({{ imperial: false }}).addTo(map);

      const pointsLayer = L.layerGroup().addTo(map);
      const circlesLayer = L.layerGroup().addTo(map);
      const features = sampleData.features;
      const slider = document.getElementById('diameter-slider');
      const diameterValue = document.getElementById('diameter-value');
      const radiusValue = document.getElementById('radius-value');
      const countryCheckboxes = Array.from(document.querySelectorAll('.country-checkbox'));
      const selectAllButton = document.getElementById('select-all');
      const clearAllButton = document.getElementById('clear-all');
      const countryStyles = {{
        'Sweden': {{ fill: '#2563eb', stroke: '#0f172a' }},
        'Norway': {{ fill: '#0f766e', stroke: '#134e4a' }},
        'Finland': {{ fill: '#ca8a04', stroke: '#854d0e' }}
      }};

      function popupHtml(properties, latitude, longitude) {{
        const datasets = Array.isArray(properties.datasets) ? properties.datasets.join(', ') : '';
        return `
          <div class="popup-grid">
            <div><strong>Genetic ID</strong> ${{
              escapeHtml(properties.genetic_id || '')
            }}</div>
            <div><strong>Locality</strong> ${{
              escapeHtml(properties.locality || '')
            }}</div>
            <div><strong>Country</strong> ${{
              escapeHtml(properties.political_entity || '')
            }}</div>
            <div><strong>Master ID</strong> ${{
              escapeHtml(properties.master_id || '')
            }}</div>
            <div><strong>Group ID</strong> ${{
              escapeHtml(properties.group_id || '')
            }}</div>
            <div><strong>Datasets</strong> ${{
              escapeHtml(datasets)
            }}</div>
            <div><strong>Publication</strong> ${{
              escapeHtml(properties.publication || '')
            }}</div>
            <div><strong>Date</strong> ${{
              escapeHtml(properties.full_date || '')
            }}</div>
            <div><strong>Coords</strong> ${{
              latitude.toFixed(6)
            }}, ${{
              longitude.toFixed(6)
            }}</div>
          </div>
        `;
      }}

      function escapeHtml(value) {{
        return String(value)
          .replaceAll('&', '&amp;')
          .replaceAll('<', '&lt;')
          .replaceAll('>', '&gt;')
          .replaceAll('"', '&quot;')
          .replaceAll("'", '&#39;');
      }}

      function selectedCountries() {{
        return new Set(countryCheckboxes.filter((checkbox) => checkbox.checked).map((checkbox) => checkbox.value));
      }}

      function styleForCountry(country) {{
        return countryStyles[country] || {{ fill: '#2563eb', stroke: '#0f172a' }};
      }}

      function renderPoints(activeCountries) {{
        pointsLayer.clearLayers();
        features.forEach((feature) => {{
          const country = feature.properties.political_entity;
          if (!activeCountries.has(country)) {{
            return;
          }}
          const [longitude, latitude] = feature.geometry.coordinates;
          const style = styleForCountry(country);
          const marker = L.circleMarker([latitude, longitude], {{
            radius: 4.5,
            color: style.stroke,
            weight: 1,
            fillColor: style.fill,
            fillOpacity: 0.9
          }});
          marker.bindPopup(popupHtml(feature.properties, latitude, longitude), {{
            maxWidth: 340,
            className: 'sample-popup'
          }});
          pointsLayer.addLayer(marker);
        }});
      }}

      function renderCircles(diameterKm, activeCountries) {{
        circlesLayer.clearLayers();
        if (diameterKm <= 0) {{
          return;
        }}
        const radiusMeters = (diameterKm * 1000) / 2;
        features.forEach((feature) => {{
          const country = feature.properties.political_entity;
          if (!activeCountries.has(country)) {{
            return;
          }}
          const [longitude, latitude] = feature.geometry.coordinates;
          const style = styleForCountry(country);
          const circle = L.circle([latitude, longitude], {{
            radius: radiusMeters,
            color: style.stroke,
            weight: 1,
            opacity: 0.45,
            fillColor: style.fill,
            fillOpacity: 0.12,
            interactive: false
          }});
          circlesLayer.addLayer(circle);
        }});
      }}

      function renderMapState() {{
        const activeCountries = selectedCountries();
        const diameterKm = Number(slider.value);
        const radiusKm = diameterKm / 2;
        diameterValue.textContent = `${{diameterKm}} km`;
        radiusValue.textContent = `${{radiusKm.toFixed(1)}} km`;
        renderPoints(activeCountries);
        renderCircles(diameterKm, activeCountries);
      }}

      slider.addEventListener('input', renderMapState);
      countryCheckboxes.forEach((checkbox) => checkbox.addEventListener('change', renderMapState));
      selectAllButton.addEventListener('click', () => {{
        countryCheckboxes.forEach((checkbox) => {{
          checkbox.checked = true;
        }});
        renderMapState();
      }});
      clearAllButton.addEventListener('click', () => {{
        countryCheckboxes.forEach((checkbox) => {{
          checkbox.checked = false;
        }});
        renderMapState();
      }});
      renderMapState();

      const southWest = initialBounds[0];
      const northEast = initialBounds[1];
      const singlePointBounds = southWest[0] === northEast[0] && southWest[1] === northEast[1];

      if (singlePointBounds) {{
        map.setView(southWest, 8);
      }} else {{
        map.fitBounds(initialBounds, {{ padding: [24, 24] }});
      }}
    </script>
  </body>
</html>
"""


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


def escape_html(value: str) -> str:
    """Escape HTML text used in generated markup."""
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
