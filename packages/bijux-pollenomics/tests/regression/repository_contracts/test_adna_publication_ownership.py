from __future__ import annotations

import json
import unittest

import pytest
from bijux_pollenomics.adna.governance.audit_catalogs import (
    build_animal_atlas_candidate_accountability,
    build_cross_species_map_readiness,
)
from bijux_pollenomics.core.records import require_record_rows
from bijux_pollenomics.core.tabular import render_csv_rows
from bijux_pollenomics.reporting.adna import (
    build_tracked_animal_atlas_evidence_rows,
)

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

    def test_checked_in_atlas_candidates_match_the_current_builder_exactly(
        self,
    ) -> None:
        data_root = REPO_ROOT / "data"
        atlas_root = data_root / "adna" / "final" / "atlas"
        payload = json.loads(
            (atlas_root / "animal_atlas_point_candidates.json").read_text(
                encoding="utf-8"
            )
        )
        built_rows = build_tracked_animal_atlas_evidence_rows(data_root)

        self.assertEqual(payload["row_count"], len(built_rows))
        built_payloads = tuple(row.as_dict() for row in built_rows)
        self.assertEqual(payload["rows"], list(built_payloads))
        self.assertEqual(
            (atlas_root / "animal_atlas_point_candidates.csv").read_text(
                encoding="utf-8"
            ),
            render_csv_rows(built_payloads),
        )

        accountability = json.loads(
            (atlas_root / "animal_atlas_candidate_accountability.json").read_text(
                encoding="utf-8"
            )
        )
        expected = build_animal_atlas_candidate_accountability(data_root)
        self.assertEqual(accountability, expected)
        self.assertTrue(accountability["overall_ok"])

        readiness = build_cross_species_map_readiness(data_root)
        readiness_root = data_root / "adna" / "governance"
        checked_readiness = json.loads(
            (readiness_root / "cross_species_map_readiness.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(checked_readiness, readiness)
        self.assertEqual(
            (readiness_root / "cross_species_map_readiness.csv").read_text(
                encoding="utf-8"
            ),
            render_csv_rows(require_record_rows(readiness, "rows")),
        )


if __name__ == "__main__":
    unittest.main()
