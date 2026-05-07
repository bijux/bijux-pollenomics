from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.adna import (
    build_coordinate_caveat_surface,
    build_cross_species_archive_inventory,
    build_cross_species_bibliography,
    build_cross_species_coverage_dashboard,
    build_cross_species_map_readiness,
    build_overbroad_site_ledger,
    build_public_animal_output_audit,
    build_shipped_adna_product_audit,
    build_species_freshness_table,
    build_unresolved_site_ledger,
)
from bijux_pollenomics.adna.catalogs import (
    render_coordinate_caveat_surface_markdown,
    render_coordinate_confidence_scale_markdown,
    render_public_animal_output_audit_markdown,
)
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

    def test_public_animal_output_audit_counts_country_outputs_from_country_summary(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            report_root = Path(tmp) / "docs" / "report"
            materialize_tracked_species_adna(data_root)
            sweden_root = report_root / "sweden"
            sweden_root.mkdir(parents=True, exist_ok=True)
            (sweden_root / "sweden_animal_adna_v66_summary.json").write_text(
                """
{
  "schema_version": "country-animal-adna-summary.v1",
  "country": "Sweden",
  "species_rows": [
    {
      "species_latin_name": "Ovis aries",
      "species_common_name": "sheep",
      "support_class": "accepted",
      "nordic_relevance": "nordic_lead"
    }
  ]
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
        self.assertEqual(sheep_row["country_output_count"], 1)
        self.assertIn("country-resolved animal output hits", markdown)

    def test_cross_species_map_readiness_reports_point_ready_and_refused_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            materialize_tracked_species_adna(data_root)

            readiness = build_cross_species_map_readiness(data_root)
            unresolved = build_unresolved_site_ledger(data_root)
            overbroad = build_overbroad_site_ledger(data_root)

        horse_row = next(
            row
            for row in readiness["rows"]
            if row["species_latin_name"] == "Equus caballus"
        )
        sheep_row = next(
            row
            for row in readiness["rows"]
            if row["species_latin_name"] == "Ovis aries"
        )
        self.assertEqual(readiness["totals"]["direct_coordinate_backed"], 0)
        self.assertEqual(readiness["totals"]["indirectly_geocoded"], 2)
        self.assertEqual(readiness["totals"]["refused_from_mapping"], 8)
        self.assertEqual(readiness["totals"]["unresolved"], 30)
        self.assertEqual(horse_row["indirectly_geocoded"], 1)
        self.assertEqual(sheep_row["refused_from_mapping"], 1)
        self.assertEqual(len(unresolved), 30)
        self.assertEqual(len(overbroad), 8)

    def test_coordinate_caveat_surface_groups_current_point_and_refused_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            materialize_tracked_species_adna(data_root)

            caveat_surface = build_coordinate_caveat_surface(data_root)
            markdown = render_coordinate_caveat_surface_markdown(caveat_surface)
            confidence_scale = render_coordinate_confidence_scale_markdown()

        self.assertEqual(caveat_surface["direct_coordinates"], [])
        self.assertEqual(len(caveat_surface["place_name_resolution"]), 2)
        self.assertEqual(len(caveat_surface["still_weak_geography"]), 8)
        self.assertIn("Botai archaeological site horse context", markdown)
        self.assertIn("Site 1040 near Wadi Halfa dromedary context", markdown)
        self.assertIn("Near East and Europe pig domestication transect", markdown)
        self.assertIn("Animal point publication is currently allowed only", confidence_scale)

    def test_materialized_sample_rows_require_matching_coordinate_provenance_for_mapping(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            materialize_tracked_species_adna(data_root)

            for species_root in (data_root / "adna").iterdir():
                if not species_root.is_dir() or species_root.name == "source_library":
                    continue
                if species_root.name == "homo_sapiens":
                    continue
                sample_payload = json.loads(
                    (species_root / "normalized" / "sample_records.json").read_text(
                        encoding="utf-8"
                    )
                )
                provenance_payload = json.loads(
                    (
                        species_root / "normalized" / "coordinate_provenance.json"
                    ).read_text(encoding="utf-8")
                )
                provenance_by_accession = {
                    row["project_accession"]: row
                    for row in provenance_payload["coordinate_provenance"]
                }
                for sample in sample_payload["samples"]:
                    provenance = provenance_by_accession.get(sample["project_accession"])
                    coordinates = sample["coordinates"]
                    has_coordinates = bool(
                        coordinates["latitude_text"] and coordinates["longitude_text"]
                    )
                    if has_coordinates:
                        self.assertIsNotNone(provenance, species_root.name)
                        self.assertEqual(provenance["mapping_posture"], "mappable_point")
                        self.assertTrue(provenance["coordinate_basis"])
                        self.assertTrue(coordinates["confidence"])
                    if provenance and provenance["mapping_posture"] == "refused_region_only":
                        self.assertFalse(has_coordinates)


if __name__ == "__main__":
    unittest.main()
