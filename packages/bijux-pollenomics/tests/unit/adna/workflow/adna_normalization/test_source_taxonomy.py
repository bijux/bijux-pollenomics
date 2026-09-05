from __future__ import annotations

import unittest

from bijux_pollenomics.adna import build_species_normalization_bundle

from .marks import GENERATED_ARTIFACTS

pytestmark = GENERATED_ARTIFACTS


class AdnaNormalizationUnitTests(unittest.TestCase):
    def test_source_native_taxonomy_survives_normalization(self) -> None:
        cattle = build_species_normalization_bundle("cattle")
        aurochs = next(
            row
            for row in cattle.sample_records
            if row.source_native_scientific_name == "Bos primigenius"
        )

        self.assertEqual(aurochs.source_native_tax_id, "9909")
        self.assertEqual(aurochs.species_latin_name, "Bos taurus")
        self.assertEqual(aurochs.taxon_alignment_status, "project_species_mismatch")
        self.assertEqual(
            aurochs.as_dict()["source_native_scientific_name"], "Bos primigenius"
        )
