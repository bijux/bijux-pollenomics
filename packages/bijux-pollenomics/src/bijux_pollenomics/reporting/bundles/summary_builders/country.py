from __future__ import annotations

import json

from ...models import CountryReport
from ..paths import CountryBundlePaths


def build_country_report_summary(
    report: CountryReport, bundle_paths: CountryBundlePaths
) -> dict[str, object]:
    """Build a machine-readable summary for one country report."""
    payload = {
        "schema_version": "country-report-summary.v1",
        "country": report.country,
        "version": report.version,
        "generated_on": report.generated_on,
        "total_unique_samples": report.total_unique_samples,
        "total_unique_localities": report.total_unique_localities,
        "dataset_row_counts": report.dataset_row_counts,
        "output_dir": str(report.output_dir),
        "artifacts": {
            "bundle_manifest": bundle_paths.bundle_manifest_path.name,
            "readme": bundle_paths.readme_path.name,
            "samples_csv": bundle_paths.samples_csv_path.name,
            "localities_csv": bundle_paths.localities_csv_path.name,
            "samples_geojson": bundle_paths.samples_geojson_path.name,
            "samples_markdown": bundle_paths.samples_markdown_path.name,
            "summary_json": bundle_paths.summary_json_path.name,
        },
    }
    if bundle_paths.animal_summary_json_path.exists():
        animal_summary = json.loads(
            bundle_paths.animal_summary_json_path.read_text(encoding="utf-8")
        )
        payload["animal_adna"] = {
            "total_species": int(animal_summary.get("total_species", 0)),
            "total_localities": int(animal_summary.get("total_localities", 0)),
            "total_sample_rows": int(animal_summary.get("total_sample_rows", 0)),
            "artifacts": {
                "summary_json": bundle_paths.animal_summary_json_path.name,
                "samples_csv": bundle_paths.animal_samples_csv_path.name,
                "samples_markdown": bundle_paths.animal_samples_markdown_path.name,
                "species_csv": bundle_paths.animal_species_csv_path.name,
                "localities_geojson": bundle_paths.animal_localities_geojson_path.name,
                "citations_markdown": bundle_paths.animal_citations_markdown_path.name,
                "warnings_markdown": bundle_paths.animal_warnings_markdown_path.name,
            },
        }
    return payload


def build_country_bundle_manifest(
    report: CountryReport, bundle_paths: CountryBundlePaths
) -> dict[str, object]:
    """Build a machine-readable manifest for one country report bundle."""
    payload = {
        "schema_version": "country-report-bundle-manifest.v1",
        "bundle_type": "country_aadr_report",
        "country": report.country,
        "version": report.version,
        "generated_on": report.generated_on,
        "dataset_row_counts": report.dataset_row_counts,
        "total_unique_samples": report.total_unique_samples,
        "total_unique_localities": report.total_unique_localities,
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
    if bundle_paths.animal_summary_json_path.exists():
        payload["animal_adna"] = {
            "summary_json": bundle_paths.animal_summary_json_path.name,
            "samples_csv": bundle_paths.animal_samples_csv_path.name,
            "samples_markdown": bundle_paths.animal_samples_markdown_path.name,
            "species_csv": bundle_paths.animal_species_csv_path.name,
            "localities_geojson": bundle_paths.animal_localities_geojson_path.name,
            "citations_markdown": bundle_paths.animal_citations_markdown_path.name,
            "warnings_markdown": bundle_paths.animal_warnings_markdown_path.name,
        }
    return payload


__all__ = ["build_country_bundle_manifest", "build_country_report_summary"]
