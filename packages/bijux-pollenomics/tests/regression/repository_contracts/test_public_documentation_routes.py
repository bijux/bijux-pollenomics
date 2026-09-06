from __future__ import annotations

import unittest

import pytest

from .repository_paths import (
    REPO_ROOT,
)

pytestmark = pytest.mark.generated_artifacts


class PublicDocumentationRouteTests(unittest.TestCase):
    def test_public_docs_keep_direct_public_and_report_routes(
        self,
    ) -> None:
        docs_index = (REPO_ROOT / "docs" / "index.md").read_text(encoding="utf-8")
        sample_page = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "evidence"
            / "sample-records.md"
        ).read_text(encoding="utf-8")
        site_page = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "evidence"
            / "localities.md"
        ).read_text(encoding="utf-8")
        chronology_page = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "evidence"
            / "chronology.md"
        ).read_text(encoding="utf-8")
        temporal_semantics_page = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "evidence"
            / "temporal-semantics.md"
        ).read_text(encoding="utf-8")
        sead_handbook_page = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "sources"
            / "sead-handbook.md"
        ).read_text(encoding="utf-8")
        coordinate_page = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "evidence"
            / "coordinates.md"
        ).read_text(encoding="utf-8")
        source_index = (
            REPO_ROOT / "docs" / "public" / "pollenomics-data" / "sources" / "index.md"
        ).read_text(encoding="utf-8")
        source_family_matrix_page = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "sources"
            / "source-family-matrix.md"
        ).read_text(encoding="utf-8")
        publication_model_page = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "overview"
            / "pollenomics-publication-model.md"
        ).read_text(encoding="utf-8")
        cross_domain_page = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "overview"
            / "cross-domain-evidence-matrix.md"
        ).read_text(encoding="utf-8")
        inventory_page = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "sources"
            / "animal-source-intake.md"
        ).read_text(encoding="utf-8")
        cross_domain_roles_page = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "sources"
            / "cross-domain-source-roles.md"
        ).read_text(encoding="utf-8")
        atlas_index = (
            REPO_ROOT / "docs" / "public" / "nordic-atlas" / "index.md"
        ).read_text(encoding="utf-8")
        published_reports = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "publications"
            / "reports.md"
        ).read_text(encoding="utf-8")
        outputs_index = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "publications"
            / "index.md"
        ).read_text(encoding="utf-8")
        atlas_outputs = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "publications"
            / "maps.md"
        ).read_text(encoding="utf-8")
        atlas_inputs_page = (
            REPO_ROOT
            / "docs"
            / "public"
            / "pollenomics-data"
            / "publications"
            / "map-inputs.md"
        ).read_text(encoding="utf-8")
        sead_review_page = (
            REPO_ROOT / "docs" / "report" / "repository_sead_legibility_review.md"
        ).read_text(encoding="utf-8")

        self.assertIn("public/pollenomics-data/", docs_index)
        self.assertIn("report/", docs_index)
        self.assertIn("public/nordic-atlas/", docs_index)
        self.assertIn(
            "data/adna/governance/source_library/project_sample_master_completeness.json",
            sample_page,
        )
        self.assertIn(
            "data/adna/species/<latin_name>/normalized/sample_records.json",
            sample_page,
        )
        self.assertIn(
            "data/adna/species/<species-slug>/normalized/site_evidence.json",
            site_page,
        )
        self.assertIn(
            "data/adna/governance/source_library/project_sample_chronology_review.json",
            chronology_page,
        )
        self.assertIn(
            "sample_chronology_precision_audit.json",
            chronology_page,
        )
        self.assertIn(
            "data/sead/review/temporal_review.json",
            temporal_semantics_page,
        )
        self.assertIn(
            "data/source_spatiotemporal_posture_registry.json",
            temporal_semantics_page,
        )
        self.assertIn(
            "data/sead/review/access_model.json",
            sead_handbook_page,
        )
        self.assertIn(
            "data/sead/review/recovery_requirements.json",
            sead_handbook_page,
        )
        self.assertIn(
            "data/adna/species/<species-slug>/normalized/coordinate_provenance.json",
            coordinate_page,
        )
        self.assertIn(
            "../../report/animal_atlas_exclusion_report.md",
            atlas_index,
        )
        self.assertIn(
            "../../report/regions/nordic/nordic_map_publication_contract.md",
            atlas_index,
        )
        self.assertIn(
            "../../report/regions/nordic/nordic_point_traceability.md",
            atlas_index,
        )
        self.assertIn(
            "data/collection_summary.json",
            source_index,
        )
        self.assertIn(
            "source-family-matrix.md",
            source_index,
        )
        self.assertIn(
            "../../../report/repository_source_family_matrix.json",
            source_family_matrix_page,
        )
        self.assertIn(
            "data/sead/review/evidence_legibility_review.json", sead_review_page
        )
        self.assertIn(
            "../../../report/repository_cross_domain_evidence_matrix.json",
            source_family_matrix_page,
        )
        self.assertIn(
            "../../../report/repository_source_explainer_audit.md",
            source_family_matrix_page,
        )
        self.assertIn(
            "../../../report/repository_source_acquisition_queue.json",
            source_family_matrix_page,
        )
        self.assertIn(
            "../../../report/repository_cross_domain_evidence_matrix.md",
            cross_domain_page,
        )
        self.assertIn(
            "../../../report/repository_atlas_input_audit.md",
            cross_domain_page,
        )
        self.assertIn("cross-domain evidence matrix", publication_model_page.lower())
        self.assertIn(
            "data/adna/governance/source_library/project_registry.json",
            inventory_page,
        )
        self.assertIn("source_bundle_path", inventory_page)
        self.assertIn("data/adna/species/<species-slug>/", inventory_page)
        self.assertIn(
            "data/adna/governance/source_library/projects/<project-accession>/",
            inventory_page,
        )
        self.assertIn("sample_master.json", inventory_page)
        self.assertIn("sample_locality_evidence.json", inventory_page)
        self.assertIn("sample_chronology_evidence.json", inventory_page)
        self.assertIn(
            "observation unit",
            cross_domain_roles_page,
        )
        self.assertIn("temporal posture", cross_domain_roles_page)
        self.assertIn("evidence roles", cross_domain_roles_page)
        self.assertIn(
            "../../../report/animal_sample_database_review.md",
            published_reports,
        )
        self.assertIn(
            "../../../report/animal_intake_recovery_review.md",
            published_reports,
        )
        self.assertIn(
            "../../../report/animal_point_evidence_review.md",
            published_reports,
        )
        self.assertIn("../../../report/animal_output_honesty.md", published_reports)
        self.assertIn(
            "../../../report/animal_atlas_exclusion_report.md",
            published_reports,
        )
        self.assertIn(
            "../../../report/world/world_map_publication_contract.md",
            published_reports,
        )
        self.assertIn(
            "../../../report/regions/nordic/nordic_point_traceability.md",
            published_reports,
        )
        self.assertIn(
            "../../../report/repository_truth_posture.md",
            published_reports,
        )
        self.assertIn(
            "../../../report/repository_source_family_matrix.md",
            published_reports,
        )
        self.assertIn("publication-types.md", outputs_index)
        self.assertIn("point-rules.md", outputs_index)
        self.assertIn("filters-and-popups.md", outputs_index)
        self.assertIn("limits.md", outputs_index)
        self.assertIn(
            "../../../report/world/world_map_publication_contract.md",
            atlas_outputs,
        )
        self.assertIn(
            "../../../report/regions/nordic/nordic_point_traceability.md",
            atlas_outputs,
        )
        self.assertIn(
            "../../../report/repository_atlas_input_audit.md",
            atlas_inputs_page,
        )
        self.assertIn(
            "../../../report/repository_cross_domain_evidence_matrix.md",
            atlas_inputs_page,
        )
        self.assertIn(
            "../../../report/countries/sweden/sweden_animal_adna_v66_samples.md",
            published_reports,
        )
        self.assertIn("../../../report/countries/sweden/README.md", published_reports)
        self.assertIn("animal_atlas_candidate_accountability.md", atlas_outputs)


if __name__ == "__main__":
    unittest.main()
