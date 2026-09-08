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
        self.assertEqual(galician_sample.inclusion_status, "sample_context_blocked")
        self.assertEqual(galician_sample.chronology.evidence_class, "unresolved")
        self.assertEqual(galician_sample.chronology.precision_posture, "unresolved")
        self.assertIsNone(galician_sample.time_start_bp)
        self.assertIsNone(galician_sample.time_end_bp)
        self.assertIsNone(galician_sample.locality)
        self.assertIsNone(galician_sample.coordinates.latitude)
        self.assertIsNone(galician_sample.coordinates.longitude)

    def test_species_normalization_bundle_refuses_unlocated_reindeer_locality(
        self,
    ) -> None:
        bundle = build_species_normalization_bundle("reindeer")
        project = next(
            item
            for item in bundle.project_summaries
            if item.project_accession == "PRJEB60484"
        )

        self.assertEqual(project.domestication_status, "comparator_only")
        self.assertFalse(bundle.locality_records)
        self.assertTrue(
            any(
                refusal.reason == "locality_text_not_evidenced"
                and refusal.source_token == "PRJEB60484:unresolved"
                for refusal in bundle.refusals
            )
        )
        sample = next(
            item
            for item in bundle.sample_records
            if item.project_accession == "PRJEB60484"
        )
        self.assertEqual(sample.inclusion_status, "sample_context_blocked")
        self.assertEqual(sample.chronology.precision_posture, "unresolved")
        self.assertIsNone(sample.time_start_bp)
        self.assertIsNone(sample.time_end_bp)
