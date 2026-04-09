from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from ..models import MultiCountryMapReport, PublishedReportsReport
from .paths import AtlasBundlePaths

__all__ = ["publish_published_reports_tree"]


def publish_published_reports_tree(
    staging_output_root: Path,
    *,
    version_dir: Path,
    output_root: Path,
    normalized_countries: tuple[str, ...],
    title: str,
    atlas_slug: str,
    context_root: Path | None,
    build_atlas_bundle_paths_fn: Callable[..., AtlasBundlePaths],
    build_published_reports_summary_fn: Callable[..., dict[str, object]],
    generate_country_report_fn: Callable[..., object],
    generate_multi_country_map_fn: Callable[..., MultiCountryMapReport],
    slugify_fn: Callable[[str], str],
    write_summary_json_fn: Callable[[Path, dict[str, object]], None],
) -> PublishedReportsReport:
    """Publish the full report tree: one shared atlas plus one country bundle per country."""
    shared_map_dir = staging_output_root / atlas_slug
    map_report = generate_multi_country_map_fn(
        version_dir=version_dir,
        countries=normalized_countries,
        output_dir=shared_map_dir,
        title=title,
        slug=atlas_slug,
        context_root=context_root,
        published_output_dir=output_root / shared_map_dir.name,
    )

    country_output_dirs: list[Path] = []
    shared_bundle_paths = build_atlas_bundle_paths_fn(
        output_dir=shared_map_dir,
        slug=map_report.slug,
        version=map_report.version,
    )
    shared_map_path = (
        f"../{shared_map_dir.name}/{shared_bundle_paths.map_html_path.name}"
    )
    for country in normalized_countries:
        country_dir = staging_output_root / slugify_fn(country)
        generate_country_report_fn(
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
        country_output_dirs=tuple(
            output_root / path.name for path in country_output_dirs
        ),
        summary_path=output_root / summary_path.name,
    )
    write_summary_json_fn(
        summary_path, build_published_reports_summary_fn(generated_report, map_report)
    )
    return generated_report
