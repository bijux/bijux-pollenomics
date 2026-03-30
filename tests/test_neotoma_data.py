from __future__ import annotations

import unittest
from unittest.mock import patch

from bijux_pollenomics.data_downloader.neotoma import fetch_neotoma_pollen_rows, normalize_neotoma_rows


class NeotomaDataTests(unittest.TestCase):
    def test_fetch_neotoma_pollen_rows_merges_dataset_and_site_endpoints(self) -> None:
        def fake_fetch_json(url: str, params: dict[str, str] | None = None, **_: object) -> object:
            endpoint = url.rsplit("/", 1)[-1]
            offset = params.get("offset") if params else None

            if endpoint == "datasets" and offset == "0":
                return {
                    "status": "success",
                    "message": "ok",
                    "data": [
                        {
                            "site": {
                                "siteid": 20,
                                "sitename": "Dataset overlap",
                                "sitedescription": "",
                                "geography": '{"type":"Point","coordinates":[18.0,59.0]}',
                                "altitude": 10,
                                "collectionunitid": 1,
                                "collectionunit": "Core A",
                                "handle": "CORE-A",
                                "unittype": "Core",
                                "datasets": [{"datasetid": 201, "datasettype": "pollen"}],
                            }
                        },
                        {
                            "site": {
                                "siteid": 20,
                                "sitename": "Dataset overlap",
                                "sitedescription": "",
                                "geography": '{"type":"Point","coordinates":[18.0,59.0]}',
                                "altitude": 10,
                                "collectionunitid": 2,
                                "collectionunit": "Core B",
                                "handle": "CORE-B",
                                "unittype": "Core",
                                "datasets": [{"datasetid": 202, "datasettype": "pollen"}],
                            }
                        },
                        {
                            "site": {
                                "siteid": 30,
                                "sitename": "Dataset only",
                                "sitedescription": "Carried only by /datasets.",
                                "geography": '{"type":"Point","coordinates":[19.0,60.0]}',
                                "altitude": 25,
                                "collectionunitid": 3,
                                "collectionunit": "Core C",
                                "handle": "CORE-C",
                                "unittype": "Core",
                                "datasets": [{"datasetid": 301, "datasettype": "pollen"}],
                            }
                        },
                    ],
                }
            if endpoint == "datasets":
                return {"status": "success", "message": "ok", "data": []}

            if endpoint == "sites" and offset == "0":
                return {
                    "status": "success",
                    "message": "ok",
                    "data": [
                        {
                            "siteid": 10,
                            "sitename": "Site only",
                            "sitedescription": "Carried only by /sites.",
                            "geography": '{"type":"Point","coordinates":[17.0,58.0]}',
                            "altitude": 15,
                            "collectionunits": [
                                {
                                    "collectionunitid": 10,
                                    "collectionunit": "Core Z",
                                    "handle": "CORE-Z",
                                    "collectionunittype": "Core",
                                    "datasets": [{"datasetid": 101, "datasettype": "pollen"}],
                                }
                            ],
                        },
                        {
                            "siteid": 20,
                            "sitename": "Dataset overlap",
                            "sitedescription": "Supplemental description from /sites.",
                            "geography": '{"type":"Point","coordinates":[18.0,59.0]}',
                            "altitude": 10,
                            "collectionunits": [
                                {
                                    "collectionunitid": 1,
                                    "collectionunit": "Core A",
                                    "handle": "CORE-A",
                                    "collectionunittype": "Core",
                                    "datasets": [{"datasetid": 201, "datasettype": "pollen"}],
                                }
                            ],
                        },
                    ],
                }
            if endpoint == "sites":
                return {"status": "success", "message": "ok", "data": []}

            raise AssertionError(f"Unexpected URL: {url}")

        with patch("bijux_pollenomics.data_downloader.neotoma.fetch_json", side_effect=fake_fetch_json):
            rows = fetch_neotoma_pollen_rows()

        self.assertEqual([row["siteid"] for row in rows], [10, 20, 30])
        row_by_id = {row["siteid"]: row for row in rows}

        self.assertEqual(row_by_id[10]["sitename"], "Site only")
        self.assertEqual(row_by_id[30]["sitename"], "Dataset only")
        self.assertEqual(row_by_id[20]["sitedescription"], "Supplemental description from /sites.")
        self.assertEqual(
            [unit["collectionunitid"] for unit in row_by_id[20]["collectionunits"]],
            [1, 2],
        )
        self.assertEqual(
            [
                dataset["datasetid"]
                for unit in row_by_id[20]["collectionunits"]
                for dataset in unit["datasets"]
            ],
            [201, 202],
        )

    def test_normalize_neotoma_rows_recovers_coastal_nordic_sites_without_widening_scope(self) -> None:
        country_boundaries = {
            "Norway": {
                "features": [
                    {
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [[10.0, 60.0], [13.0, 60.0], [13.0, 63.0], [10.0, 63.0], [10.0, 60.0]]
                            ],
                        }
                    }
                ]
            }
        }
        rows = [
            {
                "siteid": 1,
                "sitename": "Coastal site",
                "sitedescription": "",
                "geography": '{"type":"Point","coordinates":[13.05,61.5]}',
                "collectionunits": [
                    {
                        "datasets": [{"datasetid": 10, "datasettype": "pollen"}],
                    }
                ],
            },
            {
                "siteid": 2,
                "sitename": "Too far away",
                "sitedescription": "",
                "geography": '{"type":"Point","coordinates":[13.5,61.5]}',
                "collectionunits": [
                    {
                        "datasets": [{"datasetid": 20, "datasettype": "pollen"}],
                    }
                ],
            },
        ]

        records = normalize_neotoma_rows(rows, (4.0, 54.0, 35.0, 72.0), country_boundaries)

        self.assertEqual([record.name for record in records], ["Coastal site"])
        self.assertEqual(records[0].country, "Norway")


if __name__ == "__main__":
    unittest.main()
