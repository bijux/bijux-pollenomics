from __future__ import annotations

import json
from pathlib import Path
import tempfile

from bijux_pollenomics.reporting.review import publish_repository_truth_outputs

from .support import RepositoryTruthTestCase


class RepositoryTruthPublicationTests(RepositoryTruthTestCase):
    def test_publish_repository_truth_outputs_writes_all_truth_packets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "report"
            output_root.mkdir(parents=True, exist_ok=True)
            for name in (
                "animal_sample_database_review.json",
                "animal_publication_release_gate.json",
            ):
                (output_root / name).write_text(
                    (self.report_root / name).read_text(encoding="utf-8"),
                    encoding="utf-8",
                )

            artifacts = publish_repository_truth_outputs(
                output_root,
                data_root=self.data_root,
                docs_root=self.docs_root,
            )

            self.assertIn("repository_truth_posture_json", artifacts)
            self.assertIn("repository_claim_audit_markdown", artifacts)
            self.assertIn("repository_source_family_matrix_json", artifacts)
            self.assertIn("repository_source_explainer_audit_markdown", artifacts)
            self.assertIn("repository_source_ecosystem_review_markdown", artifacts)
            self.assertIn("repository_atlas_input_audit_json", artifacts)
            self.assertIn("repository_cross_domain_evidence_matrix_markdown", artifacts)
            self.assertIn("repository_docs_restoration_ledger_json", artifacts)
            self.assertIn("repository_docs_scope_validation_markdown", artifacts)
            self.assertIn("repository_docs_recovery_review_markdown", artifacts)
            self.assertIn("repository_source_acquisition_queue_markdown", artifacts)
            self.assertIn("repository_product_model_markdown", artifacts)
            self.assertIn("repository_credibility_dashboard_json", artifacts)
            self.assertIn("repository_output_sustainability_review_json", artifacts)
            self.assertIn("repository_extension_review_markdown", artifacts)
            self.assertIn("repository_brutal_honesty_review_json", artifacts)
            self.assertIn("repository_final_release_refusal_markdown", artifacts)
            self.assertIn("repository_generated_output_policy_json", artifacts)
            self.assertTrue((output_root / "repository_truth_posture.json").is_file())
            self.assertTrue((output_root / "repository_product_model.md").is_file())
            self.assertTrue(
                (output_root / "repository_credibility_dashboard.json").is_file()
            )
            self.assertTrue((output_root / "repository_recovery_review.md").is_file())
            self.assertTrue(
                (output_root / "repository_output_sustainability_review.md").is_file()
            )
            self.assertTrue(
                (output_root / "repository_extension_review.json").is_file()
            )
            self.assertTrue(
                (output_root / "repository_source_family_matrix.md").is_file()
            )
            self.assertTrue(
                (output_root / "repository_source_explainer_audit.md").is_file()
            )
            self.assertTrue(
                (output_root / "repository_source_ecosystem_review.json").is_file()
            )
            self.assertTrue(
                (output_root / "repository_atlas_input_audit.json").is_file()
            )
            self.assertTrue(
                (output_root / "repository_cross_domain_evidence_matrix.md").is_file()
            )
            self.assertTrue(
                (output_root / "repository_docs_restoration_ledger.json").is_file()
            )
            self.assertTrue(
                (output_root / "repository_docs_scope_validation.md").is_file()
            )
            self.assertTrue(
                (output_root / "repository_docs_recovery_review.md").is_file()
            )
            self.assertTrue(
                (output_root / "repository_source_acquisition_queue.json").is_file()
            )
            self.assertTrue(
                (output_root / "repository_brutal_honesty_review.md").is_file()
            )
            self.assertTrue(
                (output_root / "repository_final_release_refusal.json").is_file()
            )
            self.assertTrue(
                (output_root / "repository_generated_output_policy.md").is_file()
            )
            sustainability = json.loads(
                (
                    output_root / "repository_output_sustainability_review.json"
                ).read_text(encoding="utf-8")
            )
            balance_counts = sustainability["balance_counts"]
            self.assertEqual(
                balance_counts["report_file_count"],
                sum(1 for path in output_root.rglob("*") if path.is_file()),
            )
            self.assertEqual(
                balance_counts["maintainer_root_review_file_count"],
                sum(1 for _ in output_root.glob("repository_*.json")),
            )
            sustainability_markdown = (
                output_root / "repository_output_sustainability_review.md"
            ).read_text(encoding="utf-8")
            self.assertIn(
                f"- Report files: `{balance_counts['report_file_count']}`",
                sustainability_markdown,
            )
            self.assertIn(
                "- Maintainer root review files: "
                f"`{balance_counts['maintainer_root_review_file_count']}`",
                sustainability_markdown,
            )
            claim_audit = (output_root / "repository_claim_audit.json").read_text(
                encoding="utf-8"
            )
            self.assertIn('"overall_ok": true', claim_audit)
