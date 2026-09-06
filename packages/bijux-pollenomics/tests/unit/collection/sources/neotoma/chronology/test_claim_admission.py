from __future__ import annotations

import unittest

from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from tests.support.neotoma import download_row


class NeotomaChronologyClaimAdmissionTests(unittest.TestCase):
    def test_refuses_negative_bp_without_turning_missing_age_into_zero(self) -> None:
        row = download_row()
        sample = row["site"]["collectionunit"]["dataset"]["samples"][0]
        sample["ages"] = [
            {
                "age": -2,
                "ageyounger": None,
                "ageolder": None,
                "agetype": "Calendar years BP",
                "chronologyid": 7001,
            },
            {
                "age": None,
                "ageyounger": None,
                "ageolder": None,
                "agetype": None,
                "chronologyid": None,
            },
            {
                "age": 0,
                "ageyounger": None,
                "ageolder": None,
                "agetype": "Calendar years BP",
                "chronologyid": 7001,
            },
        ]

        payload = build_neotoma_relational_snapshot(
            [row], source_snapshot_id="sha256:fixture", build_id="fixture-build"
        )
        by_status = payload["reconciliation"]["age_comparability_counts"]
        self.assertEqual(by_status, {"comparable": 1, "refused": 1, "unresolved": 1})
        zero = next(
            claim for claim in payload["age_claims"] if claim["source_age_value"] == 0
        )
        missing = next(
            claim
            for claim in payload["age_claims"]
            if claim["source_age_value"] is None
        )
        self.assertEqual((zero["younger_bp"], zero["older_bp"]), (0, 0))
        self.assertIsNone(missing["younger_bp"])
        self.assertIsNone(missing["older_bp"])
