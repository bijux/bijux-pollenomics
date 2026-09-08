from __future__ import annotations

import unittest

from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from bijux_pollenomics.collection.sources.neotoma.site_inventory import (
    build_neotoma_site_rows_from_downloads,
)
from tests.support.neotoma import download_row


class NeotomaDefaultChronologySelectionTests(unittest.TestCase):
    def test_site_rows_retain_collection_unit_owned_chronologies(self) -> None:
        rows = build_neotoma_site_rows_from_downloads([download_row()])

        dataset = rows[0]["collectionunits"][0]["datasets"][0]
        self.assertEqual(dataset["defaultchronology"], 7001)
        self.assertEqual(len(dataset["chronologies"]), 2)
        self.assertEqual(rows[0]["chronology_count"], 2)

    def test_explicit_default_governs_and_source_assertion_conflict_is_visible(
        self,
    ) -> None:
        payload = build_neotoma_relational_snapshot(
            [download_row()],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
        )

        selected = {
            chronology["source_chronology_id"]: chronology[
                "selected_by_collection_unit_reference"
            ]
            for chronology in payload["chronologies"]
        }
        source_assertions = {
            chronology["source_chronology_id"]: chronology[
                "source_is_default_assertion"
            ]
            for chronology in payload["chronologies"]
        }
        self.assertEqual(selected, {7001: True, 7002: False})
        self.assertEqual(source_assertions, {7001: True, 7002: True})
        default_conflicts = [
            conflict
            for conflict in payload["conflicts"]
            if conflict["conflict_kind"] == "default_chronology_assertions_conflict"
        ]
        self.assertEqual(len(default_conflicts), 1)
        self.assertEqual(
            default_conflicts[0]["detail"]["governing_selection"],
            "collection_unit.defaultchronology",
        )
        self.assertEqual(
            default_conflicts[0]["detail"]["explicit_default_chronology_id"],
            "neotoma:chronology:301:7001",
        )
        self.assertEqual(
            default_conflicts[0]["detail"]["source_flagged_default_chronology_ids"],
            ["neotoma:chronology:301:7001", "neotoma:chronology:301:7002"],
        )
        chronology_ids = {
            chronology["chronology_id"] for chronology in payload["chronologies"]
        }
        self.assertIn(
            default_conflicts[0]["detail"]["explicit_default_chronology_id"],
            chronology_ids,
        )
        self.assertTrue(
            set(
                default_conflicts[0]["detail"]["source_flagged_default_chronology_ids"]
            ).issubset(chronology_ids)
        )
