from __future__ import annotations

from dataclasses import asdict

from ...geography import PublishedGeographyPlan
from ...models import MultiCountryMapReport, PublishedReportsReport


def build_published_reports_summary(
    report: PublishedReportsReport,
    map_report: MultiCountryMapReport,
    *,
    plan: PublishedGeographyPlan,
    scientific_artifacts: dict[str, str] | None = None,
    repository_truth_artifacts: dict[str, str] | None = None,
) -> dict[str, object]:
    """Build a machine-readable summary for the current published report set."""
    payload = asdict(report)
    payload["schema_version"] = "published-reports-summary.v1"
    payload["shared_map_dir"] = str(report.shared_map_dir)
    payload["regional_output_dirs"] = [str(path) for path in report.regional_output_dirs]
    payload["country_output_dirs"] = [str(path) for path in report.country_output_dirs]
    payload["summary_path"] = str(report.summary_path)
    payload["country_output_root"] = (
        None if report.country_output_root is None else str(report.country_output_root)
    )
    regional_output_dirs = {
        scope.slug: path
        for scope in plan.regional_scopes
        for path in report.regional_output_dirs
        if tuple(path.parts[-len(scope.output_dir_parts) :]) == scope.output_dir_parts
    }
    country_output_dirs = {
        scope.slug: path
        for scope in plan.country_scopes
        for path in report.country_output_dirs
        if tuple(path.parts[-len(scope.output_dir_parts) :]) == scope.output_dir_parts
    }
    geography_bundles = {
        "world": {
            "directory": str(report.shared_map_dir),
            "slug": plan.world_scope.slug,
            "title": map_report.title,
            "countries": list(plan.world_scope.countries),
        },
        "regions": {
            scope.slug: {
                "directory": str(regional_output_dirs[scope.slug]),
                "slug": scope.slug,
                "title": scope.map_title,
                "countries": list(scope.countries),
            }
            for scope in plan.regional_scopes
            if scope.slug in regional_output_dirs
        },
        "countries": {
            scope.slug: {
                "directory": str(country_output_dirs[scope.slug]),
                "country": scope.countries[0],
                "parent_scope": scope.parent_key,
            }
            for scope in plan.country_scopes
            if scope.slug in country_output_dirs
        },
    }
    payload["artifacts"] = {
        "world_bundle": {
            "slug": map_report.slug,
            "directory": str(report.shared_map_dir),
            "bundle_manifest": f"{map_report.slug}_bundle.json",
            "summary_json": f"{map_report.slug}_summary.json",
        },
        "regional_bundles": geography_bundles["regions"],
        "animal_output_audit_json": "animal_output_audit.json",
        "animal_output_audit_markdown": "animal_output_audit.md",
        "publication_geography_registry_json": "publication_geography_registry.json",
        "publication_geography_registry_markdown": "publication_geography_registry.md",
        "publication_geography_subset_validation_json": "publication_geography_subset_validation.json",
        "publication_geography_subset_validation_markdown": "publication_geography_subset_validation.md",
        "publication_country_onboarding_contract_json": "publication_country_onboarding_contract.json",
        "publication_country_onboarding_contract_markdown": "publication_country_onboarding_contract.md",
        "public_animal_reporting": scientific_artifacts or {},
        "repository_truth": repository_truth_artifacts or {},
        "country_bundles": {
            scope.slug: {
                "directory": str(country_output_dirs[scope.slug]),
                "bundle_manifest": f"{scope.slug}_aadr_{report.version}_bundle.json",
                "summary_json": f"{scope.slug}_aadr_{report.version}_summary.json",
                "parent_scope": scope.parent_key,
            }
            for scope in plan.country_scopes
            if scope.slug in country_output_dirs
        },
    }
    payload["geography_bundles"] = geography_bundles
    return payload


__all__ = ["build_published_reports_summary"]
