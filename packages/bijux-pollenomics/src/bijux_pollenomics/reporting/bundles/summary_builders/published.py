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
            "bundle_manifest": f"{map_report.slug}_bundle.json",
            "summary_json": f"{map_report.slug}_summary.json",
        },
        "country_bundles": {
            path.name: {
                "directory": str(path),
                "bundle_manifest": f"{path.name}_aadr_{report.version}_bundle.json",
                "summary_json": f"{path.name}_aadr_{report.version}_summary.json",
            }
            for path in report.country_output_dirs
        },
    }
    return payload


__all__ = ["build_published_reports_summary"]
