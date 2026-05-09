from __future__ import annotations

from collections import Counter
import unittest

from bijux_pollenomics.adna.sample_registry import build_species_curated_sample_rows


class AdnaSampleRegistryUnitTests(unittest.TestCase):
    def test_species_curated_sample_rows_cover_all_tracked_project_units(self) -> None:
        rows = build_species_curated_sample_rows("horse")

        self.assertEqual(
            Counter(row.project_accession for row in rows),
            Counter(
                {
                    "PRJEB10854": 1,
                    "PRJEB19970": 14,
                    "PRJEB22390": 42,
                    "PRJEB31613": 244,
                    "PRJEB44430": 248,
                    "PRJEB56293": 1,
                    "PRJEB7537": 1,
                    "PRJEB9799": 1,
                }
            ),
        )
        botai = next(
            row
            for row in rows
            if row.project_accession == "PRJEB22390" and row.site_label == "Botai"
        )
        self.assertEqual(botai.site_label, "Botai")
        self.assertEqual(botai.inclusion_status, "site_curated")

        nordic = next(
            row for row in rows if row.project_accession == "PRJEB31613" and row.site_label == "Uppsala"
        )
        self.assertEqual(nordic.political_entity, "Sweden")
        self.assertEqual(nordic.coordinate_basis, "supplementary_table_coordinates")
        self.assertEqual(nordic.chronology_text, "1217-1417 BP")

        ginnerup = next(
            row for row in rows if row.project_accession == "PRJEB44430" and row.site_label == "Ginnerup"
        )
        self.assertEqual(ginnerup.political_entity, "Denmark")
        self.assertEqual(ginnerup.latitude_text, "56.41134")
        self.assertEqual(ginnerup.longitude_text, "10.74481")
        self.assertEqual(ginnerup.chronology_text, "4961 BP")

    def test_species_curated_sample_rows_preserve_supplementary_path_when_archived(self) -> None:
        rows = build_species_curated_sample_rows("sheep")
        baltic = next(row for row in rows if row.project_accession == "PRJEB59481")

        self.assertEqual(baltic.paper_doi, "10.1093/gbe/evae114")
        self.assertEqual(baltic.inclusion_status, "nordic_lead_site_curated")
        self.assertEqual(baltic.supplementary_source, "")

    def test_species_curated_sample_rows_mark_comparator_context_explicitly(self) -> None:
        donkey_rows = build_species_curated_sample_rows("donkey")
        donkey = next(row for row in donkey_rows if row.project_accession == "PRJEB52849")
        reindeer_rows = build_species_curated_sample_rows("reindeer")
        reindeer = next(row for row in reindeer_rows if row.project_accession == "PRJEB60484")

        self.assertEqual(donkey.sample_basis, "project_accession_anchor")
        self.assertEqual(donkey.inclusion_status, "comparator_site_curated")
        self.assertEqual(reindeer.inclusion_status, "comparator_site_curated")
        self.assertIn("comparator", reindeer.inclusion_note.casefold())


if __name__ == "__main__":
    unittest.main()
