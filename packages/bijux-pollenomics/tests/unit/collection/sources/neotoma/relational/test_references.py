from __future__ import annotations

import unittest

from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from tests.support.neotoma import country_decisions, download_row
from tests.support.neotoma.relational_shapes import rows


class NeotomaRelationalReferenceTests(unittest.TestCase):
    def test_every_emitted_relational_reference_targets_its_table(self) -> None:
        payload = build_neotoma_relational_snapshot(
            [download_row()],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
            country_by_site_id=country_decisions([download_row()]),
        )
        site_ids = {row["site_id"] for row in rows(payload["sites"])}
        unit_ids = {
            row["collection_unit_id"] for row in rows(payload["collection_units"])
        }
        dataset_ids = {row["dataset_id"] for row in rows(payload["datasets"])}
        chronology_ids = {row["chronology_id"] for row in rows(payload["chronologies"])}
        sample_ids = {row["sample_id"] for row in rows(payload["samples"])}
        variable_ids = {row["variable_id"] for row in rows(payload["variables"])}

        self.assertTrue(
            all(row["site_id"] in site_ids for row in rows(payload["collection_units"]))
        )
        self.assertTrue(
            all(
                row["site_id"] in site_ids and row["collection_unit_id"] in unit_ids
                for row in rows(payload["datasets"])
            )
        )
        self.assertTrue(
            all(
                row["site_id"] in site_ids and row["collection_unit_id"] in unit_ids
                for row in rows(payload["chronologies"])
            )
        )
        self.assertTrue(
            all(
                row["site_id"] in site_ids
                and row["collection_unit_id"] in unit_ids
                and row["chronology_id"] in chronology_ids
                for row in rows(payload["chronology_controls"])
            )
        )
        self.assertTrue(
            all(
                row["site_id"] in site_ids
                and row["collection_unit_id"] in unit_ids
                and row["dataset_id"] in dataset_ids
                for row in rows(payload["samples"])
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
                for row in rows(payload["age_claims"])
            )
        )
        self.assertTrue(
            all(
                row["site_id"] in site_ids
                and row["collection_unit_id"] in unit_ids
                and row["dataset_id"] in dataset_ids
                and row["sample_id"] in sample_ids
                and row["variable_id"] in variable_ids
                for row in rows(payload["observations"])
            )
        )
