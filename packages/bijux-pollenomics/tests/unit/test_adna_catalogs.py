from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.adna import (
    build_cross_species_archive_inventory,
    build_cross_species_bibliography,
    build_cross_species_coverage_dashboard,
    build_public_animal_output_audit,
    build_shipped_adna_product_audit,
    build_species_freshness_table,
)
from bijux_pollenomics.adna.catalogs import render_public_animal_output_audit_markdown
from bijux_pollenomics.adna.tracked_data import materialize_tracked_species_adna


class AdnaCatalogUnitTests(unittest.TestCase):
    def test_cross_species_bibliography_deduplicates_shared_literature(self) -> None:
        bibliography = build_cross_species_bibliography()

        self.assertTrue(
            any(
                row["paper_doi"] == "10.1038/s41586-021-04018-9"
                and "Equus caballus" in row["species_latin_names"]
                for row in bibliography
            )
        )

    def test_cross_species_archive_inventory_reports_access_policies(self) -> None:
        inventory = build_cross_species_archive_inventory()

        self.assertTrue(
            any(
                row["project_accession"] == "PRJEB22390"
                and row["access_policy"] == "public_downloadable"
                for row in inventory
            )
        )

    def test_cross_species_freshness_table_tracks_nordic_unmapped_leads(self) -> None:
        freshness_rows = build_species_freshness_table()
        sheep_row = next(
            row
            for row in freshness_rows
            if row["species_latin_name"] == "Ovis aries"
        )

        self.assertTrue(sheep_row["has_nordic_unmapped_lead"])
        self.assertEqual(sheep_row["inventory_last_checked_on"], "2026-05-07")

    def test_cross_species_dashboard_and_public_audit_expose_missing_public_outputs(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            report_root = Path(tmp) / "docs" / "report"
            materialize_tracked_species_adna(data_root)

            dashboard = build_cross_species_coverage_dashboard(data_root, report_root)
            product_audit = build_shipped_adna_product_audit(data_root, report_root)
            public_audit = build_public_animal_output_audit(data_root, report_root)
            markdown = render_public_animal_output_audit_markdown(public_audit)

        horse_row = next(
            row
            for row in dashboard["rows"]
            if row["species_latin_name"] == "Equus caballus"
        )
        self.assertTrue(horse_row["raw_inventory_present"])
        self.assertTrue(horse_row["raw_source_snapshot_present"])
        self.assertTrue(horse_row["citation_manifest_present"])
        self.assertEqual(horse_row["country_output_count"], 0)
        self.assertEqual(horse_row["atlas_layer_count"], 0)
        self.assertEqual(product_audit["species_with_source_snapshots"], 10)
        self.assertIn("Equus caballus", product_audit["missing_public_outputs"])
        self.assertIn("ships no mapped non-human animal atlas layers", markdown)

    def test_public_animal_output_audit_counts_species_layers_from_shipped_atlas_summary(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            report_root = Path(tmp) / "docs" / "report"
            materialize_tracked_species_adna(data_root)
            atlas_root = report_root / "nordic-atlas"
            atlas_root.mkdir(parents=True, exist_ok=True)
            (atlas_root / "README.md").write_text("# Nordic Evidence Atlas\n", encoding="utf-8")
            (atlas_root / "nordic-atlas_summary.json").write_text(
                """
{
  "animal_atlas": {
    "species_layers": [
      {"latin_name": "Ovis aries", "common_name": "sheep", "animal_scope": "domesticated_core", "locality_count": 1},
      {"latin_name": "Rangifer tarandus", "common_name": "reindeer", "animal_scope": "comparator", "locality_count": 1}
    ]
  }
}
""".strip(),
                encoding="utf-8",
            )

            public_audit = build_public_animal_output_audit(data_root, report_root)
            markdown = render_public_animal_output_audit_markdown(public_audit)

        sheep_row = next(
            row
            for row in public_audit["species_rows"]
            if row["species_latin_name"] == "Ovis aries"
        )
        self.assertEqual(sheep_row["atlas_layer_count"], 1)
        self.assertIn("now ships `2` mapped non-human animal atlas layer rows", markdown)


if __name__ == "__main__":
    unittest.main()
