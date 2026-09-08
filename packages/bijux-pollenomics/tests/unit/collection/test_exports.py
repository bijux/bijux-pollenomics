"""Collection export coverage."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
from typing import cast
import unittest

from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.collection.exports import (
    write_context_points_csv,
    write_context_points_geojson,
)


class ContextExportTests(unittest.TestCase):
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
            description="First line   \nSecond line",
            source_url="https://example.test/site-1",
            record_count=3,
            popup_rows=(("Time windows", "0-100 BP, 350-700 BP"),),
            time_start_bp=0,
            time_end_bp=700,
            time_mean_bp=350,
            time_label="0-700 BP",
            temporal_semantics={
                "schema_version": "temporal-semantics.v1",
                "comparability_posture": "numeric_interval",
                "temporal_window_key": "recent_historical",
                "temporal_window_label": "Recent and historical (0-1000 BP)",
            },
            site_uuid="site-uuid-1",
        )

        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "records.csv"
            geojson_path = Path(tmp) / "records.geojson"

            write_context_points_csv(csv_path, [record])
            write_context_points_geojson(geojson_path, [record])

            csv_text = csv_path.read_text(encoding="utf-8")
            csv_bytes = csv_path.read_bytes()
            with csv_path.open(encoding="utf-8", newline="") as handle:
                csv_rows = list(csv.DictReader(handle))
            geojson = json.loads(geojson_path.read_text(encoding="utf-8"))
            geojson_features = cast(
                list[dict[str, object]], cast(dict[str, object], geojson)["features"]
            )

        self.assertIn("time_start_bp", csv_text)
        self.assertIn("time_end_bp", csv_text)
        self.assertIn("time_mean_bp", csv_text)
        self.assertIn("time_label", csv_text)
        self.assertIn("temporal_semantics_json", csv_text)
        self.assertEqual(csv_rows[0]["site_uuid"], "site-uuid-1")
        self.assertNotIn(b"\r\n", csv_bytes)
        self.assertIn("First line\nSecond line", csv_text)
        self.assertNotIn("First line   \n", csv_text)
        properties = cast(dict[str, object], geojson_features[0]["properties"])
        self.assertEqual(properties["site_uuid"], "site-uuid-1")
        self.assertEqual(properties["time_start_bp"], 0)
        self.assertEqual(properties["time_end_bp"], 700)
        self.assertEqual(properties["time_mean_bp"], 350)
        self.assertEqual(properties["time_label"], "0-700 BP")
        temporal_semantics = cast(dict[str, object], properties["temporal_semantics"])
        self.assertEqual(
            temporal_semantics["temporal_window_label"],
            "Recent and historical (0-1000 BP)",
        )
