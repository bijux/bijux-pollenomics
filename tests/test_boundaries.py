from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bijux_pollenomics.data_downloader.boundaries import (
    build_combined_country_boundaries,
    build_country_boundary_collection,
    collect_boundaries_data,
)


class BoundariesTests(unittest.TestCase):
    def test_build_country_boundary_collection_filters_natural_earth_by_adm0_code(self) -> None:
        global_boundaries = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [[[10.0, 55.0], [11.0, 55.0], [11.0, 56.0], [10.0, 56.0], [10.0, 55.0]]]},
                    "properties": {"ADM0_A3": "DNK", "NAME": "Denmark"},
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [[[-45.0, 59.0], [-40.0, 59.0], [-40.0, 61.0], [-45.0, 61.0], [-45.0, 59.0]]]},
                    "properties": {"ADM0_A3": "GRL", "NAME": "Greenland"},
                },
            ],
        }

        denmark = build_country_boundary_collection(global_boundaries, "DNK")

        self.assertEqual(len(denmark["features"]), 1)
        self.assertEqual(denmark["features"][0]["properties"]["NAME"], "Denmark")

    def test_collect_boundaries_data_writes_country_files_and_combined_geojson(self) -> None:
        natural_earth_payload = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [[[16.0, 58.0], [19.0, 58.0], [19.0, 60.0], [16.0, 60.0], [16.0, 58.0]]]},
                    "properties": {"ADM0_A3": "SWE", "NAME": "Sweden"},
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [[[4.0, 58.0], [12.0, 58.0], [12.0, 71.0], [4.0, 71.0], [4.0, 58.0]]]},
                    "properties": {"ADM0_A3": "NOR", "NAME": "Norway"},
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [[[20.0, 60.0], [31.0, 60.0], [31.0, 70.0], [20.0, 70.0], [20.0, 60.0]]]},
                    "properties": {"ADM0_A3": "FIN", "NAME": "Finland"},
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Polygon", "coordinates": [[[8.0, 54.0], [13.0, 54.0], [13.0, 58.0], [8.0, 58.0], [8.0, 54.0]]]},
                    "properties": {"ADM0_A3": "DNK", "NAME": "Denmark"},
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "boundaries"
            with patch("bijux_pollenomics.data_downloader.boundaries.fetch_json", return_value=natural_earth_payload):
                country_boundaries, report = collect_boundaries_data(output_root)

            self.assertEqual(tuple(country_boundaries.keys()), ("Sweden", "Norway", "Finland", "Denmark"))
            self.assertTrue((output_root / "raw" / "sweden.geojson").exists())
            self.assertTrue(report.combined_path.exists())

            combined = build_combined_country_boundaries(country_boundaries)
            self.assertEqual(len(combined["features"]), 4)
            self.assertEqual(combined["features"][0]["properties"]["layer_key"], "country-boundaries")


if __name__ == "__main__":
    unittest.main()
