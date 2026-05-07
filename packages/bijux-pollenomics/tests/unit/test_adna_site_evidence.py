from __future__ import annotations

import unittest

from bijux_pollenomics.adna.site_evidence import (
    build_species_site_evidence_rows,
    resolve_project_site_evidence,
)


class AdnaSiteEvidenceUnitTests(unittest.TestCase):
    def test_resolve_project_site_evidence_returns_exact_botai_quote(self) -> None:
        rows = resolve_project_site_evidence("PRJEB22390")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].site_label, "Botai culture steppe context")
        self.assertEqual(rows[0].source_support_status, "article_exact_quote")
        self.assertIn("horse husbandry", rows[0].exact_source_text)
        self.assertTrue(rows[0].source_artifact_path.endswith("article.html"))

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
