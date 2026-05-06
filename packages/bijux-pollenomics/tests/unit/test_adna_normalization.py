from __future__ import annotations

import unittest

from bijux_pollenomics.adna import (
    ADNA_DOMESTICATION_STATUSES,
    build_species_normalization_bundle,
    normalize_breed_label,
    normalize_species_anchor,
)


class AdnaNormalizationUnitTests(unittest.TestCase):
    def test_species_normalization_bundle_builds_project_and_study_summaries_for_horse(
        self,
    ) -> None:
        bundle = build_species_normalization_bundle("horse")

        self.assertEqual(
            bundle.schema_version,
            "adna-nonhuman-normalization-bundle.v1",
        )
        self.assertEqual(bundle.species.latin_name, "Equus caballus")
        self.assertEqual(bundle.sample_records, ())
        self.assertEqual(bundle.locality_records, ())
        self.assertTrue(bundle.project_summaries)
        self.assertTrue(bundle.study_summaries)
        project = next(
            item
            for item in bundle.project_summaries
            if item.project_accession == "PRJEB22390"
        )
        self.assertEqual(project.domestication_status, "domesticated_core")
        self.assertEqual(project.coordinate_policy, "site_level_coordinates_expected")
        self.assertEqual(project.chronology_policy, "bp_interval_expected")
        self.assertEqual(project.review_strength, "primary_paper_pinned")

    def test_species_normalization_bundle_marks_donkey_as_comparator_only(self) -> None:
        bundle = build_species_normalization_bundle("donkey")

        self.assertEqual(bundle.species.latin_name, "Equus asinus")
        self.assertIn("comparator_only", ADNA_DOMESTICATION_STATUSES)
        self.assertTrue(all(item.comparator_status for item in bundle.project_summaries))
        self.assertTrue(
            all(
                item.domestication_status == "comparator_only"
                for item in bundle.project_summaries
            )
        )

    def test_species_normalization_bundle_deduplicates_project_tokens_deterministically(
        self,
    ) -> None:
        first = build_species_normalization_bundle("horse")
        second = build_species_normalization_bundle("horse")

        self.assertEqual(
            [item.summary_token for item in first.project_summaries],
            sorted(item.summary_token for item in first.project_summaries),
        )
        self.assertEqual(first.as_dict(), second.as_dict())

    def test_normalize_species_anchor_accepts_alias_and_rejects_mismatch(self) -> None:
        species = normalize_species_anchor("pig", expected_species_name="Sus scrofa domesticus")

        self.assertEqual(species.latin_name, "Sus scrofa domesticus")
        with self.assertRaisesRegex(ValueError, "Species anchor mismatch"):
            normalize_species_anchor("horse", expected_species_name="pig")

    def test_normalize_breed_label_keeps_meaningful_text_only(self) -> None:
        self.assertEqual(normalize_breed_label(" Przewalski_Associated "), "przewalski associated")
        self.assertIsNone(normalize_breed_label("unknown"))
        self.assertIsNone(normalize_breed_label("   "))

    def test_homo_sapiens_normalization_bundle_is_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "Homo sapiens normalization"):
            build_species_normalization_bundle("Homo sapiens")


if __name__ == "__main__":
    unittest.main()
