from __future__ import annotations

import unittest

from bijux_pollenomics.collection.sources.neotoma.collection import (
    normalize_neotoma_rows,
)


class NeotomaSiteSpanProjectionTests(unittest.TestCase):
    def test_normalize_neotoma_rows_keeps_site_ranges_contextual(self) -> None:
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
        self.assertIsNone(records[0].time_start_bp)
        self.assertIsNone(records[0].time_end_bp)
        self.assertIsNone(records[0].time_mean_bp)
        self.assertEqual(
            records[0].time_label,
            "Source site age ranges (non-continuous context only)",
        )
        temporal_semantics = records[0].temporal_semantics
        self.assertIsInstance(temporal_semantics, dict)
        assert temporal_semantics is not None
        self.assertEqual(
            temporal_semantics["comparability_posture"],
            "contextual_label_only",
        )
        self.assertEqual(
            temporal_semantics["normalized_labels"],
            ["calibrated_radiocarbon_bp", "uncalibrated_radiocarbon_bp"],
        )
        self.assertEqual(
            temporal_semantics["evidence_class"],
            "neotoma_site_age_range_context",
        )
        self.assertEqual(
            temporal_semantics["precision_posture"],
            "site_extrema_without_continuity",
        )
        self.assertIsNone(temporal_semantics["time_start_bp"])
        self.assertIsNone(temporal_semantics["time_end_bp"])
        self.assertIsNone(temporal_semantics["time_mean_bp"])
        uncertainty_notes = temporal_semantics["uncertainty_notes"]
        self.assertIsInstance(uncertainty_notes, list)
        assert isinstance(uncertainty_notes, list)
        self.assertIn(
            "one interval would fill unobserved gaps",
            uncertainty_notes[0],
        )
        self.assertEqual(
            temporal_semantics["temporal_window_label"],
            "Unresolved time window",
        )

    def test_negative_bp_source_value_remains_visible_without_numeric_projection(
        self,
    ) -> None:
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
                "siteid": 12,
                "sitename": "Ageröds Mosse",
                "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                "age_ranges": [
                    {
                        "units": "Calibrated radiocarbon years BP",
                        "ageold": 11004,
                        "ageyoung": -26,
                    }
                ],
                "collectionunits": [],
            }
        ]

        records = normalize_neotoma_rows(
            rows, (4.0, 54.0, 35.0, 72.0), country_boundaries
        )

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertIsNone(record.time_start_bp)
        self.assertIsNone(record.time_end_bp)
        self.assertEqual(
            dict(record.popup_rows)["Age coverage (Calibrated radiocarbon years BP)"],
            "-26 to 11004",
        )
