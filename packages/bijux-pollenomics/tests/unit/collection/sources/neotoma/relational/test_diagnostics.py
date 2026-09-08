from __future__ import annotations

import unittest

from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from tests.support.neotoma import download_row


class NeotomaRelationalDiagnosticTests(unittest.TestCase):
    def test_missing_chronology_identifiers_are_preserved_and_reported(self) -> None:
        row = download_row()
        chronology = row["site"]["collectionunit"]["chronologies"][0]["chronology"]
        chronology["chronologyid"] = None
        chronology["chroncontrols"][0]["chroncontrolid"] = None
        row["site"]["collectionunit"]["defaultchronology"] = 7002

        payload = build_neotoma_relational_snapshot(
            [row], source_snapshot_id="sha256:fixture", build_id="fixture-build"
        )

        self.assertEqual(len(payload["chronologies"]), 2)
        self.assertEqual(len(payload["chronology_controls"]), 1)
        self.assertEqual(payload["reconciliation"]["orphan_count"], 3)
        self.assertEqual(
            {orphan["entity_type"] for orphan in payload["orphans"]},
            {"chronology", "chronology_control", "age_claim"},
        )
