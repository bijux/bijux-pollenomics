from __future__ import annotations

from pathlib import Path
import unittest

from bijux_pollenomics.adna.project_sample_locality_evidence import (
    build_project_locality_substitution_ledger,
    build_project_locality_worksheet_rows,
    build_project_sample_locality_evidence_rows,
    build_sample_locality_conflict_ledger,
    build_sample_locality_manual_curation_workflow_rows,
)


class AdnaProjectSampleLocalityEvidenceUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = Path(__file__).resolve().parents[4] / "data"

    def test_horse_project_locality_packets_keep_sample_owned_site_traceability(self) -> None:
        rows = build_project_sample_locality_evidence_rows(self.data_root, "PRJEB31613")

        self.assertEqual(len(rows), 244)
        uppsala = next(
            row for row in rows if row["preferred_sample_label"] == "Uppsala_Upps02_1317"
        )
        self.assertEqual(uppsala["assigned_locality_text"], "Uppsala")
        self.assertEqual(uppsala["assigned_locality_class"], "excavation_site")
        self.assertEqual(uppsala["locality_evidence_bucket"], "exact_site_evidence")
        self.assertEqual(uppsala["evidence_source_surface"], "supplementary_table")
        self.assertEqual(uppsala["coordinate_confidence"], "exact")

    def test_context_only_sheep_project_locality_worksheet_keeps_broader_classes_visible(
        self,
    ) -> None:
        rows = build_project_locality_worksheet_rows(self.data_root, "PRJEB59481")

        self.assertEqual(len(rows), 3)
        self.assertEqual(
            {row["source_surface"] for row in rows},
            {"coordinate_resolution", "crossref_metadata"},
        )
        self.assertTrue(all(row["locality_class"] == "broader_locality" for row in rows))
        self.assertTrue(
            any(
                row["source_claim_scope"] == "resolved_place_string"
                and row["resolved_locality_text"]
                == "Baltic Sea Region short-tailed sheep context"
                for row in rows
            )
        )

    def test_conflict_curation_and_substitution_surfaces_flag_blocked_multi_sample_projects(
        self,
    ) -> None:
        conflicts = build_sample_locality_conflict_ledger(self.data_root)
        curation = build_sample_locality_manual_curation_workflow_rows(self.data_root)
        substitution = build_project_locality_substitution_ledger(self.data_root)

        self.assertTrue(
            any(
                row["project_accession"] == "SRS1407451"
                and row["conflicting_source_surface"] == "article_text"
                for row in conflicts
            )
        )
        self.assertTrue(
            any(
                row["project_accession"] == "SRS1407451"
                and row["decision_status"] == "pending_manual_curation"
                for row in curation
            )
        )
        self.assertTrue(
            any(
                row["project_accession"] == "KU605068-KU605080"
                and row["publication_blocked"]
                and row["reason"]
                == "project_level_locality_row_cannot_stand_in_for_all_samples"
                for row in substitution
            )
        )


if __name__ == "__main__":
    unittest.main()
