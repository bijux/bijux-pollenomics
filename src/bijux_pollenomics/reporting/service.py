from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Iterable

from .aadr import load_country_samples, summarize_localities
from .artifacts import (
    build_samples_geojson,
    copy_map_assets,
    write_localities_csv,
    write_samples_csv,
    write_samples_geojson,
    write_summary_json,
)
from .context_layers import build_context_layers
from .html import render_multi_country_map_html
from .markdown import render_multi_country_map_markdown, render_sample_markdown, render_summary_markdown
from .models import CountryReport, MultiCountryMapReport, PublishedReportsReport, SampleRecord
from .paths import build_atlas_bundle_paths, build_country_bundle_paths
from .staging import publish_into_staging_dir
from .summaries import (
    build_country_report_summary,
    build_multi_country_map_summary,
    build_published_reports_summary,
)
from .utils import slugify
from .countries import normalize_requested_countries
from ..settings import DEFAULT_ATLAS_SLUG, DEFAULT_ATLAS_TITLE


def generate_country_report(
    version_dir: Path,
    country: str,
    output_dir: Path,
    map_reference: tuple[str, str] | None = None,
    published_output_dir: Path | None = None,
) -> CountryReport:
    """Read all AADR anno files for a version, filter by country, and write report artifacts."""
    version_dir = Path(version_dir)
    output_dir = Path(output_dir)
    published_output_dir = Path(published_output_dir) if published_output_dir is not None else output_dir
    normalized_country = country.strip()
    if not normalized_country:
        raise ValueError("Country is required to build a country report")

    samples, dataset_counts = load_country_samples(version_dir=version_dir, country=normalized_country)
    localities = summarize_localities(samples)
    version = version_dir.name
    report = CountryReport(
        country=normalized_country,
        version=version,
        generated_on=str(date.today()),
        total_unique_samples=len(samples),
        total_unique_localities=len(localities),
        dataset_row_counts=dict(sorted(dataset_counts.items())),
        samples=tuple(samples),
        localities=tuple(localities),
        output_dir=published_output_dir,
    )

    def publish_country_bundle(staging_output_dir: Path) -> None:
        bundle_paths = build_country_bundle_paths(
            output_dir=staging_output_dir,
            country=normalized_country,
            version=version,
        )
        write_samples_csv(bundle_paths.samples_csv_path, report.samples)
        write_localities_csv(bundle_paths.localities_csv_path, report.localities)
        write_samples_geojson(bundle_paths.samples_geojson_path, report.samples)
        write_summary_json(bundle_paths.summary_json_path, build_country_report_summary(report, bundle_paths))
        bundle_paths.samples_markdown_path.write_text(render_sample_markdown(report), encoding="utf-8")
        bundle_paths.readme_path.write_text(
            render_summary_markdown(
                report=report,
                samples_csv_name=bundle_paths.samples_csv_path.name,
                localities_csv_name=bundle_paths.localities_csv_path.name,
                geojson_name=bundle_paths.samples_geojson_path.name,
                sample_markdown_name=bundle_paths.samples_markdown_path.name,
                summary_json_name=bundle_paths.summary_json_path.name,
                map_reference=map_reference,
            ),
            encoding="utf-8",
        )

    publish_into_staging_dir(output_dir, publish_country_bundle)
    return report


def generate_multi_country_map(
    version_dir: Path,
    countries: Iterable[str],
    output_dir: Path,
    title: str,
    slug: str,
    context_root: Path | None = None,
    published_output_dir: Path | None = None,
) -> MultiCountryMapReport:
    """Write a shared interactive map for multiple countries with country toggles."""
    version_dir = Path(version_dir)
    output_dir = Path(output_dir)
    published_output_dir = Path(published_output_dir) if published_output_dir is not None else output_dir

    normalized_countries = normalize_requested_countries(countries)
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
    map_report = MultiCountryMapReport(
        title=title,
        slug=slug,
        version=version,
        generated_on=generated_on,
        countries=normalized_countries,
        country_sample_counts=country_sample_counts,
        total_unique_samples=len(all_samples),
        output_dir=published_output_dir,
    )

    def publish_map_bundle(staging_output_dir: Path) -> None:
        bundle_paths = build_atlas_bundle_paths(output_dir=staging_output_dir, slug=slug, version=version)
        map_geojson = build_samples_geojson(all_samples)
        bundle_paths.samples_geojson_path.write_text(json.dumps(map_geojson, indent=2), encoding="utf-8")
        point_layers, polygon_layers, extra_artifacts = build_context_layers(
            samples=all_samples,
            output_dir=staging_output_dir,
            context_root=context_root,
        )
        copy_map_assets(staging_output_dir)
        write_summary_json(
            bundle_paths.summary_json_path,
            build_multi_country_map_summary(map_report, bundle_paths, extra_artifacts),
        )
        bundle_paths.map_html_path.write_text(
            render_multi_country_map_html(
                title=title,
                version=version,
                generated_on=generated_on,
                countries=normalized_countries,
                point_layers=point_layers,
                polygon_layers=polygon_layers,
                asset_base_path="./_map_assets",
            ),
            encoding="utf-8",
        )
        bundle_paths.readme_path.write_text(
            render_multi_country_map_markdown(
                title=title,
                version=version,
                generated_on=generated_on,
                countries=normalized_countries,
                country_sample_counts=country_sample_counts,
                map_html_name=bundle_paths.map_html_path.name,
                geojson_name=bundle_paths.samples_geojson_path.name,
                summary_json_name=bundle_paths.summary_json_path.name,
                extra_artifacts=extra_artifacts,
            ),
            encoding="utf-8",
        )

    publish_into_staging_dir(output_dir, publish_map_bundle)
    return map_report


def generate_published_reports(
    version_dir: Path,
    countries: Iterable[str],
    output_root: Path,
    title: str = DEFAULT_ATLAS_TITLE,
    slug: str = DEFAULT_ATLAS_SLUG,
    context_root: Path | None = None,
) -> PublishedReportsReport:
    """Generate the current published report set: one shared map and one bundle per country."""
    version_dir = Path(version_dir)
    output_root = Path(output_root)

    normalized_countries = normalize_requested_countries(countries)
    if not normalized_countries:
        raise ValueError("At least one country is required to publish reports")

    atlas_slug = slugify(slug)
    generated_report: PublishedReportsReport | None = None

    def publish_report_tree(staging_output_root: Path) -> None:
        nonlocal generated_report
        shared_map_dir = staging_output_root / atlas_slug
        map_report = generate_multi_country_map(
            version_dir=version_dir,
            countries=normalized_countries,
            output_dir=shared_map_dir,
            title=title,
            slug=atlas_slug,
            context_root=context_root,
            published_output_dir=output_root / shared_map_dir.name,
        )

        country_output_dirs: list[Path] = []
        shared_bundle_paths = build_atlas_bundle_paths(
            output_dir=shared_map_dir,
            slug=map_report.slug,
            version=map_report.version,
        )
        shared_map_path = f"../{shared_map_dir.name}/{shared_bundle_paths.map_html_path.name}"
        for country in normalized_countries:
            country_dir = staging_output_root / slugify(country)
            generate_country_report(
                version_dir=version_dir,
                country=country,
                output_dir=country_dir,
                map_reference=(title, shared_map_path),
                published_output_dir=output_root / country_dir.name,
            )
            country_output_dirs.append(country_dir)

        summary_path = staging_output_root / "published_reports_summary.json"
        generated_report = PublishedReportsReport(
            version=map_report.version,
            generated_on=map_report.generated_on,
            countries=normalized_countries,
            shared_map_dir=output_root / shared_map_dir.name,
            country_output_dirs=tuple(output_root / path.name for path in country_output_dirs),
            summary_path=output_root / summary_path.name,
        )
        write_summary_json(summary_path, build_published_reports_summary(generated_report, map_report))

    publish_into_staging_dir(output_root, publish_report_tree)
    if generated_report is None:
        raise AssertionError("published reports should be created before returning")
    return generated_report
