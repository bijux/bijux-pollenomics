from __future__ import annotations

import unittest

from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from tests.support.neotoma import download_row
from tests.support.neotoma.relational_shapes import mapping, nested, rows


class NeotomaRelationalDiagnosticTests(unittest.TestCase):
    def test_missing_chronology_identifiers_are_preserved_and_reported(self) -> None:
        row = download_row()
        chronology = nested(
            rows(nested(row, "site", "collectionunit")["chronologies"])[0], "chronology"
        )
        chronology["chronologyid"] = None
        rows(chronology["chroncontrols"])[0]["chroncontrolid"] = None
        nested(row, "site", "collectionunit")["defaultchronology"] = 7002

        payload = build_neotoma_relational_snapshot(
            [row], source_snapshot_id="sha256:fixture", build_id="fixture-build"
        )

        self.assertEqual(len(rows(payload["chronologies"])), 2)
        self.assertEqual(len(rows(payload["chronology_controls"])), 1)
        self.assertEqual(mapping(payload["reconciliation"])["orphan_count"], 3)
        self.assertEqual(
            {orphan["entity_type"] for orphan in rows(payload["orphans"])},
            {"chronology", "chronology_control", "age_claim"},
        )
