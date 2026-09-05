from __future__ import annotations

import unittest

from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from tests.support.neotoma import country_decisions, download_row


class NeotomaRelationalTests(unittest.TestCase):
    def test_every_emitted_relational_reference_targets_its_table(self) -> None:
        payload = build_neotoma_relational_snapshot(
            [download_row()],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
            country_by_site_id=country_decisions([download_row()]),
        )
        site_ids = {row["site_id"] for row in payload["sites"]}
        unit_ids = {row["collection_unit_id"] for row in payload["collection_units"]}
        dataset_ids = {row["dataset_id"] for row in payload["datasets"]}
        chronology_ids = {row["chronology_id"] for row in payload["chronologies"]}
        sample_ids = {row["sample_id"] for row in payload["samples"]}
        variable_ids = {row["variable_id"] for row in payload["variables"]}

        self.assertTrue(
            all(row["site_id"] in site_ids for row in payload["collection_units"])
        )
        self.assertTrue(
            all(
                row["site_id"] in site_ids and row["collection_unit_id"] in unit_ids
                for row in payload["datasets"]
            )
        )
        self.assertTrue(
            all(
                row["site_id"] in site_ids and row["collection_unit_id"] in unit_ids
                for row in payload["chronologies"]
            )
        )
        self.assertTrue(
            all(
                row["site_id"] in site_ids
                and row["collection_unit_id"] in unit_ids
                and row["chronology_id"] in chronology_ids
                for row in payload["chronology_controls"]
            )
        )
        self.assertTrue(
            all(
                row["site_id"] in site_ids
                and row["collection_unit_id"] in unit_ids
                and row["dataset_id"] in dataset_ids
                for row in payload["samples"]
            )
        )
        self.assertTrue(
            all(
                row["site_id"] in site_ids
                and row["collection_unit_id"] in unit_ids
                and row["dataset_id"] in dataset_ids
                and row["subject_type"] == "sample"
                and row["subject_id"] in sample_ids
                and (
                    row["chronology_id"] is None
                    or row["chronology_id"] in chronology_ids
                )
                for row in payload["age_claims"]
            )
        )
        self.assertTrue(
            all(
                row["site_id"] in site_ids
                and row["collection_unit_id"] in unit_ids
                and row["dataset_id"] in dataset_ids
                and row["sample_id"] in sample_ids
                and row["variable_id"] in variable_ids
                for row in payload["observations"]
            )
        )
