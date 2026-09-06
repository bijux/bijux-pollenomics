from __future__ import annotations

from bijux_pollenomics.governance import (
    build_repository_docs_recovery_review,
    build_repository_docs_restoration_ledger,
    build_repository_docs_scope_validation,
    render_repository_docs_recovery_review_markdown,
    render_repository_docs_restoration_ledger_markdown,
    render_repository_docs_scope_validation_markdown,
)

from .support import RepositoryTruthTestCase


class RepositoryDocumentationTests(RepositoryTruthTestCase):
    def test_docs_recovery_surfaces_report_verified_replacements(
        self,
    ) -> None:
        ledger_payload = build_repository_docs_restoration_ledger(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        scope_payload = build_repository_docs_scope_validation(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        review_payload = build_repository_docs_recovery_review(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )

        self.assertEqual(
            ledger_payload["schema_version"],
            "repository-docs-restoration-ledger.v1",
        )
        self.assertEqual(
            scope_payload["schema_version"],
            "repository-docs-scope-validation.v1",
        )
        self.assertEqual(
            review_payload["schema_version"],
            "repository-docs-recovery-review.v1",
        )
        self.assertEqual(ledger_payload["row_count"], 68)
        self.assertEqual(ledger_payload["status_counts"]["verified_replacement"], 68)
        self.assertEqual(ledger_payload["status_counts"]["replacement_incomplete"], 0)
        self.assertTrue(scope_payload["overall_ok"])
        self.assertEqual(
            review_payload["overall_posture"],
            "moving_toward_elegant_correctness",
        )
        self.assertIn(
            "# Repository docs restoration ledger",
            render_repository_docs_restoration_ledger_markdown(ledger_payload),
        )
        self.assertIn(
            "# Repository docs scope validation",
            render_repository_docs_scope_validation_markdown(scope_payload),
        )
        self.assertIn(
            "# Repository docs recovery review",
            render_repository_docs_recovery_review_markdown(review_payload),
        )
