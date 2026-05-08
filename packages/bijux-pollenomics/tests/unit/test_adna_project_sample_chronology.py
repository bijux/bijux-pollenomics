from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import unittest

from bijux_pollenomics.adna.project_sample_chronology import (
    build_cross_project_sample_chronology_audit,
    build_project_chronology_completeness_rows,
    build_project_sample_chronology_review_rows,
    build_project_sample_chronology_rows,
    build_sample_chronology_ambiguity_ledger,
    build_sample_chronology_viewer_rows,
    build_species_chronology_completeness_rows,
)
from bijux_pollenomics.adna.project_sample_chronology import _resolve_chronology_source

CONFLICTING_CHRONOLOGY_CASES = (
    {
        "sample_text": "1200-1500 BP",
        "site_text": "900-1100 BP",
        "site_start_bp": 900,
        "site_end_bp": 1100,
        "expected_fragment": "interval",
    },
    {
        "sample_text": "Late Bronze Age",
        "site_text": "Early Iron Age",
        "site_start_bp": None,
        "site_end_bp": None,
        "expected_fragment": "wording",
    },
)


class AdnaProjectSampleChronologyUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = Path(__file__).resolve().parents[4] / "data"

    def test_sheep_project_sample_chronology_rows_publish_strengths_and_provenance(self) -> None:
        rows = build_project_sample_chronology_rows(self.data_root, "PRJEB36540")

        self.assertEqual(len(rows), 190)
        first = next(row for row in rows if row.preferred_sample_label == "BH 28")
        self.assertEqual(first.chronology_strength, "sample_owned_interval")
        self.assertEqual(first.chronology_normalization_status, "normalized_interval")
        self.assertIn("42003_2021_2794_MOESM4_ESM.zip", first.chronology_provenance_path)
        self.assertEqual(first.chronology_provenance_kind, "supplementary_spreadsheet_row")
        self.assertTrue(first.chronology_provenance_locator.startswith("Sheet1!row"))

    def test_horse_project_sample_chronology_rows_publish_sample_owned_bp_points(self) -> None:
        rows = build_project_sample_chronology_rows(self.data_root, "PRJEB22390")

        botai = next(row for row in rows if row.preferred_sample_label == "Botai 1 5500")
        self.assertEqual(botai.chronology_strength, "sample_owned_interval")
        self.assertEqual(botai.chronology_normalization_status, "normalized_point")
        self.assertEqual(botai.chronology_text, "5500 BP")
        self.assertEqual((botai.time_start_bp, botai.time_end_bp), (5500, 5500))
        self.assertIn("aao3297_tables15.xlsx", botai.chronology_provenance_path)

    def test_chronology_review_audit_and_completeness_surfaces_stay_reader_visible(self) -> None:
        review_rows = build_project_sample_chronology_review_rows(self.data_root)
        audit = build_cross_project_sample_chronology_audit(self.data_root)
        ambiguity_rows = build_sample_chronology_ambiguity_ledger(self.data_root)
        species_rows = build_species_chronology_completeness_rows(self.data_root)
        project_rows = build_project_chronology_completeness_rows(self.data_root)
        viewer_rows = build_sample_chronology_viewer_rows(self.data_root)

        self.assertEqual(len(review_rows), 40)
        sheep_review = next(
            row for row in review_rows if row["project_accession"] == "PRJEB36540"
        )
        self.assertEqual(sheep_review["sample_owned_interval_count"], 167)
        self.assertEqual(sheep_review["text_only_unparsed_count"], 13)
        self.assertEqual(audit["sample_row_count"], 249)
        self.assertEqual(audit["normalized_interval_count"], 156)
        self.assertEqual(audit["normalized_point_count"], 54)
        self.assertEqual(audit["unresolved_count"], 26)
        self.assertTrue(
            any(
                row["project_accession"] == "KU605068-KU605080"
                and row["chronology_strength"] == "unresolved"
                for row in ambiguity_rows
            )
        )
        sheep_species = next(
            row for row in species_rows if row["species_latin_name"] == "Ovis aries"
        )
        self.assertEqual(sheep_species["normalized_row_count"], 167)
        camel_project = next(
            row for row in project_rows if row["project_accession"] == "KU605068-KU605080"
        )
        self.assertEqual(camel_project["unresolved_count"], 13)
        horse_project = next(
            row for row in project_rows if row["project_accession"] == "PRJEB22390"
        )
        self.assertEqual(horse_project["normalized_row_count"], 42)
        self.assertEqual(len(viewer_rows), 249)

    def test_conflicting_chronology_corpus_surfaces_disagreement_notes(self) -> None:
        for case in CONFLICTING_CHRONOLOGY_CASES:
            master_row = SimpleNamespace(
                chronology_text=case["sample_text"],
                sample_lineage_path="data/adna/governance/source_library/projects/TEST/sample_master.csv",
                sample_lineage_locator="row:1",
                sample_lineage_excerpt=case["sample_text"],
            )
            site_row = SimpleNamespace(
                chronology_text=case["site_text"],
                time_start_bp=case["site_start_bp"],
                time_end_bp=case["site_end_bp"],
                source_artifact_path="data/adna/governance/source_library/papers/test/article.html",
                source_artifact_kind="article_or_archive_text",
                source_locator="body",
                exact_source_text=case["site_text"],
            )

            resolved = _resolve_chronology_source(
                master_row=master_row,
                site_row=site_row,
                dating_basis="mixed_radiocarbon_and_archaeological_context",
            )

            self.assertIn(case["expected_fragment"], resolved.chronology_conflict_note)
            self.assertEqual(resolved.chronology_strength[:12], "sample_owned")


if __name__ == "__main__":
    unittest.main()
