from __future__ import annotations

from dataclasses import asdict

from ...models import MultiCountryMapReport, PublishedReportsReport


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
            path.name: str(path) for path in report.country_output_dirs
        },
    }
    return payload


__all__ = ["build_published_reports_summary"]
