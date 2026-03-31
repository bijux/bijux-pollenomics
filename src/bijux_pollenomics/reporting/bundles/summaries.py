from __future__ import annotations

from dataclasses import asdict

from ..models import CountryReport, MultiCountryMapReport, PublishedReportsReport

__all__ = [
    "build_country_report_summary",
    "build_multi_country_map_summary",
    "build_published_reports_summary",
]


def build_country_report_summary(report: CountryReport, bundle_paths: object) -> dict[str, object]:
    """Build a machine-readable summary for one country report."""
    return {
        "country": report.country,
        "version": report.version,
        "generated_on": report.generated_on,
        "total_unique_samples": report.total_unique_samples,
        "total_unique_localities": report.total_unique_localities,
        "dataset_row_counts": report.dataset_row_counts,
        "output_dir": str(report.output_dir),
        "artifacts": {
            "readme": bundle_paths.readme_path.name,
            "samples_csv": bundle_paths.samples_csv_path.name,
            "localities_csv": bundle_paths.localities_csv_path.name,
            "samples_geojson": bundle_paths.samples_geojson_path.name,
            "samples_markdown": bundle_paths.samples_markdown_path.name,
            "summary_json": bundle_paths.summary_json_path.name,
        },
    }


def build_multi_country_map_summary(
    report: MultiCountryMapReport,
    bundle_paths: object,
    extra_artifacts: list[tuple[str, str]],
) -> dict[str, object]:
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
        "artifacts": {
            "readme": bundle_paths.readme_path.name,
            "map_html": bundle_paths.map_html_path.name,
            "samples_geojson": bundle_paths.samples_geojson_path.name,
            "summary_json": bundle_paths.summary_json_path.name,
            "extra_files": [
                {"label": label, "filename": filename}
                for label, filename in extra_artifacts
            ],
        },
    }


def build_published_reports_summary(
    report: PublishedReportsReport,
    map_report: MultiCountryMapReport,
) -> dict[str, object]:
    """Build a machine-readable summary for the current published report set."""
    payload = asdict(report)
    payload["shared_map_dir"] = str(report.shared_map_dir)
    payload["country_output_dirs"] = [str(path) for path in report.country_output_dirs]
    payload["summary_path"] = str(report.summary_path)
    payload["artifacts"] = {
        "shared_bundle": {
            "slug": map_report.slug,
            "directory": str(report.shared_map_dir),
        },
        "country_bundles": {
            path.name: str(path)
            for path in report.country_output_dirs
        },
    }
    return payload
