from __future__ import annotations

from bijux_pollenomics.governance import (
    build_repository_recovery_review,
    build_repository_truth_posture,
    render_repository_recovery_review_markdown,
    render_repository_truth_posture_markdown,
)

from .support import RepositoryTruthTestCase


class RepositoryPostureTests(RepositoryTruthTestCase):
    def test_truth_posture_names_primary_scope_and_current_claim_freeze_reasons(
        self,
    ) -> None:
        payload = build_repository_truth_posture(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        markdown = render_repository_truth_posture_markdown(payload)

        self.assertEqual(payload["schema_version"], "repository-truth-posture.v2")
        self.assertEqual(
            payload["primary_domains"],
            ["pollen_context", "environmental_context"],
        )
        self.assertEqual(payload["counts"]["tracked_paper_count"], 18)
        self.assertEqual(payload["counts"]["papers_with_archived_supplements"], 18)
        self.assertEqual(
            payload["counts"]["papers_with_local_reference_supplements"], 0
        )
        self.assertEqual(payload["counts"]["published_atlas_point_count"], 271)
        self.assertTrue(
            any(
                "unresolved" in row or "refused" in row
                for row in payload["claim_freeze_reasons"]
            )
        )
        self.assertIn("# Repository truth posture", markdown)
        self.assertIn("Do Not Repeat", markdown)

    def test_recovery_review_reflects_animal_evidence_and_docs_scope(
        self,
    ) -> None:
        payload = build_repository_recovery_review(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        markdown = render_repository_recovery_review_markdown(payload)

        self.assertEqual(payload["schema_version"], "repository-recovery-review.v2")
        animal_row = next(
            row
            for row in payload["rows"]
            if row["surface_key"] == "ancient_dna_context"
        )
        docs_row = next(
            row
            for row in payload["rows"]
            if row["surface_key"] == "documentation_architecture"
        )
        self.assertEqual(payload["overall_recovery_posture"], "moderate_recovery")
        self.assertEqual(animal_row["data_completeness"], 4)
        self.assertEqual(docs_row["documentation_clarity"], 4)
        self.assertIn("| Ancient DNA context | 4 |", markdown)
