from __future__ import annotations

import json
import unittest

from bijux_pollen.context_data import normalize_neotoma_rows, normalize_sead_rows


class ContextDataTests(unittest.TestCase):
    def test_normalize_neotoma_rows_filters_to_nordic_bbox_and_reduces_polygons(self) -> None:
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
                "geography": json.dumps({"type": "Point", "coordinates": [-100.0, 40.0]}),
                "altitude": 10,
                "collectionunits": [],
            },
        ]

        records = normalize_neotoma_rows(rows, bbox=(4.0, 54.0, 35.0, 72.0))

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].record_id, "2961")
        self.assertEqual(records[0].geometry_type, "Polygon")
        self.assertAlmostEqual(records[0].longitude, 17.5)
        self.assertAlmostEqual(records[0].latitude, 59.5)
        self.assertEqual(records[0].record_count, 1)

    def test_normalize_sead_rows_preserves_site_identity(self) -> None:
        rows = [
            {
                "site_id": 6468,
                "site_name": "10412 Fjalkinge",
                "national_site_identifier": "10412",
                "latitude_dd": 56.05,
                "longitude_dd": 14.28,
                "altitude": 24,
                "site_description": "",
                "site_uuid": "uuid-1",
            }
        ]

        records = normalize_sead_rows(rows)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].record_id, "6468")
        self.assertEqual(records[0].name, "10412 Fjalkinge")
        self.assertEqual(records[0].category, "Environmental archaeology")
        self.assertEqual(records[0].popup_rows[0], ("Site ID", "6468"))


if __name__ == "__main__":
    unittest.main()
