from __future__ import annotations

import unittest

from bijux_pollenomics.adna import build_species_normalization_bundle
from bijux_pollenomics.adna.workflow.normalization import (
    RECOVERED_SAMPLE_EVIDENCE_STATUSES,
)

from .marks import GENERATED_ARTIFACTS

pytestmark = GENERATED_ARTIFACTS


class AdnaNormalizationUnitTests(unittest.TestCase):
    def test_normalized_animal_samples_are_final_non_pollen_evidence(self) -> None:
        self.assertEqual(
            RECOVERED_SAMPLE_EVIDENCE_STATUSES,
            {"archive_native", "article_text_extracted", "direct_table_extracted"},
        )
        bundles = [
            build_species_normalization_bundle(species)
            for species in (
                "horse",
                "pig",
                "sheep",
                "cattle",
                "goat",
                "dog",
                "cat",
                "camel",
                "reindeer",
                "donkey",
            )
        ]
        samples = [sample for bundle in bundles for sample in bundle.sample_records]

        self.assertEqual(len(samples), 1451)
        self.assertEqual(
            sum(
                1
                for bundle in bundles
                for refusal in bundle.refusals
                if refusal.record_kind == "sample_record"
            ),
            38,
        )
        camel = next(
            bundle
            for bundle in bundles
            if bundle.species.latin_name == "Camelus dromedarius"
        )
        experiment_refusals = [
            refusal
            for refusal in camel.refusals
            if refusal.reason == "experiment_to_biological_sample_mapping_unavailable"
        ]
        self.assertEqual(len(experiment_refusals), 20)
        self.assertTrue(
            all(
                "sequencing experiment" in refusal.detail
                for refusal in experiment_refusals
            )
        )
        self.assertTrue(
            all(sample.sample_identity_resolution == "final" for sample in samples)
        )
        self.assertTrue(
            all(
                sample.sample_evidence_status != "not_yet_recoverable"
                for sample in samples
            )
        )
        self.assertTrue(
            all(
                sample.inclusion_status != "sample_context_blocked"
                for sample in samples
            )
        )
        for bundle in bundles:
            payload = bundle.as_dict()
            self.assertEqual(payload["evidence_domain"], "animal_ancient_dna")
            self.assertFalse(payload["pollen_eligible"])
            self.assertFalse(payload["pollen_propagation_eligible"])
