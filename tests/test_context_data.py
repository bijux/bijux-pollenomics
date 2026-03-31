from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bijux_pollenomics.data_downloader.contracts import BOUNDARY_COLLECTION, LANDCLIM_GRID_GEOJSON, NEOTOMA_POINT_GEOJSON
from bijux_pollenomics.data_downloader.models import ContextPointRecord
from bijux_pollenomics.data_downloader.neotoma import normalize_neotoma_rows
from bijux_pollenomics.data_downloader.sead import normalize_sead_rows
from bijux_pollenomics.data_downloader.writers import write_context_points_csv, write_context_points_geojson


class ContextDataTests(unittest.TestCase):
    def test_data_artifact_contracts_resolve_stable_paths(self) -> None:
        root = Path("/tmp/data")

        self.assertEqual(
            BOUNDARY_COLLECTION.path_under(root),
            root / "boundaries" / "normalized" / "nordic_country_boundaries.geojson",
        )
        self.assertEqual(
            NEOTOMA_POINT_GEOJSON.path_under(root),
            root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
        )
        self.assertEqual(
            LANDCLIM_GRID_GEOJSON.path_under(root),
            root / "landclim" / "normalized" / "nordic_reveals_grid_cells.geojson",
        )

    def setUp(self) -> None:
        self.country_boundaries = {
            "Sweden": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[10.0, 55.0], [25.0, 55.0], [25.0, 70.0], [10.0, 70.0], [10.0, 55.0]]],
                        },
                        "properties": {"name": "Sweden"},
                    }
                ],
            }
        }

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

        records = normalize_sead_rows(rows, country_boundaries=self.country_boundaries)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].record_id, "6468")
        self.assertEqual(records[0].name, "10412 Fjalkinge")
        self.assertEqual(records[0].country, "Sweden")
        self.assertEqual(records[0].category, "Environmental archaeology")
        self.assertEqual(records[0].popup_rows[0], ("Site ID", "6468"))

    def test_context_point_exports_preserve_temporal_fields(self) -> None:
        record = ContextPointRecord(
            source="LandClim",
            layer_key="landclim-sites",
            layer_label="LandClim pollen sites",
            category="Pollen sequence",
            country="Sweden",
            record_id="site-1",
            name="Lake One",
            latitude=59.5,
            longitude=17.5,
            geometry_type="Point",
            subtitle="Sequence",
            description="Test record",
            source_url="https://example.test/site-1",
            record_count=3,
            popup_rows=(("Time windows", "0-100 BP, 350-700 BP"),),
            time_start_bp=0,
            time_end_bp=700,
            time_mean_bp=350,
            time_label="0-700 BP",
        )

        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "records.csv"
            geojson_path = Path(tmp) / "records.geojson"

            write_context_points_csv(csv_path, [record])
            write_context_points_geojson(geojson_path, [record])

            csv_text = csv_path.read_text(encoding="utf-8")
            geojson = json.loads(geojson_path.read_text(encoding="utf-8"))

        self.assertIn("time_start_bp", csv_text)
        self.assertIn("time_end_bp", csv_text)
        self.assertIn("time_mean_bp", csv_text)
        self.assertIn("time_label", csv_text)
        properties = geojson["features"][0]["properties"]
        self.assertEqual(properties["time_start_bp"], 0)
        self.assertEqual(properties["time_end_bp"], 700)
        self.assertEqual(properties["time_mean_bp"], 350)
        self.assertEqual(properties["time_label"], "0-700 BP")


if __name__ == "__main__":
    unittest.main()
