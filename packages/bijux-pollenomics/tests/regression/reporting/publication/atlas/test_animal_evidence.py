from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import pytest

from bijux_pollenomics.reporting import (
    generate_multi_country_map,
)


from ..fixtures.aadr import write_anno
from ..fixtures.animal_adna import write_tracked_animal_species
from ..static_assets import read_static_atlas_payload_text


pytestmark = pytest.mark.generated_artifacts


class CountryReportTests(unittest.TestCase):
    def test_generate_multi_country_map_ships_public_animal_layers_and_filters(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "v62.0"
            output = Path(tmp) / "docs" / "report" / "nordic-atlas"
            context_root = Path(tmp) / "data"
            write_anno(
                root / "1240k" / "v62.0_1240k_public.anno",
                [
                    "SE1\tSE1\tSweden_Group\tUppsala\tSweden\t59.8586\t17.6389\tPaperA\t2022\t500 BCE\t2450\tAG\tF",
                ],
            )
            write_tracked_animal_species(
                context_root / "adna" / "species" / "ovis_aries",
                latin_name="Ovis aries",
                common_name="sheep",
                locality="Baltic sheep lead",
                political_entity="Sweden",
                project_accession="PRJEB59481",
                support_class="accepted",
                product_role="domesticated_core",
                nordic_inclusion=True,
                chronology_bucket="1001-3000 BP",
                paper_title="Baltic short-tailed sheep aDNA",
                paper_doi="10.1000/sheep",
            )
            write_tracked_animal_species(
                context_root / "adna" / "species" / "rangifer_tarandus",
                latin_name="Rangifer tarandus",
                common_name="reindeer",
                locality="Svalbard reindeer lead",
                political_entity="Norway",
                project_accession="PRJEB60484",
                support_class="comparator_only",
                product_role="comparator",
                nordic_inclusion=True,
                chronology_bucket="0-1000 BP",
                paper_title="Ancient reindeer context",
                paper_doi="10.1000/reindeer",
            )

            generate_multi_country_map(
                version_dir=root,
                countries=["Sweden", "Norway"],
                output_dir=output,
                title="Nordic Evidence Atlas",
                slug="nordic-atlas",
                context_root=context_root,
            )

            self.assertTrue(
                (output / "nordic-atlas_animal_localities.geojson").exists()
            )
            self.assertTrue(
                (
                    output / "nordic-atlas_domesticated_animal_localities.geojson"
                ).exists()
            )
            self.assertTrue(
                (output / "nordic-atlas_comparator_animal_localities.geojson").exists()
            )
            self.assertTrue(
                (output / "nordic-atlas_animal_atlas_evidence.csv").exists()
            )
            self.assertTrue(
                (output / "nordic-atlas_animal_atlas_evidence.json").exists()
            )
            self.assertTrue(
                (output / "nordic-atlas_animal_point_traceability.json").exists()
            )
            self.assertTrue((output / "nordic-atlas_point_traceability.json").exists())
            self.assertTrue(
                (output / "nordic-atlas_map_publication_contract.json").exists()
            )

            map_html = (output / "nordic-atlas_map.html").read_text(encoding="utf-8")
            atlas_payload_text = read_static_atlas_payload_text(output, "nordic-atlas")
            readme_text = (output / "README.md").read_text(encoding="utf-8")
            summary = json.loads(
                (output / "nordic-atlas_summary.json").read_text(encoding="utf-8")
            )
            animal_geojson = json.loads(
                (output / "nordic-atlas_animal_localities.geojson").read_text(
                    encoding="utf-8"
                )
            )
            map_contract = json.loads(
                (output / "nordic-atlas_map_publication_contract.json").read_text(
                    encoding="utf-8"
                )
            )

            self.assertIn("Animal Evidence", map_html)
            self.assertIn("Species Focus", map_html)
            self.assertIn("Animal Scope", map_html)
            self.assertIn("Coordinate Confidence", map_html)
            self.assertIn("Temporal Windows", map_html)
            self.assertIn("Nordic animal leads only", map_html)
            self.assertIn("Atlas-side summary", map_html)
            self.assertIn("Visible animal evidence", map_html)
            self.assertIn('id="animal-evidence-metrics"', map_html)
            self.assertIn('id="animal-evidence-confidence"', map_html)
            self.assertIn('id="animal-evidence-state"', map_html)
            self.assertIn("Domesticated animal aDNA", map_html)
            self.assertIn("Comparator animal aDNA", map_html)
            self.assertIn("data-animal-species", map_html)
            self.assertIn("data-animal-scope", map_html)
            self.assertIn("data-animal-confidence", map_html)
            self.assertIn("data-animal-temporal-window", map_html)
            self.assertIn("featureMatchesAnimalFilters", map_html)
            self.assertIn("summarizeAnimalMetrics", map_html)
            self.assertIn("renderAnimalEvidencePanel", map_html)
            self.assertIn("Coordinate trust", map_html)
            self.assertIn("Tracked species", map_html)
            self.assertIn("popup-section-title", map_html)
            self.assertIn("Citation and provenance", map_html)
            self.assertIn("Sample and locality detail", map_html)
            self.assertIn("Warnings and caveats", map_html)
            self.assertIn("Ovis aries", atlas_payload_text)
            self.assertIn("Rangifer tarandus", atlas_payload_text)
            self.assertIn("Baltic sheep lead", atlas_payload_text)
            self.assertIn("Svalbard reindeer lead", atlas_payload_text)

            self.assertIn("## Animal aDNA Layers", readme_text)
            self.assertIn("Public Animal Filters", readme_text)
            self.assertIn("Animal Inspection Surfaces", readme_text)
            self.assertIn("Visible Coordinate Confidence", readme_text)
            self.assertIn("Domesticated-core animal evidence", readme_text)
            self.assertIn("Comparator animal evidence", readme_text)
            self.assertIn("Nordic animal leads only", readme_text)
            self.assertIn(
                "Approximate or inferred coordinates remain visible", readme_text
            )
            self.assertIn("Map publication contract JSON", readme_text)
            self.assertIn("Point traceability JSON", readme_text)
            self.assertIn("Visible Layer Contract", readme_text)
            self.assertIn("shared_world_scale_layer", readme_text)

            self.assertEqual(summary["animal_atlas"]["total_species"], 2)
            self.assertEqual(summary["animal_atlas"]["domesticated_species_count"], 1)
            self.assertEqual(summary["animal_atlas"]["comparator_species_count"], 1)
            self.assertEqual(
                summary["artifacts"]["map_publication_contract_json"],
                "nordic-atlas_map_publication_contract.json",
            )
            self.assertEqual(
                summary["artifacts"]["point_traceability_json"],
                "nordic-atlas_point_traceability.json",
            )
            self.assertEqual(
                summary["artifacts"]["animal_localities_geojson"],
                "nordic-atlas_animal_localities.geojson",
            )
            self.assertEqual(
                summary["artifacts"]["animal_atlas_evidence_csv"],
                "nordic-atlas_animal_atlas_evidence.csv",
            )
            self.assertEqual(
                summary["artifacts"]["animal_atlas_evidence_json"],
                "nordic-atlas_animal_atlas_evidence.json",
            )
            self.assertEqual(
                summary["artifacts"]["animal_point_traceability_json"],
                "nordic-atlas_animal_point_traceability.json",
            )
            self.assertEqual(map_contract["default_basemap"], "street")
            self.assertIn("Species focus", summary["animal_atlas"]["filter_surfaces"])
            self.assertIn(
                "Coordinate confidence",
                summary["animal_atlas"]["filter_surfaces"],
            )
            self.assertIn(
                "Nordic animal leads only",
                summary["animal_atlas"]["filter_surfaces"],
            )
            self.assertIn(
                "Animal evidence summary panel",
                summary["animal_atlas"]["ui_surfaces"],
            )
            self.assertIn(
                "Citation-aware animal popups",
                summary["animal_atlas"]["ui_surfaces"],
            )
            self.assertEqual(
                summary["animal_atlas"]["direct_coordinate_feature_count"],
                0,
            )
            self.assertEqual(
                summary["animal_atlas"]["named_site_geocoded_feature_count"],
                2,
            )
            self.assertEqual(
                summary["animal_atlas"]["weaker_geography_feature_count"],
                0,
            )
            self.assertEqual(
                summary["animal_atlas"]["coordinate_confidence_counts"]["approximate"],
                2,
            )
            self.assertTrue(
                all(
                    row["applies_country_filter"]
                    for row in map_contract["layer_rows"]
                    if row["key"].startswith("animal-")
                )
            )

            self.assertEqual(len(animal_geojson["features"]), 2)
            sheep_properties = animal_geojson["features"][0]["properties"]
            self.assertIn("feature_id", sheep_properties)
            self.assertIn("evidence_row_id", sheep_properties)
            self.assertIn("site_record_id", sheep_properties)
            self.assertIn("sample_record_ids", sheep_properties)
            self.assertIn("coordinate_basis", sheep_properties)
            self.assertIn("source_artifact_path", sheep_properties)
