from __future__ import annotations

import unittest

from bijux_pollenomics.adna import build_species_normalization_bundle

from .marks import GENERATED_ARTIFACTS

pytestmark = GENERATED_ARTIFACTS


class AdnaNormalizationUnitTests(unittest.TestCase):
    def test_homo_sapiens_normalization_bundle_is_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "Homo sapiens normalization"):
            build_species_normalization_bundle("Homo sapiens")
