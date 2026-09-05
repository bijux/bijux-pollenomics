from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.collection.sources.neotoma.collection import (
    materialize_neotoma_repository_surfaces,
)


class NeotomaDataTests(unittest.TestCase):
    def test_materialize_neotoma_repository_surfaces_writes_temporal_review(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            raw_root = data_root / "neotoma" / "raw"
            raw_root.mkdir(parents=True, exist_ok=True)
            (data_root / "boundaries" / "raw").mkdir(parents=True, exist_ok=True)
            (raw_root / "neotoma_pollen_sites.json").write_text(
                json.dumps(
                    {
                        "generated_on": "2026-06-22",
                        "source": "Neotoma",
                        "datasettype": "pollen",
                        "rows": [
                            {
                                "siteid": 20,
                                "sitename": "Ageröds Mosse",
                                "sitedescription": "Forested bog.",
                                "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                                "dataset_count": 1,
                                "sample_count": 3,
                                "chronology_count": 1,
                                "age_ranges": [
                                    {
                                        "units": "Calibrated radiocarbon years BP",
                                        "ageold": 3600,
                                        "ageyoung": -20,
                                    }
                                ],
                                "collectionunits": [{"datasets": []}],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            sweden_boundary = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
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
                        },
                        "properties": {"ADM0_A3": "SWE"},
                    }
                ],
            }
            placeholder_boundary = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [0.0, 0.0],
                                    [1.0, 0.0],
                                    [1.0, 1.0],
                                    [0.0, 1.0],
                                    [0.0, 0.0],
                                ]
                            ],
                        },
                        "properties": {"ADM0_A3": "DNK"},
                    }
                ],
            }
            (data_root / "boundaries" / "raw" / "sweden.geojson").write_text(
                json.dumps(sweden_boundary),
                encoding="utf-8",
            )
            for country, code in (
                ("denmark", "DNK"),
                ("norway", "NOR"),
                ("finland", "FIN"),
            ):
                payload = json.loads(json.dumps(placeholder_boundary))
                payload["features"][0]["properties"]["ADM0_A3"] = code
                (data_root / "boundaries" / "raw" / f"{country}.geojson").write_text(
                    json.dumps(payload),
                    encoding="utf-8",
                )

            report = materialize_neotoma_repository_surfaces(data_root)

            normalized_payload = json.loads(
                report.normalized_geojson_path.read_text(encoding="utf-8")
            )
            temporal_review = json.loads(
                (data_root / "neotoma" / "review" / "temporal_review.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(report.point_count, 1)
        feature = normalized_payload["features"][0]
        self.assertEqual(feature["properties"]["country"], "Sweden")
        self.assertEqual(
            feature["properties"]["temporal_semantics"]["comparability_posture"],
            "numeric_interval",
        )
        self.assertEqual(
            temporal_review["comparability_posture_counts"]["numeric_interval"], 1
        )
        self.assertEqual(
            temporal_review["coverage_summary"]["site_count_with_bp_age_ranges"], 1
        )
        self.assertEqual(
            temporal_review["coverage_summary"][
                "site_count_with_bp_age_ranges_but_no_chronology_rows"
            ],
            0,
        )
        self.assertEqual(
            temporal_review["coverage_summary"][
                "site_count_with_bp_age_ranges_and_chronology_rows"
            ],
            1,
        )
        self.assertEqual(
            temporal_review["coverage_summary"]["chronology_capture_posture"],
            "bp_site_spans_with_some_chronology_rows",
        )
        self.assertEqual(
            temporal_review["coverage_summary"]["site_count_without_bp_age_ranges"], 0
        )
        self.assertEqual(
            temporal_review["rows"][0]["bp_support_posture"],
            "bp_age_ranges_with_chronology_rows",
        )
