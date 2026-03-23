from __future__ import annotations

import csv
import json
import shutil
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
    context_root: Path | None = None,
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

    point_layers, polygon_layers, extra_artifacts = build_context_layers(
        samples=all_samples,
        output_dir=output_dir,
        context_root=context_root,
    )
    map_html_path.write_text(
        render_multi_country_map_html(
            title=title,
            version=version,
            generated_on=generated_on,
            countries=normalized_countries,
            point_layers=point_layers,
            polygon_layers=polygon_layers,
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
            extra_artifacts=extra_artifacts,
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


def build_context_layers(
    samples: Iterable[SampleRecord],
    output_dir: Path,
    context_root: Path | None,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[tuple[str, str]]]:
    """Build embedded point layers and service-backed overlays for the shared map."""
    point_layers = [build_aadr_point_layer(samples)]
    polygon_layers: list[dict[str, object]] = []
    extra_artifacts: list[tuple[str, str]] = []

    if context_root is None:
        return point_layers, polygon_layers, extra_artifacts

    context_root = Path(context_root)
    point_sources = [
        ("Neotoma pollen GeoJSON", context_root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson"),
        ("SEAD site GeoJSON", context_root / "sead" / "normalized" / "nordic_environmental_sites.geojson"),
    ]
    for label, source_path in point_sources:
        if not source_path.exists():
            continue
        destination_path = output_dir / source_path.name
        shutil.copyfile(source_path, destination_path)
        geojson = json.loads(destination_path.read_text(encoding="utf-8"))
        point_layers.append(build_external_point_layer(geojson))
        extra_artifacts.append((label, destination_path.name))

    boundary_path = context_root / "boundaries" / "normalized" / "nordic_country_boundaries.geojson"
    if boundary_path.exists():
        destination_path = output_dir / boundary_path.name
        shutil.copyfile(boundary_path, destination_path)
        geojson = json.loads(destination_path.read_text(encoding="utf-8"))
        polygon_layers.append(build_country_boundary_layer(geojson))
        extra_artifacts.append(("Nordic country boundaries", destination_path.name))

    archaeology_path = context_root / "raa" / "normalized" / "sweden_archaeology_layer.json"
    archaeology_density_path = context_root / "raa" / "normalized" / "sweden_archaeology_density.geojson"
    if archaeology_path.exists():
        destination_path = output_dir / archaeology_path.name
        shutil.copyfile(archaeology_path, destination_path)
        extra_artifacts.append(("RAÄ archaeology layer metadata", destination_path.name))
    if archaeology_density_path.exists():
        destination_path = output_dir / archaeology_density_path.name
        shutil.copyfile(archaeology_density_path, destination_path)
        geojson = json.loads(destination_path.read_text(encoding="utf-8"))
        polygon_layers.append(build_density_polygon_layer(geojson))
        extra_artifacts.append(("RAÄ archaeology density", destination_path.name))

    return point_layers, polygon_layers, extra_artifacts


def build_aadr_point_layer(samples: Iterable[SampleRecord]) -> dict[str, object]:
    """Build the AADR point layer payload used by the shared map."""
    features = []
    for sample in samples:
        features.append(
            {
                "latitude": sample.latitude,
                "longitude": sample.longitude,
                "country": sample.political_entity,
                "title": sample.genetic_id,
                "subtitle": sample.locality,
                "popup_rows": [
                    {"label": "Genetic ID", "value": sample.genetic_id},
                    {"label": "Locality", "value": sample.locality},
                    {"label": "Country", "value": sample.political_entity},
                    {"label": "Master ID", "value": sample.master_id},
                    {"label": "Group ID", "value": sample.group_id},
                    {"label": "Datasets", "value": ", ".join(sample.datasets)},
                    {"label": "Publication", "value": sample.publication},
                    {"label": "Date", "value": sample.full_date},
                ],
            }
        )
    return {
        "key": "aadr",
        "label": "AADR aDNA samples",
        "count": len(features),
        "description": "Ancient DNA sample locations from AADR.",
        "group": "primary-evidence",
        "source_name": "Allen Ancient DNA Resource",
        "coverage_label": "Country assignment follows the AADR political entity field.",
        "geometry_label": "Point records",
        "default_enabled": True,
        "applies_country_filter": True,
        "circle_enabled": True,
        "style": {
            "fill": "#2563eb",
            "stroke": "#0f172a",
            "circleStroke": "rgba(37, 99, 235, 0.42)",
            "circleFill": "rgba(37, 99, 235, 0.10)",
        },
        "features": features,
    }


def build_external_point_layer(geojson: dict[str, object]) -> dict[str, object]:
    """Convert normalized GeoJSON into a map layer payload."""
    features = []
    raw_features = geojson.get("features", [])
    if not isinstance(raw_features, list) or not raw_features:
        raise ValueError("External GeoJSON did not contain any features")

    sample_properties = raw_features[0].get("properties", {})
    if not isinstance(sample_properties, dict):
        raise ValueError("External GeoJSON properties must be an object")

    layer_key = str(sample_properties.get("layer_key", "")).strip()
    layer_label = str(sample_properties.get("layer_label", "")).strip()
    styles = {
        "neotoma-pollen": {
            "fill": "#b45309",
            "stroke": "#78350f",
            "circleStroke": "rgba(180, 83, 9, 0.42)",
            "circleFill": "rgba(251, 191, 36, 0.10)",
        },
        "sead-sites": {
            "fill": "#0f766e",
            "stroke": "#134e4a",
            "circleStroke": "rgba(15, 118, 110, 0.42)",
            "circleFill": "rgba(20, 184, 166, 0.10)",
        },
    }
    metadata = {
        "neotoma-pollen": {
            "group": "environmental-context",
            "source_name": "Neotoma",
            "coverage_label": "Nordic pollen and paleoecology sites with coordinates.",
            "geometry_label": "Point records",
        },
        "sead-sites": {
            "group": "environmental-context",
            "source_name": "SEAD",
            "coverage_label": "Nordic environmental archaeology sites with coordinates.",
            "geometry_label": "Point records",
        },
    }
    for feature in raw_features:
        geometry = feature.get("geometry", {})
        properties = feature.get("properties", {})
        if not isinstance(geometry, dict) or not isinstance(properties, dict):
            continue
        coordinates = geometry.get("coordinates", [])
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            continue
        popup_rows = properties.get("popup_rows", [])
        if not isinstance(popup_rows, list):
            popup_rows = []
        features.append(
            {
                "latitude": float(coordinates[1]),
                "longitude": float(coordinates[0]),
                "country": str(properties.get("country", "")).strip(),
                "title": str(properties.get("name", "")).strip(),
                "subtitle": str(properties.get("category", "")).strip(),
                "popup_rows": popup_rows,
                "source_url": str(properties.get("source_url", "")).strip(),
            }
        )

    applies_country_filter = any(feature.get("country") for feature in features)

    return {
        "key": layer_key,
        "label": layer_label,
        "count": len(features),
        "description": str(sample_properties.get("subtitle", "")).strip(),
        "group": metadata.get(layer_key, {}).get("group", "context"),
        "source_name": metadata.get(layer_key, {}).get("source_name", layer_label),
        "coverage_label": metadata.get(layer_key, {}).get("coverage_label", "Country-aware contextual points."),
        "geometry_label": metadata.get(layer_key, {}).get("geometry_label", "Point records"),
        "default_enabled": True,
        "applies_country_filter": applies_country_filter,
        "circle_enabled": True,
        "style": styles.get(
            layer_key,
            {
                "fill": "#475569",
                "stroke": "#1e293b",
                "circleStroke": "rgba(71, 85, 105, 0.42)",
                "circleFill": "rgba(148, 163, 184, 0.10)",
            },
        ),
        "features": features,
    }


def build_country_boundary_layer(geojson: dict[str, object]) -> dict[str, object]:
    """Convert country boundary GeoJSON into a map polygon layer payload."""
    return {
        "key": "country-boundaries",
        "label": "Country boundaries",
        "count": len(geojson.get("features", [])),
        "description": "Administrative outlines used for country filtering and visual framing.",
        "group": "orientation",
        "source_name": "Natural Earth country boundaries",
        "coverage_label": "Nordic country outlines used for framing and map filtering.",
        "geometry_label": "Polygon outlines",
        "default_enabled": True,
        "kind": "country-boundaries",
        "applies_country_filter": True,
        "style": {
            "stroke": "#334155",
            "fill": "rgba(148, 163, 184, 0.06)",
        },
        "geojson": geojson,
    }


def build_density_polygon_layer(geojson: dict[str, object]) -> dict[str, object]:
    """Convert RAÄ archaeology density GeoJSON into a map polygon layer payload."""
    counts = [
        int(feature.get("properties", {}).get("count", 0))
        for feature in geojson.get("features", [])
        if int(feature.get("properties", {}).get("count", 0)) > 0
    ]
    return {
        "key": "raa-archaeology",
        "label": "RAÄ archaeology density",
        "count": len(geojson.get("features", [])),
        "description": "Swedish archaeology density from RAÄ Fornsök `Fornlämning` counts in 1° grid cells.",
        "group": "archaeology-context",
        "source_name": "RAÄ Fornsök",
        "coverage_label": "Sweden only. Density cells summarize `Fornlämning` counts.",
        "geometry_label": "Density polygons",
        "default_enabled": True,
        "kind": "density",
        "applies_country_filter": True,
        "max_count": max(counts) if counts else 0,
        "style": {
            "stroke": "#7f1d1d",
            "fills": ["#fee2e2", "#fca5a5", "#f87171", "#ef4444", "#b91c1c", "#7f1d1d"],
        },
        "geojson": geojson,
    }


def render_multi_country_map_markdown(
    title: str,
    version: str,
    generated_on: str,
    countries: tuple[str, ...],
    country_sample_counts: dict[str, int],
    map_html_name: str,
    geojson_name: str,
    extra_artifacts: list[tuple[str, str]],
) -> str:
    """Render a README for a shared multi-country map bundle."""
    rows = "\n".join(
        f"| {country} | {country_sample_counts[country]} |"
        for country in countries
    )
    artifact_lines = "\n".join(
        f"- {label}: [`{filename}`](./{filename})"
        for label, filename in extra_artifacts
    )
    artifact_block = artifact_lines if artifact_lines else ""
    return f"""# {title} Research Map

This shared interactive map was generated on `{generated_on}` and combines AADR `{version}` with the contextual datasets that are present in the repository at generation time.

## Included Countries

| Country | Unique samples |
| --- | ---: |
{rows}

## Output Files

- Interactive map: [`{map_html_name}`](./{map_html_name})
- Combined GeoJSON: [`{geojson_name}`](./{geojson_name})
{artifact_block}
"""


def render_multi_country_map_html(
    title: str,
    version: str,
    generated_on: str,
    countries: tuple[str, ...],
    point_layers: list[dict[str, object]],
    polygon_layers: list[dict[str, object]],
) -> str:
    """Render an advanced standalone interactive HTML map."""
    initial_diameter_km = 20
    map_points = [feature for layer in point_layers for feature in layer["features"]]
    latitude_values = [float(feature["latitude"]) for feature in map_points]
    longitude_values = [float(feature["longitude"]) for feature in map_points]
    bounds = [
        [min(latitude_values), min(longitude_values)],
        [max(latitude_values), max(longitude_values)],
    ]
    template = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>__TITLE__ Research Map</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="">
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css">
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css">
    <style>
      :root {
        --ink: #14213d;
        --muted: #5f6b85;
        --surface: rgba(251, 248, 242, 0.92);
        --surface-strong: rgba(255, 252, 247, 0.96);
        --surface-edge: rgba(27, 40, 64, 0.12);
        --blue: #2563eb;
        --teal: #0f766e;
        --gold: #b45309;
        --rose: #b91c1c;
        --shadow-lg: 0 24px 64px rgba(20, 33, 61, 0.18);
        --shadow-md: 0 10px 32px rgba(20, 33, 61, 0.12);
      }
      * { box-sizing: border-box; }
      html, body {
        margin: 0;
        min-height: 100%;
        background:
          radial-gradient(circle at top left, rgba(37, 99, 235, 0.16), transparent 30%),
          radial-gradient(circle at right center, rgba(180, 83, 9, 0.12), transparent 22%),
          linear-gradient(180deg, #f8f4ee 0%, #efe7dc 100%);
        color: var(--ink);
        font-family: "IBM Plex Sans", sans-serif;
      }
      body { min-height: 100vh; }
      .app-shell { position: relative; min-height: 100vh; }
      .sidebar {
        position: absolute;
        top: 16px;
        left: 16px;
        bottom: 16px;
        width: min(420px, calc(100vw - 32px));
        z-index: 1200;
        transition: transform 180ms ease, opacity 180ms ease;
      }
      .sidebar.is-collapsed {
        transform: translateX(calc(-100% - 24px));
        opacity: 0;
        pointer-events: none;
      }
      .sidebar-inner {
        height: 100%;
        overflow-y: auto;
        padding: 24px;
        border: 1px solid var(--surface-edge);
        border-radius: 28px;
        background: linear-gradient(180deg, rgba(255, 252, 247, 0.97), rgba(246, 241, 233, 0.92));
        backdrop-filter: blur(18px);
        box-shadow: var(--shadow-lg);
      }
      .map-stage { position: relative; min-height: 100vh; }
      #map { height: 100vh; width: 100%; }
      .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(37, 99, 235, 0.12);
        color: var(--blue);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      h1 {
        margin: 16px 0 10px;
        font-family: "Space Grotesk", sans-serif;
        font-size: clamp(32px, 4vw, 44px);
        line-height: 1;
      }
      .lede {
        margin: 0 0 22px;
        color: var(--muted);
        font-size: 15px;
        line-height: 1.7;
      }
      .stats-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
        margin-bottom: 18px;
      }
      .stat-card,
      .panel-card,
      .floating-legend,
      .map-topbar,
      .map-status {
        border: 1px solid var(--surface-edge);
        background: var(--surface);
        backdrop-filter: blur(16px);
        box-shadow: var(--shadow-md);
      }
      .stat-card { padding: 16px; border-radius: 18px; }
      .stat-label {
        display: block;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 11px;
        font-weight: 700;
        margin-bottom: 8px;
      }
      .stat-value { font-size: 24px; font-weight: 700; }
      .stat-value--compact { font-size: 18px; }
      .section-stack { display: grid; gap: 16px; }
      .panel-card { border-radius: 20px; padding: 18px; }
      .section-head {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: baseline;
        margin-bottom: 10px;
      }
      .section-head h2 { margin: 0; font-size: 17px; }
      .section-head span { color: var(--muted); font-size: 12px; }
      .panel-copy {
        margin: 0 0 14px;
        color: var(--muted);
        font-size: 13px;
        line-height: 1.6;
      }
      .chip-grid { display: flex; flex-wrap: wrap; gap: 10px; }
      .chip-toggle,
      .toolbar-button,
      .preset-button,
      .inline-button,
      .basemap-button {
        appearance: none;
        border: 1px solid rgba(20, 33, 61, 0.12);
        background: rgba(255, 255, 255, 0.88);
        color: var(--ink);
        border-radius: 999px;
        font: inherit;
        cursor: pointer;
        transition: transform 120ms ease, background 120ms ease, border-color 120ms ease, box-shadow 120ms ease;
      }
      .chip-toggle:hover,
      .toolbar-button:hover,
      .preset-button:hover,
      .inline-button:hover,
      .basemap-button:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 24px rgba(20, 33, 61, 0.10);
      }
      .chip-toggle {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 10px 14px;
      }
      .chip-toggle input { margin: 0; }
      .chip-count {
        padding: 3px 8px;
        border-radius: 999px;
        background: rgba(20, 33, 61, 0.08);
        color: var(--muted);
        font-size: 11px;
        font-weight: 700;
      }
      .chip-swatch,
      .legend-swatch {
        width: 12px;
        height: 12px;
        border-radius: 999px;
        display: inline-block;
        border: 1px solid rgba(20, 33, 61, 0.35);
      }
      .inline-actions,
      .preset-row,
      .topbar-row,
      .basemap-switch,
      .map-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }
      .inline-actions { margin-top: 12px; }
      .inline-button,
      .preset-button,
      .toolbar-button,
      .basemap-button {
        padding: 10px 14px;
        font-size: 13px;
        font-weight: 600;
      }
      .inline-button.is-primary,
      .toolbar-button.is-primary,
      .preset-button.is-active,
      .basemap-button.is-active {
        background: linear-gradient(135deg, #1d4ed8, #2563eb);
        color: white;
        border-color: transparent;
      }
      .field-label {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 8px;
      }
      .range-input,
      .search-input { width: 100%; }
      .range-input { accent-color: var(--gold); }
      .search-input {
        padding: 12px 14px;
        border-radius: 14px;
        border: 1px solid rgba(20, 33, 61, 0.14);
        background: rgba(255, 255, 255, 0.95);
        color: var(--ink);
        font: inherit;
      }
      .search-input:focus {
        outline: 2px solid rgba(37, 99, 235, 0.25);
        border-color: rgba(37, 99, 235, 0.40);
      }
      .search-meta {
        margin: 10px 0 12px;
        color: var(--muted);
        font-size: 12px;
      }
      .search-results,
      .summary-list,
      .legend-list,
      .layer-stack {
        display: grid;
        gap: 10px;
      }
      .search-result,
      .summary-item,
      .layer-card {
        padding: 12px 14px;
        border: 1px solid rgba(20, 33, 61, 0.10);
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.76);
      }
      .search-result {
        cursor: pointer;
        width: 100%;
        text-align: left;
        appearance: none;
        font: inherit;
        color: inherit;
      }
      .search-result strong,
      .layer-card strong { display: block; font-size: 14px; }
      .search-result span,
      .layer-card span,
      .summary-item span {
        display: block;
        color: var(--muted);
        font-size: 12px;
        line-height: 1.55;
      }
      .layer-card-top {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: flex-start;
      }
      .layer-card label {
        display: flex;
        gap: 10px;
        align-items: flex-start;
        width: 100%;
      }
      .layer-card input { margin-top: 3px; }
      .layer-group {
        display: grid;
        gap: 10px;
      }
      .layer-group-head {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        align-items: baseline;
        padding: 0 2px;
      }
      .layer-group-head h3 {
        margin: 0;
        font-size: 13px;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }
      .layer-group-head span {
        color: var(--muted);
        font-size: 11px;
      }
      .layer-meta {
        margin-top: 8px;
        display: grid;
        gap: 6px;
      }
      .layer-meta span {
        display: block;
        color: var(--muted);
        font-size: 12px;
        line-height: 1.5;
      }
      .layer-badge {
        padding: 5px 10px;
        border-radius: 999px;
        background: rgba(20, 33, 61, 0.08);
        color: var(--muted);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }
      .map-topbar {
        position: absolute;
        top: 16px;
        left: max(452px, 26vw);
        right: 16px;
        z-index: 1100;
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: center;
        padding: 12px;
        border-radius: 20px;
      }
      .floating-legend {
        position: absolute;
        left: max(452px, 26vw);
        bottom: 24px;
        z-index: 1100;
        width: min(360px, calc(100vw - 48px));
        padding: 16px;
        border-radius: 20px;
      }
      .legend-title { font-size: 13px; font-weight: 700; margin-bottom: 10px; }
      .legend-list { margin-bottom: 14px; }
      .legend-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        color: var(--muted);
        font-size: 12px;
        line-height: 1.5;
      }
      .density-ramp { display: grid; gap: 8px; }
      .density-bar {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        overflow: hidden;
        border-radius: 999px;
        height: 12px;
      }
      .density-bar span:nth-child(1) { background: #fee2e2; }
      .density-bar span:nth-child(2) { background: #fca5a5; }
      .density-bar span:nth-child(3) { background: #f87171; }
      .density-bar span:nth-child(4) { background: #ef4444; }
      .density-bar span:nth-child(5) { background: #b91c1c; }
      .density-bar span:nth-child(6) { background: #7f1d1d; }
      .density-labels {
        display: flex;
        justify-content: space-between;
        color: var(--muted);
        font-size: 11px;
      }
      .map-status {
        position: absolute;
        right: 16px;
        bottom: 24px;
        z-index: 1100;
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        padding: 12px 16px;
        border-radius: 999px;
        color: var(--muted);
        font-size: 12px;
      }
      .empty-state {
        position: absolute;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        z-index: 1150;
        width: min(460px, calc(100vw - 48px));
        padding: 18px 20px;
        border: 1px solid var(--surface-edge);
        border-radius: 22px;
        background: rgba(255, 252, 247, 0.96);
        box-shadow: var(--shadow-lg);
        text-align: center;
      }
      .empty-state strong {
        display: block;
        margin-bottom: 8px;
        font-size: 16px;
      }
      .empty-state span {
        display: block;
        color: var(--muted);
        font-size: 13px;
        line-height: 1.6;
      }
      .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
      }
      button:focus-visible,
      input:focus-visible,
      .search-result:focus-visible {
        outline: 3px solid rgba(37, 99, 235, 0.28);
        outline-offset: 2px;
      }
      .leaflet-popup-content-wrapper { border-radius: 18px; }
      .popup-grid { display: grid; gap: 6px; font-size: 13px; }
      .popup-grid strong { display: inline-block; min-width: 96px; }
      .cluster-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 42px;
        height: 42px;
        border-radius: 999px;
        color: white;
        border: 3px solid rgba(255, 255, 255, 0.88);
        font-weight: 700;
        box-shadow: 0 10px 24px rgba(20, 33, 61, 0.20);
      }
      @media (max-width: 1080px) {
        .sidebar {
          width: min(400px, calc(100vw - 24px));
          top: 12px;
          left: 12px;
          bottom: auto;
          max-height: min(72vh, 920px);
        }
        .map-topbar,
        .floating-legend {
          left: 12px;
          width: auto;
        }
        .map-topbar {
          top: auto;
          bottom: 132px;
          right: 12px;
        }
        .floating-legend { bottom: 76px; }
        .map-status {
          left: 12px;
          right: 12px;
          bottom: 12px;
          border-radius: 18px;
          justify-content: space-between;
        }
      }
      @media (max-width: 760px) {
        .sidebar {
          width: calc(100vw - 20px);
          left: 10px;
          top: 10px;
        }
        .sidebar-inner { padding: 18px; }
        .stats-grid { grid-template-columns: 1fr 1fr; }
        .map-topbar {
          top: auto;
          left: 10px;
          right: 10px;
          bottom: 164px;
          flex-direction: column;
          align-items: stretch;
        }
        .floating-legend {
          left: 10px;
          right: 10px;
          bottom: 98px;
          width: auto;
        }
      }
    </style>
  </head>
  <body>
    <div class="app-shell">
      <aside id="sidebar" class="sidebar">
        <div class="sidebar-inner">
          <span class="eyebrow">Nordic Multi-Evidence Map</span>
          <h1>__TITLE__</h1>
          <p class="lede">
            A shared decision map for ancient DNA, pollen, environmental archaeology, and archaeology context.
            AADR `__VERSION__` is one input to this view, not the whole map. Use the filters, search, and acceptance-distance controls to compare evidence in one workspace.
          </p>
          <section class="stats-grid">
            <div class="stat-card"><span class="stat-label">Visible Points</span><strong class="stat-value" id="stat-visible-points">0</strong></div>
            <div class="stat-card"><span class="stat-label">Visible Overlays</span><strong class="stat-value" id="stat-visible-layers">0</strong></div>
            <div class="stat-card"><span class="stat-label">Active Countries</span><strong class="stat-value" id="stat-visible-countries">0</strong></div>
            <div class="stat-card"><span class="stat-label">Acceptance Radius</span><strong class="stat-value" id="stat-radius">0 km</strong></div>
            <div class="stat-card"><span class="stat-label">AADR Release</span><strong class="stat-value stat-value--compact">__VERSION__</strong></div>
            <div class="stat-card"><span class="stat-label">Context Sources</span><strong class="stat-value stat-value--compact" id="stat-context-sources">0</strong></div>
          </section>
          <div class="section-stack">
            <section class="panel-card">
              <div class="section-head"><h2>Map Scope</h2><span>What is included</span></div>
              <p class="panel-copy">This map combines one primary evidence layer with environmental and archaeological context. Coverage is not identical across sources, so every layer card states its geographic scope.</p>
              <div id="scope-summary" class="summary-list"></div>
            </section>
            <section class="panel-card">
              <div class="section-head"><h2>Country Filters</h2><span id="country-summary" aria-live="polite">All countries visible</span></div>
              <p class="panel-copy">These filters apply to every layer that carries country metadata. RAÄ archaeology density is Sweden-only and will disappear automatically when Sweden is excluded.</p>
              <div id="country-filters" class="chip-grid"></div>
              <div class="inline-actions">
                <button id="countries-all" class="inline-button is-primary" type="button">Show all</button>
                <button id="countries-none" class="inline-button" type="button">Hide all</button>
                <button id="countries-fit" class="inline-button" type="button">Fit selected countries</button>
                <button id="restore-defaults" class="inline-button" type="button">Restore defaults</button>
              </div>
            </section>
            <section class="panel-card">
              <div class="section-head"><h2>Research Layers</h2><span id="layer-summary" aria-live="polite">All layers enabled</span></div>
              <p class="panel-copy">Layers are grouped by role so the map separates primary evidence, environmental context, archaeology context, and orientation aids.</p>
              <div id="layer-filters" class="layer-stack"></div>
            </section>
            <section class="panel-card">
              <div class="section-head"><h2>Search Visible Records</h2><span id="search-count" aria-live="polite">0 matches</span></div>
              <label class="sr-only" for="search-input">Search visible records</label>
              <input id="search-input" class="search-input" type="search" placeholder="Search by sample ID, locality, site name, or source" aria-describedby="search-meta">
              <div id="search-meta" class="search-meta">Search only scans records that are visible under the current country and layer filters. Press Enter to jump to the first visible match.</div>
              <div id="search-results" class="search-results"></div>
            </section>
            <section class="panel-card">
              <div class="section-head"><h2>Acceptance Distance</h2><span id="diameter-value">__INITIAL_DIAMETER__ km diameter</span></div>
              <div class="field-label"><span>Search radius around visible point layers</span><span id="radius-value">__INITIAL_RADIUS__ km</span></div>
              <label class="sr-only" for="diameter-slider">Acceptance diameter in kilometers</label>
              <input id="diameter-slider" class="range-input" type="range" min="0" max="100" step="5" value="__INITIAL_DIAMETER__" aria-describedby="distance-help">
              <div class="preset-row" style="margin-top: 12px;">
                <button class="preset-button" type="button" data-km="0">0 km</button>
                <button class="preset-button" type="button" data-km="10">10 km</button>
                <button class="preset-button is-active" type="button" data-km="20">20 km</button>
                <button class="preset-button" type="button" data-km="30">30 km</button>
                <button class="preset-button" type="button" data-km="50">50 km</button>
              </div>
              <div id="distance-help" class="search-meta">Distance circles are available only for point layers. Set to `0 km` to hide acceptance circles everywhere.</div>
              <div class="field-label" style="margin-top: 16px;"><span>Archaeology density opacity</span><span id="density-opacity-value">60%</span></div>
              <label class="sr-only" for="density-opacity-slider">Archaeology density opacity</label>
              <input id="density-opacity-slider" class="range-input" type="range" min="0" max="100" step="5" value="60">
            </section>
            <section class="panel-card">
              <div class="section-head"><h2>Active View</h2><span>Live provenance</span></div>
              <div id="active-summary" class="summary-list"></div>
            </section>
          </div>
        </div>
      </aside>
      <main class="map-stage">
        <div class="map-topbar">
          <div class="topbar-row">
            <button id="panel-toggle" class="toolbar-button" type="button">Hide panel</button>
            <div class="basemap-switch">
              <button class="basemap-button is-active" type="button" data-basemap="voyager">Voyager</button>
              <button class="basemap-button" type="button" data-basemap="light">Light</button>
              <button class="basemap-button" type="button" data-basemap="terrain">Terrain</button>
            </div>
          </div>
          <div class="map-actions">
            <button id="fit-active" class="toolbar-button is-primary" type="button">Fit active</button>
            <button id="reset-view" class="toolbar-button" type="button">Reset view</button>
            <button id="copy-link" class="toolbar-button" type="button">Copy link</button>
            <button id="fullscreen-toggle" class="toolbar-button" type="button">Fullscreen</button>
          </div>
        </div>
        <div id="map" aria-label="__TITLE__ research map"></div>
        <div id="empty-state" class="empty-state" hidden>
          <strong>No visible records</strong>
          <span>Change the country filters, re-enable one or more layers, or restore the default map state.</span>
        </div>
        <div class="floating-legend">
          <div class="legend-title">Legend</div>
          <div id="legend-items" class="legend-list"></div>
          <div id="density-ramp" class="density-ramp">
            <div class="legend-item"><span class="legend-swatch" style="background: rgba(37, 99, 235, 0.10); border-color: rgba(37, 99, 235, 0.45);"></span><span>Acceptance circles use semi-transparent fills so overlap remains visible.</span></div>
            <div class="legend-item"><span class="legend-swatch" style="background: rgba(239, 68, 68, 0.22); border-color: #7f1d1d;"></span><span>RAÄ archaeology density shows Swedish `Fornlämning` counts in 1° grid cells.</span></div>
            <div class="density-bar"><span></span><span></span><span></span><span></span><span></span><span></span></div>
            <div class="density-labels"><span>Lower density</span><span>Higher density</span></div>
          </div>
        </div>
        <div class="map-status">
          <span id="zoom-readout">Zoom --</span>
          <span id="cursor-readout">Cursor --</span>
          <span id="selection-readout">Visible --</span>
        </div>
      </main>
    </div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
    <script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>
    <script>
      const COUNTRIES = __COUNTRIES_JSON__;
      const POINT_LAYERS = __POINT_LAYERS_JSON__;
      const POLYGON_LAYERS = __POLYGON_LAYERS_JSON__;
      const INITIAL_BOUNDS = __BOUNDS_JSON__;
      const ALL_LAYERS = [...POINT_LAYERS, ...POLYGON_LAYERS];
      const DEFAULT_COUNTRIES = [...COUNTRIES];
      const DEFAULT_LAYER_KEYS = ALL_LAYERS.filter((layer) => layer.default_enabled !== false).map((layer) => layer.key);
      const map = L.map('map', { preferCanvas: true, zoomControl: false });
      const basemaps = {
        voyager: L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', { attribution: '&copy; OpenStreetMap contributors &copy; CARTO', subdomains: 'abcd', maxZoom: 20 }),
        light: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', { attribution: '&copy; OpenStreetMap contributors &copy; CARTO', subdomains: 'abcd', maxZoom: 20 }),
        terrain: L.tileLayer('https://tile.opentopomap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap contributors, SRTM &copy; OpenTopoMap', maxZoom: 17 })
      };
      basemaps.voyager.addTo(map);
      L.control.zoom({ position: 'bottomright' }).addTo(map);
      L.control.scale({ imperial: false }).addTo(map);
      map.createPane('pointPane').style.zIndex = 650;
      map.createPane('circlePane').style.zIndex = 500;
      map.createPane('polygonPane').style.zIndex = 420;
      map.createPane('boundaryPane').style.zIndex = 430;
      const circleLayerGroup = L.layerGroup().addTo(map);
      let renderedPointGroups = [];
      let renderedPolygonLayers = [];
      let visiblePointEntries = [];
      const sidebar = document.getElementById('sidebar');
      const panelToggleButton = document.getElementById('panel-toggle');
      const countryFilters = document.getElementById('country-filters');
      const layerFilters = document.getElementById('layer-filters');
      const legendItems = document.getElementById('legend-items');
      const scopeSummary = document.getElementById('scope-summary');
      const searchInput = document.getElementById('search-input');
      const searchResults = document.getElementById('search-results');
      const searchCount = document.getElementById('search-count');
      const slider = document.getElementById('diameter-slider');
      const diameterValue = document.getElementById('diameter-value');
      const radiusValue = document.getElementById('radius-value');
      const densityOpacitySlider = document.getElementById('density-opacity-slider');
      const densityOpacityValue = document.getElementById('density-opacity-value');
      const emptyState = document.getElementById('empty-state');
      const densityRamp = document.getElementById('density-ramp');
      const countrySummary = document.getElementById('country-summary');
      const layerSummary = document.getElementById('layer-summary');
      const activeSummary = document.getElementById('active-summary');
      const selectionReadout = document.getElementById('selection-readout');
      const zoomReadout = document.getElementById('zoom-readout');
      const cursorReadout = document.getElementById('cursor-readout');
      const statVisiblePoints = document.getElementById('stat-visible-points');
      const statVisibleLayers = document.getElementById('stat-visible-layers');
      const statVisibleCountries = document.getElementById('stat-visible-countries');
      const statRadius = document.getElementById('stat-radius');
      const statContextSources = document.getElementById('stat-context-sources');
      function parseHashState() {
        const raw = window.location.hash.startsWith('#') ? window.location.hash.slice(1) : '';
        const params = new URLSearchParams(raw);
        return {
          countries: params.get('countries'),
          layers: params.get('layers'),
          diameter: params.get('diameter'),
          density: params.get('density'),
          basemap: params.get('basemap'),
          panel: params.get('panel'),
        };
      }
      function normalizedSetFromList(raw, allowed, fallbackValues) {
        if (String(raw || '').trim() === 'none') return new Set();
        const allowedSet = new Set(allowed);
        const values = String(raw || '')
          .split(',')
          .map((value) => value.trim())
          .filter((value) => value && allowedSet.has(value));
        return new Set(values.length ? values : fallbackValues);
      }
      const initialState = parseHashState();
      let activeCountries = normalizedSetFromList(initialState.countries, COUNTRIES, DEFAULT_COUNTRIES);
      let activeLayerKeys = normalizedSetFromList(initialState.layers, ALL_LAYERS.map((layer) => layer.key), DEFAULT_LAYER_KEYS);
      let densityOpacity = Math.max(0, Math.min(1, Number(initialState.density || '60') / 100 || 0.6));
      let currentBasemap = basemaps[initialState.basemap || ''] ? String(initialState.basemap) : 'voyager';
      const countryColors = {
        Sweden: { fill: '#2563eb', stroke: '#1d4ed8' },
        Norway: { fill: '#0f766e', stroke: '#115e59' },
        Finland: { fill: '#b45309', stroke: '#92400e' },
        Denmark: { fill: '#be123c', stroke: '#9f1239' }
      };
      function escapeHtml(value) {
        return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#39;');
      }
      function countryStyle(country) { return countryColors[country] || { fill: '#475569', stroke: '#1e293b' }; }
      function layerColor(layer) { return layer.style && layer.style.fill ? layer.style.fill : (layer.style && layer.style.stroke ? layer.style.stroke : '#475569'); }
      function layerUnit(layer) { if (layer.kind === 'density') return 'cells'; if (layer.kind === 'country-boundaries') return 'countries'; return 'points'; }
      function layerGroupLabel(group) {
        return {
          'primary-evidence': 'Primary Evidence',
          'environmental-context': 'Environmental Context',
          'archaeology-context': 'Archaeology Context',
          'orientation': 'Orientation'
        }[group] || 'Other Layers';
      }
      function layerGroupSummary(group) {
        return {
          'primary-evidence': 'Core evidence used for ancient DNA site comparison.',
          'environmental-context': 'Pollen and environmental archaeology context layers.',
          'archaeology-context': 'Archaeological context layers and summarized national coverage.',
          'orientation': 'Reference layers used for framing and navigation.'
        }[group] || 'Supporting layers.';
      }
      function humanLayerList(keys) {
        return ALL_LAYERS
          .filter((layer) => keys.has(layer.key))
          .map((layer) => layer.label)
          .join(', ');
      }
      function syncPresetButtons() {
        document.querySelectorAll('.preset-button').forEach((button) => {
          button.classList.toggle('is-active', Number(button.dataset.km) === Number(slider.value));
        });
      }
      function syncHashState() {
        const params = new URLSearchParams();
        if (activeCountries.size !== COUNTRIES.length) params.set('countries', activeCountries.size ? [...activeCountries].join(',') : 'none');
        if (activeLayerKeys.size !== DEFAULT_LAYER_KEYS.length || DEFAULT_LAYER_KEYS.some((key) => !activeLayerKeys.has(key))) params.set('layers', activeLayerKeys.size ? [...activeLayerKeys].join(',') : 'none');
        if (Number(slider.value) !== __INITIAL_DIAMETER__) params.set('diameter', String(Number(slider.value)));
        if (Math.round(densityOpacity * 100) !== 60) params.set('density', String(Math.round(densityOpacity * 100)));
        if (currentBasemap !== 'voyager') params.set('basemap', currentBasemap);
        if (sidebar.classList.contains('is-collapsed')) params.set('panel', 'collapsed');
        const nextHash = params.toString();
        const desiredHash = nextHash ? `#${nextHash}` : '';
        if (window.location.hash !== desiredHash) window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}${desiredHash}`);
      }
      function renderScopeSummary() {
        const summaries = [
          `Primary evidence: ${POINT_LAYERS.find((layer) => layer.key === 'aadr')?.label || 'AADR'}`,
          `Environmental context: ${ALL_LAYERS.filter((layer) => layer.group === 'environmental-context').map((layer) => layer.source_name).join(', ') || 'none'}`,
          `Archaeology context: ${ALL_LAYERS.filter((layer) => layer.group === 'archaeology-context').map((layer) => layer.coverage_label).join(' ') || 'none'}`,
          `Orientation: ${ALL_LAYERS.filter((layer) => layer.group === 'orientation').map((layer) => layer.label).join(', ') || 'none'}`
        ];
        scopeSummary.innerHTML = summaries.map((item) => `<div class="summary-item"><span>${escapeHtml(item)}</span></div>`).join('');
      }
      function renderCountryControls() {
        const pointCountsByCountry = Object.fromEntries(
          COUNTRIES.map((country) => [
            country,
            POINT_LAYERS
              .filter((layer) => activeLayerKeys.has(layer.key))
              .reduce((count, layer) => count + layer.features.filter((feature) => feature.country === country).length, 0),
          ])
        );
        countryFilters.innerHTML = COUNTRIES.map((country) => {
          const style = countryStyle(country);
          const checked = activeCountries.has(country) ? 'checked' : '';
          return `<label class="chip-toggle"><input class="country-checkbox" type="checkbox" value="${escapeHtml(country)}" ${checked} aria-label="Toggle ${escapeHtml(country)}"><span class="chip-swatch" style="background:${escapeHtml(style.fill)};border-color:${escapeHtml(style.stroke)};"></span><span>${escapeHtml(country)}</span><span class="chip-count">${escapeHtml(String(pointCountsByCountry[country] || 0))}</span></label>`;
        }).join('');
        document.querySelectorAll('.country-checkbox').forEach((checkbox) => {
          checkbox.addEventListener('change', () => {
            if (checkbox.checked) { activeCountries.add(checkbox.value); } else { activeCountries.delete(checkbox.value); }
            renderMapState();
          });
        });
      }
      function renderLayerControls() {
        const groupOrder = ['primary-evidence', 'environmental-context', 'archaeology-context', 'orientation'];
        layerFilters.innerHTML = groupOrder
          .map((group) => {
            const layers = ALL_LAYERS.filter((layer) => layer.group === group);
            if (!layers.length) return '';
            const cards = layers.map((layer) => {
              const checked = activeLayerKeys.has(layer.key) ? 'checked' : '';
              return `<div class="layer-card"><label><input class="layer-checkbox" type="checkbox" value="${escapeHtml(layer.key)}" ${checked} aria-label="Toggle ${escapeHtml(layer.label)}"><div style="width:100%;"><div class="layer-card-top"><div><strong>${escapeHtml(layer.label)}</strong><span>${escapeHtml(layer.description)}</span></div><span class="layer-badge" id="layer-count-${escapeHtml(layer.key)}">${escapeHtml(String(layer.count))} ${escapeHtml(layerUnit(layer))}</span></div><div class="layer-meta"><span><strong>Source</strong> ${escapeHtml(layer.source_name || layer.label)}</span><span><strong>Coverage</strong> ${escapeHtml(layer.coverage_label || '')}</span><span><strong>Geometry</strong> ${escapeHtml(layer.geometry_label || layerUnit(layer))}</span></div></div></label></div>`;
            }).join('');
            return `<section class="layer-group"><div class="layer-group-head"><h3>${escapeHtml(layerGroupLabel(group))}</h3><span>${escapeHtml(layerGroupSummary(group))}</span></div>${cards}</section>`;
          })
          .join('');
        document.querySelectorAll('.layer-checkbox').forEach((checkbox) => {
          checkbox.addEventListener('change', () => {
            if (checkbox.checked) { activeLayerKeys.add(checkbox.value); } else { activeLayerKeys.delete(checkbox.value); }
            renderMapState();
          });
        });
      }
      function renderLegend() {
        const activeLegendLayers = ALL_LAYERS.filter((layer) => activeLayerKeys.has(layer.key));
        legendItems.innerHTML = activeLegendLayers.map((layer) => `<div class="legend-item"><span class="legend-swatch" style="background:${escapeHtml(layerColor(layer))};border-color:${escapeHtml(layer.style.stroke || layerColor(layer))};"></span><span>${escapeHtml(layer.label)}: ${escapeHtml(layer.description)} ${layer.coverage_label ? `(${escapeHtml(layer.coverage_label)})` : ''}</span></div>`).join('') || '<div class="legend-item"><span>No layers are visible. Restore defaults or enable one or more layers.</span></div>';
        densityRamp.hidden = !activeLayerKeys.has('raa-archaeology');
      }
      function popupHtml(feature) {
        const rows = Array.isArray(feature.popup_rows) ? feature.popup_rows : [];
        const rowHtml = rows.filter((row) => row && row.value).map((row) => `<div><strong>${escapeHtml(row.label || '')}</strong> ${escapeHtml(row.value || '')}</div>`).join('');
        return `<div class="popup-grid"><div><strong>Name</strong> ${escapeHtml(feature.title || '')}</div><div><strong>Type</strong> ${escapeHtml(feature.subtitle || '')}</div>${rowHtml}<div><strong>Coords</strong> ${Number(feature.latitude).toFixed(6)}, ${Number(feature.longitude).toFixed(6)}</div>${feature.source_url ? `<div><strong>Source</strong> <a href="${escapeHtml(feature.source_url)}" target="_blank" rel="noreferrer">Open</a></div>` : ''}</div>`;
      }
      function densityFillColor(count, maxCount) {
        if (!maxCount || count <= 0) return '#fee2e2';
        const ratio = count / maxCount;
        if (ratio >= 0.75) return '#7f1d1d';
        if (ratio >= 0.55) return '#b91c1c';
        if (ratio >= 0.35) return '#ef4444';
        if (ratio >= 0.20) return '#f87171';
        if (ratio >= 0.08) return '#fca5a5';
        return '#fee2e2';
      }
      function pointFeatureVisible(layer, feature) { return activeLayerKeys.has(layer.key) && (!layer.applies_country_filter || !feature.country || activeCountries.has(feature.country)); }
      function polygonFeatureVisible(layer, properties) {
        const country = properties.country || '';
        return activeLayerKeys.has(layer.key) && (!layer.applies_country_filter || !country || activeCountries.has(country));
      }
      function removeRenderedLayers() {
        renderedPointGroups.forEach((group) => map.removeLayer(group));
        renderedPolygonLayers.forEach((layer) => map.removeLayer(layer));
        renderedPointGroups = [];
        renderedPolygonLayers = [];
        circleLayerGroup.clearLayers();
        visiblePointEntries = [];
      }
      function createClusterGroup(layer) {
        return L.markerClusterGroup({
          showCoverageOnHover: false,
          spiderfyOnMaxZoom: true,
          maxClusterRadius: 46,
          disableClusteringAtZoom: 10,
          iconCreateFunction(cluster) {
            const count = cluster.getChildCount();
            const size = count > 100 ? 50 : count > 25 ? 44 : 38;
            return L.divIcon({ html: `<div class="cluster-pill" style="width:${size}px;height:${size}px;background:${layer.style.fill};">${count}</div>`, className: '', iconSize: [size, size] });
          }
        });
      }
      function renderPointLayers() {
        const diameterKm = Number(slider.value);
        const radiusMeters = (diameterKm * 1000) / 2;
        POINT_LAYERS.forEach((layer) => {
          const clusterGroup = createClusterGroup(layer);
          layer.features.forEach((feature) => {
            if (!pointFeatureVisible(layer, feature)) return;
            const marker = L.circleMarker([feature.latitude, feature.longitude], { pane: 'pointPane', radius: layer.key === 'aadr' ? 4.5 : 6, color: layer.style.stroke, weight: 1.3, fillColor: layer.style.fill, fillOpacity: 0.92 });
            marker.bindPopup(popupHtml(feature), { maxWidth: 360 });
            clusterGroup.addLayer(marker);
            visiblePointEntries.push({ layer, feature, marker });
            if (layer.circle_enabled && diameterKm > 0) {
              const circle = L.circle([feature.latitude, feature.longitude], { pane: 'circlePane', radius: radiusMeters, color: layer.style.circleStroke, weight: 1, opacity: 0.55, fillColor: layer.style.circleFill, fillOpacity: 0.12, interactive: false });
              circleLayerGroup.addLayer(circle);
            }
          });
          if (clusterGroup.getLayers().length > 0) { clusterGroup.addTo(map); renderedPointGroups.push(clusterGroup); }
        });
      }
      function renderPolygonLayers() {
        POLYGON_LAYERS.forEach((layer) => {
          const visibleFeatures = (layer.geojson.features || []).filter((feature) => polygonFeatureVisible(layer, feature.properties || {}));
          if (!visibleFeatures.length) return;
          let geoJsonLayer;
          if (layer.kind === 'country-boundaries') {
            geoJsonLayer = L.geoJSON({ type: 'FeatureCollection', features: visibleFeatures }, {
              pane: 'boundaryPane',
              style(feature) {
                const country = feature.properties.country || '';
                const style = countryStyle(country);
                return { color: style.stroke, weight: activeCountries.has(country) ? 2.2 : 1.2, fillColor: style.fill, fillOpacity: activeCountries.has(country) ? 0.10 : 0.02, opacity: activeCountries.has(country) ? 0.95 : 0.45 };
              },
              onEachFeature(feature, featureLayer) {
                featureLayer.bindPopup(`<div class="popup-grid"><div><strong>Country</strong> ${escapeHtml(feature.properties.name || '')}</div><div><strong>Filter state</strong> ${activeCountries.has(feature.properties.country) ? 'Visible' : 'Hidden'}</div></div>`);
              }
            });
          } else {
            geoJsonLayer = L.geoJSON({ type: 'FeatureCollection', features: visibleFeatures }, {
              pane: 'polygonPane',
              style(feature) {
                const count = Number(feature.properties.count || 0);
                return { color: layer.style.stroke, weight: 1.1, fillColor: densityFillColor(count, Number(layer.max_count || 0)), fillOpacity: densityOpacity, opacity: 0.75 };
              },
              onEachFeature(feature, featureLayer) {
                featureLayer.bindPopup(`<div class="popup-grid"><div><strong>Layer</strong> ${escapeHtml(layer.label)}</div><div><strong>Country</strong> ${escapeHtml(feature.properties.country || '')}</div><div><strong>Records</strong> ${escapeHtml(String(feature.properties.count_label || feature.properties.count || '0'))}</div></div>`);
              }
            });
          }
          geoJsonLayer.addTo(map);
          renderedPolygonLayers.push(geoJsonLayer);
        });
      }
      function activeBounds() {
        const latLngs = visiblePointEntries.map((entry) => [entry.feature.latitude, entry.feature.longitude]);
        renderedPolygonLayers.forEach((layer) => {
          const bounds = layer.getBounds();
          if (bounds.isValid()) {
            latLngs.push([bounds.getSouth(), bounds.getWest()]);
            latLngs.push([bounds.getNorth(), bounds.getEast()]);
          }
        });
        return latLngs.length ? L.latLngBounds(latLngs) : null;
      }
      function updateStats() {
        const enabledLayers = ALL_LAYERS.filter((layer) => activeLayerKeys.has(layer.key)).length;
        statVisiblePoints.textContent = String(visiblePointEntries.length);
        statVisibleLayers.textContent = String(enabledLayers);
        statVisibleCountries.textContent = String(activeCountries.size);
        statRadius.textContent = `${(Number(slider.value) / 2).toFixed(1)} km`;
        statContextSources.textContent = String(ALL_LAYERS.filter((layer) => layer.key !== 'aadr').length);
        const visiblePolygonLayers = renderedPolygonLayers.length;
        selectionReadout.textContent = `Visible points ${visiblePointEntries.length} · overlays ${visiblePolygonLayers}`;
        countrySummary.textContent = activeCountries.size === COUNTRIES.length ? 'All countries visible' : activeCountries.size ? `${activeCountries.size} countries active` : 'No countries active';
        layerSummary.textContent = enabledLayers ? `${enabledLayers} layers enabled` : 'No layers enabled';
        ALL_LAYERS.forEach((layer) => {
          const badge = document.getElementById(`layer-count-${layer.key}`);
          if (!badge) return;
          if (Object.prototype.hasOwnProperty.call(layer, 'features')) {
            const count = layer.features.filter((feature) => pointFeatureVisible(layer, feature)).length;
            badge.textContent = `${count} ${layerUnit(layer)}`;
          } else {
            const count = (layer.geojson.features || []).filter((feature) => polygonFeatureVisible(layer, feature.properties || {})).length;
            badge.textContent = `${count} ${layerUnit(layer)}`;
          }
        });
      }
      function updateSummary() {
        const visibleCountriesText = activeCountries.size ? [...activeCountries].join(', ') : 'none selected';
        const visibleLayersText = activeLayerKeys.size ? humanLayerList(activeLayerKeys) : 'none selected';
        const items = [
          `Visible countries: ${visibleCountriesText}`,
          `Visible layers: ${visibleLayersText}`,
          `Acceptance diameter: ${Number(slider.value)} km`,
          `Acceptance radius: ${(Number(slider.value) / 2).toFixed(1)} km`,
          `Archaeology opacity: ${Math.round(densityOpacity * 100)}%`,
          `Map build date: __GENERATED_ON__`,
          `AADR release: __VERSION__`,
          `Archaeology coverage note: Sweden only in the current RAÄ layer`
        ];
        activeSummary.innerHTML = items.map((item) => `<div class="summary-item"><span>${escapeHtml(item)}</span></div>`).join('');
      }
      function buildSearchResults() {
        const query = searchInput.value.trim().toLowerCase();
        if (!query) {
          const initial = visiblePointEntries.slice(0, 8);
          searchCount.textContent = `${visiblePointEntries.length} visible records`;
          searchResults.innerHTML = initial.map(({ layer, feature }, index) => `<button class="search-result" type="button" data-search-index="${index}"><strong>${escapeHtml(feature.title || '')}</strong><span>${escapeHtml(layer.label)} · ${escapeHtml(feature.subtitle || '')} · ${escapeHtml(feature.country || 'Unassigned')}</span></button>`).join('') || '<div class="summary-item"><span>No visible point records are available under the current filters.</span></div>';
          searchResults.querySelectorAll('[data-search-index]').forEach((button, index) => {
            button.addEventListener('click', () => {
              const match = initial[index];
              if (!match) return;
              map.flyTo([match.feature.latitude, match.feature.longitude], Math.max(map.getZoom(), 8), { duration: 0.7 });
              window.setTimeout(() => match.marker.openPopup(), 250);
            });
          });
          return;
        }
        const matches = visiblePointEntries.filter(({ layer, feature }) => `${feature.title || ''} ${feature.subtitle || ''} ${feature.country || ''} ${layer.label || ''}`.toLowerCase().includes(query)).slice(0, 12);
        searchCount.textContent = `${matches.length} matches`;
        searchResults.innerHTML = matches.map(({ layer, feature }, index) => `<button class="search-result" type="button" data-search-index="${index}"><strong>${escapeHtml(feature.title || '')}</strong><span>${escapeHtml(layer.label)} · ${escapeHtml(feature.subtitle || '')} · ${escapeHtml(feature.country || 'Unassigned')}</span></button>`).join('') || '<div class="summary-item"><span>No visible records match the current query.</span></div>';
        searchResults.querySelectorAll('[data-search-index]').forEach((button, index) => {
          button.addEventListener('click', () => {
            const match = matches[index];
            if (!match) return;
            map.flyTo([match.feature.latitude, match.feature.longitude], Math.max(map.getZoom(), 8), { duration: 0.7 });
            window.setTimeout(() => match.marker.openPopup(), 250);
          });
        });
      }
      function renderMapState() {
        removeRenderedLayers();
        renderPointLayers();
        renderPolygonLayers();
        renderCountryControls();
        renderLegend();
        updateStats();
        updateSummary();
        buildSearchResults();
        syncPresetButtons();
        diameterValue.textContent = `${Number(slider.value)} km diameter`;
        radiusValue.textContent = `${(Number(slider.value) / 2).toFixed(1)} km`;
        densityOpacityValue.textContent = `${Math.round(densityOpacity * 100)}%`;
        emptyState.hidden = visiblePointEntries.length > 0 || renderedPolygonLayers.length > 0;
        syncHashState();
      }
      function setBasemap(name) {
        if (name === currentBasemap || !basemaps[name]) return;
        map.removeLayer(basemaps[currentBasemap]);
        basemaps[name].addTo(map);
        currentBasemap = name;
        document.querySelectorAll('.basemap-button').forEach((button) => button.classList.toggle('is-active', button.dataset.basemap === name));
        syncHashState();
      }
      function fitToActive() {
        const bounds = activeBounds();
        if (bounds && bounds.isValid()) map.fitBounds(bounds, { padding: [36, 36] });
      }
      function resetView() { map.fitBounds(INITIAL_BOUNDS, { padding: [36, 36] }); }
      function restoreDefaults() {
        activeCountries = new Set(DEFAULT_COUNTRIES);
        activeLayerKeys = new Set(DEFAULT_LAYER_KEYS);
        slider.value = __INITIAL_DIAMETER__;
        densityOpacity = 0.6;
        densityOpacitySlider.value = '60';
        if (sidebar.classList.contains('is-collapsed')) sidebar.classList.remove('is-collapsed');
        panelToggleButton.textContent = 'Hide panel';
        searchInput.value = '';
        if (currentBasemap !== 'voyager') setBasemap('voyager');
        renderCountryControls();
        renderLayerControls();
        renderMapState();
        resetView();
      }
      document.getElementById('countries-all').addEventListener('click', () => { activeCountries = new Set(COUNTRIES); renderCountryControls(); renderMapState(); });
      document.getElementById('countries-none').addEventListener('click', () => { activeCountries = new Set(); renderCountryControls(); renderMapState(); });
      document.getElementById('countries-fit').addEventListener('click', fitToActive);
      document.getElementById('fit-active').addEventListener('click', fitToActive);
      document.getElementById('reset-view').addEventListener('click', resetView);
      document.getElementById('restore-defaults').addEventListener('click', restoreDefaults);
      document.getElementById('copy-link').addEventListener('click', async () => {
        syncHashState();
        const button = document.getElementById('copy-link');
        const previous = button.textContent;
        try {
          await navigator.clipboard.writeText(window.location.href);
          button.textContent = 'Link copied';
        } catch (error) {
          button.textContent = 'Copy failed';
        }
        window.setTimeout(() => { button.textContent = previous; }, 1400);
      });
      document.getElementById('fullscreen-toggle').addEventListener('click', async () => {
        const target = document.querySelector('.map-stage');
        if (!document.fullscreenElement) { await target.requestFullscreen(); } else { await document.exitFullscreen(); }
      });
      document.querySelectorAll('.basemap-button').forEach((button) => button.addEventListener('click', () => setBasemap(button.dataset.basemap)));
      panelToggleButton.addEventListener('click', () => {
        sidebar.classList.toggle('is-collapsed');
        panelToggleButton.textContent = sidebar.classList.contains('is-collapsed') ? 'Show panel' : 'Hide panel';
        window.setTimeout(() => map.invalidateSize(), 180);
        syncHashState();
      });
      slider.addEventListener('input', renderMapState);
      densityOpacitySlider.addEventListener('input', () => { densityOpacity = Number(densityOpacitySlider.value) / 100; renderMapState(); });
      document.querySelectorAll('.preset-button').forEach((button) => {
        button.addEventListener('click', () => {
          slider.value = button.dataset.km;
          renderMapState();
        });
      });
      searchInput.addEventListener('input', buildSearchResults);
      searchInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
          const firstResult = searchResults.querySelector('[data-search-index]');
          if (firstResult) firstResult.click();
        }
      });
      map.on('zoomend', () => { zoomReadout.textContent = `Zoom ${map.getZoom().toFixed(1)}`; });
      map.on('mousemove', (event) => { cursorReadout.textContent = `Cursor ${event.latlng.lat.toFixed(3)}, ${event.latlng.lng.toFixed(3)}`; });
      document.addEventListener('fullscreenchange', () => window.setTimeout(() => map.invalidateSize(), 160));
      densityOpacitySlider.value = String(Math.round(densityOpacity * 100));
      slider.value = String(Number(initialState.diameter || __INITIAL_DIAMETER__));
      renderScopeSummary();
      renderCountryControls();
      renderLayerControls();
      renderMapState();
      setBasemap(currentBasemap);
      if (initialState.panel === 'collapsed') {
        sidebar.classList.add('is-collapsed');
        panelToggleButton.textContent = 'Show panel';
      }
      resetView();
      zoomReadout.textContent = `Zoom ${map.getZoom().toFixed(1)}`;
    </script>
  </body>
</html>
"""
    return (
        template
        .replace("__TITLE__", escape_html(title))
        .replace("__VERSION__", escape_html(version))
        .replace("__GENERATED_ON__", escape_html(generated_on))
        .replace("__COUNTRIES_JSON__", json.dumps(list(countries), ensure_ascii=False))
        .replace("__POINT_LAYERS_JSON__", json.dumps(point_layers, ensure_ascii=False))
        .replace("__POLYGON_LAYERS_JSON__", json.dumps(polygon_layers, ensure_ascii=False))
        .replace("__BOUNDS_JSON__", json.dumps(bounds))
        .replace("__INITIAL_DIAMETER__", str(initial_diameter_km))
        .replace("__INITIAL_RADIUS__", f"{initial_diameter_km / 2:.1f}")
    )


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
