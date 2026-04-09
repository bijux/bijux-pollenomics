from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from pathlib import Path

from ..config import DEFAULT_ATLAS_SLUG, DEFAULT_ATLAS_TITLE
from .aadr import load_country_samples, summarize_localities
from .bundles.atlas_bundle import publish_multi_country_map_bundle
from .bundles.country_bundle import publish_country_report_bundle
from .bundles.country_selection import normalize_requested_countries
from .bundles.map_inputs import load_multi_country_map_inputs
from .bundles.paths import build_atlas_bundle_paths
from .bundles.published_reports import publish_published_reports_tree
from .bundles.staging import publish_into_staging_dir
from .bundles.summary_builders import (
    build_country_report_summary,
    build_multi_country_map_summary,
    build_published_reports_summary,
)
from .context import build_context_layers
from .models import CountryReport, MultiCountryMapReport, PublishedReportsReport
from .rendering import (
    build_samples_geojson,
    copy_map_assets,
    render_multi_country_map_html,
    render_multi_country_map_markdown,
    render_sample_markdown,
    render_summary_markdown,
    write_localities_csv,
    write_samples_csv,
    write_samples_geojson,
    write_summary_json,
)
from .shared.text import slugify


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
    published_output_dir = (
        Path(published_output_dir) if published_output_dir is not None else output_dir
    )
    normalized_country = country.strip()
    if not normalized_country:
        raise ValueError("Country is required to build a country report")

    samples, dataset_counts = load_country_samples(
        version_dir=version_dir, country=normalized_country
    )
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
        publish_country_report_bundle(
            staging_output_dir,
            report=report,
            country=normalized_country,
            version=version,
            map_reference=map_reference,
            build_country_report_summary_fn=build_country_report_summary,
            render_sample_markdown_fn=render_sample_markdown,
            render_summary_markdown_fn=render_summary_markdown,
            write_localities_csv_fn=write_localities_csv,
            write_samples_csv_fn=write_samples_csv,
            write_samples_geojson_fn=write_samples_geojson,
            write_summary_json_fn=write_summary_json,
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
    published_output_dir = (
        Path(published_output_dir) if published_output_dir is not None else output_dir
    )

    normalized_countries = normalize_requested_countries(countries)
    if not normalized_countries:
        raise ValueError(
            "At least one country is required to build a multi-country map"
        )

    map_inputs = load_multi_country_map_inputs(
        version_dir=version_dir,
        countries=normalized_countries,
        load_country_samples_fn=load_country_samples,
    )
    version = version_dir.name
    generated_on = str(date.today())
    map_report = MultiCountryMapReport(
        title=title,
        slug=slug,
        version=version,
        generated_on=generated_on,
        countries=normalized_countries,
        country_sample_counts=map_inputs.country_sample_counts,
        total_unique_samples=len(map_inputs.all_samples),
        output_dir=published_output_dir,
    )

    def publish_map_bundle(staging_output_dir: Path) -> None:
        publish_multi_country_map_bundle(
            staging_output_dir,
            report=map_report,
            title=title,
            version=version,
            generated_on=generated_on,
            countries=normalized_countries,
            country_sample_counts=map_inputs.country_sample_counts,
            all_samples=map_inputs.all_samples,
            context_root=context_root,
            asset_base_path="./_map_assets",
            build_atlas_bundle_paths_fn=build_atlas_bundle_paths,
            build_context_layers_fn=build_context_layers,
            build_multi_country_map_summary_fn=build_multi_country_map_summary,
            build_samples_geojson_fn=build_samples_geojson,
            copy_map_assets_fn=copy_map_assets,
            render_multi_country_map_html_fn=render_multi_country_map_html,
            render_multi_country_map_markdown_fn=render_multi_country_map_markdown,
            write_summary_json_fn=write_summary_json,
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
    return publish_into_staging_dir(
        output_root,
        lambda staging_output_root: publish_published_reports_tree(
            staging_output_root,
            version_dir=version_dir,
            output_root=output_root,
            normalized_countries=normalized_countries,
            title=title,
            atlas_slug=atlas_slug,
            context_root=context_root,
            build_atlas_bundle_paths_fn=build_atlas_bundle_paths,
            build_published_reports_summary_fn=build_published_reports_summary,
            generate_country_report_fn=generate_country_report,
            generate_multi_country_map_fn=generate_multi_country_map,
            slugify_fn=slugify,
            write_summary_json_fn=write_summary_json,
        ),
    )
