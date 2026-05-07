from __future__ import annotations

import unittest

from bijux_pollenomics.adna import (
    ADNA_DOMESTICATION_STATUSES,
    build_species_normalization_bundle,
    normalize_breed_label,
    normalize_chronology_text,
    normalize_coordinate_resolution,
    normalize_explicit_bp_window,
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
        self.assertTrue(bundle.lineage_records)
        self.assertTrue(bundle.refusals)
        project = next(
            item
            for item in bundle.project_summaries
            if item.project_accession == "PRJEB22390"
        )
        self.assertEqual(project.domestication_status, "domesticated_core")
        self.assertEqual(project.support_class, "domesticated_core_curated")
        self.assertEqual(project.coordinate_policy, "site_level_coordinates_expected")
        self.assertEqual(project.chronology_policy, "bp_interval_expected")
        self.assertEqual(project.paper_url, "https://doi.org/10.1126/science.aao3297")
        self.assertEqual(project.review_strength, "primary_paper_pinned")
        self.assertEqual(
            bundle.lineage_records[0].schema_version,
            "adna-normalization-lineage.v1",
        )

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
        self.assertTrue(
            {
                item.support_class
                for item in bundle.project_summaries
            }.issubset({"comparator_only", "rejected_or_out_of_scope"})
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

    def test_species_normalization_bundle_records_sample_and_locality_refusals(self) -> None:
        bundle = build_species_normalization_bundle("horse")

        refusal_kinds = {item.record_kind for item in bundle.refusals}
        self.assertIn("sample_records", refusal_kinds)
        self.assertIn("locality_records", refusal_kinds)

    def test_species_normalization_bundle_carries_nordic_context_and_caveats(self) -> None:
        sheep_bundle = build_species_normalization_bundle("sheep")
        sheep_project = next(
            item
            for item in sheep_bundle.project_summaries
            if item.project_accession == "PRJEB59481"
        )
        camel_bundle = build_species_normalization_bundle("camel")
        camel_project = next(
            item
            for item in camel_bundle.project_summaries
            if item.project_accession == "SRP073444"
        )

        self.assertEqual(sheep_project.nordic_relevance, "nordic_relevant_unmapped")
        self.assertIn("unmapped", sheep_project.interpretation_caveat)
        self.assertEqual(camel_project.nordic_relevance, "non_nordic")
        self.assertIn("not as shipped Nordic evidence", camel_project.interpretation_caveat)

    def test_species_normalization_bundle_marks_bovine_progenitor_context_explicitly(
        self,
    ) -> None:
        bundle = build_species_normalization_bundle("cattle")
        aurochs_project = next(
            item
            for item in bundle.project_summaries
            if item.project_accession == "PRJEB75467"
        )

        self.assertEqual(aurochs_project.domestication_scope, "wild_or_progenitor_context")
        self.assertEqual(aurochs_project.support_class, "wild_or_progenitor_context")
        self.assertIn("wild or progenitor context", aurochs_project.interpretation_caveat)

    def test_normalize_species_anchor_accepts_alias_and_rejects_mismatch(self) -> None:
        species = normalize_species_anchor("pig", expected_species_name="Sus scrofa domesticus")

        self.assertEqual(species.latin_name, "Sus scrofa domesticus")
        with self.assertRaisesRegex(ValueError, "Species anchor mismatch"):
            normalize_species_anchor("horse", expected_species_name="pig")

    def test_normalize_breed_label_keeps_meaningful_text_only(self) -> None:
        self.assertEqual(normalize_breed_label(" Przewalski_Associated "), "przewalski associated")
        self.assertIsNone(normalize_breed_label("unknown"))
        self.assertIsNone(normalize_breed_label("   "))

    def test_normalize_coordinate_resolution_parses_pairs_and_allows_withheld(self) -> None:
        exact = normalize_coordinate_resolution(
            latitude_text="59.1",
            longitude_text="17.3",
            geographic_basis="exact_coordinates",
        )
        withheld = normalize_coordinate_resolution(
            latitude_text="",
            longitude_text="",
            geographic_basis="country_only",
        )

        self.assertEqual(exact.confidence, "exact")
        self.assertIsNotNone(exact.coordinate)
        assert exact.coordinate is not None
        self.assertEqual(exact.coordinate.latitude, 59.1)
        self.assertIsNone(withheld.coordinate)
        self.assertEqual(withheld.confidence, "withheld")

    def test_normalize_coordinate_resolution_refuses_invalid_pairs(self) -> None:
        with self.assertRaisesRegex(ValueError, "both latitude and longitude"):
            normalize_coordinate_resolution(
                latitude_text="59.1",
                longitude_text="",
                geographic_basis="site_level_localities",
            )
        with self.assertRaisesRegex(ValueError, "Latitude out of range"):
            normalize_coordinate_resolution(
                latitude_text="120",
                longitude_text="17.3",
                geographic_basis="site_level_localities",
            )

    def test_normalize_chronology_text_parses_bp_and_calendar_ranges(self) -> None:
        bp_window = normalize_chronology_text("1200-1500 BP", dating_basis="radiocarbon")
        cal_bce = normalize_chronology_text(
            "803-425 calBCE (2562±47 BP)",
            dating_basis="mixed_radiocarbon_and_archaeological_context",
        )
        vague = normalize_chronology_text(
            "Late Bronze Age",
            dating_basis="archaeological_period",
        )

        self.assertEqual((bp_window.time_start_bp, bp_window.time_end_bp), (1200, 1500))
        self.assertEqual(cal_bce.time_start_bp, 2374)
        self.assertEqual(cal_bce.time_end_bp, 2752)
        self.assertIsNone(vague.time_start_bp)
        self.assertEqual(vague.dating_basis, "archaeological_period")

    def test_normalize_explicit_bp_window_refuses_inverted_ranges(self) -> None:
        chronology = normalize_explicit_bp_window(
            1200,
            1500,
            original_text="1200-1500 BP",
        )

        self.assertEqual(chronology.time_mean_bp, 1350)
        with self.assertRaisesRegex(ValueError, "younger-to-older"):
            normalize_explicit_bp_window(1500, 1200, original_text="1500-1200 BP")

    def test_homo_sapiens_normalization_bundle_is_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "Homo sapiens normalization"):
            build_species_normalization_bundle("Homo sapiens")


if __name__ == "__main__":
    unittest.main()
