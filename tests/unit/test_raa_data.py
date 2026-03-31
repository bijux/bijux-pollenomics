from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bijux_pollenomics.data_downloader.raa import collect_raa_data, fetch_raa_feature_inventory


class RaaDataTests(unittest.TestCase):
    def test_fetch_raa_feature_inventory_paginates_all_features(self) -> None:
        pages = [
            {
                "type": "FeatureCollection",
                "features": [
                    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [18.0, 57.0]}, "properties": {"lamningsnummer": "A"}},
                    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [19.0, 58.0]}, "properties": {"lamningsnummer": "B"}},
                ],
                "numberMatched": 3,
                "timeStamp": "2026-03-31T11:00:00Z",
            },
            {
                "type": "FeatureCollection",
                "features": [
                    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [20.0, 59.0]}, "properties": {"lamningsnummer": "C"}},
                ],
                "numberMatched": 3,
                "timeStamp": "2026-03-31T11:00:01Z",
            },
        ]

        with patch("bijux_pollenomics.data_downloader.raa.fetch_raa_feature_page", side_effect=pages):
            payload = fetch_raa_feature_inventory()

        self.assertEqual(len(payload["features"]), 3)
        self.assertEqual(payload["numberMatched"], 3)

    def test_collect_raa_data_writes_raw_feature_archive(self) -> None:
        feature_inventory = {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": {"type": "Point", "coordinates": [18.0, 57.0]}, "properties": {"lamningsnummer": "A"}}
            ],
            "numberMatched": 1,
        }
        metadata = {
            "capabilities_xml": "<wfs />",
            "schema_xml": "<schema />",
            "domain_payload": {"domains": []},
            "layer_metadata": {
                "counts": {
                    "all_published_sites": 1,
                    "fornlamning": 1,
                }
            },
            "density_geojson": {"type": "FeatureCollection", "features": []},
        }

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "raa"
            with patch("bijux_pollenomics.data_downloader.raa.fetch_raa_feature_inventory", return_value=feature_inventory), patch(
                "bijux_pollenomics.data_downloader.raa.fetch_raa_archaeology_metadata",
                return_value=metadata,
            ):
                report = collect_raa_data(output_root, country_boundaries={"Sweden": {"features": []}})

            raw_payload = json.loads(report.raw_points_path.read_text(encoding="utf-8"))

        self.assertEqual(raw_payload["numberMatched"], 1)
        self.assertEqual(raw_payload["features"][0]["properties"]["lamningsnummer"], "A")


if __name__ == "__main__":
    unittest.main()
