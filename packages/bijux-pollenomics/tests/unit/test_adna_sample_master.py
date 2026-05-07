from __future__ import annotations

from pathlib import Path
import unittest

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
        self.assertEqual(ambiguity_rows, ())


if __name__ == "__main__":
    unittest.main()
