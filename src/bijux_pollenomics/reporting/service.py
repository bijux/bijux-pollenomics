from __future__ import annotations

from dataclasses import asdict
import json
import shutil
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
from .utils import slugify
from ..settings import DEFAULT_ATLAS_SLUG, DEFAULT_ATLAS_TITLE


def generate_country_report(
    version_dir: Path,
    country: str,
    output_dir: Path,
    map_reference: tuple[str, str] | None = None,
) -> CountryReport:
    """Read all AADR anno files for a version, filter by country, and write report artifacts."""
    version_dir = Path(version_dir)
    output_dir = Path(output_dir)
    reset_generated_output_dir(output_dir)
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

    bundle_paths = build_country_bundle_paths(output_dir=output_dir, country=country, version=version)

    write_samples_csv(bundle_paths.samples_csv_path, report.samples)
    write_localities_csv(bundle_paths.localities_csv_path, report.localities)
    write_samples_geojson(bundle_paths.samples_geojson_path, report.samples)
    write_summary_json(bundle_paths.summary_json_path, build_country_report_summary(report))
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
    reset_generated_output_dir(output_dir)
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

    bundle_paths = build_atlas_bundle_paths(output_dir=output_dir, slug=slug, version=version)

    map_geojson = build_samples_geojson(all_samples)
    bundle_paths.samples_geojson_path.write_text(json.dumps(map_geojson, indent=2), encoding="utf-8")

    point_layers, polygon_layers, extra_artifacts = build_context_layers(
        samples=all_samples,
        output_dir=output_dir,
        context_root=context_root,
    )
    copy_map_assets(output_dir)
    map_report = MultiCountryMapReport(
        title=title,
        slug=slug,
        version=version,
        generated_on=generated_on,
        countries=normalized_countries,
        country_sample_counts=country_sample_counts,
        total_unique_samples=len(all_samples),
        output_dir=output_dir,
    )
    write_summary_json(bundle_paths.summary_json_path, build_multi_country_map_summary(map_report))
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
    output_root.mkdir(parents=True, exist_ok=True)

    normalized_countries = tuple(dict.fromkeys(country.strip() for country in countries if country.strip()))
    if not normalized_countries:
        raise ValueError("At least one country is required to publish reports")

    shared_map_dir = output_root / slugify(slug)
    desired_bundle_dirs = {shared_map_dir, *(output_root / slugify(country) for country in normalized_countries)}
    remove_stale_published_bundle_dirs(output_root=output_root, keep_dirs=desired_bundle_dirs)
    map_report = generate_multi_country_map(
        version_dir=version_dir,
        countries=normalized_countries,
        output_dir=shared_map_dir,
        title=title,
        slug=slugify(slug),
        context_root=context_root,
    )

    country_output_dirs: list[Path] = []
    shared_map_path = f"../{shared_map_dir.name}/{shared_map_dir.name}_aadr_{map_report.version}_map.html"
    for country in normalized_countries:
        country_dir = output_root / slugify(country)
        generate_country_report(
            version_dir=version_dir,
            country=country,
            output_dir=country_dir,
            map_reference=(title, shared_map_path),
        )
        country_output_dirs.append(country_dir)

    summary_path = output_root / "published_reports_summary.json"
    report = PublishedReportsReport(
        version=map_report.version,
        generated_on=map_report.generated_on,
        countries=normalized_countries,
        shared_map_dir=shared_map_dir,
        country_output_dirs=tuple(country_output_dirs),
        summary_path=summary_path,
    )
    write_summary_json(summary_path, build_published_reports_summary(report))
    return report


def build_country_report_summary(report: CountryReport) -> dict[str, object]:
    """Build a machine-readable summary for one country report."""
    return {
        "country": report.country,
        "version": report.version,
        "generated_on": report.generated_on,
        "total_unique_samples": report.total_unique_samples,
        "total_unique_localities": report.total_unique_localities,
        "dataset_row_counts": report.dataset_row_counts,
        "output_dir": str(report.output_dir),
    }


def build_multi_country_map_summary(report: MultiCountryMapReport) -> dict[str, object]:
    """Build a machine-readable summary for one shared map bundle."""
    return {
        "title": report.title,
        "slug": report.slug,
        "version": report.version,
        "generated_on": report.generated_on,
        "countries": list(report.countries),
        "country_sample_counts": report.country_sample_counts,
        "total_unique_samples": report.total_unique_samples,
        "output_dir": str(report.output_dir),
    }


def build_published_reports_summary(report: PublishedReportsReport) -> dict[str, object]:
    """Build a machine-readable summary for the current published report set."""
    payload = asdict(report)
    payload["shared_map_dir"] = str(report.shared_map_dir)
    payload["country_output_dirs"] = [str(path) for path in report.country_output_dirs]
    payload["summary_path"] = str(report.summary_path)
    return payload


def reset_generated_output_dir(path: Path) -> None:
    """Remove one generated report bundle directory before regenerating it."""
    if path.exists():
        shutil.rmtree(path)


def remove_stale_published_bundle_dirs(output_root: Path, keep_dirs: set[Path]) -> None:
    """Remove previously published bundle directories that are no longer part of the current output set."""
    summary_path = Path(output_root) / "published_reports_summary.json"
    if not summary_path.exists():
        return

    previous = json.loads(summary_path.read_text(encoding="utf-8"))
    candidate_paths = [previous.get("shared_map_dir"), *(previous.get("country_output_dirs") or [])]
    normalized_keep_dirs = {Path(path).resolve() for path in keep_dirs}
    normalized_output_root = Path(output_root).resolve()
    for candidate in candidate_paths:
        if not isinstance(candidate, str) or not candidate.strip():
            continue
        path = Path(candidate)
        if not path.is_absolute():
            path = normalized_output_root / path
        resolved_path = path.resolve()
        if resolved_path in normalized_keep_dirs:
            continue
        if resolved_path.parent != normalized_output_root:
            continue
        if resolved_path.exists():
            shutil.rmtree(resolved_path)
