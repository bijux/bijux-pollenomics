from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.collection.models import ContextPointRecord
from bijux_pollenomics.collection.sources.sead.discovery import (
    build_sweden_archaeology_site_discovery,
    write_sweden_archaeology_site_discovery,
)


def _site(site_id: str, name: str, longitude: float) -> ContextPointRecord:
    return ContextPointRecord(
        source="SEAD",
        layer_key="sead-sites",
        layer_label="SEAD sites",
        category="Environmental archaeology",
        country="Sweden",
        record_id=site_id,
        name=name,
        latitude=59.5,
        longitude=longitude,
        geometry_type="Point",
        subtitle="SEAD site",
        description="",
        source_url=f"https://browser.sead.se/site/{site_id}",
        record_count=1,
        popup_rows=(),
    )


class SwedenArchaeologySiteDiscoveryTests(unittest.TestCase):
    def test_discovery_retains_resolved_and_unresolved_sites(self) -> None:
        sites = [_site("10", "Dated site", 17.5), _site("20", "Undated site", 18.5)]
        chronology = ContextPointRecord(
            **{
                **sites[0].__dict__,
                "layer_key": "sead-temporal-evidence",
                "record_id": "10:dating_range:7",
                "record_count": 2,
                "time_start_bp": 1000,
                "time_end_bp": 1200,
                "time_mean_bp": 1100,
                "time_label": "1000-1200 BP",
                "temporal_semantics": {
                    "evidence_class": "sead_dating_range",
                    "comparability_posture": "numeric_interval",
                },
            }
        )
        raw_rows = [
            {
                "site_id": 10,
                "bibliography_rows": [{"ref": 1}],
                "dataset_count": 3,
            },
            {"site_id": 20, "bibliography_rows": [], "dataset_count": 1},
        ]
        density = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [17.0, 59.0],
                                [19.0, 59.0],
                                [19.0, 60.0],
                                [17.0, 60.0],
                                [17.0, 59.0],
                            ]
                        ],
                    },
                    "properties": {"count": 42},
                }
            ],
        }

        discovery = build_sweden_archaeology_site_discovery(
            site_records=sites,
            temporal_records=[chronology],
            raw_rows=raw_rows,
            raa_density_geojson=density,
        )

        self.assertEqual(discovery.summary["site_count"], 2)
        self.assertEqual(discovery.summary["chronology_resolved_site_count"], 1)
        self.assertEqual(discovery.summary["chronology_unresolved_site_count"], 1)
        self.assertEqual(discovery.summary["map_feature_count"], 2)
        self.assertEqual(discovery.site_rows[0]["site_id"], "10")
        self.assertEqual(discovery.site_rows[0]["discovery_rank"], 1)
        self.assertEqual(discovery.site_rows[0]["raa_density_context_count"], 42)
        self.assertEqual(discovery.map_records[0].time_start_bp, 1000)
        unresolved = discovery.map_records[1]
        self.assertIsNone(unresolved.time_start_bp)
        self.assertEqual(
            unresolved.temporal_semantics["comparability_posture"], "unresolved"
        )
        self.assertEqual(
            discovery.site_rows[1]["current_activity_status"],
            "not_captured_by_repository_sources",
        )
        self.assertIn(
            "never changes rank", discovery.ranking_contract["raa_density_role"]
        )

    def test_discovery_writes_complete_companion_products(self) -> None:
        discovery = build_sweden_archaeology_site_discovery(
            site_records=[_site("20", "Undated site", 18.5)],
            temporal_records=[],
            raw_rows=[{"site_id": 20, "bibliography_rows": []}],
        )

        with tempfile.TemporaryDirectory() as directory:
            paths = write_sweden_archaeology_site_discovery(Path(directory), discovery)
            payload = json.loads(paths["json"].read_text(encoding="utf-8"))
            geojson = json.loads(paths["geojson"].read_text(encoding="utf-8"))
            with paths["csv"].open(encoding="utf-8", newline="") as handle:
                csv_rows = list(csv.DictReader(handle))
            markdown = paths["markdown"].read_text(encoding="utf-8")

        self.assertEqual(len(payload["sites"]), 1)
        self.assertEqual(len(csv_rows), 1)
        self.assertEqual(len(geojson["features"]), 1)
        self.assertIn("every geolocated Swedish SEAD site", markdown)


if __name__ == "__main__":
    unittest.main()
