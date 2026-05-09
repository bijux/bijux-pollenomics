from __future__ import annotations

from pathlib import Path
import re
import subprocess
import unittest

import pytest
import yaml

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(__file__).resolve().parents[4]
WORKFLOW_URL_RE = re.compile(
    r"https://github\.com/(?P<repo>[^/\s]+/[^/\s]+)/actions/workflows/"
    r"(?P<workflow>[A-Za-z0-9_.-]+)"
)
MERMAID_RESERVED_IDS = {
    "class",
    "classdef",
    "click",
    "default",
    "end",
    "graph",
    "linkstyle",
    "style",
    "subgraph",
}

pytestmark = pytest.mark.generated_artifacts


class RepositoryContractRegressionTests(unittest.TestCase):
    def test_shared_mkdocs_redirect_targets_exist(self) -> None:
        config = yaml.unsafe_load(
            (REPO_ROOT / "mkdocs.shared.yml").read_text(encoding="utf-8")
        )
        redirect_maps = config["plugins"][2]["redirects"]["redirect_maps"]

        missing_targets = [
            target
            for target in redirect_maps.values()
            if not (REPO_ROOT / "docs" / target).is_file()
        ]

        self.assertEqual(missing_targets, [])

    def test_shared_mkdocs_excludes_badge_template_from_public_docs_graph(self) -> None:
        config = yaml.unsafe_load(
            (REPO_ROOT / "mkdocs.shared.yml").read_text(encoding="utf-8")
        )

        self.assertEqual(config["exclude_docs"].strip(), "badges.md")

    def test_generated_data_readme_targets_existing_docs_pages(self) -> None:
        readme_text = (REPO_ROOT / "data" / "README.md").read_text(encoding="utf-8")
        targets = re.findall(r"\]\((\.\./docs/[^\)]+)\)", readme_text)

        self.assertIn("adna/species/homo_sapiens", readme_text)
        self.assertIn("adna/species/equus_caballus", readme_text)
        self.assertIn("adna/species/bos_taurus", readme_text)
        self.assertIn("adna/species/canis_lupus_familiaris", readme_text)
        self.assertIn("adna/species/camelus_dromedarius", readme_text)
        self.assertIn("adna/species/rangifer_tarandus", readme_text)
        self.assertIn("adna/species/equus_asinus", readme_text)
        self.assertIn("domesticated-animal curation program", readme_text)
        self.assertIn("aadr -> ../../../../aadr", readme_text)
        self.assertGreaterEqual(len(targets), 2)
        for target in targets:
            resolved = (REPO_ROOT / "data" / target).resolve()
            self.assertTrue(
                resolved.exists(),
                f"data/README.md points at a missing docs page: {target}",
            )

    def test_data_root_ships_contract_and_state_surfaces(self) -> None:
        data_root = REPO_ROOT / "data"

        self.assertTrue((data_root / "collection_summary.json").is_file())
        self.assertTrue((data_root / "source_family_contracts.json").is_file())
        self.assertTrue(
            (data_root / "source_family_evidence_stage_matrix.json").is_file()
        )
        self.assertTrue((data_root / "source_fact_ownership_registry.json").is_file())
        self.assertTrue((data_root / "evidence_artifact_contracts.json").is_file())

    def test_tracked_adna_root_ships_cross_species_audit_artifacts(self) -> None:
        adna_root = REPO_ROOT / "data" / "adna"
        governance_root = adna_root / "governance"

        self.assertTrue((governance_root / "cross_species_bibliography.json").is_file())
        self.assertTrue((governance_root / "cross_species_bibliography.csv").is_file())
        self.assertTrue(
            (governance_root / "cross_species_archive_inventory.json").is_file()
        )
        self.assertTrue(
            (governance_root / "cross_species_archive_inventory.csv").is_file()
        )
        self.assertTrue((governance_root / "cross_species_freshness.json").is_file())
        self.assertTrue((governance_root / "cross_species_freshness.csv").is_file())
        self.assertTrue(
            (governance_root / "cross_species_coverage_dashboard.json").is_file()
        )
        self.assertTrue(
            (governance_root / "cross_species_coverage_dashboard.csv").is_file()
        )
        self.assertTrue(
            (governance_root / "animal_sample_product_contract.json").is_file()
        )
        self.assertTrue(
            (governance_root / "animal_sample_product_contract.md").is_file()
        )
        self.assertTrue(
            (governance_root / "animal_sample_foundation_truth.json").is_file()
        )
        self.assertTrue(
            (governance_root / "animal_sample_foundation_truth.md").is_file()
        )
        self.assertTrue(
            (governance_root / "animal_sample_foundation_truth_species.csv").is_file()
        )
        self.assertTrue(
            (governance_root / "animal_sample_foundation_truth_projects.csv").is_file()
        )
        self.assertTrue(
            (governance_root / "animal_sample_aggregation_warnings.json").is_file()
        )
        self.assertTrue(
            (governance_root / "animal_sample_aggregation_warnings.md").is_file()
        )
        self.assertTrue(
            (governance_root / "cross_species_map_readiness.json").is_file()
        )
        self.assertTrue((governance_root / "cross_species_map_readiness.csv").is_file())
        self.assertTrue((governance_root / "unresolved_site_ledger.json").is_file())
        self.assertTrue((governance_root / "unresolved_site_ledger.csv").is_file())
        self.assertTrue((governance_root / "overbroad_site_ledger.json").is_file())
        self.assertTrue((governance_root / "overbroad_site_ledger.csv").is_file())
        self.assertTrue((governance_root / "coordinate_caveat_surface.json").is_file())
        self.assertTrue((governance_root / "coordinate_caveat_surface.md").is_file())
        self.assertTrue((governance_root / "coordinate_confidence_scale.md").is_file())
        self.assertTrue((governance_root / "shipped_product_audit.json").is_file())
        self.assertTrue((governance_root / "surface_role_registry.json").is_file())
        self.assertTrue((governance_root / "surface_role_registry.md").is_file())
        self.assertTrue(
            (governance_root / "source_library" / "project_registry.json").is_file()
        )
        self.assertTrue(
            (
                governance_root / "source_library" / "project_surface_contract.json"
            ).is_file()
        )
        self.assertTrue(
            (governance_root / "source_library" / "paper_registry.json").is_file()
        )
        self.assertTrue(
            (governance_root / "source_library" / "supplement_registry.json").is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "supplement_zip_member_registry.json"
            ).is_file()
        )
        self.assertTrue(
            (governance_root / "source_library" / "source_audit.json").is_file()
        )
        self.assertTrue(
            (governance_root / "source_library" / "source_blockers.json").is_file()
        )
        self.assertTrue(
            (governance_root / "source_library" / "source_intake_audit.json").is_file()
        )
        self.assertTrue(
            (
                governance_root / "source_library" / "source_intake_release_guard.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "tracked_project_and_paper_inventory.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "tracked_project_and_paper_inventory.md"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "project_sample_master_completeness.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "project_sample_master_completeness.csv"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "sample_identity_ambiguity_ledger.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "sample_identity_ambiguity_ledger.md"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root / "source_library" / "project_sample_site_review.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root / "source_library" / "project_sample_site_review.csv"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root / "source_library" / "sample_site_ambiguity_ledger.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root / "source_library" / "sample_site_ambiguity_ledger.md"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "sample_site_manual_curation_queue.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "sample_site_manual_curation_queue.md"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "sample_locality_conflict_ledger.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "sample_locality_conflict_ledger.md"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "sample_locality_manual_curation_workflow.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "sample_locality_manual_curation_workflow.md"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "project_locality_substitution_ledger.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "project_locality_substitution_ledger.md"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "site_name_normalization_dictionary.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "site_name_normalization_dictionary.csv"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "species_locality_completeness.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root / "source_library" / "species_locality_completeness.csv"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "project_locality_completeness.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root / "source_library" / "project_locality_completeness.csv"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "project_sample_chronology_review.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "project_sample_chronology_review.csv"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "sample_chronology_normalization_audit.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "sample_chronology_normalization_audit.md"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "sample_chronology_ambiguity_ledger.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "sample_chronology_ambiguity_ledger.md"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "sample_chronology_conflict_ledger.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "sample_chronology_conflict_ledger.md"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "sample_chronology_precision_audit.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "sample_chronology_precision_audit.md"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "species_chronology_completeness.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "species_chronology_completeness.csv"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "project_chronology_completeness.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "project_chronology_completeness.csv"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root / "source_library" / "sample_chronology_review.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root / "source_library" / "sample_chronology_review.md"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root / "source_library" / "date_evidence_gap_queue.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root / "source_library" / "date_evidence_gap_queue.md"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "projects"
                / "PRJEB22390"
                / "bundle_manifest.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "projects"
                / "PRJEB22390"
                / "intake_dossier.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "projects"
                / "PRJEB36540"
                / "sample_master.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "projects"
                / "PRJEB36540"
                / "locality_worksheet.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "projects"
                / "PRJEB36540"
                / "sample_locality_evidence.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "projects"
                / "PRJEB36540"
                / "sample_sites.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "projects"
                / "PRJEB36540"
                / "sample_chronology.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "projects"
                / "PRJEB36540"
                / "sample_chronology_evidence.json"
            ).is_file()
        )
        self.assertTrue(
            (
                governance_root
                / "source_library"
                / "papers"
                / "10.1038-s42003-021-02794-8"
                / "supplementary_manifest.json"
            ).is_file()
        )

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

    def test_tracked_species_readmes_start_from_counted_sample_and_map_posture(
        self,
    ) -> None:
        readme_text = (
            REPO_ROOT / "data" / "adna" / "species" / "ovis_aries" / "README.md"
        ).read_text(encoding="utf-8")

        self.assertIn("- Curated sample rows:", readme_text)
        self.assertIn("- Curated projects:", readme_text)
        self.assertIn("- Curated site rows:", readme_text)
        self.assertIn("- Direct-coordinate rows:", readme_text)
        self.assertIn("- Geocoded rows:", readme_text)
        self.assertIn("- Unresolved sample rows:", readme_text)
        self.assertIn("- Mapped Nordic rows:", readme_text)
        self.assertIn("- Tracked intake projects:", readme_text)

    def test_public_data_docs_keep_the_evidence_chain_directly_linked(self) -> None:
        inventory_page = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "sources"
            / "animal-source-intake.md"
        )

        self.assertTrue(inventory_page.is_file())
        inventory_text = inventory_page.read_text(encoding="utf-8")
        self.assertIn("tracked_project_and_paper_inventory.json", inventory_text)
        self.assertIn("paper_registry.json", inventory_text)
        self.assertIn("supplement_acquisition_checklist.json", inventory_text)
        self.assertIn("supplement_file_family_audit.json", inventory_text)
        self.assertIn("Animal Source Intake", inventory_text)
        self.assertIn("source_intake_audit.json", inventory_text)
        self.assertIn("project_sample_master_completeness.json", inventory_text)
        self.assertIn("sample_master.json", inventory_text)
        self.assertIn("project_sample_site_review.json", inventory_text)
        self.assertIn("sample_sites.json", inventory_text)
        self.assertIn("locality_worksheet.json", inventory_text)
        self.assertIn("sample_locality_evidence.json", inventory_text)
        self.assertIn("sample_locality_conflict_ledger.json", inventory_text)
        self.assertIn("site_name_normalization_dictionary.json", inventory_text)
        self.assertIn("project_sample_chronology_review.json", inventory_text)
        self.assertIn("sample_chronology.json", inventory_text)

    def test_project_sample_master_completeness_keeps_traceable_expected_counts(
        self,
    ) -> None:
        import json

        payload = json.loads(
            (
                REPO_ROOT
                / "data"
                / "adna"
                / "governance"
                / "source_library"
                / "project_sample_master_completeness.json"
            ).read_text(encoding="utf-8")
        )
        rows = payload["rows"]

        self.assertTrue(rows)
        for row in rows:
            if row["expected_sample_count"] is None:
                continue
            self.assertTrue(
                str(row["expected_sample_count_provenance"]).strip(),
                f"Expected sample count for {row['project_accession']} lacks provenance.",
            )
            self.assertTrue(
                str(row["expected_sample_count_artifact_path"]).strip(),
                f"Expected sample count for {row['project_accession']} lacks an artifact path.",
            )

    def test_sample_master_rows_do_not_claim_final_status_with_unresolved_ambiguity(
        self,
    ) -> None:
        import json

        project_root = (
            REPO_ROOT / "data" / "adna" / "governance" / "source_library" / "projects"
        )
        for path in project_root.glob("*/sample_master.json"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            for row in payload["rows"]:
                if row["sample_identity_resolution"] != "final":
                    continue
                self.assertFalse(
                    str(row["sample_ambiguity_note"]).strip(),
                    f"{path.relative_to(REPO_ROOT)} publishes a final sample row with an ambiguity note.",
                )

    @staticmethod
    def _declared_mermaid_node_ids(block: str) -> set[str]:
        ids: set[str] = set()
        for line in block.splitlines():
            match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_-]*)\s*\[", line)
            if match:
                ids.add(match.group(1).lower())
        return ids

    def test_docs_mermaid_diagrams_avoid_reserved_node_ids(self) -> None:
        failures: list[str] = []

        for path in (REPO_ROOT / "docs").rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            for match in re.finditer(r"```mermaid\n([\s\S]*?)\n```", text):
                reserved_ids = sorted(
                    MERMAID_RESERVED_IDS.intersection(
                        self._declared_mermaid_node_ids(match.group(1))
                    )
                )
                if reserved_ids:
                    failures.append(
                        f"{path.relative_to(REPO_ROOT)}: reserved Mermaid ids "
                        + ", ".join(reserved_ids)
                    )

        self.assertFalse(
            failures,
            "Mermaid diagrams use reserved node ids:\n" + "\n".join(failures),
        )

    def test_pyproject_declares_apache_license_and_author(self) -> None:
        root_pyproject_text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        package_pyproject_text = (PACKAGE_ROOT / "pyproject.toml").read_text(
            encoding="utf-8"
        )

        self.assertIn('members = ["packages/*"]', root_pyproject_text)
        self.assertIn('docs_package = "bijux-pollenomics-dev"', root_pyproject_text)
        self.assertIn('license = { text = "Apache-2.0" }', package_pyproject_text)
        self.assertIn(
            'force-include = { "LICENSE" = "LICENSE", "NOTICE" = "NOTICE" }',
            package_pyproject_text,
        )
        self.assertIn(
            '{ name = "Bijan Mousavi", email = "bijan@bijux.io" }',
            package_pyproject_text,
        )

    def test_makefile_exposes_named_test_suites(self) -> None:
        makefile_text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
        root_make_text = (REPO_ROOT / "makes" / "root.mk").read_text(encoding="utf-8")
        root_env_text = (
            REPO_ROOT / "makes" / "bijux-py" / "root" / "env.mk"
        ).read_text(encoding="utf-8")
        test_targets_text = (
            REPO_ROOT / "makes" / "bijux-py" / "ci" / "test.mk"
        ).read_text(encoding="utf-8")
        build_targets_text = (
            REPO_ROOT / "makes" / "bijux-py" / "ci" / "build.mk"
        ).read_text(encoding="utf-8")
        package_make_text = (
            REPO_ROOT / "makes" / "packages" / "bijux-pollenomics.mk"
        ).read_text(encoding="utf-8")

        self.assertIn("include makes/root.mk", makefile_text)
        self.assertIn("lock", root_make_text)
        self.assertIn("lock-check", root_make_text)
        self.assertIn("package-verify", root_make_text)
        self.assertIn("package-check", root_make_text)
        self.assertIn("package-smoke", root_make_text)
        self.assertIn("package-source-smoke", root_make_text)
        self.assertIn("test-unit:", test_targets_text)
        self.assertIn("test-regression:", test_targets_text)
        self.assertIn("test-e2e:", test_targets_text)
        self.assertIn(
            'ls -l "$$out_dir" || true',
            build_targets_text,
        )
        self.assertIn("BUILD_POST_TARGETS := build-install-smoke", package_make_text)
        self.assertIn("build-install-smoke:", package_make_text)
        self.assertIn(
            "ROOT_ARTIFACTS_DIR ?= $(PROJECT_ARTIFACTS_DIR)/root", root_env_text
        )
        self.assertIn("ROOT_VENV ?= $(ROOT_ARTIFACTS_DIR)/venv", root_env_text)
        self.assertIn(
            "export PYTHONPYCACHEPREFIX ?= $(ROOT_PYCACHE_DIR)", root_env_text
        )

    def test_readme_and_docs_describe_license_and_test_suites(self) -> None:
        readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        docs_text = (
            REPO_ROOT / "docs" / "01-bijux-pollenomics" / "quality" / "test-strategy.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Apache License 2.0", readme_text)
        self.assertIn("make lock-check", readme_text)
        self.assertIn("make package-check", readme_text)
        self.assertIn("make package-source-smoke", readme_text)
        self.assertIn("make test-unit", readme_text)
        self.assertIn("make test-regression", readme_text)
        self.assertIn("make test-e2e", readme_text)
        self.assertIn("`tests/unit/`", docs_text)
        self.assertIn("`tests/regression/`", docs_text)
        self.assertIn("`tests/e2e/`", docs_text)

    def test_docs_home_page_uses_repository_name_for_title_and_h1(self) -> None:
        docs_index = (REPO_ROOT / "docs" / "index.md").read_text(encoding="utf-8")

        self.assertIn("title: Bijux Pollenomics", docs_index)
        self.assertIn("# Bijux Pollenomics", docs_index)
        self.assertNotIn("# Docs Index", docs_index)
        self.assertIn("pollenomics and environmental evidence", docs_index)
        self.assertIn(
            "animal aDNA extraction already equals the whole pollenomics engine",
            docs_index,
        )

    def test_public_docs_keep_direct_sample_database_packet_and_query_links(
        self,
    ) -> None:
        docs_index = (REPO_ROOT / "docs" / "index.md").read_text(encoding="utf-8")
        sample_page = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "evidence"
            / "sample-records.md"
        ).read_text(encoding="utf-8")
        site_page = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "evidence"
            / "localities.md"
        ).read_text(encoding="utf-8")
        chronology_page = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "evidence"
            / "chronology.md"
        ).read_text(encoding="utf-8")
        temporal_semantics_page = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "evidence"
            / "temporal-semantics.md"
        ).read_text(encoding="utf-8")
        sead_handbook_page = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "sources"
            / "sead-handbook.md"
        ).read_text(encoding="utf-8")
        coordinate_page = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "evidence"
            / "coordinates.md"
        ).read_text(encoding="utf-8")
        source_index = (
            REPO_ROOT / "docs" / "02-bijux-pollenomics-data" / "sources" / "index.md"
        ).read_text(encoding="utf-8")
        source_family_matrix_page = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "sources"
            / "source-family-matrix.md"
        ).read_text(encoding="utf-8")
        publication_model_page = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "overview"
            / "pollenomics-publication-model.md"
        ).read_text(encoding="utf-8")
        cross_domain_page = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "overview"
            / "cross-domain-evidence-matrix.md"
        ).read_text(encoding="utf-8")
        inventory_page = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "sources"
            / "animal-source-intake.md"
        ).read_text(encoding="utf-8")
        source_recovery_page = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "sources"
            / "non-adna-explainer-recovery.md"
        ).read_text(encoding="utf-8")
        atlas_index = (
            REPO_ROOT / "docs" / "05-nordic-evidence-atlas" / "index.md"
        ).read_text(encoding="utf-8")
        published_reports = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "outputs"
            / "published-reports.md"
        ).read_text(encoding="utf-8")
        outputs_index = (
            REPO_ROOT / "docs" / "02-bijux-pollenomics-data" / "outputs" / "index.md"
        ).read_text(encoding="utf-8")
        atlas_outputs = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "outputs"
            / "geographic-evidence-surfaces.md"
        ).read_text(encoding="utf-8")
        atlas_inputs_page = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "outputs"
            / "geographic-input-surfaces.md"
        ).read_text(encoding="utf-8")
        sead_review_page = (
            REPO_ROOT / "docs" / "report" / "repository_sead_legibility_review.md"
        ).read_text(encoding="utf-8")

        self.assertIn("02-bijux-pollenomics-data/", docs_index)
        self.assertIn("report/world/world_map.html", docs_index)
        self.assertIn(
            "data/adna/governance/animal_sample_foundation_truth.json", sample_page
        )
        self.assertIn(
            "data/adna/species/ovis_aries/normalized/sample_records.json", sample_page
        )
        self.assertIn(
            "data/adna/species/ovis_aries/normalized/site_evidence.json", site_page
        )
        self.assertIn(
            "data/adna/governance/source_library/project_sample_chronology_review.json",
            chronology_page,
        )
        self.assertIn(
            "sample_chronology_provenance_review.json",
            chronology_page,
        )
        self.assertIn(
            "data/sead/review/temporal_review.json",
            temporal_semantics_page,
        )
        self.assertIn(
            "data/sead/review/evidence_legibility_review.json",
            temporal_semantics_page,
        )
        self.assertIn(
            "data/sead/review/access_model.json",
            sead_handbook_page,
        )
        self.assertIn(
            "data/sead/review/recovery_roadmap.json",
            sead_handbook_page,
        )
        self.assertIn(
            "data/adna/species/ovis_aries/normalized/coordinate_provenance.json",
            coordinate_page,
        )
        self.assertIn(
            "../report/animal_point_evidence_review.md",
            atlas_index,
        )
        self.assertIn(
            "../report/regions/nordic/nordic_map_publication_contract.md",
            atlas_index,
        )
        self.assertIn(
            "../report/regions/nordic/nordic_point_traceability.md",
            atlas_index,
        )
        self.assertIn(
            "data/adna/governance/source_library/project_source_evidence_matrix.json",
            source_index,
        )
        self.assertIn(
            "source-family-matrix.md",
            source_index,
        )
        self.assertIn(
            "../../report/repository_source_family_matrix.json",
            source_family_matrix_page,
        )
        self.assertIn(
            "data/sead/review/evidence_legibility_review.json", sead_review_page
        )
        self.assertIn(
            "../../report/repository_cross_domain_evidence_matrix.json",
            source_family_matrix_page,
        )
        self.assertIn(
            "../../report/repository_source_explainer_audit.md",
            source_family_matrix_page,
        )
        self.assertIn(
            "../../report/repository_source_acquisition_queue.json",
            source_family_matrix_page,
        )
        self.assertIn(
            "../../report/repository_cross_domain_evidence_matrix.md", cross_domain_page
        )
        self.assertIn("../../report/repository_atlas_input_audit.md", cross_domain_page)
        self.assertIn("cross-domain evidence matrix", publication_model_page.lower())
        self.assertIn(
            "data/adna/governance/source_library/reference_stash_reconciliation.json",
            inventory_page,
        )
        self.assertIn(
            "data/adna/governance/source_library/source_blocker_review.json",
            inventory_page,
        )
        self.assertIn(
            "data/adna/governance/source_library/project_recovery_stage_review.json",
            inventory_page,
        )
        self.assertIn(
            "data/adna/governance/source_library/project_expected_sample_yield_review.json",
            inventory_page,
        )
        self.assertIn(
            "data/adna/governance/source_library/manual_curation_worklist.json",
            inventory_page,
        )
        self.assertIn(
            "data/adna/governance/source_library/source_recovery_release_guard.json",
            inventory_page,
        )
        self.assertIn(
            "../../report/repository_source_explainer_audit.md", source_recovery_page
        )
        self.assertIn(
            "../../report/animal_sample_database_review.md", published_reports
        )
        self.assertIn(
            "../../report/animal_intake_recovery_review.md", published_reports
        )
        self.assertIn("../../report/animal_point_evidence_review.md", published_reports)
        self.assertIn("../../report/animal_output_honesty.md", published_reports)
        self.assertIn(
            "../../report/animal_atlas_exclusion_report.md", published_reports
        )
        self.assertIn(
            "../../report/world/world_map_publication_contract.md", published_reports
        )
        self.assertIn(
            "../../report/regions/nordic/nordic_point_traceability.md",
            published_reports,
        )
        self.assertIn("../../report/repository_truth_posture.md", published_reports)
        self.assertIn(
            "../../report/repository_source_family_matrix.md", published_reports
        )
        self.assertIn("output-surface-classes.md", outputs_index)
        self.assertIn("geographic-point-publication.md", outputs_index)
        self.assertIn("geographic-filters-and-inspection.md", outputs_index)
        self.assertIn("geographic-limits-and-honesty.md", outputs_index)
        self.assertIn(
            "../../report/world/world_map_publication_contract.md", atlas_outputs
        )
        self.assertIn(
            "../../report/regions/nordic/nordic_point_traceability.md", atlas_outputs
        )
        self.assertIn("../../report/repository_atlas_input_audit.md", atlas_inputs_page)
        self.assertIn(
            "../../report/repository_cross_domain_evidence_matrix.md", atlas_inputs_page
        )
        self.assertIn(
            "../../report/countries/sweden/sweden_animal_adna_v66_samples.md",
            published_reports,
        )
        self.assertIn("../../report/countries/sweden/README.md", published_reports)
        self.assertIn("animal_atlas_candidate_accountability.md", atlas_outputs)

    def test_public_docs_do_not_ship_reference_grade_phrase(self) -> None:
        failures: list[str] = []

        for path in (REPO_ROOT / "docs").rglob("*.md"):
            text = path.read_text(encoding="utf-8").lower()
            if "reference-grade" in text:
                failures.append(str(path.relative_to(REPO_ROOT)))

        self.assertFalse(
            failures,
            "Public docs still ship the forbidden reference-grade phrase:\n"
            + "\n".join(failures),
        )

    def test_top_level_product_descriptions_stay_pollenomics_first(self) -> None:
        root_readme = " ".join(
            (REPO_ROOT / "README.md").read_text(encoding="utf-8").split()
        )
        runtime_readme = " ".join(
            (REPO_ROOT / "packages" / "bijux-pollenomics" / "README.md")
            .read_text(encoding="utf-8")
            .split()
        )
        alias_readme = (REPO_ROOT / "packages" / "pollenomics" / "README.md").read_text(
            encoding="utf-8"
        )
        runtime_index = (
            REPO_ROOT / "docs" / "01-bijux-pollenomics" / "index.md"
        ).read_text(encoding="utf-8")
        data_index = (
            REPO_ROOT / "docs" / "02-bijux-pollenomics-data" / "index.md"
        ).read_text(encoding="utf-8")
        atlas_index = (
            REPO_ROOT / "docs" / "05-nordic-evidence-atlas" / "index.md"
        ).read_text(encoding="utf-8")
        atlas_files = sorted(
            path.name
            for path in (REPO_ROOT / "docs" / "05-nordic-evidence-atlas").glob("*.md")
        )

        self.assertIn("pollenomics and environmental evidence repository", root_readme)
        self.assertIn(
            "animal aDNA sample extraction and atlas publication path is still under recovery",
            root_readme,
        )
        self.assertIn(
            "pollenomics, environmental, archaeology, boundary, fieldwork, and ancient-DNA",
            runtime_readme,
        )
        self.assertIn("same pollenomics-first runtime behavior", alias_readme)
        self.assertIn(
            "checked-in evidence surfaces across pollen context", runtime_index
        )
        self.assertIn("pollen context, environmental archaeology", data_index)
        self.assertIn("downstream view of the repository evidence tree", atlas_index)
        self.assertEqual(atlas_files, ["index.md"])
        self.assertIn("How animal points are built", atlas_index)
        self.assertIn("How filters and popups work", atlas_index)
        self.assertIn("Current limits and audits", atlas_index)

    def test_top_level_landings_keep_pollenomics_scope_and_source_breadth(self) -> None:
        readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8").lower()
        docs_index = (REPO_ROOT / "docs" / "index.md").read_text(encoding="utf-8")
        data_index = (
            REPO_ROOT / "docs" / "02-bijux-pollenomics-data" / "index.md"
        ).read_text(encoding="utf-8")
        source_index = (
            (REPO_ROOT / "docs" / "02-bijux-pollenomics-data" / "sources" / "index.md")
            .read_text(encoding="utf-8")
            .lower()
        )

        for expected in (
            "landclim",
            "neotoma",
            "sead",
            "raä",
            "boundaries",
            "aadr",
        ):
            self.assertIn(expected, readme_text)
            self.assertIn(expected, source_index)
        self.assertIn("Open the repository truth review", docs_index)
        self.assertIn("Open the docs recovery review", docs_index)
        self.assertIn("Open the report portal", docs_index)
        self.assertIn("How to read the report tree", docs_index)
        self.assertIn(
            "pollen-context layers, environmental archaeology context", docs_index
        )
        self.assertIn("source-family comparison", data_index)
        self.assertIn(
            "[report portal](../../report/index.md)",
            (
                REPO_ROOT
                / "docs"
                / "02-bijux-pollenomics-data"
                / "outputs"
                / "published-reports.md"
            ).read_text(encoding="utf-8"),
        )
        self.assertIn(
            "[report portal](../report/index.md)",
            (REPO_ROOT / "docs" / "05-nordic-evidence-atlas" / "index.md").read_text(
                encoding="utf-8"
            ),
        )

    def test_readme_bootstrap_flow_installs_before_running_the_console_script(
        self,
    ) -> None:
        readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        install_index = readme_text.index("make install")
        console_version_index = readme_text.index(
            "artifacts/root/check-venv/bin/bijux-pollenomics --version"
        )

        self.assertLess(install_index, console_version_index)
        self.assertIn("make package-verify", readme_text)

    def test_install_workflow_uses_console_script_smoke_after_install(self) -> None:
        workflow_text = (
            REPO_ROOT
            / "docs"
            / "01-bijux-pollenomics"
            / "operations"
            / "installation-and-setup.md"
        ).read_text(encoding="utf-8")

        install_index = workflow_text.index("make install")
        console_version_index = workflow_text.index(
            "artifacts/root/check-venv/bin/bijux-pollenomics --version"
        )

        self.assertLess(install_index, console_version_index)
        self.assertNotIn(
            "make package-check\nmake package-smoke\nmake package-source-smoke",
            workflow_text,
        )

    def test_command_reference_uses_installed_cli_examples(self) -> None:
        command_reference = (
            REPO_ROOT
            / "docs"
            / "01-bijux-pollenomics"
            / "interfaces"
            / "cli-surface.md"
        ).read_text(encoding="utf-8")

        self.assertIn("collect-data <sources...>", command_reference)
        self.assertIn("adna-layout --species <name>", command_reference)
        self.assertIn("adna-runtime-manifest --species <name>", command_reference)
        self.assertIn("adna-artifact-plan --species <name>", command_reference)
        self.assertIn("adna-curation-manifest --species <name>", command_reference)
        self.assertIn("adna-normalization-bundle --species <name>", command_reference)
        self.assertIn("adna-archive-projects", command_reference)
        self.assertIn("adna-domestication-coverage", command_reference)
        self.assertIn("adna-species", command_reference)
        self.assertIn("adna-species-review --species <name>", command_reference)
        self.assertIn("deterministic species rebuild", command_reference)
        self.assertIn("project summaries, study summaries, lineage", command_reference)
        self.assertIn("curated, pending, and rejected projects", command_reference)
        self.assertIn("cross-species curation coverage", command_reference)
        self.assertIn(
            "project-side metadata that still needs to feed sample extraction",
            command_reference,
        )
        self.assertIn("project admission reviews", command_reference)
        self.assertIn("report-country <country>", command_reference)
        self.assertIn("report-multi-country-map <countries...>", command_reference)
        self.assertIn("publish-reports", command_reference)
        self.assertIn(
            "`--output-root` defaults to `data` for collection", command_reference
        )
        self.assertIn("for collection or `docs/report` for", command_reference)
        self.assertNotIn("python -m bijux_pollenomics.cli", command_reference)

    def test_package_readmes_keep_sharp_audiences(self) -> None:
        runtime_readme = (
            REPO_ROOT / "packages" / "bijux-pollenomics" / "README.md"
        ).read_text(encoding="utf-8")
        alias_readme = (REPO_ROOT / "packages" / "pollenomics" / "README.md").read_text(
            encoding="utf-8"
        )
        maintainer_readme = (
            REPO_ROOT / "packages" / "bijux-pollenomics-dev" / "README.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Use this package if you want the canonical CLI", runtime_readme)
        self.assertIn("tracked source collection, animal aDNA intake", runtime_readme)
        self.assertIn("Alias distribution", alias_readme)
        self.assertIn("Maintainer-only package", maintainer_readme)
        self.assertIn("It is not the owner of runtime commands", maintainer_readme)

    def test_runtime_package_boundary_doc_names_durable_scientific_ownership(
        self,
    ) -> None:
        boundary_doc = (
            REPO_ROOT
            / "packages"
            / "bijux-pollenomics"
            / "src"
            / "bijux_pollenomics"
            / "package_boundaries.md"
        ).read_text(encoding="utf-8")

        self.assertIn("# Runtime Package Boundaries", boundary_doc)
        self.assertIn("## Runtime Command Surface", boundary_doc)
        self.assertIn("## Source Collection And Intake", boundary_doc)
        self.assertIn("## Evidence Normalization", boundary_doc)
        self.assertIn("## Evidence Review", boundary_doc)
        self.assertIn("## Publication Assembly", boundary_doc)
        self.assertIn("## Public Artifact Writing", boundary_doc)
        self.assertIn("## Package Split", boundary_doc)
        self.assertIn("bijux_pollenomics.adna.project_sample_sites", boundary_doc)
        self.assertIn("bijux_pollenomics.reporting.review", boundary_doc)

    def test_module_map_mentions_adna_runtime_boundary(self) -> None:
        module_map = (
            REPO_ROOT
            / "docs"
            / "01-bijux-pollenomics"
            / "architecture"
            / "module-map.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "`command_line/` owns parsing, dispatch, and the durable command registry",
            module_map,
        )
        self.assertIn(
            "`data_downloader/pipeline/`, `data_downloader/sources/`", module_map
        )
        self.assertIn(
            "`analysis/review/` owns candidate-site ranking reviews", module_map
        )
        self.assertIn("`reporting/presentation/`", module_map)
        self.assertIn("`reporting/review/`", module_map)
        self.assertIn("compatibility shims", module_map)
        self.assertIn("alias distribution", module_map)
        self.assertIn("`src/bijux_pollenomics/adna/`", module_map)

    def test_directory_layout_docs_mentions_curated_species_roots(self) -> None:
        directory_layout = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "overview"
            / "data-directory-layout.md"
        ).read_text(encoding="utf-8")

        self.assertIn("species-centered animal ancient DNA recovery", directory_layout)
        self.assertIn("data/adna/final/", directory_layout)
        self.assertIn("`data/adna/species/equus_caballus/`", directory_layout)
        self.assertIn("`data/adna/species/bos_taurus/`", directory_layout)
        self.assertIn("`data/adna/species/canis_lupus_familiaris/`", directory_layout)
        self.assertIn("`data/adna/species/camelus_dromedarius/`", directory_layout)
        self.assertIn("`data/adna/species/rangifer_tarandus/`", directory_layout)
        self.assertIn("`data/adna/species/equus_asinus/`", directory_layout)
        self.assertIn("`data/adna/species/felis_catus/`", directory_layout)

    def test_homo_sapiens_adna_layout_exists_in_tracked_data_tree(self) -> None:
        species_root = REPO_ROOT / "data" / "adna" / "species" / "homo_sapiens"

        self.assertTrue((species_root / "README.md").exists())
        self.assertTrue((species_root / "normalized").is_dir())
        self.assertTrue((species_root / "manifests").is_dir())
        self.assertTrue((species_root / "reports").is_dir())
        self.assertTrue((species_root / "review").is_dir())
        raw_aadr = species_root / "raw" / "aadr"
        self.assertTrue(raw_aadr.is_symlink())
        self.assertEqual(raw_aadr.readlink().as_posix(), "../../../../aadr")

    def test_tracked_nonhuman_adna_roots_ship_real_reviewable_files(self) -> None:
        tracked_roots = (
            "equus_caballus",
            "sus_scrofa_domesticus",
            "ovis_aries",
            "bos_taurus",
            "capra_hircus",
            "canis_lupus_familiaris",
            "felis_catus",
            "camelus_dromedarius",
            "rangifer_tarandus",
            "equus_asinus",
        )

        for slug in tracked_roots:
            species_root = REPO_ROOT / "data" / "adna" / "species" / slug
            self.assertTrue((species_root / "README.md").is_file(), slug)
            self.assertTrue(
                (species_root / "raw" / "archive_inventory.json").is_file(), slug
            )
            self.assertTrue(
                (species_root / "raw" / "archive_inventory.csv").is_file(), slug
            )
            self.assertTrue(
                (species_root / "raw" / "source_snapshot.json").is_file(), slug
            )
            self.assertTrue(
                (species_root / "raw" / "source_snapshot.csv").is_file(), slug
            )
            self.assertTrue(
                (species_root / "normalized" / "sample_records.csv").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "normalized" / "sample_records.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "normalized" / "coordinate_provenance.csv").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "normalized" / "coordinate_provenance.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "normalized" / "site_evidence.csv").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "normalized" / "site_evidence.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "normalized" / "project_summaries.csv").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "normalized" / "project_summaries.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "normalized" / "locality_summaries.csv").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "normalized" / "locality_summaries.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "manifests" / "species_manifest.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "manifests" / "curation_manifest.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "manifests" / "project_manifest.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "manifests" / "runtime_manifest.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "manifests" / "normalization_bundle.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "manifests" / "citation_manifest.csv").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "reports" / "support_summary.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "reports" / "support_summary.md").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "reports" / "project_recovery_deficits.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "reports" / "project_recovery_deficits.md").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "review" / "species_review.json").is_file(),
                slug,
            )
            self.assertTrue(
                (species_root / "review" / "archive_integrity.json").is_file(),
                slug,
            )

    def test_adna_root_keeps_only_named_entrypoints_and_index_files(self) -> None:
        adna_root = REPO_ROOT / "data" / "adna"
        names = {
            path.name for path in adna_root.iterdir() if not path.name.startswith(".")
        }

        self.assertEqual(names, {"README.md", "species", "governance", "final"})

    def test_governance_files_do_not_spill_into_adna_root(self) -> None:
        adna_root = REPO_ROOT / "data" / "adna"
        disallowed_prefixes = (
            "cross_species_",
            "animal_sample_",
            "coordinate_",
            "unresolved_site_",
            "overbroad_site_",
            "shipped_product_",
            "source_",
        )
        offenders = [
            path.name
            for path in adna_root.iterdir()
            if path.is_file() and path.name.startswith(disallowed_prefixes)
        ]

        self.assertFalse(
            offenders,
            f"data/adna root contains governance-style files: {offenders}",
        )

    def test_cross_species_publishable_outputs_live_under_adna_final(self) -> None:
        final_root = REPO_ROOT / "data" / "adna" / "final"

        self.assertTrue(
            (final_root / "atlas" / "animal_atlas_point_candidates.json").is_file()
        )
        self.assertTrue(
            (final_root / "atlas" / "animal_atlas_point_candidates.csv").is_file()
        )
        self.assertTrue(
            (final_root / "countries" / "country_publication_index.json").is_file()
        )
        self.assertTrue(
            (final_root / "countries" / "country_publication_index.csv").is_file()
        )

    def test_mkdocs_uses_main_branch_edit_links_and_local_mermaid_bundle(self) -> None:
        mkdocs_text = (REPO_ROOT / "mkdocs.yml").read_text(encoding="utf-8")

        self.assertIn("https://bijux.io/bijux-pollenomics/", mkdocs_text)
        self.assertIn("edit/main/docs/", mkdocs_text)
        self.assertIn("https://bijux.io/bijux-core/", mkdocs_text)
        self.assertNotIn("bijux-genomics", mkdocs_text)
        self.assertIn("site_dir: artifacts/root/docs/site", mkdocs_text)
        self.assertIn("custom_dir: docs/overrides", mkdocs_text)
        self.assertIn(
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/docs",
            mkdocs_text,
        )
        self.assertNotIn(
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev\n",
            mkdocs_text,
        )
        self.assertNotIn("docs/hooks/publish_site_assets.py", mkdocs_text)
        self.assertTrue(
            (
                REPO_ROOT
                / "docs"
                / "assets"
                / "javascripts"
                / "vendor"
                / "mermaid-11.6.0.min.js"
            ).exists()
        )
        self.assertNotIn("cdn.jsdelivr.net/npm/mermaid", mkdocs_text)

    def test_docs_header_uses_repository_label_for_repository_handbook(self) -> None:
        header_text = (
            REPO_ROOT / "docs" / "overrides" / "partials" / "header.html"
        ).read_text(encoding="utf-8")

        self.assertIn('title == "Repository Handbook"', header_text)
        self.assertIn("Repository", header_text)
        self.assertNotIn("\n    Home\n", header_text)

    def test_docs_keep_browser_icon_sources_under_assets(self) -> None:
        self.assertTrue(
            (REPO_ROOT / "docs" / "assets" / "site-icons" / "favicon.ico").exists()
        )
        self.assertTrue(
            (
                REPO_ROOT / "docs" / "assets" / "site-icons" / "apple-touch-icon.png"
            ).exists()
        )
        self.assertTrue(
            (
                REPO_ROOT
                / "docs"
                / "assets"
                / "site-icons"
                / "apple-touch-icon-precomposed.png"
            ).exists()
        )
        self.assertTrue(
            (REPO_ROOT / "docs" / "overrides" / "partials" / "header.html").exists()
        )
        self.assertFalse((REPO_ROOT / "docs" / "favicon.ico").exists())
        self.assertFalse((REPO_ROOT / "docs" / "apple-touch-icon.png").exists())
        self.assertFalse(
            (REPO_ROOT / "docs" / "apple-touch-icon-precomposed.png").exists()
        )
        self.assertFalse((REPO_ROOT / "docs" / "outputs" / "gallery").exists())

    def test_navigation_sync_bootstraps_shared_navigation_shell(self) -> None:
        script_text = (
            REPO_ROOT / "docs" / "assets" / "javascripts" / "navigation-sync.js"
        ).read_text(encoding="utf-8")
        nav_state_text = (
            REPO_ROOT / "docs" / "assets" / "javascripts" / "shell" / "nav-state.js"
        ).read_text(encoding="utf-8")
        detail_tabs_text = (
            REPO_ROOT / "docs" / "assets" / "javascripts" / "shell" / "detail-tabs.js"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "window.bijuxShell?.bootstrap?.ensureBound",
            script_text,
        )
        self.assertIn(
            "[data-bijux-site-path][aria-current='page']",
            nav_state_text,
        )
        self.assertIn(
            "[data-bijux-detail-path][aria-current='page']",
            detail_tabs_text,
        )

    def test_fieldwork_page_embeds_video_from_site_root_gallery(self) -> None:
        fieldwork_text = (
            REPO_ROOT / "docs" / "04-fieldwork" / "lyngsjon-lake-fieldwork" / "index.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            '<source src="../../gallery/2026-02-26-data-collection.mp4"',
            fieldwork_text,
        )
        self.assertIn(
            '<a href="../../gallery/2026-02-26-data-collection.mp4">',
            fieldwork_text,
        )

    def test_github_workflows_cover_repository_checks_and_docs_deploy(self) -> None:
        ci_workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        release_artifacts_workflow = (
            REPO_ROOT / ".github" / "workflows" / "release-artifacts.yml"
        ).read_text(encoding="utf-8")
        release_pypi_workflow = (
            REPO_ROOT / ".github" / "workflows" / "release-pypi.yml"
        ).read_text(encoding="utf-8")
        release_ghcr_workflow = (
            REPO_ROOT / ".github" / "workflows" / "release-ghcr.yml"
        ).read_text(encoding="utf-8")
        release_github_workflow = (
            REPO_ROOT / ".github" / "workflows" / "release-github.yml"
        ).read_text(encoding="utf-8")
        verify_workflow = (
            REPO_ROOT / ".github" / "workflows" / "verify.yml"
        ).read_text(encoding="utf-8")
        deploy_workflow = (
            REPO_ROOT / ".github" / "workflows" / "deploy-docs.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("workflow_call:", ci_workflow)
        self.assertIn(
            "tests-${{ inputs.package_slug }}-py${{ matrix.python-version }}",
            ci_workflow,
        )
        self.assertIn(
            "checks-${{ inputs.package_slug }}-${{ matrix.target }}",
            ci_workflow,
        )
        self.assertIn("lint-${{ inputs.package_slug }}", ci_workflow)
        self.assertIn("cache-dependency-glob: uv.lock", ci_workflow)
        self.assertIn('make -f \\"$makefile\\" -C', ci_workflow)
        self.assertIn("name: release-artifacts", release_artifacts_workflow)
        self.assertIn('find "$dist_dir" -type f', release_artifacts_workflow)
        self.assertIn(
            "No publish artifacts found under $dist_dir",
            release_artifacts_workflow,
        )
        self.assertIn(
            "name: release-artifacts-${{ inputs.package_slug }}",
            release_artifacts_workflow,
        )
        self.assertIn("Stage GitHub release assets", release_artifacts_workflow)
        self.assertIn('sbom_dir="${ARTIFACTS_DIR}/sbom"', release_artifacts_workflow)
        self.assertIn("-dist-$(basename", release_artifacts_workflow)
        self.assertIn("-sbom-prod.cdx.json", release_artifacts_workflow)
        self.assertIn("-sbom-dev.cdx.json", release_artifacts_workflow)
        self.assertIn("-sbom-summary.txt", release_artifacts_workflow)
        self.assertIn("name: release-pypi", release_pypi_workflow)
        self.assertIn("pypa/gh-action-pypi-publish@", release_pypi_workflow)
        self.assertIn("publish_auth_default", release_pypi_workflow)
        self.assertIn("PYPI_API_TOKEN", release_pypi_workflow)
        self.assertIn("name: release-ghcr", release_ghcr_workflow)
        self.assertIn("packages: write", release_ghcr_workflow)
        self.assertIn("name: release-github", release_github_workflow)
        self.assertIn("softprops/action-gh-release@", release_github_workflow)
        self.assertIn("overwrite_files: true", release_github_workflow)
        self.assertIn("check-shared-bijux-py", verify_workflow)
        self.assertIn("check-config-layout", verify_workflow)
        self.assertIn("check-make-layout", verify_workflow)
        self.assertIn('"apis/**"', verify_workflow)
        self.assertIn("mkdocs.shared.yml", verify_workflow)
        self.assertIn("tox.ini", verify_workflow)
        self.assertIn(
            "make check-shared-bijux-py check-config-layout check-make-layout help",
            verify_workflow,
        )
        self.assertIn("uses: ./.github/workflows/ci.yml", verify_workflow)
        self.assertIn("bijux-pollenomics-dev", verify_workflow)
        self.assertIn("openapi-drift", verify_workflow)
        self.assertIn("check_targets:", verify_workflow)
        self.assertIn("api_toolchain_targets:", verify_workflow)
        self.assertIn("pull_request:", verify_workflow)
        self.assertIn("astral-sh/setup-uv", verify_workflow)
        self.assertIn("workflow_dispatch:", deploy_workflow)
        self.assertIn("workflow_call:", deploy_workflow)
        self.assertIn("astral-sh/setup-uv", deploy_workflow)
        self.assertIn("pages: write", deploy_workflow)
        self.assertIn("id-token: write", deploy_workflow)
        self.assertIn("actions/configure-pages@", deploy_workflow)
        self.assertIn("actions/upload-pages-artifact@", deploy_workflow)
        self.assertIn("actions/deploy-pages@", deploy_workflow)
        self.assertIn("github.ref == 'refs/heads/main'", deploy_workflow)
        self.assertIn("github.ref == 'refs/heads/master'", deploy_workflow)
        self.assertIn("startsWith(github.ref, 'refs/tags/v')", deploy_workflow)
        self.assertIn("site_dir", deploy_workflow)
        self.assertIn("artifacts/root/docs/build-site", deploy_workflow)
        self.assertIn("mkdocs.shared.yml", deploy_workflow)

    def test_root_readme_workflow_links_follow_checked_in_workflow_tree(self) -> None:
        readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        workflows_dir = REPO_ROOT / ".github" / "workflows"
        known_workflows = {path.name for path in workflows_dir.glob("*.yml")}
        found_workflows = set()

        for match in WORKFLOW_URL_RE.finditer(readme_text):
            self.assertEqual(match.group("repo"), "bijux/bijux-pollenomics")
            workflow_name = match.group("workflow")
            self.assertIn(workflow_name, known_workflows)
            found_workflows.add(workflow_name)

        self.assertTrue(
            {
                "verify.yml",
                "release-pypi.yml",
                "release-ghcr.yml",
                "release-github.yml",
                "deploy-docs.yml",
            }
            <= found_workflows
        )

    def test_report_docs_describe_final_summary_paths(self) -> None:
        published_artifacts = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "outputs"
            / "published-reports.md"
        ).read_text(encoding="utf-8")
        atlas_outputs = (
            REPO_ROOT
            / "docs"
            / "02-bijux-pollenomics-data"
            / "outputs"
            / "geographic-evidence-surfaces.md"
        ).read_text(encoding="utf-8")
        report_layout = (
            REPO_ROOT
            / "docs"
            / "01-bijux-pollenomics"
            / "interfaces"
            / "artifact-contracts.md"
        ).read_text(encoding="utf-8")
        quality_index = (
            REPO_ROOT / "docs" / "01-bijux-pollenomics" / "quality" / "index.md"
        ).read_text(encoding="utf-8")
        documentation_integrity = (
            REPO_ROOT
            / "docs"
            / "03-bijux-pollenomics-maintain"
            / "bijux-pollenomics-dev"
            / "documentation-integrity.md"
        ).read_text(encoding="utf-8")
        release_support = (
            REPO_ROOT
            / "docs"
            / "03-bijux-pollenomics-maintain"
            / "bijux-pollenomics-dev"
            / "release-support.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "Published report bundles now live under one governed geography tree:",
            published_artifacts,
        )
        self.assertIn(
            "../../report/repository_truth_posture.md",
            atlas_outputs,
        )
        self.assertIn(
            "../../report/repository_claim_audit.md",
            atlas_outputs,
        )
        self.assertIn(
            "country bundles under `docs/report/countries/<country-slug>/`",
            report_layout,
        )
        self.assertIn(
            "the world surface under `docs/report/world/` and regional surfaces under `docs/report/regions/`",
            report_layout,
        )
        self.assertIn(
            "repository truth reviews",
            report_layout,
        )
        self.assertIn(
            "../../report/repository_truth_posture.md",
            quality_index,
        )
        self.assertIn(
            "../../report/repository_claim_audit.md",
            documentation_integrity,
        )
        self.assertIn(
            "../../report/repository_governance_artifact_review.md",
            release_support,
        )

    def test_engineering_docs_describe_clean_verification_and_docs_asset_checks(
        self,
    ) -> None:
        automation_workflows = (
            REPO_ROOT
            / "docs"
            / "03-bijux-pollenomics-maintain"
            / "gh-workflows"
            / "deploy-docs.md"
        ).read_text(encoding="utf-8")
        testing_and_evidence = (
            REPO_ROOT
            / "docs"
            / "03-bijux-pollenomics-maintain"
            / "bijux-pollenomics-dev"
            / "documentation-integrity.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "`deploy-docs.yml` builds the strict MkDocs site", automation_workflows
        )
        self.assertIn(
            "workflow follows the shared Bijux docs contract",
            automation_workflows,
        )
        self.assertIn("`mkdocs.shared.yml`", automation_workflows)
        self.assertIn("strict MkDocs builds", testing_and_evidence)
        self.assertIn("`docs/assets/site-icons/`", testing_and_evidence)
        self.assertIn("shared Bijux docs theme contract", testing_and_evidence)

    def test_notice_file_keeps_copyright_holder(self) -> None:
        notice_text = (REPO_ROOT / "NOTICE").read_text(encoding="utf-8")

        self.assertIn("Bijan Mousavi <bijan@bijux.io>", notice_text)

    def test_repository_does_not_track_generated_cache_files(self) -> None:
        tracked_files = subprocess.run(
            ["git", "ls-files"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()

        generated_cache_files = [
            path
            for path in tracked_files
            if "/__pycache__/" in f"/{path}"
            or path.endswith((".pyc", ".pyo", ".DS_Store"))
        ]

        self.assertEqual(generated_cache_files, [])
