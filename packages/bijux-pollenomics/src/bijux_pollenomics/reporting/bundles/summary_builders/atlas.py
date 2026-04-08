from __future__ import annotations

from ...models import MultiCountryMapReport


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


__all__ = ["build_multi_country_map_summary"]
