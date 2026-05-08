from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.foundation import (
    build_repository_atlas_input_audit,
    build_repository_claim_audit,
    build_repository_cross_domain_evidence_matrix,
    build_repository_docs_breadth_guard,
    build_repository_docs_recovery_review,
    build_repository_docs_restoration_ledger,
    build_repository_governance_artifact_review,
    build_repository_recovery_scorecard,
    build_repository_source_acquisition_queue,
    build_repository_source_explainer_audit,
    build_repository_source_family_matrix,
    build_repository_scientific_progress_audit,
    build_repository_truth_posture,
    render_repository_atlas_input_audit_markdown,
    render_repository_claim_audit_markdown,
    render_repository_cross_domain_evidence_matrix_markdown,
    render_repository_docs_breadth_guard_markdown,
    render_repository_docs_recovery_review_markdown,
    render_repository_docs_restoration_ledger_markdown,
    render_repository_governance_artifact_review_markdown,
    render_repository_recovery_scorecard_markdown,
    render_repository_source_acquisition_queue_markdown,
    render_repository_source_explainer_audit_markdown,
    render_repository_source_family_matrix_markdown,
    render_repository_scientific_progress_audit_markdown,
    render_repository_truth_posture_markdown,
)
from bijux_pollenomics.reporting.foundation import publish_repository_truth_outputs


class RepositoryTruthUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[4]
        self.data_root = self.repo_root / "data"
        self.docs_root = self.repo_root / "docs"
        self.report_root = self.docs_root / "report"

    def test_truth_posture_names_primary_scope_and_current_claim_freeze_reasons(
        self,
    ) -> None:
        payload = build_repository_truth_posture(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        markdown = render_repository_truth_posture_markdown(payload)

        self.assertEqual(payload["schema_version"], "repository-truth-posture.v1")
        self.assertEqual(
            payload["primary_domains"],
            ["pollen_context", "environmental_context"],
        )
        self.assertEqual(payload["counts"]["tracked_paper_count"], 18)
        self.assertEqual(payload["counts"]["papers_with_archived_supplements"], 18)
        self.assertEqual(payload["counts"]["papers_with_local_reference_supplements"], 18)
        self.assertEqual(payload["counts"]["published_atlas_point_count"], 234)
        self.assertTrue(
            any(
                "under-reports" in row
                for row in payload["claim_freeze_reasons"]
            )
        )
        self.assertIn("# Repository truth posture", markdown)
        self.assertIn("Do Not Repeat", markdown)

    def test_recovery_scorecard_keeps_animal_context_low_and_docs_breadth_visible(
        self,
    ) -> None:
        payload = build_repository_recovery_scorecard(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        markdown = render_repository_recovery_scorecard_markdown(payload)

        self.assertEqual(payload["schema_version"], "repository-recovery-scorecard.v1")
        animal_row = next(
            row for row in payload["rows"] if row["surface_key"] == "ancient_dna_context"
        )
        docs_row = next(
            row
            for row in payload["rows"]
            if row["surface_key"] == "documentation_architecture"
        )
        self.assertEqual(payload["overall_recovery_posture"], "recovery_required")
        self.assertEqual(animal_row["data_completeness"], 4)
        self.assertEqual(docs_row["documentation_clarity"], 4)
        self.assertIn("| Ancient DNA context | 4 |", markdown)

    def test_governance_artifact_review_marks_accounting_surfaces_for_retirement(
        self,
    ) -> None:
        payload = build_repository_governance_artifact_review(
            data_root=self.data_root,
            report_root=self.report_root,
        )
        markdown = render_repository_governance_artifact_review_markdown(payload)

        self.assertEqual(
            payload["schema_version"], "repository-governance-artifact-review.v1"
        )
        self.assertEqual(payload["summary"]["retire"], 1)
        retired_row = next(
            row for row in payload["rows"] if row["action"] == "retire"
        )
        self.assertEqual(
            retired_row["artifact_path"],
            "docs/report/animal_output_audit.json",
        )
        self.assertIn("publication_accounting", markdown)

    def test_claim_audit_passes_once_animal_review_freezes_broad_readiness(
        self,
    ) -> None:
        payload = build_repository_claim_audit(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        markdown = render_repository_claim_audit_markdown(payload)

        self.assertEqual(payload["schema_version"], "repository-claim-audit.v1")
        self.assertTrue(payload["overall_ok"])
        self.assertTrue(all(row["passed"] for row in payload["checks"]))
        docs_breadth_row = next(
            row
            for row in payload["checks"]
            if row["check_id"]
            == "docs_breadth_guard_keeps_repository_story_wide_enough"
        )
        self.assertTrue(docs_breadth_row["passed"])
        self.assertIn("# Repository claim audit", markdown)

    def test_source_family_matrix_and_acquisition_queue_keep_cross_domain_pressure_visible(
        self,
    ) -> None:
        matrix_payload = build_repository_source_family_matrix(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        queue_payload = build_repository_source_acquisition_queue(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        matrix_markdown = render_repository_source_family_matrix_markdown(matrix_payload)
        queue_markdown = render_repository_source_acquisition_queue_markdown(queue_payload)

        self.assertEqual(matrix_payload["schema_version"], "repository-source-family-matrix.v1")
        self.assertEqual(queue_payload["schema_version"], "repository-source-acquisition-queue.v1")
        self.assertEqual(matrix_payload["row_count"], 8)
        self.assertGreaterEqual(queue_payload["row_count"], 1)
        self.assertIn("Animal aDNA papers and supplements", matrix_markdown)
        self.assertIn("animal_adna", queue_markdown)

    def test_source_explainer_atlas_input_and_cross_domain_packets_keep_pollen_first(
        self,
    ) -> None:
        explainer_payload = build_repository_source_explainer_audit(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        atlas_payload = build_repository_atlas_input_audit(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        matrix_payload = build_repository_cross_domain_evidence_matrix(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        explainer_markdown = render_repository_source_explainer_audit_markdown(
            explainer_payload
        )
        atlas_markdown = render_repository_atlas_input_audit_markdown(atlas_payload)
        matrix_markdown = render_repository_cross_domain_evidence_matrix_markdown(
            matrix_payload
        )

        self.assertEqual(
            explainer_payload["schema_version"],
            "repository-source-explainer-audit.v1",
        )
        self.assertEqual(
            atlas_payload["schema_version"], "repository-atlas-input-audit.v1"
        )
        self.assertEqual(
            matrix_payload["schema_version"],
            "repository-cross-domain-evidence-matrix.v1",
        )
        self.assertEqual(explainer_payload["status_counts"]["present_useful_form"], 15)
        self.assertEqual(
            explainer_payload["status_counts"]["restoration_plan_required"], 0
        )
        self.assertEqual(atlas_payload["row_count"], 6)
        pollen_row = next(
            row for row in matrix_payload["rows"] if row["domain_key"] == "pollen_context"
        )
        self.assertEqual(pollen_row["tracked_metrics"]["landclim_site_count"], 492)
        self.assertEqual(pollen_row["tracked_metrics"]["neotoma_site_count"], 200)
        self.assertIn("Repository source explainer audit", explainer_markdown)
        self.assertIn("Repository atlas input audit", atlas_markdown)
        self.assertIn("Repository cross-domain evidence matrix", matrix_markdown)

    def test_scientific_progress_audit_prefers_evidence_depth_over_file_count(
        self,
    ) -> None:
        payload = build_repository_scientific_progress_audit(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        markdown = render_repository_scientific_progress_audit_markdown(payload)

        self.assertEqual(
            payload["schema_version"], "repository-scientific-progress-audit.v1"
        )
        self.assertEqual(payload["overall_progress_posture"], "data_recovery_required")
        self.assertIn("checked-in JSON file count", payload["anti_measures"])
        self.assertTrue(
            any(
                "all 18 tracked papers now ship archived supplementary material" in row
                for row in payload["findings"]
            )
        )
        self.assertIn("Do Not Use These As Progress", markdown)

    def test_docs_restoration_ledger_breadth_guard_and_recovery_review_hold(
        self,
    ) -> None:
        ledger_payload = build_repository_docs_restoration_ledger(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        breadth_payload = build_repository_docs_breadth_guard(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        review_payload = build_repository_docs_recovery_review(
            data_root=self.data_root,
            docs_root=self.docs_root,
            report_root=self.report_root,
        )
        ledger_markdown = render_repository_docs_restoration_ledger_markdown(
            ledger_payload
        )
        breadth_markdown = render_repository_docs_breadth_guard_markdown(
            breadth_payload
        )
        review_markdown = render_repository_docs_recovery_review_markdown(
            review_payload
        )

        self.assertEqual(
            ledger_payload["schema_version"],
            "repository-docs-restoration-ledger.v1",
        )
        self.assertEqual(
            breadth_payload["schema_version"],
            "repository-docs-breadth-guard.v1",
        )
        self.assertEqual(
            review_payload["schema_version"],
            "repository-docs-recovery-review.v1",
        )
        self.assertEqual(ledger_payload["row_count"], 68)
        self.assertEqual(
            ledger_payload["status_counts"]["replacement_incomplete"], 0
        )
        self.assertEqual(
            ledger_payload["status_counts"]["verified_replacement"], 68
        )
        self.assertTrue(breadth_payload["overall_ok"])
        self.assertEqual(
            review_payload["overall_posture"],
            "moving_toward_elegant_correctness",
        )
        self.assertIn("Repository docs restoration ledger", ledger_markdown)
        self.assertIn("Repository docs breadth guard", breadth_markdown)
        self.assertIn("Repository docs recovery review", review_markdown)

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
            self.assertIn("repository_atlas_input_audit_json", artifacts)
            self.assertIn("repository_cross_domain_evidence_matrix_markdown", artifacts)
            self.assertIn("repository_docs_restoration_ledger_json", artifacts)
            self.assertIn("repository_docs_breadth_guard_markdown", artifacts)
            self.assertIn("repository_docs_recovery_review_markdown", artifacts)
            self.assertIn("repository_source_acquisition_queue_markdown", artifacts)
            self.assertTrue((output_root / "repository_truth_posture.json").is_file())
            self.assertTrue((output_root / "repository_recovery_scorecard.md").is_file())
            self.assertTrue((output_root / "repository_source_family_matrix.md").is_file())
            self.assertTrue(
                (output_root / "repository_source_explainer_audit.md").is_file()
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
                (output_root / "repository_docs_breadth_guard.md").is_file()
            )
            self.assertTrue(
                (output_root / "repository_docs_recovery_review.md").is_file()
            )
            self.assertTrue((output_root / "repository_source_acquisition_queue.json").is_file())
            claim_audit = (output_root / "repository_claim_audit.json").read_text(
                encoding="utf-8"
            )
            self.assertIn('"overall_ok": true', claim_audit)
