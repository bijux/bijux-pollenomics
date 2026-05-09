from __future__ import annotations

from ...models import MultiCountryMapReport
from ..paths import AtlasBundlePaths


def build_multi_country_map_summary(
    report: MultiCountryMapReport,
    bundle_paths: AtlasBundlePaths,
    extra_artifacts: list[tuple[str, str]],
    map_publication_contract: dict[str, object],
    animal_atlas_summary: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build a machine-readable summary for one shared map bundle."""
    artifacts: dict[str, object] = {
        "bundle_manifest": bundle_paths.bundle_manifest_path.name,
        "readme": bundle_paths.readme_path.name,
        "map_html": bundle_paths.map_html_path.name,
        "samples_geojson": bundle_paths.samples_geojson_path.name,
        "map_publication_contract_json": bundle_paths.map_publication_contract_json_path.name,
        "map_publication_contract_markdown": bundle_paths.map_publication_contract_markdown_path.name,
        "point_traceability_json": bundle_paths.map_point_traceability_json_path.name,
        "point_traceability_markdown": bundle_paths.map_point_traceability_markdown_path.name,
        "evidence_surface_json": bundle_paths.evidence_surface_json_path.name,
        "evidence_surface_markdown": bundle_paths.evidence_surface_markdown_path.name,
        "scientific_review_json": bundle_paths.scientific_review_json_path.name,
        "scientific_review_markdown": bundle_paths.scientific_review_markdown_path.name,
        "summary_json": bundle_paths.summary_json_path.name,
        "extra_files": [
            {"label": label, "filename": filename}
            for label, filename in extra_artifacts
        ],
    }
    if animal_atlas_summary and int(animal_atlas_summary.get("total_locality_points", 0)) > 0:
        artifacts.update(
            {
                "animal_localities_geojson": bundle_paths.animal_localities_geojson_path.name,
                "domesticated_animal_localities_geojson": (
                    bundle_paths.domesticated_animal_localities_geojson_path.name
                ),
                "comparator_animal_localities_geojson": (
                    bundle_paths.comparator_animal_localities_geojson_path.name
                ),
                "animal_atlas_evidence_csv": bundle_paths.animal_atlas_evidence_csv_path.name,
                "animal_atlas_evidence_json": bundle_paths.animal_atlas_evidence_json_path.name,
                "animal_point_traceability_json": (
                    bundle_paths.animal_point_traceability_json_path.name
                ),
            }
        )
    return {
        "schema_version": "geographic-evidence-surface-summary.v1",
        "title": report.title,
        "slug": report.slug,
        "version": report.version,
        "generated_on": report.generated_on,
        "scope_key": report.scope_key,
        "scope_label": report.scope_label or report.title,
        "scope_kind": report.scope_kind,
        "parent_scope_key": report.parent_scope_key,
        "countries": list(report.countries),
        "country_sample_counts": report.country_sample_counts,
        "total_unique_samples": report.total_unique_samples,
        "output_dir": str(report.output_dir),
        "artifacts": artifacts,
        "map_publication_contract": map_publication_contract,
        "animal_atlas": animal_atlas_summary or {},
    }


def build_multi_country_bundle_manifest(
    report: MultiCountryMapReport,
    bundle_paths: AtlasBundlePaths,
    extra_artifacts: list[tuple[str, str]],
    map_publication_contract: dict[str, object],
    animal_atlas_summary: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build a machine-readable manifest for one atlas bundle."""
    artifacts: dict[str, object] = {
        "readme": bundle_paths.readme_path.name,
        "map_html": bundle_paths.map_html_path.name,
        "samples_geojson": bundle_paths.samples_geojson_path.name,
        "map_publication_contract_json": bundle_paths.map_publication_contract_json_path.name,
        "map_publication_contract_markdown": bundle_paths.map_publication_contract_markdown_path.name,
        "point_traceability_json": bundle_paths.map_point_traceability_json_path.name,
        "point_traceability_markdown": bundle_paths.map_point_traceability_markdown_path.name,
        "candidate_sites_csv": bundle_paths.candidate_sites_csv_path.name,
        "candidate_sites_json": bundle_paths.candidate_sites_json_path.name,
        "candidate_sites_markdown": bundle_paths.candidate_sites_markdown_path.name,
        "candidate_site_sensitivity_json": bundle_paths.candidate_site_sensitivity_json_path.name,
        "candidate_site_sensitivity_markdown": bundle_paths.candidate_site_sensitivity_markdown_path.name,
        "candidate_ranking_engine_manifest": bundle_paths.candidate_ranking_engine_manifest_path.name,
        "evidence_surface_json": bundle_paths.evidence_surface_json_path.name,
        "evidence_surface_markdown": bundle_paths.evidence_surface_markdown_path.name,
        "scientific_review_json": bundle_paths.scientific_review_json_path.name,
        "scientific_review_markdown": bundle_paths.scientific_review_markdown_path.name,
        "summary_json": bundle_paths.summary_json_path.name,
        "extra_files": [
            {"label": label, "filename": filename}
            for label, filename in extra_artifacts
        ],
    }
    if animal_atlas_summary and int(animal_atlas_summary.get("total_locality_points", 0)) > 0:
        artifacts.update(
            {
                "animal_localities_geojson": bundle_paths.animal_localities_geojson_path.name,
                "domesticated_animal_localities_geojson": (
                    bundle_paths.domesticated_animal_localities_geojson_path.name
                ),
                "comparator_animal_localities_geojson": (
                    bundle_paths.comparator_animal_localities_geojson_path.name
                ),
                "animal_atlas_evidence_csv": bundle_paths.animal_atlas_evidence_csv_path.name,
                "animal_atlas_evidence_json": bundle_paths.animal_atlas_evidence_json_path.name,
                "animal_point_traceability_json": (
                    bundle_paths.animal_point_traceability_json_path.name
                ),
            }
        )
    return {
        "schema_version": "geographic-evidence-surface-manifest.v1",
        "bundle_type": "geographic_evidence_surface",
        "title": report.title,
        "slug": report.slug,
        "version": report.version,
        "generated_on": report.generated_on,
        "scope_key": report.scope_key,
        "scope_label": report.scope_label or report.title,
        "scope_kind": report.scope_kind,
        "parent_scope_key": report.parent_scope_key,
        "countries": list(report.countries),
        "country_sample_counts": report.country_sample_counts,
        "total_unique_samples": report.total_unique_samples,
        "output_dir": str(report.output_dir),
        "artifacts": artifacts,
        "map_publication_contract": map_publication_contract,
        "animal_atlas": animal_atlas_summary or {},
    }


__all__ = ["build_multi_country_bundle_manifest", "build_multi_country_map_summary"]
