from __future__ import annotations

import pytest

from bijux_pollenomics.reporting.adna.foundation_outputs.chronology import (
    build_animal_sample_chronology_review,
)
from bijux_pollenomics.reporting.adna.foundation_outputs.recovery import (
    _mapped_sample_count,
    build_animal_intake_recovery_review,
    build_animal_sample_database_review,
)
from bijux_pollenomics.reporting.adna.foundation_outputs.review import (
    build_animal_point_evidence_review,
)

from .support import AnimalFoundationOutputsTestCase

pytestmark = pytest.mark.generated_artifacts


class AnimalFoundationEvidenceReviewTests(AnimalFoundationOutputsTestCase):
    def test_mapped_sample_count_uses_distinct_source_identities(self) -> None:
        payload = {
            "rows": [
                {
                    "sample_record_ids": ["sample:1", "sample:2"],
                },
                {
                    "sample_record_ids": ["sample:1"],
                },
            ]
        }

        self.assertEqual(_mapped_sample_count(payload), 2)

        with self.assertRaisesRegex(ValueError, "sample_record_ids must be a list"):
            _mapped_sample_count(
                {
                    "rows": [
                        {
                            "sample_record_ids": "sample:3",
                            "sample_rows": [
                                {"identity": {"stable_token": "must-not-fallback"}},
                            ],
                        }
                    ]
                }
            )

    def test_sample_chronology_review_keeps_current_governed_rows_reader_visible(
        self,
    ) -> None:
        payload = build_animal_sample_chronology_review(data_root=self.data_root)

        self.assertEqual(
            payload["schema_version"], "animal-sample-chronology-review.v1"
        )
        self.assertEqual(payload["row_count"], 1451)
        self.assertEqual(payload["normalization_counts"]["normalized_interval"], 753)
        self.assertEqual(payload["normalization_counts"]["normalized_point"], 480)
        self.assertEqual(payload["normalization_counts"]["unresolved"], 126)
        self.assertEqual(payload["precision_counts"]["contextual_interval"], 485)
        self.assertEqual(payload["comparability_counts"]["numeric_interval"], 748)
        self.assertEqual(
            payload["comparability_counts"]["numeric_interval_with_caveat"], 485
        )
        self.assertEqual(payload["comparability_counts"]["contextual_label_only"], 92)
        self.assertEqual(payload["comparability_counts"]["unresolved"], 126)
        self.assertTrue(
            any(
                row["project_accession"] == "PRJEB36540"
                and row["chronology_strength"] == "sample_owned_interval"
                for row in payload["rows"]
            )
        )

    def test_animal_intake_recovery_review_keeps_project_gap_surfaces_visible(
        self,
    ) -> None:
        payload = build_animal_intake_recovery_review(data_root=self.data_root)

        self.assertEqual(payload["schema_version"], "animal-intake-recovery-review.v1")
        self.assertEqual(
            payload["public_posture"],
            "sample_recovery_still_partial_and_project_gaps_explicit",
        )
        self.assertGreater(payload["stage_review"]["blocked_projects"], 0)
        self.assertTrue(payload["release_guard"]["passing"])
        self.assertEqual(
            payload["release_guard"]["implausibly_low_recovery_project_count"], 0
        )
        self.assertIn("source_recovery_progress", payload["direct_links"])
        self.assertTrue(payload["top_gap_projects"])

    def test_sample_database_review_packet_proves_sample_owned_public_posture(
        self,
    ) -> None:
        point_payload = build_animal_point_evidence_review(
            data_root=self.data_root,
            report_root=self.report_root,
        )
        intake_recovery_payload = build_animal_intake_recovery_review(
            data_root=self.data_root
        )
        payload = build_animal_sample_database_review(
            data_root=self.data_root,
            report_root=self.report_root,
            point_payload=point_payload,
            review_payload={"blockers": ["foundation_validation_not_yet_clean"]},
            intake_recovery_payload=intake_recovery_payload,
        )

        self.assertEqual(payload["schema_version"], "animal-sample-database-review.v1")
        self.assertEqual(
            payload["public_posture"],
            "partial_sample_owned_animal_evidence_surface",
        )
        self.assertTrue(payload["sample_database_claim_supported"])
        self.assertTrue(payload["nordic_view_supported_now"])
        self.assertFalse(payload["region_agnostic_contract_ready"])
        self.assertEqual(payload["counts"]["published_atlas_point_count"], 233)
        self.assertEqual(payload["counts"]["mapped_sample_count"], 554)
        self.assertEqual(payload["counts"]["mapped_sample_share"], 0.3818)
        self.assertEqual(payload["counts"]["papers_with_archived_supplements"], 18)
        self.assertGreater(payload["counts"]["locality_conflict_row_count"], 0)
        self.assertGreater(payload["counts"]["locality_dictionary_row_count"], 0)
        self.assertGreater(
            payload["locality_completeness_counts"]["exact_site_evidence_count"],
            0,
        )
        self.assertNotIn(
            "project_recovery_release_guard_still_failing",
            payload["posture_findings"],
        )
        self.assertNotIn(
            "supplement_backed_paper_coverage_still_too_low",
            payload["posture_findings"],
        )
        self.assertIn("sample_foundation_truth", payload["direct_links"])
        self.assertIn("locality_conflicts", payload["direct_links"])
        self.assertIn("chronology_precision_audit", payload["direct_links"])
        self.assertIn("source_recovery_progress", payload["direct_links"])
        self.assertGreater(payload["intake_recovery_counts"]["blocked_projects"], 0)
