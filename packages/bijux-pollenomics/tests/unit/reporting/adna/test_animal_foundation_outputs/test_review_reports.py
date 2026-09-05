from __future__ import annotations


import pytest

from bijux_pollenomics.reporting.adna.foundation_outputs.drift import (
    build_animal_cross_surface_drift_report,
)
from bijux_pollenomics.reporting.adna.foundation_outputs.review import (
    build_animal_point_evidence_review,
    build_animal_project_publication_gap_review,
    build_animal_scientific_caveat_ledger,
)
from bijux_pollenomics.reporting.adna.foundation_outputs.validation import (
    build_animal_foundation_validation_report,
)
from .support import AnimalFoundationOutputsTestCase

pytestmark = pytest.mark.generated_artifacts


class AnimalFoundationReviewReportTests(AnimalFoundationOutputsTestCase):
    def test_foundation_validation_exposes_structural_gaps_without_hiding_traceability(
        self,
    ) -> None:
        payload = build_animal_foundation_validation_report(
            data_root=self.data_root,
            report_root=self.report_root,
        )

        self.assertEqual(payload["schema_version"], "animal-foundation-validation.v1")
        paper_linkage_check = next(
            row
            for row in payload["checks"]
            if row["check_id"] == "sample_paper_linkage_present"
        )
        supplement_check = next(
            row
            for row in payload["checks"]
            if row["check_id"] == "supplement_required_projects_archived"
        )
        traceability_check = next(
            row
            for row in payload["checks"]
            if row["check_id"] == "atlas_rows_keep_traceability"
        )
        self.assertFalse(payload["overall_ok"])
        self.assertFalse(paper_linkage_check["passed"])
        self.assertTrue(supplement_check["passed"])
        self.assertTrue(traceability_check["passed"])

    def test_cross_surface_drift_report_stays_clean_for_current_shipped_rows(
        self,
    ) -> None:
        payload = build_animal_cross_surface_drift_report(
            data_root=self.data_root,
            report_root=self.report_root,
        )

        self.assertEqual(payload["schema_version"], "animal-cross-surface-drift.v1")
        self.assertEqual(len(payload["rows"]), 9)
        self.assertFalse(payload["drift_detected"])

    def test_scientific_caveat_ledger_groups_current_weak_points(self) -> None:
        payload = build_animal_scientific_caveat_ledger(self.data_root)

        self.assertEqual(
            payload["schema_version"], "animal-scientific-caveat-ledger.v1"
        )
        self.assertGreater(payload["summary"]["unreadable_table_count"], 0)
        self.assertGreater(payload["summary"]["uncertain_site_assignment_count"], 0)
        self.assertGreater(payload["summary"]["region_only_geography_count"], 0)

    def test_point_evidence_review_keeps_sample_site_and_coordinate_support_together(
        self,
    ) -> None:
        payload = build_animal_point_evidence_review(
            data_root=self.data_root,
            report_root=self.report_root,
        )

        self.assertEqual(payload["schema_version"], "animal-point-evidence-review.v1")
        self.assertEqual(payload["row_count"], 233)
        self.assertTrue(all(row["sample_rows"] for row in payload["rows"]))
        first_row = payload["rows"][0]
        self.assertTrue(first_row["sample_rows"])
        self.assertTrue(first_row["site_evidence"])
        self.assertTrue(first_row["coordinate_provenance"])

    def test_project_publication_gap_review_explains_non_published_projects(
        self,
    ) -> None:
        payload = build_animal_project_publication_gap_review(
            data_root=self.data_root,
            report_root=self.report_root,
        )

        self.assertEqual(
            payload["schema_version"],
            "animal-project-publication-gap-review.v1",
        )
        self.assertGreater(payload["row_count"], 0)
        self.assertTrue(
            any(
                row["absence_stage"]
                in {
                    "paper_or_metadata_capture",
                    "supplement_capture",
                    "site_extraction",
                    "coordinate_resolution",
                    "comparator_context_only",
                }
                for row in payload["rows"]
            )
        )
