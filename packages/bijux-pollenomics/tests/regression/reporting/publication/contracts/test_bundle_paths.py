from __future__ import annotations

from pathlib import Path
import unittest

import pytest

from bijux_pollenomics.reporting.bundles import (
    build_atlas_bundle_paths,
    build_country_bundle_paths,
)

pytestmark = pytest.mark.generated_artifacts


class CountryReportTests(unittest.TestCase):
    def test_bundle_path_builders_keep_artifact_names_stable(self) -> None:
        country_paths = build_country_bundle_paths(
            Path("/tmp/sweden"), "Sweden", "v62.0"
        )
        atlas_paths = build_atlas_bundle_paths(
            Path("/tmp/nordic-atlas"), "nordic-atlas", "v62.0"
        )

        self.assertEqual(
            country_paths.samples_csv_path.name, "sweden_aadr_v62.0_samples.csv"
        )
        self.assertEqual(
            country_paths.localities_csv_path.name, "sweden_aadr_v62.0_localities.csv"
        )
        self.assertEqual(
            country_paths.samples_markdown_path.name, "sweden_aadr_v62.0_samples.md"
        )
        self.assertEqual(
            country_paths.bundle_manifest_path.name, "sweden_aadr_v62.0_bundle.json"
        )
        self.assertEqual(
            country_paths.animal_summary_json_path.name,
            "sweden_animal_adna_v62.0_summary.json",
        )
        self.assertEqual(
            country_paths.animal_samples_csv_path.name,
            "sweden_animal_adna_v62.0_samples.csv",
        )
        self.assertEqual(
            country_paths.animal_samples_markdown_path.name,
            "sweden_animal_adna_v62.0_samples.md",
        )
        self.assertEqual(
            country_paths.animal_species_csv_path.name,
            "sweden_animal_adna_v62.0_species.csv",
        )
        self.assertEqual(
            country_paths.animal_localities_geojson_path.name,
            "sweden_animal_adna_v62.0_localities.geojson",
        )
        self.assertEqual(
            country_paths.animal_citations_markdown_path.name,
            "sweden_animal_adna_v62.0_citations.md",
        )
        self.assertEqual(
            country_paths.animal_warnings_markdown_path.name,
            "sweden_animal_adna_v62.0_warnings.md",
        )
        self.assertEqual(
            country_paths.lake_evidence_richness_json_path.name,
            "sweden_lake_evidence_richness_v62.0.json",
        )
        self.assertEqual(
            country_paths.lake_evidence_richness_registry_csv_path.name,
            "sweden_lake_evidence_richness_v62.0_registry.csv",
        )
        self.assertEqual(
            country_paths.lake_evidence_richness_scenarios_csv_path.name,
            "sweden_lake_evidence_richness_v62.0_scenarios.csv",
        )
        self.assertEqual(
            country_paths.lake_evidence_richness_bands_csv_path.name,
            "sweden_lake_evidence_richness_v62.0_bands.csv",
        )
        self.assertEqual(
            country_paths.lake_evidence_richness_geojson_path.name,
            "sweden_lake_evidence_richness_v62.0.geojson",
        )
        self.assertEqual(
            country_paths.lake_evidence_richness_map_html_path.name,
            "sweden_lake_evidence_richness_v62.0_map.html",
        )
        self.assertEqual(
            country_paths.lake_evidence_richness_markdown_path.name,
            "sweden_lake_evidence_richness_v62.0.md",
        )
        self.assertEqual(atlas_paths.map_html_path.name, "nordic-atlas_map.html")
        self.assertEqual(
            atlas_paths.map_static_assets_manifest_path.name,
            "nordic-atlas_map_assets.json",
        )
        self.assertEqual(
            atlas_paths.playback_storyboards_path.name,
            "nordic-atlas_playback_storyboards.json",
        )
        self.assertEqual(
            atlas_paths.samples_geojson_path.name, "nordic-atlas_samples.geojson"
        )
        self.assertEqual(
            atlas_paths.animal_localities_geojson_path.name,
            "nordic-atlas_animal_localities.geojson",
        )
        self.assertEqual(
            atlas_paths.domesticated_animal_localities_geojson_path.name,
            "nordic-atlas_domesticated_animal_localities.geojson",
        )
        self.assertEqual(
            atlas_paths.comparator_animal_localities_geojson_path.name,
            "nordic-atlas_comparator_animal_localities.geojson",
        )
        self.assertEqual(
            atlas_paths.animal_atlas_evidence_csv_path.name,
            "nordic-atlas_animal_atlas_evidence.csv",
        )
        self.assertEqual(
            atlas_paths.animal_atlas_evidence_json_path.name,
            "nordic-atlas_animal_atlas_evidence.json",
        )
        self.assertEqual(
            atlas_paths.animal_point_traceability_json_path.name,
            "nordic-atlas_animal_point_traceability.json",
        )
        self.assertEqual(
            atlas_paths.map_point_traceability_json_path.name,
            "nordic-atlas_point_traceability.json",
        )
        self.assertEqual(
            atlas_paths.map_point_traceability_markdown_path.name,
            "nordic-atlas_point_traceability.md",
        )
        self.assertEqual(
            atlas_paths.map_publication_contract_json_path.name,
            "nordic-atlas_map_publication_contract.json",
        )
        self.assertEqual(
            atlas_paths.map_publication_contract_markdown_path.name,
            "nordic-atlas_map_publication_contract.md",
        )
        self.assertEqual(
            atlas_paths.candidate_sites_csv_path.name,
            "nordic-atlas_candidate_sites.csv",
        )
        self.assertEqual(
            atlas_paths.candidate_sites_json_path.name,
            "nordic-atlas_candidate_sites.json",
        )
        self.assertEqual(
            atlas_paths.candidate_sites_markdown_path.name,
            "nordic-atlas_candidate_sites.md",
        )
        self.assertEqual(
            atlas_paths.candidate_site_sensitivity_json_path.name,
            "nordic-atlas_candidate_site_sensitivity.json",
        )
        self.assertEqual(
            atlas_paths.candidate_site_sensitivity_markdown_path.name,
            "nordic-atlas_candidate_site_sensitivity.md",
        )
        self.assertEqual(
            atlas_paths.candidate_ranking_engine_manifest_path.name,
            "nordic-atlas_candidate_ranking_engine_manifest.json",
        )
        self.assertEqual(
            atlas_paths.evidence_surface_json_path.name,
            "nordic-atlas_evidence_surface.json",
        )
        self.assertEqual(
            atlas_paths.evidence_surface_markdown_path.name,
            "nordic-atlas_evidence_surface.md",
        )
        self.assertEqual(
            atlas_paths.scientific_review_json_path.name,
            "nordic-atlas_scientific_review.json",
        )
        self.assertEqual(
            atlas_paths.scientific_review_markdown_path.name,
            "nordic-atlas_scientific_review.md",
        )
        self.assertEqual(
            atlas_paths.bundle_manifest_path.name, "nordic-atlas_bundle.json"
        )
        self.assertEqual(
            atlas_paths.summary_json_path.name, "nordic-atlas_summary.json"
        )
