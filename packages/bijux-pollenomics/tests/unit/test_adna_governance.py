from __future__ import annotations

import unittest

from bijux_pollenomics.adna import (
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
        self.assertFalse(horse.eligible_for_supported_status)

        self.assertEqual(human.dataset_bucket, "paper_pinned_core")
        self.assertTrue(human.eligible_for_supported_status)

        self.assertEqual(rabbit.dataset_bucket, "reject_or_out_of_scope")


if __name__ == "__main__":
    unittest.main()
