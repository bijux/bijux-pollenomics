"""SEAD collection normalization coverage."""

from __future__ import annotations

from typing import cast

from bijux_pollenomics.collection.sources.sead.collection import (
    normalize_sead_rows,
    normalize_sead_temporal_evidence,
)
from tests.support.context_data import NordicBoundaryTestCase


class SeadNormalizationTests(NordicBoundaryTestCase):
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
                "dataset_count": 2,
                "analysis_entity_count": 3,
                "time_start_bp": 200,
                "time_end_bp": 800,
            }
        ]

        records = normalize_sead_rows(rows, country_boundaries=self.country_boundaries)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].record_id, "6468")
        self.assertEqual(records[0].site_uuid, "uuid-1")
        self.assertEqual(records[0].name, "10412 Fjalkinge")
        self.assertEqual(records[0].country, "Sweden")
        self.assertEqual(records[0].category, "Environmental archaeology")
        self.assertEqual(records[0].popup_rows[0], ("Site ID", "6468"))
        self.assertEqual(records[0].time_start_bp, 200)
        self.assertEqual(records[0].time_end_bp, 800)
        self.assertEqual(records[0].time_mean_bp, 500)
        self.assertIsNotNone(records[0].temporal_semantics)
        temporal_semantics = cast(dict[str, object], records[0].temporal_semantics)
        self.assertEqual(
            temporal_semantics["comparability_posture"],
            "numeric_interval",
        )
        self.assertEqual(
            temporal_semantics["temporal_window_label"],
            "Recent and historical (0-1000 BP)",
        )

    def test_normalize_sead_temporal_evidence_groups_only_matching_intervals(
        self,
    ) -> None:
        rows = [
            {
                "site_id": 6468,
                "site_name": "10412 Fjalkinge",
                "latitude_dd": 56.05,
                "longitude_dd": 14.28,
                "site_uuid": "uuid-1",
                "bibliography_rows": [{"biblio_id": 60}],
                "dating_range_rows": [
                    {
                        "analysis_dating_range_id": 34,
                        "analysis_entity_id": 30,
                        "age_type": "calibrated years BP",
                        "time_start_bp": 200,
                        "time_end_bp": 800,
                    },
                    {
                        "analysis_dating_range_id": 35,
                        "analysis_entity_id": 30,
                        "age_type": "calibrated years BP",
                        "time_start_bp": 200,
                        "time_end_bp": 800,
                    },
                    {
                        "analysis_dating_range_id": 36,
                        "analysis_entity_id": 30,
                        "age_type": "calibrated years BP",
                        "time_start_bp": 900,
                        "time_end_bp": 1000,
                    },
                ],
                "relative_period_rows": [
                    {
                        "relative_date_id": 37,
                        "analysis_entity_id": 30,
                        "relative_age_label": "Neolithic",
                        "time_start_bp": 4000,
                        "time_end_bp": 6000,
                    }
                ],
                "geochronology_rows": [
                    {
                        "geochron_id": 38,
                        "analysis_entity_id": 30,
                        "age": 1200,
                        "time_start_bp": 1100,
                        "time_end_bp": 1300,
                    }
                ],
            }
        ]

        records = normalize_sead_temporal_evidence(
            rows, country_boundaries=self.country_boundaries
        )

        self.assertEqual(len(records), 2)
        self.assertEqual(sum(record.record_count for record in records), 3)
        first = records[0]
        self.assertEqual(first.site_uuid, "uuid-1")
        self.assertEqual(first.layer_key, "sead-temporal-evidence")
        self.assertEqual(first.time_start_bp, 200)
        self.assertEqual(first.time_end_bp, 800)
        temporal_semantics = cast(dict[str, object], first.temporal_semantics)
        self.assertEqual(
            temporal_semantics["source_record_ids"],
            [34, 35],
        )

    def test_sead_normalization_refuses_missing_stable_site_identity(self) -> None:
        site = {
            "site_id": 6468,
            "site_name": "10412 Fjalkinge",
            "latitude_dd": 56.05,
            "longitude_dd": 14.28,
        }

        with self.assertRaisesRegex(ValueError, "site_uuid"):
            normalize_sead_rows(
                [dict(site)], country_boundaries=self.country_boundaries
            )

        site["dating_range_rows"] = [
            {
                "analysis_dating_range_id": 34,
                "analysis_entity_id": 30,
                "age_type": "calibrated years BP",
                "time_start_bp": 200,
                "time_end_bp": 800,
            }
        ]
        with self.assertRaisesRegex(ValueError, "site_uuid"):
            normalize_sead_temporal_evidence(
                [site], country_boundaries=self.country_boundaries
            )
