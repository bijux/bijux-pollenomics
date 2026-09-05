from __future__ import annotations

import unittest

import pytest

from .repository_paths import (
    REPO_ROOT,
)

pytestmark = pytest.mark.generated_artifacts


class AdnaPublicationOwnershipTests(unittest.TestCase):
    def test_adna_root_keeps_only_named_entrypoints_and_index_files(self) -> None:
        adna_root = REPO_ROOT / "data" / "adna"
        names = {
            path.name for path in adna_root.iterdir() if not path.name.startswith(".")
        }

        self.assertEqual(names, {"README.md", "species", "governance", "final"})


    def test_governance_files_do_not_spill_into_adna_root(self) -> None:
        adna_root = REPO_ROOT / "data" / "adna"
        disallowed_prefixes = (
            "cross_species_",
            "animal_sample_",
            "coordinate_",
            "unresolved_site_",
            "overbroad_site_",
            "shipped_product_",
            "source_",
        )
        offenders = [
            path.name
            for path in adna_root.iterdir()
            if path.is_file() and path.name.startswith(disallowed_prefixes)
        ]

        self.assertFalse(
            offenders,
            f"data/adna root contains governance-style files: {offenders}",
        )


    def test_cross_species_publishable_outputs_live_under_adna_final(self) -> None:
        final_root = REPO_ROOT / "data" / "adna" / "final"

        self.assertTrue(
            (final_root / "atlas" / "animal_atlas_point_candidates.json").is_file()
        )
        self.assertTrue(
            (final_root / "atlas" / "animal_atlas_point_candidates.csv").is_file()
        )
        self.assertTrue(
            (final_root / "countries" / "country_publication_index.json").is_file()
        )
        self.assertTrue(
            (final_root / "countries" / "country_publication_index.csv").is_file()
        )



if __name__ == "__main__":
    unittest.main()
