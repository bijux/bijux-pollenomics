"""Neotoma context normalization coverage."""

from __future__ import annotations

import json

from bijux_pollenomics.collection.sources.neotoma.collection import (
    normalize_neotoma_rows,
)
from tests.support.context_data import NordicBoundaryTestCase


class NeotomaNormalizationTests(NordicBoundaryTestCase):
    def test_normalize_neotoma_rows_filters_to_nordic_bbox_and_reduces_polygons(
        self,
    ) -> None:
        rows = [
            {
                "siteid": 2961,
                "sitename": "Aborregol",
                "sitedescription": "Small lake.",
                "geography": json.dumps(
                    {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [17.0, 59.0],
                                [18.0, 59.0],
                                [18.0, 60.0],
                                [17.0, 60.0],
                                [17.0, 59.0],
                            ]
                        ],
                    }
                ),
                "altitude": 81,
                "collectionunits": [
                    {
                        "collectionunitid": 1,
                        "datasets": [{"datasetid": 10, "datasettype": "pollen"}],
                    }
                ],
            },
            {
                "siteid": 5000,
                "sitename": "Outside Nordic",
                "sitedescription": "Ignored.",
                "geography": json.dumps(
                    {"type": "Point", "coordinates": [-100.0, 40.0]}
                ),
                "altitude": 10,
                "collectionunits": [],
            },
        ]

        records = normalize_neotoma_rows(
            rows,
            bbox=(4.0, 54.0, 35.0, 72.0),
            country_boundaries=self.country_boundaries,
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].record_id, "2961")
        self.assertEqual(records[0].geometry_type, "Polygon")
        self.assertEqual(records[0].country, "Sweden")
        self.assertAlmostEqual(records[0].longitude, 17.5)
        self.assertAlmostEqual(records[0].latitude, 59.5)
        self.assertEqual(records[0].record_count, 1)
