from __future__ import annotations

import unittest

import pytest

from .repository_paths import (
    REPO_ROOT,
)

pytestmark = pytest.mark.generated_artifacts


class AnimalReportArtifactTests(unittest.TestCase):
    def test_public_report_root_ships_animal_output_audit(self) -> None:
        report_root = REPO_ROOT / "docs" / "report"
        audit_json = report_root / "animal_output_audit.json"
        audit_markdown = report_root / "animal_output_audit.md"
        readiness_json = report_root / "animal_atlas_readiness.json"
        readiness_markdown = report_root / "animal_atlas_readiness.md"
        honesty_json = report_root / "animal_output_honesty.json"
        honesty_markdown = report_root / "animal_output_honesty.md"
        exclusion_json = report_root / "animal_atlas_exclusion_report.json"
        exclusion_markdown = report_root / "animal_atlas_exclusion_report.md"
        validation_json = report_root / "animal_foundation_validation.json"
        validation_markdown = report_root / "animal_foundation_validation.md"
        drift_json = report_root / "animal_cross_surface_drift.json"
        drift_markdown = report_root / "animal_cross_surface_drift.md"
        caveat_json = report_root / "animal_scientific_caveat_ledger.json"
        caveat_markdown = report_root / "animal_scientific_caveat_ledger.md"
        point_json = report_root / "animal_point_evidence_review.json"
        point_markdown = report_root / "animal_point_evidence_review.md"
        absence_json = report_root / "animal_project_publication_gap_review.json"
        absence_markdown = report_root / "animal_project_publication_gap_review.md"
        review_json = report_root / "animal_foundation_review.json"
        review_markdown = report_root / "animal_foundation_review.md"
        chronology_json = report_root / "animal_sample_chronology_review.json"
        chronology_markdown = report_root / "animal_sample_chronology_review.md"
        intake_recovery_json = report_root / "animal_intake_recovery_review.json"
        intake_recovery_markdown = report_root / "animal_intake_recovery_review.md"
        gate_json = report_root / "animal_publication_release_gate.json"
        gate_markdown = report_root / "animal_publication_release_gate.md"
        sample_database_review_json = report_root / "animal_sample_database_review.json"
        sample_database_review_markdown = (
            report_root / "animal_sample_database_review.md"
        )
        repository_truth_json = report_root / "repository_truth_posture.json"
        repository_truth_markdown = report_root / "repository_truth_posture.md"
        repository_product_model_json = report_root / "repository_product_model.json"
        repository_product_model_markdown = report_root / "repository_product_model.md"
        repository_credibility_json = (
            report_root / "repository_credibility_dashboard.json"
        )
        repository_credibility_markdown = (
            report_root / "repository_credibility_dashboard.md"
        )
        repository_scorecard_json = report_root / "repository_recovery_review.json"
        repository_scorecard_markdown = report_root / "repository_recovery_review.md"
        repository_sustainability_json = (
            report_root / "repository_output_sustainability_review.json"
        )
        repository_sustainability_markdown = (
            report_root / "repository_output_sustainability_review.md"
        )
        repository_extension_json = report_root / "repository_extension_review.json"
        repository_extension_markdown = report_root / "repository_extension_review.md"
        repository_governance_json = (
            report_root / "repository_governance_artifact_review.json"
        )
        repository_governance_markdown = (
            report_root / "repository_governance_artifact_review.md"
        )
        repository_claim_json = report_root / "repository_claim_audit.json"
        repository_claim_markdown = report_root / "repository_claim_audit.md"
        repository_brutal_json = report_root / "repository_brutal_honesty_review.json"
        repository_brutal_markdown = report_root / "repository_brutal_honesty_review.md"
        repository_refusal_json = report_root / "repository_final_release_refusal.json"
        repository_refusal_markdown = (
            report_root / "repository_final_release_refusal.md"
        )
        repository_output_policy_json = (
            report_root / "repository_generated_output_policy.json"
        )
        repository_output_policy_markdown = (
            report_root / "repository_generated_output_policy.md"
        )
        repository_explainer_json = (
            report_root / "repository_source_explainer_audit.json"
        )
        repository_explainer_markdown = (
            report_root / "repository_source_explainer_audit.md"
        )
        repository_atlas_inputs_json = report_root / "repository_atlas_input_audit.json"
        repository_atlas_inputs_markdown = (
            report_root / "repository_atlas_input_audit.md"
        )
        repository_domain_matrix_json = (
            report_root / "repository_cross_domain_evidence_matrix.json"
        )
        repository_domain_matrix_markdown = (
            report_root / "repository_cross_domain_evidence_matrix.md"
        )
        repository_docs_ledger_json = (
            report_root / "repository_docs_restoration_ledger.json"
        )
        repository_docs_ledger_markdown = (
            report_root / "repository_docs_restoration_ledger.md"
        )
        repository_docs_guard_json = (
            report_root / "repository_docs_scope_validation.json"
        )
        repository_docs_guard_markdown = (
            report_root / "repository_docs_scope_validation.md"
        )
        repository_docs_review_json = (
            report_root / "repository_docs_recovery_review.json"
        )
        repository_docs_review_markdown = (
            report_root / "repository_docs_recovery_review.md"
        )
        repository_progress_json = (
            report_root / "repository_scientific_progress_audit.json"
        )
        repository_progress_markdown = (
            report_root / "repository_scientific_progress_audit.md"
        )

        self.assertTrue(audit_json.is_file())
        self.assertTrue(audit_markdown.is_file())
        self.assertTrue(readiness_json.is_file())
        self.assertTrue(readiness_markdown.is_file())
        self.assertTrue(honesty_json.is_file())
        self.assertTrue(honesty_markdown.is_file())
        self.assertTrue(exclusion_json.is_file())
        self.assertTrue(exclusion_markdown.is_file())
        self.assertTrue(validation_json.is_file())
        self.assertTrue(validation_markdown.is_file())
        self.assertTrue(drift_json.is_file())
        self.assertTrue(drift_markdown.is_file())
        self.assertTrue(caveat_json.is_file())
        self.assertTrue(caveat_markdown.is_file())
        self.assertTrue(point_json.is_file())
        self.assertTrue(point_markdown.is_file())
        self.assertTrue(absence_json.is_file())
        self.assertTrue(absence_markdown.is_file())
        self.assertTrue(review_json.is_file())
        self.assertTrue(review_markdown.is_file())
        self.assertTrue(chronology_json.is_file())
        self.assertTrue(chronology_markdown.is_file())
        self.assertTrue(intake_recovery_json.is_file())
        self.assertTrue(intake_recovery_markdown.is_file())
        self.assertTrue(gate_json.is_file())
        self.assertTrue(gate_markdown.is_file())
        self.assertTrue(sample_database_review_json.is_file())
        self.assertTrue(sample_database_review_markdown.is_file())
        self.assertTrue(repository_truth_json.is_file())
        self.assertTrue(repository_truth_markdown.is_file())
        self.assertTrue(repository_product_model_json.is_file())
        self.assertTrue(repository_product_model_markdown.is_file())
        self.assertTrue(repository_credibility_json.is_file())
        self.assertTrue(repository_credibility_markdown.is_file())
        self.assertTrue(repository_scorecard_json.is_file())
        self.assertTrue(repository_scorecard_markdown.is_file())
        self.assertTrue(repository_sustainability_json.is_file())
        self.assertTrue(repository_sustainability_markdown.is_file())
        self.assertTrue(repository_extension_json.is_file())
        self.assertTrue(repository_extension_markdown.is_file())
        self.assertTrue(repository_governance_json.is_file())
        self.assertTrue(repository_governance_markdown.is_file())
        self.assertTrue(repository_claim_json.is_file())
        self.assertTrue(repository_claim_markdown.is_file())
        self.assertTrue(repository_brutal_json.is_file())
        self.assertTrue(repository_brutal_markdown.is_file())
        self.assertTrue(repository_refusal_json.is_file())
        self.assertTrue(repository_refusal_markdown.is_file())
        self.assertTrue(repository_output_policy_json.is_file())
        self.assertTrue(repository_output_policy_markdown.is_file())
        self.assertTrue(repository_explainer_json.is_file())
        self.assertTrue(repository_explainer_markdown.is_file())
        self.assertTrue(repository_atlas_inputs_json.is_file())
        self.assertTrue(repository_atlas_inputs_markdown.is_file())
        self.assertTrue(repository_domain_matrix_json.is_file())
        self.assertTrue(repository_domain_matrix_markdown.is_file())
        self.assertTrue(repository_docs_ledger_json.is_file())
        self.assertTrue(repository_docs_ledger_markdown.is_file())
        self.assertTrue(repository_docs_guard_json.is_file())
        self.assertTrue(repository_docs_guard_markdown.is_file())
        self.assertTrue(repository_docs_review_json.is_file())
        self.assertTrue(repository_docs_review_markdown.is_file())
        self.assertTrue(repository_progress_json.is_file())
        self.assertTrue(repository_progress_markdown.is_file())
        self.assertIn("Animal output audit", audit_markdown.read_text(encoding="utf-8"))
        self.assertIn(
            "Animal atlas readiness",
            readiness_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Animal intake recovery review",
            intake_recovery_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Animal foundation validation",
            validation_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Repository product model",
            repository_product_model_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Repository credibility dashboard",
            repository_credibility_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Repository output sustainability review",
            repository_sustainability_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Repository extension review",
            repository_extension_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Animal cross-surface drift",
            drift_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Animal scientific caveat ledger",
            caveat_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Repository brutal honesty review",
            repository_brutal_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Repository final release refusal",
            repository_refusal_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Repository generated output policy",
            repository_output_policy_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Animal point evidence review",
            point_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Animal project publication gap review",
            absence_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Animal foundation review",
            review_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Animal sample chronology review",
            chronology_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Animal publication release gate",
            gate_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Repository docs restoration ledger",
            repository_docs_ledger_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Repository docs scope validation",
            repository_docs_guard_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Repository docs recovery review",
            repository_docs_review_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Animal sample database review",
            sample_database_review_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Repository truth posture",
            repository_truth_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Repository recovery review",
            repository_scorecard_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Repository governance artifact review",
            repository_governance_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Repository claim audit",
            repository_claim_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Repository source explainer audit",
            repository_explainer_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Repository atlas input audit",
            repository_atlas_inputs_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Repository cross-domain evidence matrix",
            repository_domain_matrix_markdown.read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Repository scientific progress audit",
            repository_progress_markdown.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
