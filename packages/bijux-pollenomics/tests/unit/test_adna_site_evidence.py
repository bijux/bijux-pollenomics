from __future__ import annotations

import unittest

from bijux_pollenomics.adna.site_evidence import (
    build_species_site_evidence_rows,
    resolve_project_site_evidence,
)


class AdnaSiteEvidenceUnitTests(unittest.TestCase):
    def test_resolve_project_site_evidence_expands_botai_to_sample_owned_sites(self) -> None:
        rows = resolve_project_site_evidence("PRJEB22390")

        self.assertGreater(len(rows), 10)
        botai = next(row for row in rows if row.site_label == "Botai")
        self.assertEqual(botai.source_support_status, "supplementary_table_row")
        self.assertIn("Botai_1_5500", botai.exact_source_text)
        self.assertIn("aao3297_tables15.xlsx", botai.source_artifact_path)

    def test_resolve_project_site_evidence_prefers_direct_horse_sample_rows(self) -> None:
        rows = resolve_project_site_evidence("PRJEB31613")

        uppsala = next(row for row in rows if row.site_label == "Uppsala")
        self.assertEqual(uppsala.political_entity, "Sweden")
        self.assertEqual(uppsala.source_support_status, "supplementary_table_row")
        self.assertEqual(uppsala.coordinate_basis, "supplementary_table_coordinates")
        self.assertEqual(uppsala.latitude_text, "59.860999999999997")
        self.assertEqual(uppsala.longitude_text, "17.638999999999999")
        self.assertIn("Uppsala_Upps02_1317", uppsala.exact_source_text)

    def test_build_species_site_evidence_rows_keeps_requested_accession_order(self) -> None:
        rows = build_species_site_evidence_rows(
            ("PRJEB59481", "PRJEB60484", "unknown")
        )

        self.assertEqual(
            [row.project_accession for row in rows],
            ["PRJEB59481", "PRJEB60484"],
        )

    def test_cattle_site_evidence_marks_archive_backed_gap_explicitly(self) -> None:
        rows = resolve_project_site_evidence("PRJNA705960")

        self.assertEqual(rows[0].source_support_status, "archive_description_quote")
        self.assertIn("Galicia", rows[0].exact_source_text)
        self.assertIn("No local primary paper", rows[0].support_gap_note)
        self.assertIn("progenitor", rows[0].interpretation_note)

    def test_comparator_site_evidence_rows_stay_marked_as_comparators(self) -> None:
        reindeer = resolve_project_site_evidence("PRJEB60484")[0]
        donkey = resolve_project_site_evidence("PRJEB52849")[0]

        self.assertTrue(reindeer.comparator_context)
        self.assertTrue(donkey.comparator_context)
        self.assertEqual(reindeer.domestication_context, "comparator_context")
        self.assertEqual(donkey.domestication_context, "comparator_context")


if __name__ == "__main__":
    unittest.main()
