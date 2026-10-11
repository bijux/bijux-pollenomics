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

    def test_explicit_default_coexists_with_other_age_type_default(
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
        self.assertEqual(default_conflicts, [])

    def test_two_defaults_of_same_age_type_remain_a_conflict(self) -> None:
        row = download_row()
        chronologies = row["site"]["collectionunit"]["chronologies"]
        chronologies[1]["chronology"]["chronology"]["modelagetype"] = (
            "Calibrated radiocarbon years BP"
        )
        payload = build_neotoma_relational_snapshot(
            [row], source_snapshot_id="sha256:fixture", build_id="fixture-build"
        )
        conflicts = [
            conflict
            for conflict in payload["conflicts"]
            if conflict["conflict_kind"] == "default_chronology_assertions_conflict"
        ]
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(
            conflicts[0]["detail"]["duplicate_default_age_types"],
            {"Calibrated radiocarbon years BP": ["7001", "7002"]},
        )
