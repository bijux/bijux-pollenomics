from __future__ import annotations

from typing import cast
import unittest

from bijux_pollenomics.collection.sources.neotoma.collection import (
    build_neotoma_site_snapshot_rows,
)


class NeotomaSiteInventorySnapshotTests(unittest.TestCase):
    def test_build_neotoma_site_snapshot_rows_drops_nested_sample_payloads(
        self,
    ) -> None:
        rows = [
            {
                "siteid": 20,
                "sitename": "Snapshot test",
                "collectionunits": [
                    {
                        "collectionunitid": 1,
                        "datasets": [
                            {
                                "datasetid": 201,
                                "datasettype": "pollen",
                                "database": "European Pollen Database",
                                "chronologies": [{"chronologyid": 7001}],
                                "samples": [
                                    {
                                        "sampleid": 9001,
                                        "analysisunitid": 9101,
                                        "datum": [
                                            {"taxonid": 1, "variablename": "Betula"},
                                            {"taxonid": 2, "variablename": "Pinus"},
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ]

        snapshot_rows = build_neotoma_site_snapshot_rows(rows)
        collection_units = cast(
            list[dict[str, object]], snapshot_rows[0]["collectionunits"]
        )
        datasets = cast(list[dict[str, object]], collection_units[0]["datasets"])
        dataset = datasets[0]
        self.assertEqual(dataset["sample_count"], 1)
        self.assertEqual(dataset["analysis_unit_count"], 1)
        self.assertEqual(dataset["chronology_count"], 1)
        self.assertEqual(dataset["taxon_count"], 2)
        self.assertNotIn("samples", dataset)
        self.assertNotIn("chronologies", dataset)
