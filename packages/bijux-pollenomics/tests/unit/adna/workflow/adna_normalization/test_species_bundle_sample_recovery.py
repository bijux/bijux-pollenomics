from __future__ import annotations

import unittest

from bijux_pollenomics.adna import build_species_normalization_bundle

from .marks import GENERATED_ARTIFACTS

pytestmark = GENERATED_ARTIFACTS


class AdnaNormalizationUnitTests(unittest.TestCase):
    def test_species_normalization_bundle_records_sample_and_locality_refusals(
        self,
    ) -> None:
        bundle = build_species_normalization_bundle("horse")

        refusal_kinds = {item.record_kind for item in bundle.refusals}
        self.assertIn("locality_records", refusal_kinds)
        self.assertIn("sample_record", refusal_kinds)
        refused_samples = [
            item for item in bundle.refusals if item.record_kind == "sample_record"
        ]
        self.assertEqual(len(refused_samples), 4)
        self.assertTrue(
            all(
                item.reason == "sample_evidence_not_yet_recoverable"
                for item in refused_samples
            )
        )
        self.assertNotIn(
            "PRJEB9799",
            {sample.project_accession for sample in bundle.sample_records},
        )

    def test_species_normalization_bundle_recovers_goat_sample_owned_chronology(
        self,
    ) -> None:
        bundle = build_species_normalization_bundle("goat")

        self.assertEqual(len(bundle.sample_records), 82)
        qinghai_sample = next(
            item
            for item in bundle.sample_records
            if item.project_accession == "PRJNA1328209"
        )
        self.assertEqual(
            qinghai_sample.chronology.evidence_class, "direct_radiocarbon_date"
        )
        self.assertEqual(
            qinghai_sample.chronology.precision_posture, "sample_precise_interval"
        )
        self.assertEqual(
            (qinghai_sample.time_start_bp, qinghai_sample.time_end_bp),
            (3480, 3580),
        )
