from __future__ import annotations

import unittest

from bijux_pollenomics.adna.sample_registry import build_species_curated_sample_rows


class AdnaSampleRegistryUnitTests(unittest.TestCase):
    def test_species_curated_sample_rows_cover_all_tracked_project_units(self) -> None:
        rows = build_species_curated_sample_rows("horse")

        self.assertEqual(
            [row.project_accession for row in rows],
            [
                "PRJEB10854",
                "PRJEB19970",
                "PRJEB22390",
                "PRJEB31613",
                "PRJEB44430",
                "PRJEB56293",
                "PRJEB7537",
                "PRJEB9799",
            ],
        )
        botai = next(row for row in rows if row.project_accession == "PRJEB22390")
        self.assertEqual(botai.site_label, "Botai archaeological site horse context")
        self.assertEqual(botai.inclusion_status, "site_curated")

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
        self.assertIn("comparator", reindeer.inclusion_note)


if __name__ == "__main__":
    unittest.main()
