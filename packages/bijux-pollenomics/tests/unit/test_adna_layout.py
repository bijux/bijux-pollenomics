from __future__ import annotations

import unittest

from bijux_pollenomics.adna import build_locality_identity, build_species_layout


class AdnaLayoutUnitTests(unittest.TestCase):
    def test_species_layout_uses_data_adna_latin_slug_root(self) -> None:
        layout = build_species_layout("Homo sapiens")

        self.assertEqual(layout.root_dir, "data/adna/species/homo_sapiens")
        self.assertEqual(layout.raw_dir, "data/adna/species/homo_sapiens/raw")
        self.assertEqual(
            layout.manifests_dir, "data/adna/species/homo_sapiens/manifests"
        )
        self.assertEqual(layout.review_dir, "data/adna/species/homo_sapiens/review")

    def test_locality_identity_is_shared_species_aware_anchor(self) -> None:
        identity = build_locality_identity(
            species_name="Homo sapiens",
            source_family="AADR",
            locality_text="Uppsala",
            political_entity="Sweden",
            latitude_text="59.8586",
            longitude_text="17.6389",
        )

        self.assertEqual(identity.namespace, "homo_sapiens:locality")
        self.assertIn("uppsala", identity.stable_token)
        self.assertEqual(identity.source_anchor_tokens, ("AADR", "59.8586", "17.6389"))


if __name__ == "__main__":
    unittest.main()
