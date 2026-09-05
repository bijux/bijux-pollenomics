from __future__ import annotations


from tests.support.repository import REPOSITORY_ROOT
import unittest

import pytest

from bijux_pollenomics.adna.projects.evidence.localities import (
    build_project_locality_substitution_ledger,
    build_project_locality_worksheet_rows,
    build_project_sample_locality_evidence_rows,
    build_sample_locality_conflict_ledger,
    build_sample_locality_manual_curation_workflow_rows,
)

pytestmark = pytest.mark.generated_artifacts


class AdnaProjectSampleLocalityEvidenceUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = REPOSITORY_ROOT / "data"

    def test_horse_project_locality_packets_keep_sample_owned_site_traceability(
        self,
    ) -> None:
        rows = build_project_sample_locality_evidence_rows(self.data_root, "PRJEB31613")

        self.assertEqual(len(rows), 244)
        uppsala = next(
            row
            for row in rows
            if row["preferred_sample_label"] == "Uppsala_Upps02_1317"
        )
        self.assertEqual(uppsala["assigned_locality_text"], "Uppsala")
        self.assertEqual(uppsala["assigned_locality_class"], "excavation_site")
        self.assertEqual(uppsala["locality_evidence_bucket"], "exact_site_evidence")
        self.assertEqual(uppsala["evidence_source_surface"], "supplementary_table")
        self.assertEqual(uppsala["coordinate_confidence"], "exact")

    def test_experiment_only_archive_evidence_does_not_become_locality_packets(
        self,
    ) -> None:
        rows = build_project_sample_locality_evidence_rows(self.data_root, "SRP073444")

        self.assertEqual(rows, ())

    def test_baltic_sheep_locality_worksheet_exposes_sample_owned_sites(
        self,
    ) -> None:
        rows = build_project_locality_worksheet_rows(self.data_root, "PRJEB59481")

        self.assertEqual(len(rows), 8)
        self.assertEqual(
            {row["source_surface"] for row in rows},
            {"coordinate_resolution", "supplementary_table"},
        )
        sample_owned = {
            row["resolved_locality_text"]: row["supporting_sample_count"]
            for row in rows
            if row["source_claim_scope"] == "sample_owned_locality"
        }
        self.assertEqual(sample_owned, {"Kastelholm": 2, "Stora Förvar": 3})
        self.assertTrue(
            all(
                row["locality_class"] == "excavation_site"
                for row in rows
                if row["source_claim_scope"] == "sample_owned_locality"
            )
        )
        self.assertFalse(any("Baltic Sea Region" in str(row) for row in rows))

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
        self.assertFalse(
            any(
                row["project_accession"] == "KU605068-KU605080"
                and row["publication_blocked"]
                for row in substitution
            )
        )


if __name__ == "__main__":
    unittest.main()
