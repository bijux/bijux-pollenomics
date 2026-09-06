from __future__ import annotations

import unittest

import pytest
import re

from .repository_paths import (
    REPO_ROOT,
)

pytestmark = pytest.mark.generated_artifacts


class AdnaGovernanceArtifactTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
