from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

from ..models import CountryReport, LocalitySummary, SampleRecord
from .paths import CountryBundlePaths, build_country_bundle_paths
from .summary_builders.country import build_country_bundle_manifest

__all__ = ["publish_country_report_bundle"]


def publish_country_report_bundle(
    staging_output_dir: Path,
    *,
    report: CountryReport,
    country: str,
    version: str,
    map_reference: tuple[str, str] | None,
    build_country_report_summary_fn: Callable[
        [CountryReport, CountryBundlePaths], dict[str, object]
    ],
    render_sample_markdown_fn: Callable[[CountryReport], str],
    render_summary_markdown_fn: Callable[..., str],
    write_localities_csv_fn: Callable[[Path, Iterable[LocalitySummary]], None],
    write_samples_csv_fn: Callable[[Path, Iterable[SampleRecord]], None],
    write_samples_geojson_fn: Callable[[Path, Iterable[SampleRecord]], None],
    write_summary_json_fn: Callable[[Path, dict[str, object]], None],
) -> None:
    """Write the full country report artifact bundle into one staging directory."""
    bundle_paths = build_country_bundle_paths(
        output_dir=staging_output_dir,
        country=country,
        version=version,
    )
    write_samples_csv_fn(bundle_paths.samples_csv_path, report.samples)
    write_localities_csv_fn(bundle_paths.localities_csv_path, report.localities)
    write_samples_geojson_fn(bundle_paths.samples_geojson_path, report.samples)
    write_summary_json_fn(
        bundle_paths.bundle_manifest_path,
        build_country_bundle_manifest(report, bundle_paths),
    )
    write_summary_json_fn(
        bundle_paths.summary_json_path,
        build_country_report_summary_fn(report, bundle_paths),
    )
    bundle_paths.samples_markdown_path.write_text(
        render_sample_markdown_fn(report), encoding="utf-8"
    )
    bundle_paths.readme_path.write_text(
        render_summary_markdown_fn(
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
