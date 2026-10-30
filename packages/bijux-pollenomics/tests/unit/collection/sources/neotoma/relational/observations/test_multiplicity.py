from __future__ import annotations

import copy
import unittest

from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from tests.support.neotoma import download_row
from tests.support.neotoma.relational_shapes import mapping, nested, rows


class NeotomaRelationalMultiplicityTests(unittest.TestCase):
    def test_identical_source_rows_preserve_multiplicity_with_stable_ids(self) -> None:
        row = download_row()
        sample = rows(nested(row, "site", "collectionunit", "dataset")["samples"])[0]
        ages = sample["ages"]
        datum = sample["datum"]
        assert isinstance(ages, list)
        assert isinstance(datum, list)
        ages.append(copy.deepcopy(mapping(ages[0])))
        datum.append(copy.deepcopy(mapping(datum[0])))

        payload = build_neotoma_relational_snapshot(
            [row], source_snapshot_id="sha256:fixture", build_id="fixture-build"
        )

        self.assertEqual(len(rows(payload["age_claims"])), 3)
        self.assertEqual(len(rows(payload["observations"])), 3)
        self.assertEqual(
            len(
                {claim["chronology_claim_id"] for claim in rows(payload["age_claims"])}
            ),
            3,
        )
        self.assertEqual(
            len(
                {
                    observation["observation_id"]
                    for observation in rows(payload["observations"])
                }
            ),
            3,
        )
