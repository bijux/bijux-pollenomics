from __future__ import annotations

import unittest

from bijux_pollenomics.adna import (
    ADNA_MODALITIES,
    ADNA_SUPPORT_STATUSES,
    build_species_support_matrix,
    resolve_species_definition,
)


class AdnaSpeciesSupportUnitTests(unittest.TestCase):
    def test_species_support_matrix_uses_registered_statuses_and_modalities(self) -> None:
        matrix = build_species_support_matrix()

        self.assertGreaterEqual(len(matrix), 10)
        self.assertIn("supported", ADNA_SUPPORT_STATUSES)
        self.assertIn("metadata_only", ADNA_MODALITIES)
        for entry in matrix:
            self.assertIn(entry.support_status, ADNA_SUPPORT_STATUSES)
            for modality in entry.modalities:
                self.assertIn(modality, ADNA_MODALITIES)

    def test_homo_sapiens_is_the_supported_species_for_current_aadr_runtime(self) -> None:
        species = resolve_species_definition("Homo sapiens")

        self.assertEqual(species.slug, "homo_sapiens")
        self.assertEqual(species.support_status, "supported")
        self.assertEqual(species.source_families, ("AADR",))
        self.assertEqual(species.modalities, ("metadata_only",))

    def test_species_resolution_accepts_aliases_and_slugs(self) -> None:
        horse = resolve_species_definition("horse")
        human = resolve_species_definition("homo_sapiens")
        donkey = resolve_species_definition("donkey")

        self.assertEqual(horse.latin_name, "Equus caballus")
        self.assertEqual(human.latin_name, "Homo sapiens")
        self.assertEqual(donkey.support_status, "comparator_only")

    def test_species_resolution_rejects_unknown_species(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported aDNA species"):
            resolve_species_definition("woolly mammoth")


if __name__ == "__main__":
    unittest.main()
