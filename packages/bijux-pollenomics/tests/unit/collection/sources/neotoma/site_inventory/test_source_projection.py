from __future__ import annotations

import unittest
from typing import cast
from unittest.mock import patch

from bijux_pollenomics.collection.sources.neotoma.collection import (
    fetch_neotoma_pollen_rows,
    normalize_neotoma_rows,
)


class NeotomaSiteSourceProjectionTests(unittest.TestCase):
    def test_fetch_neotoma_pollen_rows_hydrates_full_dataset_downloads(self) -> None:
        country_boundaries = {
            "Sweden": {
                "features": [
                    {
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [10.0, 55.0],
                                    [25.0, 55.0],
                                    [25.0, 70.0],
                                    [10.0, 70.0],
                                    [10.0, 55.0],
                                ]
                            ],
                        }
                    }
                ]
            }
        }

        def fake_fetch_json(
            url: str, params: dict[str, str] | None = None, **_: object
        ) -> object:
            if url.endswith("/datasets"):
                return {
                    "status": "success",
                    "message": "ok",
                    "data": [
                        {
                            "site": {
                                "siteid": 20,
                                "sitename": "Ageröds Mosse",
                                "sitedescription": "",
                                "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                                "altitude": 10,
                                "datasets": [
                                    {"datasetid": 201, "datasettype": "pollen"}
                                ],
                            }
                        },
                        {
                            "site": {
                                "siteid": 20,
                                "sitename": "Ageröds Mosse",
                                "sitedescription": "",
                                "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                                "altitude": 10,
                                "datasets": [
                                    {"datasetid": 202, "datasettype": "pollen"}
                                ],
                            }
                        },
                        {
                            "site": {
                                "siteid": 30,
                                "sitename": "Outside Nordic",
                                "sitedescription": "",
                                "geography": '{"type":"Point","coordinates":[40.0,60.0]}',
                                "altitude": 25,
                                "datasets": [
                                    {"datasetid": 301, "datasettype": "pollen"}
                                ],
                            }
                        },
                    ],
                }
            if url.endswith("/downloads/201"):
                return {
                    "status": "success",
                    "message": "ok",
                    "data": [
                        {
                            "site": {
                                "siteid": 20,
                                "sitename": "Ageröds Mosse",
                                "sitedescription": "Forested bog.",
                                "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                                "altitude": 10,
                                "chronologies": [{"chronologyid": 7001}],
                                "defaultchronology": 7001,
                                "collectionunit": {
                                    "collectionunitid": 1,
                                    "collectionunit": "Core A",
                                    "handle": "CORE-A",
                                    "collunittype": "Core",
                                    "dataset": {
                                        "datasetid": 201,
                                        "datasettype": "pollen",
                                        "database": "European Pollen Database",
                                        "agerange": [
                                            {
                                                "units": "Calibrated radiocarbon years BP",
                                                "ageold": 2000,
                                                "ageyoung": 50,
                                            }
                                        ],
                                        "samples": [
                                            {
                                                "sampleid": 9001,
                                                "analysisunitid": 9101,
                                                "ages": [
                                                    {
                                                        "agetype": "Calibrated radiocarbon years BP",
                                                        "ageolder": 2100,
                                                        "ageyounger": 30,
                                                    }
                                                ],
                                                "datum": [
                                                    {
                                                        "taxonid": 1,
                                                        "variablename": "Betula",
                                                    },
                                                    {
                                                        "taxonid": 2,
                                                        "variablename": "Pinus",
                                                    },
                                                ],
                                            }
                                        ],
                                    },
                                },
                            },
                        }
                    ],
                }
            if url.endswith("/downloads/202"):
                return {
                    "status": "success",
                    "message": "ok",
                    "data": [
                        {
                            "site": {
                                "siteid": 20,
                                "sitename": "Ageröds Mosse",
                                "sitedescription": "Forested bog.",
                                "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                                "altitude": 10,
                                "chronologies": [{"chronologyid": 7002}],
                                "defaultchronology": 7002,
                                "collectionunit": {
                                    "collectionunitid": 2,
                                    "collectionunit": "Core B",
                                    "handle": "CORE-B",
                                    "collunittype": "Core",
                                    "dataset": {
                                        "datasetid": 202,
                                        "datasettype": "pollen",
                                        "database": "European Pollen Database",
                                        "agerange": [
                                            {
                                                "units": "Calibrated radiocarbon years BP",
                                                "ageold": 3500,
                                                "ageyoung": 200,
                                            }
                                        ],
                                        "samples": [
                                            {
                                                "sampleid": 9002,
                                                "analysisunitid": 9102,
                                                "ages": [
                                                    {
                                                        "agetype": "Calibrated radiocarbon years BP",
                                                        "ageolder": 3600,
                                                        "ageyounger": 180,
                                                    }
                                                ],
                                                "datum": [
                                                    {
                                                        "taxonid": 3,
                                                        "variablename": "Alnus",
                                                    },
                                                ],
                                            }
                                        ],
                                    },
                                },
                            },
                        },
                    ],
                }

            raise AssertionError(f"Unexpected URL: {url}")

        with patch(
            "bijux_pollenomics.collection.sources.neotoma.collection.fetch_json",
            side_effect=fake_fetch_json,
        ):
            rows = fetch_neotoma_pollen_rows(
                bbox=(4.0, 54.0, 35.0, 72.0),
                country_boundaries=country_boundaries,
            )

        self.assertEqual([row["siteid"] for row in rows], [20])
        row_by_id = {row["siteid"]: row for row in rows}
        collection_units = cast(
            list[dict[str, object]], row_by_id[20]["collectionunits"]
        )

        self.assertEqual(row_by_id[20]["sitename"], "Ageröds Mosse")
        self.assertEqual(row_by_id[20]["dataset_count"], 2)
        self.assertEqual(row_by_id[20]["sample_count"], 2)
        self.assertEqual(row_by_id[20]["chronology_count"], 2)
        self.assertEqual(row_by_id[20]["taxon_count"], 3)
        self.assertEqual(row_by_id[20]["databases"], ["European Pollen Database"])
        self.assertEqual(
            [unit["collectionunitid"] for unit in collection_units],
            [1, 2],
        )
        self.assertEqual(
            [
                dataset["datasetid"]
                for unit in collection_units
                for dataset in cast(list[dict[str, object]], unit["datasets"])
            ],
            [201, 202],
        )

        records = normalize_neotoma_rows(
            rows, (4.0, 54.0, 35.0, 72.0), country_boundaries
        )
        self.assertEqual(len(records), 1)
        self.assertIsNone(records[0].time_start_bp)
        self.assertIsNone(records[0].time_end_bp)
        self.assertIsNone(records[0].time_mean_bp)
        self.assertEqual(
            records[0].time_label,
            "Source site age ranges (non-continuous context only)",
        )
        temporal_semantics = records[0].temporal_semantics
        self.assertIsInstance(temporal_semantics, dict)
        assert isinstance(temporal_semantics, dict)
        self.assertEqual(
            temporal_semantics["comparability_posture"],
            "contextual_label_only",
        )
