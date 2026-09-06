"""SEAD collection chronology coverage."""

from __future__ import annotations

import unittest
from typing import cast
from unittest.mock import patch

from bijux_pollenomics.collection.sources.sead.collection import (
    fetch_sead_site_rows,
    refresh_sead_repository_rows,
    sead_dating_interval,
)


class SeadChronologyTests(unittest.TestCase):
    def test_sead_dating_interval_converts_common_era_years_to_bp(self) -> None:
        interval = sead_dating_interval(
            {
                "low_value": 1754,
                "high_value": None,
            },
            age_type="AD",
        )

        self.assertEqual(interval, (196, 196))

    def test_sead_dating_interval_converts_before_common_era_years_to_bp(self) -> None:
        interval = sead_dating_interval(
            {
                "low_value": 550,
                "high_value": 500,
            },
            age_type="before common era",
        )

        self.assertEqual(interval, (2449, 2499))

    def test_sead_dating_interval_rejects_substring_age_type_heuristics(self) -> None:
        for age_type in ("possibly cal-ish BP", "uncertain C14", "shadow AD value"):
            with self.subTest(age_type=age_type):
                self.assertIsNone(
                    sead_dating_interval(
                        {"low_value": 500, "high_value": 600},
                        age_type=age_type,
                    )
                )

    def test_sead_refresh_recovers_interval_encoded_in_relative_age_label(self) -> None:
        rows = [
            {
                "site_id": 3816,
                "relative_period_rows": [
                    {
                        "relative_age_label": "CAL_1242_AD-",
                        "normalized_period_label": "unmapped_period_label",
                        "time_start_bp": None,
                        "time_end_bp": None,
                    }
                ],
                "dating_range_rows": [],
                "bibliography_rows": [],
            }
        ]

        refresh_sead_repository_rows(rows)

        self.assertEqual(rows[0]["time_start_bp"], 0)
        self.assertEqual(rows[0]["time_end_bp"], 708)
        relative_rows = cast(list[dict[str, object]], rows[0]["relative_period_rows"])
        relative_row = relative_rows[0]
        self.assertEqual(relative_row["interval_source"], "encoded_relative_age_label")

    def test_fetch_sead_site_rows_preserves_common_era_point_dates(self) -> None:
        def fake_fetch_json(
            url: str, params: list[tuple[str, str]] | None = None, **_: object
        ) -> object:
            del params
            if url.endswith("/tbl_sites"):
                return [
                    {
                        "site_id": 3816,
                        "site_name": "Låga längan",
                        "national_site_identifier": "3816",
                        "latitude_dd": 56.05,
                        "longitude_dd": 14.28,
                        "altitude": 24,
                        "site_description": "",
                        "site_uuid": "uuid-3816",
                    }
                ]
            if url.endswith("/tbl_sample_groups"):
                return [
                    {
                        "sample_group_id": 10,
                        "site_id": 3816,
                        "sample_group_name": "Historic layer",
                    }
                ]
            if url.endswith("/tbl_physical_samples"):
                return [{"physical_sample_id": 20, "sample_group_id": 10}]
            if url.endswith("/tbl_analysis_entities"):
                return [
                    {
                        "analysis_entity_id": 30,
                        "physical_sample_id": 20,
                        "dataset_id": 0,
                    }
                ]
            if url.endswith(
                (
                    "/tbl_analysis_entity_ages",
                    "/tbl_geochronology",
                    "/tbl_dendro_dates",
                )
            ):
                return []
            if url.endswith("/tbl_analysis_values"):
                return [{"analysis_value_id": 35, "analysis_entity_id": 30}]
            if url.endswith("/tbl_analysis_dating_ranges"):
                return [
                    {
                        "analysis_dating_range_id": 34,
                        "analysis_value_id": 35,
                        "low_value": 1754,
                        "high_value": None,
                        "age_type_id": 2,
                        "dating_uncertainty_id": None,
                        "low_qualifier": "",
                        "high_qualifier": "",
                        "low_is_uncertain": False,
                        "high_is_uncertain": False,
                    }
                ]
            if url.endswith("/tbl_age_types"):
                return [
                    {
                        "age_type_id": 2,
                        "age_type": "AD",
                        "description": "Anno Domini",
                    }
                ]
            if url.endswith("/tbl_relative_dates"):
                return []
            if url.endswith("/tbl_relative_ages"):
                return []
            if url.endswith("/tbl_dating_uncertainty"):
                return []
            if url.endswith("/tbl_methods"):
                return []
            if url.endswith("/tbl_datasets"):
                return []
            if url.endswith("/tbl_site_references"):
                return []
            if url.endswith(("/tbl_sample_group_references", "/tbl_relative_age_refs")):
                return []
            if url.endswith("/tbl_biblio"):
                return []
            raise AssertionError(f"Unexpected SEAD request: {url}")

        with patch(
            "bijux_pollenomics.collection.sources.sead.collection.fetch_json",
            side_effect=fake_fetch_json,
        ):
            rows = fetch_sead_site_rows((4.0, 54.0, 35.0, 72.0))

        self.assertEqual(rows[0]["time_start_bp"], 196)
        self.assertEqual(rows[0]["time_end_bp"], 196)
        self.assertEqual(rows[0]["numeric_time_start_bp"], 196)
        self.assertEqual(rows[0]["numeric_time_end_bp"], 196)
        dating_range_rows = cast(list[dict[str, object]], rows[0]["dating_range_rows"])
        self.assertEqual(dating_range_rows[0]["time_start_bp"], 196)
        self.assertEqual(dating_range_rows[0]["time_end_bp"], 196)
