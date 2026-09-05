from __future__ import annotations

import unittest

from bijux_pollenomics.collection.sources.neotoma.collection import (
    normalize_neotoma_rows,
)


class NeotomaSiteSpanProjectionTests(unittest.TestCase):
    def test_normalize_neotoma_rows_derives_bp_interval_from_age_ranges(self) -> None:
        country_boundaries = {
            "Sweden": {
                "features": [
                    {
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
                        }
                    }
                ]
            }
        }
        rows = [
            {
                "siteid": 20,
                "sitename": "Ageröds Mosse",
                "sitedescription": "Forested bog.",
                "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                "collectionunits": [
                    {
                        "datasets": [
                            {
                                "datasetid": 201,
                                "datasettype": "pollen",
                                "database": "European Pollen Database",
                                "agerange": [
                                    {
                                        "units": "Radiocarbon years BP",
                                        "ageold": 3200,
                                        "ageyoung": 120,
                                    },
                                    {
                                        "units": "Calibrated radiocarbon years BP",
                                        "ageold": 3600,
                                        "ageyoung": 20,
                                    },
                                ],
                            }
                        ],
                    }
                ],
            }
        ]

        records = normalize_neotoma_rows(
            rows, (4.0, 54.0, 35.0, 72.0), country_boundaries
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].time_start_bp, 20)
        self.assertEqual(records[0].time_end_bp, 3600)
        self.assertEqual(records[0].time_mean_bp, 1810)
        self.assertEqual(
            records[0].time_label, "20-3600 Calibrated radiocarbon years BP"
        )
        temporal_semantics = records[0].temporal_semantics
        self.assertIsInstance(temporal_semantics, dict)
        assert temporal_semantics is not None
        self.assertEqual(
            temporal_semantics["comparability_posture"],
            "mixed_interval_and_context",
        )
        self.assertEqual(
            temporal_semantics["normalized_labels"],
            ["calibrated_radiocarbon_bp", "uncalibrated_radiocarbon_bp"],
        )
        uncertainty_notes = temporal_semantics["uncertainty_notes"]
        self.assertIsInstance(uncertainty_notes, list)
        assert isinstance(uncertainty_notes, list)
        self.assertIn(
            "incompatible source age systems were excluded",
            uncertainty_notes[0],
        )
        self.assertEqual(
            temporal_semantics["temporal_window_label"],
            "Late Holocene (1001-3000 BP)",
        )
