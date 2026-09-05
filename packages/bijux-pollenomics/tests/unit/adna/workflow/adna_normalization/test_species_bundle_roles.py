from __future__ import annotations

import unittest

from bijux_pollenomics.adna import (
    ADNA_DOMESTICATION_STATUSES,
    build_species_normalization_bundle,
)

from .marks import GENERATED_ARTIFACTS

pytestmark = GENERATED_ARTIFACTS


class AdnaNormalizationUnitTests(unittest.TestCase):
    def test_species_normalization_bundle_marks_donkey_as_comparator_only(self) -> None:
        bundle = build_species_normalization_bundle("donkey")

        self.assertEqual(bundle.species.latin_name, "Equus asinus")
        self.assertIn("comparator_only", ADNA_DOMESTICATION_STATUSES)
        self.assertTrue(
            all(item.comparator_status for item in bundle.project_summaries)
        )
        self.assertTrue(
            all(
                item.domestication_status == "comparator_only"
                for item in bundle.project_summaries
            )
        )
        self.assertTrue(
            {item.support_class for item in bundle.project_summaries}.issubset(
                {"comparator_only", "rejected_or_out_of_scope"}
            )
        )

    def test_species_normalization_bundle_marks_unresolved_sample_context_explicitly(
        self,
    ) -> None:
        bundle = build_species_normalization_bundle("horse")
        sample = next(
            item
            for item in bundle.sample_records
            if item.project_accession == "PRJEB44430"
            and item.locality_identity.locality_text == "Ginnerup"
        )

        self.assertEqual(sample.inclusion_status, "site_curated")
        self.assertEqual(sample.coordinate_confidence, "exact")
        self.assertEqual(sample.paper_doi, "10.1038/s41586-021-04018-9")
        self.assertEqual(sample.chronology_strength, "sample_owned_interval")
        self.assertEqual(sample.chronology_normalization_status, "normalized_point")
        self.assertEqual(sample.chronology.evidence_class, "direct_radiocarbon_date")
        self.assertEqual(sample.chronology.precision_posture, "sample_precise_point")
        self.assertEqual(sample.political_entity, "Denmark")
        self.assertEqual(sample.full_date, "4961 BP")

    def test_species_normalization_bundle_marks_bovine_progenitor_context_explicitly(
        self,
    ) -> None:
        bundle = build_species_normalization_bundle("cattle")
        aurochs_project = next(
            item
            for item in bundle.project_summaries
            if item.project_accession == "PRJEB75467"
        )

        self.assertEqual(
            aurochs_project.domestication_scope, "wild_or_progenitor_context"
        )
        self.assertEqual(aurochs_project.support_class, "wild_or_progenitor_context")
        self.assertIn(
            "wild or progenitor context", aurochs_project.interpretation_caveat
        )
        galician_sample = next(
            item
            for item in bundle.sample_records
            if item.project_accession == "PRJNA705960"
        )
        self.assertEqual(
            galician_sample.chronology.evidence_class, "archaeological_context_date"
        )
        self.assertEqual(
            galician_sample.chronology.precision_posture, "contextual_interval"
        )

    def test_species_normalization_bundle_marks_reindeer_locality_as_comparator_context(
        self,
    ) -> None:
        bundle = build_species_normalization_bundle("reindeer")
        locality = next(
            item
            for item in bundle.locality_records
            if "PRJEB60484" in item.project_accessions
        )

        self.assertTrue(locality.nordic_inclusion)
        self.assertIn("region or transect scale", locality.interpretation_note)
        sample = next(
            item
            for item in bundle.sample_records
            if item.project_accession == "PRJEB60484"
        )
        self.assertEqual(sample.chronology.precision_posture, "contextual_interval")
