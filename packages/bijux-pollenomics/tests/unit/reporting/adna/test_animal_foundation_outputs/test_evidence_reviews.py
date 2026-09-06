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
        self.assertEqual(payload["row_count"], 1454)
        self.assertEqual(payload["normalization_counts"]["normalized_interval"], 328)
        self.assertEqual(payload["normalization_counts"]["normalized_point"], 533)
        self.assertEqual(payload["normalization_counts"]["unresolved"], 463)
        self.assertEqual(payload["precision_counts"]["contextual_interval"], 15)
        self.assertEqual(payload["comparability_counts"]["numeric_interval"], 749)
        self.assertEqual(
            payload["comparability_counts"]["numeric_interval_with_caveat"], 112
        )
        self.assertEqual(payload["comparability_counts"]["contextual_label_only"], 130)
        self.assertEqual(payload["comparability_counts"]["unresolved"], 463)
        pig_rows = [
            row for row in payload["rows"] if row["project_accession"] == "PRJEB30282"
        ]
        admitted_pig_rows = {
            row["repo_stable_sample_id"]: row
            for row in pig_rows
            if row["chronology_normalization_status"] == "normalized_point"
        }
        self.assertEqual(len(pig_rows), 343)
        self.assertEqual(
            sum(
                row["chronology_normalization_status"] == "unresolved"
                for row in pig_rows
            ),
            341,
        )
        self.assertEqual(
            {
                sample_id: (
                    row["chronology_text"],
                    row["time_start_bp"],
                    row["time_end_bp"],
                    row["chronology_evidence_class"],
                    row["chronology_precision_posture"],
                    row["dating_basis"],
                )
                for sample_id, row in admitted_pig_rows.items()
            },
            {
                "prjeb30282:samea5160867": (
                    "4700 BP",
                    4700,
                    4700,
                    "archaeological_context_date",
                    "sample_approximate_or_modeled",
                    "archaeological_context",
                ),
                "prjeb30282:samea5160868": (
                    "1000 BP",
                    1000,
                    1000,
                    "archaeological_context_date",
                    "sample_approximate_or_modeled",
                    "archaeological_context",
                ),
            },
        )
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
        self.assertEqual(payload["counts"]["published_atlas_point_count"], 271)
        self.assertEqual(payload["counts"]["mapped_sample_count"], 606)
        self.assertEqual(payload["counts"]["mapped_sample_share"], 0.4179)
        pig_points = [
            row
            for row in point_payload["rows"]
            if row["project_accession"] == "PRJEB30282"
        ]
        self.assertEqual(
            {
                (
                    row["locality"],
                    row["sample_rows"][0]["archive_native_sample_id"],
                    row["sample_rows"][0]["chronology"]["dating_basis"],
                )
                for row in pig_points
            },
            {
                ("Bundsø", "SAMEA5160867", "archaeological_context"),
                ("Trelleborg", "SAMEA5160868", "archaeological_context"),
            },
        )
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
