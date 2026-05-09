from __future__ import annotations

from collections import Counter
from pathlib import Path
import unittest

from bijux_pollenomics.adna import sample_master as sample_master_module
from bijux_pollenomics.adna.sample_master import (
    build_cross_project_sample_master_completeness,
    build_project_sample_master,
    build_project_sample_master_rows,
    build_sample_identity_ambiguity_ledger,
)


class AdnaSampleMasterUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = Path(__file__).resolve().parents[4] / "data"

    def test_archive_native_sample_master_expands_accession_ranges(self) -> None:
        rows = build_project_sample_master_rows(self.data_root, "KU605068-KU605080")

        self.assertEqual(len(rows), 13)
        self.assertEqual(rows[0].archive_native_sample_id, "KU605068")
        self.assertEqual(rows[-1].archive_native_sample_id, "KU605080")
        self.assertTrue(all(row.sample_evidence_status == "archive_native" for row in rows))
        self.assertTrue(all(row.sample_identity_resolution == "final" for row in rows))

    def test_sheep_project_sample_master_extracts_rows_from_supplementary_tables(self) -> None:
        rows = build_project_sample_master_rows(self.data_root, "PRJEB36540")

        self.assertGreater(len(rows), 10)
        first = rows[0]
        self.assertEqual(first.sample_evidence_status, "direct_table_extracted")
        self.assertEqual(first.sample_basis, "supplementary_table_sample_label_anchor")
        self.assertIn("42003_2021_2794_MOESM4_ESM.zip", first.sample_lineage_path)
        self.assertIn("Sheet1!row", first.sample_lineage_locator)
        self.assertEqual(first.sample_identity_resolution, "final")

    def test_horse_project_sample_master_merges_lab_and_panel_tables(self) -> None:
        rows = build_project_sample_master_rows(self.data_root, "PRJEB22390")

        self.assertEqual(len(rows), 42)
        botai = next(row for row in rows if row.archive_native_sample_id == "CGG_1_018173")
        self.assertEqual(botai.preferred_sample_label, "Botai 1 5500")
        self.assertEqual(botai.locality_text, "Botai")
        self.assertEqual(botai.chronology_text, "5500 BP")
        self.assertIn("aao3297_tables11.xlsx", botai.sample_lineage_path)
        self.assertIn("aao3297_tables15.xlsx", botai.sample_lineage_path)
        self.assertEqual(botai.sample_identity_resolution, "final")

    def test_horse_time_series_and_dom2_projects_publish_recovered_sample_rows(self) -> None:
        time_series_rows = build_project_sample_master_rows(self.data_root, "PRJEB31613")
        dom2_rows = build_project_sample_master_rows(self.data_root, "PRJEB44430")
        domestication_rows = build_project_sample_master_rows(self.data_root, "PRJEB19970")

        self.assertEqual(len(time_series_rows), 244)
        self.assertEqual(len(dom2_rows), 248)
        self.assertEqual(len(domestication_rows), 14)

        uppsala = next(
            row for row in time_series_rows if row.preferred_sample_label == "Uppsala_Upps02_1317"
        )
        self.assertEqual(uppsala.locality_text, "Uppsala")
        self.assertEqual(uppsala.political_entity, "Sweden")
        self.assertEqual(uppsala.latitude_text, "59.860999999999997")
        self.assertEqual(uppsala.longitude_text, "17.638999999999999")
        self.assertEqual(uppsala.chronology_text, "1217-1417 BP")

        ginnerup = next(
            row for row in dom2_rows if row.preferred_sample_label == "DJM130x6_Dan_m3011"
        )
        self.assertEqual(ginnerup.locality_text, "Ginnerup")
        self.assertEqual(ginnerup.political_entity, "Denmark")
        self.assertEqual(ginnerup.latitude_text, "56.41134")
        self.assertEqual(ginnerup.longitude_text, "10.74481")
        self.assertEqual(ginnerup.chronology_text, "4961 BP")
        self.assertEqual(ginnerup.archive_native_sample_id, "SAMEA9533224")

        berel = next(
            row for row in domestication_rows if row.preferred_sample_label == "Berel_BER01_A_2300"
        )
        self.assertEqual(berel.locality_text, "Berel'")
        self.assertEqual(berel.political_entity, "Kazakhstan")
        self.assertEqual(berel.chronology_text, "2300 BP")

    def test_goat_cattle_and_reindeer_projects_publish_source_backed_sample_rows(self) -> None:
        goat_rows = build_project_sample_master_rows(self.data_root, "PRJNA1328209")
        cattle_rows = build_project_sample_master_rows(self.data_root, "PRJNA705960")
        reindeer_rows = build_project_sample_master_rows(self.data_root, "PRJEB60484")

        self.assertEqual(len(goat_rows), 5)
        self.assertEqual(len(cattle_rows), 11)
        self.assertEqual(len(reindeer_rows), 20)

        qinghai = next(row for row in goat_rows if row.preferred_sample_label == "DC23")
        self.assertEqual(qinghai.locality_text, "Lake Qinghai basin")
        self.assertEqual(qinghai.chronology_text, "3480-3580 BP")
        self.assertIn("Supplementary_tables.xlsx", qinghai.sample_lineage_path)

        cattle_anchor = cattle_rows[0]
        self.assertEqual(cattle_anchor.sample_basis, "archive_project_sample_accession_anchor")
        self.assertEqual(cattle_anchor.sample_evidence_status, "archive_native")
        self.assertTrue(cattle_anchor.archive_native_sample_id.startswith("SAMN"))

        reindeer_anchor = reindeer_rows[0]
        self.assertEqual(reindeer_anchor.sample_basis, "archive_project_sample_accession_anchor")
        self.assertEqual(reindeer_anchor.sample_evidence_status, "archive_native")
        self.assertTrue(reindeer_anchor.archive_native_sample_id.startswith("SAMEA"))

    def test_horse_age_text_keeps_range_labels_stable(self) -> None:
        self.assertEqual(
            sample_master_module._format_horse_age_text("5500 - 5700"),
            "5500-5700 BP",
        )
        self.assertEqual(
            sample_master_module._format_horse_age_text("2300"),
            "2300 BP",
        )

    def test_project_sample_master_completeness_tracks_expected_and_recovered_counts(self) -> None:
        camel = build_project_sample_master(self.data_root, "KU605068-KU605080")

        self.assertEqual(camel.expected_sample_count, 13)
        self.assertEqual(camel.recovered_sample_count, 13)
        self.assertEqual(camel.final_sample_count, 13)
        self.assertEqual(camel.unresolved_sample_count, 0)
        self.assertTrue(camel.expected_sample_count_provenance)
        self.assertTrue(camel.expected_sample_count_artifact_path)

    def test_cross_project_completeness_and_ambiguity_ledgers_are_reader_visible(self) -> None:
        completeness_rows = build_cross_project_sample_master_completeness(self.data_root)
        ambiguity_rows = build_sample_identity_ambiguity_ledger(self.data_root)

        self.assertEqual(len(completeness_rows), 40)
        self.assertTrue(
            any(
                row["project_accession"] == "KU605068-KU605080"
                and row["expected_sample_count"] == 13
                and row["recovered_sample_count"] == 13
                for row in completeness_rows
            )
        )
        horse_counts = Counter(
            row["recovered_sample_count"]
            for row in completeness_rows
            if row["project_accession"] in {"PRJEB19970", "PRJEB22390", "PRJEB31613", "PRJEB44430"}
        )
        self.assertEqual(horse_counts, Counter({14: 1, 42: 1, 244: 1, 248: 1}))
        self.assertEqual(ambiguity_rows, ())


if __name__ == "__main__":
    unittest.main()
