from __future__ import annotations

import unittest

from bijux_pollenomics.collection.sources.neotoma.collection import (
    normalize_neotoma_rows,
)


class NeotomaDataTests(unittest.TestCase):
    def test_normalize_neotoma_rows_refuses_coastal_proximity_without_snapping(
        self,
    ) -> None:
        country_boundaries = {
            "Norway": {
                "features": [
                    {
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [10.0, 60.0],
                                    [13.0, 60.0],
                                    [13.0, 63.0],
                                    [10.0, 63.0],
                                    [10.0, 60.0],
                                ]
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

        records = normalize_neotoma_rows(
            rows, (4.0, 54.0, 35.0, 72.0), country_boundaries
        )

        self.assertEqual(records, [])
