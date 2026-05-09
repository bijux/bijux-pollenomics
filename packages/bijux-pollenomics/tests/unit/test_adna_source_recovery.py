from __future__ import annotations

from pathlib import Path
import unittest

from bijux_pollenomics.adna.source_recovery import (
    ADNA_INTAKE_STAGE_KEYS,
    build_manual_curation_worklist,
    build_missing_source_queue,
    build_paper_expected_sample_yield_review,
    build_project_expected_sample_yield_review,
    build_project_recovery_dossier,
    build_project_recovery_stage_review,
    build_source_recovery_progress,
    build_source_recovery_release_guard,
    build_species_project_deficit_ledger,
)


class AdnaSourceRecoveryUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data_root = Path(__file__).resolve().parents[4] / "data"

    def test_project_recovery_stage_review_keeps_all_stage_keys_and_blocked_rows(
        self,
    ) -> None:
        payload = build_project_recovery_stage_review(self.data_root)

        self.assertEqual(
            payload["schema_version"],
            "animal-project-recovery-stage-review.v1",
        )
        self.assertGreater(payload["summary"]["blocked_projects"], 0)
        horse_row = next(
            row for row in payload["rows"] if row["project_accession"] == "PRJEB22390"
        )
        self.assertEqual(
            tuple(horse_row["stage_statuses"]),
            ADNA_INTAKE_STAGE_KEYS,
        )
        self.assertIn(horse_row["publication_readiness_status"], {"complete", "blocked", "not_required"})

    def test_expected_sample_yield_review_and_release_guard_surface_thin_recovery(
        self,
    ) -> None:
        payload = build_project_expected_sample_yield_review(self.data_root)
        guard = build_source_recovery_release_guard(self.data_root)

        self.assertEqual(
            payload["schema_version"],
            "animal-project-expected-sample-yield-review.v1",
        )
        self.assertGreater(
            payload["counts"]["projects_with_implausibly_low_recovery"],
            0,
        )
        self.assertFalse(guard["passing"])
        self.assertGreater(guard["implausibly_low_recovery_project_count"], 0)

    def test_paper_species_and_manual_work_surfaces_stay_actionable(self) -> None:
        paper_payload = build_paper_expected_sample_yield_review(self.data_root)
        species_payload = build_species_project_deficit_ledger(self.data_root)
        worklist_payload = build_manual_curation_worklist(self.data_root)
        progress_payload = build_source_recovery_progress(self.data_root)
        missing_source_payload = build_missing_source_queue(self.data_root)

        self.assertEqual(
            paper_payload["schema_version"],
            "animal-paper-expected-sample-yield-review.v1",
        )
        self.assertTrue(
            any(
                row["projects_with_unknown_expected_total"] > 0
                for row in paper_payload["rows"]
            )
        )
        self.assertEqual(
            species_payload["schema_version"],
            "animal-species-project-deficit-ledger.v1",
        )
        self.assertIn("Equus caballus", species_payload["species_counts"])
        self.assertGreater(worklist_payload["row_count"], 0)
        self.assertGreater(progress_payload["project_counts"]["projects_with_sample_identity_rows"], 0)
        self.assertGreater(missing_source_payload["row_count"], 0)

    def test_project_recovery_dossier_collects_assets_gaps_and_manual_work(self) -> None:
        payload = build_project_recovery_dossier(self.data_root, "PRJEB36540")

        self.assertEqual(
            payload["schema_version"],
            "animal-project-recovery-dossier.v1",
        )
        self.assertTrue(payload["known_assets"])
        self.assertIn("stage_statuses", payload)
        self.assertIn("expected_contribution_surfaces", payload)
        self.assertIn("major_deficit_reasons", payload)


if __name__ == "__main__":
    unittest.main()
