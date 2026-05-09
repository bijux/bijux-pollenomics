from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..presentation.text import slugify

__all__ = [
    "AtlasBundlePaths",
    "CountryBundlePaths",
    "build_atlas_bundle_paths",
    "build_country_bundle_paths",
]


@dataclass(frozen=True)
class CountryBundlePaths:
    output_dir: Path
    slug: str
    version: str
    readme_path: Path
    bundle_manifest_path: Path
    samples_csv_path: Path
    localities_csv_path: Path
    samples_geojson_path: Path
    samples_markdown_path: Path
    summary_json_path: Path
    animal_summary_json_path: Path
    animal_samples_csv_path: Path
    animal_samples_markdown_path: Path
    animal_species_csv_path: Path
    animal_localities_geojson_path: Path
    animal_citations_markdown_path: Path
    animal_warnings_markdown_path: Path


@dataclass(frozen=True)
class AtlasBundlePaths:
    output_dir: Path
    slug: str
    version: str
    readme_path: Path
    bundle_manifest_path: Path
    map_html_path: Path
    samples_geojson_path: Path
    animal_localities_geojson_path: Path
    domesticated_animal_localities_geojson_path: Path
    comparator_animal_localities_geojson_path: Path
    animal_atlas_evidence_csv_path: Path
    animal_atlas_evidence_json_path: Path
    animal_point_traceability_json_path: Path
    map_point_traceability_json_path: Path
    map_point_traceability_markdown_path: Path
    map_publication_contract_json_path: Path
    map_publication_contract_markdown_path: Path
    candidate_sites_csv_path: Path
    candidate_sites_json_path: Path
    candidate_sites_markdown_path: Path
    candidate_site_sensitivity_json_path: Path
    candidate_site_sensitivity_markdown_path: Path
    candidate_ranking_engine_manifest_path: Path
    evidence_surface_json_path: Path
    evidence_surface_markdown_path: Path
    scientific_review_json_path: Path
    scientific_review_markdown_path: Path
    summary_json_path: Path


def build_country_bundle_paths(
    output_dir: Path, country: str, version: str
) -> CountryBundlePaths:
    """Build the stable artifact paths for one country bundle."""
    output_dir = Path(output_dir)
    country_slug = slugify(country)
    return CountryBundlePaths(
        output_dir=output_dir,
        slug=country_slug,
        version=version,
        readme_path=output_dir / "README.md",
        bundle_manifest_path=output_dir / f"{country_slug}_aadr_{version}_bundle.json",
        samples_csv_path=output_dir / f"{country_slug}_aadr_{version}_samples.csv",
        localities_csv_path=output_dir
        / f"{country_slug}_aadr_{version}_localities.csv",
        samples_geojson_path=output_dir
        / f"{country_slug}_aadr_{version}_samples.geojson",
        samples_markdown_path=output_dir / f"{country_slug}_aadr_{version}_samples.md",
        summary_json_path=output_dir / f"{country_slug}_aadr_{version}_summary.json",
        animal_summary_json_path=output_dir
        / f"{country_slug}_animal_adna_{version}_summary.json",
        animal_samples_csv_path=output_dir
        / f"{country_slug}_animal_adna_{version}_samples.csv",
        animal_samples_markdown_path=output_dir
        / f"{country_slug}_animal_adna_{version}_samples.md",
        animal_species_csv_path=output_dir
        / f"{country_slug}_animal_adna_{version}_species.csv",
        animal_localities_geojson_path=output_dir
        / f"{country_slug}_animal_adna_{version}_localities.geojson",
        animal_citations_markdown_path=output_dir
        / f"{country_slug}_animal_adna_{version}_citations.md",
        animal_warnings_markdown_path=output_dir
        / f"{country_slug}_animal_adna_{version}_warnings.md",
    )


def build_atlas_bundle_paths(
    output_dir: Path, slug: str, version: str
) -> AtlasBundlePaths:
    """Build the stable artifact paths for one atlas bundle."""
    output_dir = Path(output_dir)
    atlas_slug = slugify(slug)
    return AtlasBundlePaths(
        output_dir=output_dir,
        slug=atlas_slug,
        version=version,
        readme_path=output_dir / "README.md",
        bundle_manifest_path=output_dir / f"{atlas_slug}_bundle.json",
        map_html_path=output_dir / f"{atlas_slug}_map.html",
        samples_geojson_path=output_dir / f"{atlas_slug}_samples.geojson",
        animal_localities_geojson_path=output_dir
        / f"{atlas_slug}_animal_localities.geojson",
        domesticated_animal_localities_geojson_path=output_dir
        / f"{atlas_slug}_domesticated_animal_localities.geojson",
        comparator_animal_localities_geojson_path=output_dir
        / f"{atlas_slug}_comparator_animal_localities.geojson",
        animal_atlas_evidence_csv_path=output_dir
        / f"{atlas_slug}_animal_atlas_evidence.csv",
        animal_atlas_evidence_json_path=output_dir
        / f"{atlas_slug}_animal_atlas_evidence.json",
        animal_point_traceability_json_path=output_dir
        / f"{atlas_slug}_animal_point_traceability.json",
        map_point_traceability_json_path=output_dir
        / f"{atlas_slug}_point_traceability.json",
        map_point_traceability_markdown_path=output_dir
        / f"{atlas_slug}_point_traceability.md",
        map_publication_contract_json_path=output_dir
        / f"{atlas_slug}_map_publication_contract.json",
        map_publication_contract_markdown_path=output_dir
        / f"{atlas_slug}_map_publication_contract.md",
        candidate_sites_csv_path=output_dir / f"{atlas_slug}_candidate_sites.csv",
        candidate_sites_json_path=output_dir / f"{atlas_slug}_candidate_sites.json",
        candidate_sites_markdown_path=output_dir / f"{atlas_slug}_candidate_sites.md",
        candidate_site_sensitivity_json_path=output_dir
        / f"{atlas_slug}_candidate_site_sensitivity.json",
        candidate_site_sensitivity_markdown_path=output_dir
        / f"{atlas_slug}_candidate_site_sensitivity.md",
        candidate_ranking_engine_manifest_path=output_dir
        / f"{atlas_slug}_candidate_ranking_engine_manifest.json",
        evidence_surface_json_path=output_dir / f"{atlas_slug}_evidence_surface.json",
        evidence_surface_markdown_path=output_dir
        / f"{atlas_slug}_evidence_surface.md",
        scientific_review_json_path=output_dir / f"{atlas_slug}_scientific_review.json",
        scientific_review_markdown_path=output_dir
        / f"{atlas_slug}_scientific_review.md",
        summary_json_path=output_dir / f"{atlas_slug}_summary.json",
    )
