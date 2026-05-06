from __future__ import annotations

import unittest

from bijux_pollenomics.adna import (
    AdnaArchiveProject,
    build_project_admission_review,
    build_species_archive_projects,
    build_species_dataset_review,
    classify_species_assignment_rule,
    classify_species_product_role,
)


class AdnaGovernanceUnitTests(unittest.TestCase):
    def test_species_product_role_separates_core_from_comparator(self) -> None:
        self.assertEqual(classify_species_product_role("horse"), "domesticated_core")
        self.assertEqual(classify_species_product_role("donkey"), "comparator")
        self.assertEqual(classify_species_product_role("Homo sapiens"), "human_reference")

    def test_species_assignment_rule_flags_equid_comparator_and_cattle_mixed_review(
        self,
    ) -> None:
        self.assertEqual(classify_species_assignment_rule("donkey"), "equid_comparator")
        self.assertEqual(
            classify_species_assignment_rule("Bos taurus"),
            "mixed_species_review_required",
        )

    def test_species_dataset_review_requires_archive_and_primary_paper_for_support(
        self,
    ) -> None:
        horse = build_species_dataset_review("horse")
        human = build_species_dataset_review("Homo sapiens")
        rabbit = build_species_dataset_review("rabbit")

        self.assertEqual(horse.dataset_bucket, "archive_verified_needs_paper_pinning")
        self.assertIn("missing_primary_paper_pins", horse.blocking_reasons)
        self.assertIn("missing_archive_paper_pinning_rationale", horse.blocking_reasons)
        self.assertFalse(horse.eligible_for_supported_status)
        self.assertFalse(horse.release_gate_satisfied)
        self.assertGreater(horse.core_project_count, horse.curated_support_project_count)

        self.assertEqual(human.dataset_bucket, "paper_pinned_core")
        self.assertTrue(human.eligible_for_supported_status)
        self.assertTrue(human.release_gate_satisfied)

        self.assertEqual(rabbit.dataset_bucket, "reject_or_out_of_scope")

    def test_project_admission_review_blocks_core_support_without_primary_paper_anchor(
        self,
    ) -> None:
        project = next(
            row
            for row in build_species_archive_projects("horse")
            if row.project_accession == "PRJEB56293"
        )

        review = build_project_admission_review(project, product_role="domesticated_core")

        self.assertTrue(review.core_project)
        self.assertFalse(review.admissible_for_curated_support)
        self.assertIn("missing_primary_paper_anchor", review.blocking_reasons)
        self.assertIn("missing_archive_paper_pinning_rationale", review.blocking_reasons)

    def test_project_admission_review_accepts_primary_paper_pinned_core_project(self) -> None:
        project = next(
            row
            for row in build_species_archive_projects("goat")
            if row.project_accession == "PRJEB90141"
        )

        review = build_project_admission_review(project, product_role="domesticated_core")

        self.assertTrue(review.core_project)
        self.assertTrue(review.admissible_for_curated_support)
        self.assertEqual(review.blocking_reasons, ())

    def test_project_admission_review_blocks_restricted_archive_even_with_paper_pin(
        self,
    ) -> None:
        review = build_project_admission_review(
            AdnaArchiveProject(
                species_latin_name="Canis lupus familiaris",
                project_accession="SRP000001",
                result_kind="read_run",
                metadata_url="https://www.ncbi.nlm.nih.gov/sra?term=SRP000001",
                source_family="SRA",
                accession_scope="project",
                archive_status="paper_pinned_core",
                notes="restricted dog archive",
                ancient_status="ancient_confirmed",
                sequencing_target="shotgun_genome",
                material_basis="individual_bone_or_tooth",
                dating_basis="archaeological_period_assignment",
                geographic_basis="site_level_localities",
                access_policy="restricted_access",
            ),
            product_role="domesticated_core",
        )

        self.assertFalse(review.admissible_for_curated_support)
        self.assertIn("archive_not_publicly_usable", review.blocking_reasons)

    def test_species_dataset_review_flags_ancient_but_not_domesticated_core_projects(
        self,
    ) -> None:
        review = build_species_dataset_review("Bos taurus")

        self.assertEqual(review.dataset_bucket, "archive_verified_needs_paper_pinning")
        self.assertIn("ancient_but_not_domesticated_core_projects", review.blocking_reasons)


if __name__ == "__main__":
    unittest.main()
