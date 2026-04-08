from __future__ import annotations

from ...models import CountryReport


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


__all__ = ["build_country_report_summary"]
