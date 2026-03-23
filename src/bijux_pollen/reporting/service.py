from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Iterable

from .aadr import load_country_samples, summarize_localities
from .artifacts import build_samples_geojson, write_localities_csv, write_samples_csv, write_samples_geojson
from .context_layers import build_context_layers
from .html import render_multi_country_map_html
from .markdown import render_multi_country_map_markdown, render_sample_markdown, render_summary_markdown
from .models import CountryReport, MultiCountryMapReport
from .utils import slugify


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

