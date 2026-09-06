from __future__ import annotations

import copy
import unittest

from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)

from tests.support.neotoma import download_row


class NeotomaRelationalMultiplicityTests(unittest.TestCase):
    def test_identical_source_rows_preserve_multiplicity_with_stable_ids(self) -> None:
        row = download_row()
        sample = row["site"]["collectionunit"]["dataset"]["samples"][0]
        sample["ages"].append(copy.deepcopy(sample["ages"][0]))
        sample["datum"].append(copy.deepcopy(sample["datum"][0]))

        payload = build_neotoma_relational_snapshot(
            [row], source_snapshot_id="sha256:fixture", build_id="fixture-build"
        )

        self.assertEqual(len(payload["age_claims"]), 3)
        self.assertEqual(len(payload["observations"]), 3)
        self.assertEqual(
            len({claim["chronology_claim_id"] for claim in payload["age_claims"]}),
            3,
        )
        self.assertEqual(
            len(
                {
                    observation["observation_id"]
                    for observation in payload["observations"]
                }
            ),
            3,
        )
