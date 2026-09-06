"""SEAD collection acquisition coverage."""

from __future__ import annotations

import unittest
from typing import cast
from unittest.mock import patch
from urllib.error import URLError

from bijux_pollenomics.collection.sources.sead.collection import (
    fetch_sead_rows,
    fetch_sead_site_rows,
)


class SeadAcquisitionTests(unittest.TestCase):
    def test_fetch_sead_site_rows_adds_linked_inventory_counts(self) -> None:
        seen_orders: list[tuple[str, ...]] = []

        def fake_fetch_json(
            url: str, params: list[tuple[str, str]] | None = None, **_: object
        ) -> object:
            params = params or []
            order_values = tuple(value for key, value in params if key == "order")
            if order_values:
                seen_orders.extend(
                    tuple(part.strip() for part in value.split(","))
                    for value in order_values
                )
            if url.endswith("/tbl_sites"):
                return [
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
            if url.endswith("/tbl_sample_groups"):
                return [
                    {
                        "sample_group_id": 10,
                        "site_id": 6468,
                        "sample_group_name": "Layer A",
                    }
                ]
            if url.endswith("/tbl_physical_samples"):
                return [{"physical_sample_id": 20, "sample_group_id": 10}]
            if url.endswith("/tbl_analysis_entities"):
                return [
                    {
                        "analysis_entity_id": 30,
                        "physical_sample_id": 20,
                        "dataset_id": 40,
                    }
                ]
            if url.endswith("/tbl_analysis_entity_ages"):
                return [
                    {
                        "analysis_entity_age_id": 31,
                        "analysis_entity_id": 30,
                        "age": None,
                        "age_older": 1600,
                        "age_younger": 1500,
                        "chronology_id": None,
                        "dating_specifier": "Chosen_Calendar",
                        "age_range": "[1500,1601)",
                    }
                ]
            if url.endswith("/tbl_geochronology"):
                return [
                    {
                        "geochron_id": 32,
                        "analysis_entity_id": 30,
                        "dating_lab_id": 3,
                        "lab_number": "Lab-32",
                        "age": 1200,
                        "error_older": 50,
                        "error_younger": 50,
                        "notes": "",
                        "dating_uncertainty_id": 70,
                    }
                ]
            if url.endswith("/tbl_dendro_dates"):
                return [
                    {
                        "dendro_date_id": 33,
                        "analysis_entity_id": 30,
                        "age_older": 1750,
                        "age_younger": None,
                        "age_type_id": 1,
                        "dating_uncertainty_id": 70,
                        "dendro_lookup_id": 4,
                        "season_id": None,
                        "age_range": "[1750,1751)",
                    }
                ]
            if url.endswith("/tbl_analysis_values"):
                return [{"analysis_value_id": 35, "analysis_entity_id": 30}]
            if url.endswith("/tbl_analysis_dating_ranges"):
                return [
                    {
                        "analysis_dating_range_id": 34,
                        "analysis_value_id": 35,
                        "low_value": 200,
                        "high_value": 800,
                        "age_type_id": 2,
                        "dating_uncertainty_id": 70,
                        "low_qualifier": "",
                        "high_qualifier": "",
                        "low_is_uncertain": False,
                        "high_is_uncertain": False,
                    }
                ]
            if url.endswith("/tbl_age_types"):
                return [
                    {
                        "age_type_id": 1,
                        "age_type": "AD",
                        "description": "Anno Domini",
                    },
                    {
                        "age_type_id": 2,
                        "age_type": "calibrated years BP",
                        "description": "calendar years before present",
                    },
                ]
            if url.endswith("/tbl_relative_dates"):
                return [
                    {
                        "relative_date_id": 45,
                        "analysis_entity_id": 30,
                        "relative_age_id": 80,
                        "dating_uncertainty_id": 70,
                        "method_id": 90,
                        "notes": "Quaternary context",
                    }
                ]
            if url.endswith("/tbl_relative_ages"):
                return [
                    {
                        "relative_age_id": 80,
                        "relative_age_name": "Quaternary",
                        "description": "Geologic period",
                        "abbreviation": "Q",
                        "cal_age_older": 2700000,
                        "cal_age_younger": 12000,
                        "c14_age_older": None,
                        "c14_age_younger": None,
                    }
                ]
            if url.endswith("/tbl_dating_uncertainty"):
                return [
                    {
                        "dating_uncertainty_id": 70,
                        "uncertainty": "site aggregate",
                        "description": "multiple rows merged into one site span",
                    }
                ]
            if url.endswith("/tbl_methods"):
                return [
                    {
                        "method_id": 90,
                        "method_name": "Archaeological period calendar years",
                        "method_abbrev_or_alt_name": "",
                        "description": "Contextual site period",
                    }
                ]
            if url.endswith("/tbl_datasets"):
                return [
                    {"dataset_id": 40, "dataset_name": "Pollen counts", "biblio_id": 60}
                ]
            if url.endswith("/tbl_site_references"):
                return [{"site_reference_id": 50, "site_id": 6468, "biblio_id": 60}]
            if url.endswith("/tbl_sample_group_references"):
                return [
                    {
                        "sample_group_reference_id": 51,
                        "sample_group_id": 10,
                        "biblio_id": 60,
                    }
                ]
            if url.endswith("/tbl_relative_age_refs"):
                return [
                    {
                        "relative_age_ref_id": 52,
                        "relative_age_id": 80,
                        "biblio_id": 60,
                    }
                ]
            if url.endswith("/tbl_biblio"):
                return [
                    {
                        "biblio_id": 60,
                        "title": "Pollen counts from Fjalkinge",
                        "full_reference": "Example reference",
                        "year": 2024,
                        "doi": "10.1234/example",
                        "url": "https://example.test/reference",
                    }
                ]
            raise AssertionError(f"Unexpected SEAD request: {url} params={params}")

        with patch(
            "bijux_pollenomics.collection.sources.sead.collection.fetch_json",
            side_effect=fake_fetch_json,
        ):
            rows = fetch_sead_site_rows((4.0, 54.0, 35.0, 72.0))

        self.assertEqual(rows[0]["sample_group_count"], 1)
        self.assertEqual(rows[0]["physical_sample_count"], 1)
        self.assertEqual(rows[0]["analysis_entity_count"], 1)
        self.assertEqual(rows[0]["dataset_count"], 1)
        self.assertEqual(rows[0]["dataset_names"], ["Pollen counts"])
        self.assertEqual(rows[0]["site_reference_count"], 1)
        self.assertEqual(rows[0]["reference_count"], 4)
        self.assertEqual(rows[0]["relative_date_count"], 1)
        self.assertEqual(rows[0]["dating_range_count"], 1)
        self.assertEqual(rows[0]["analysis_entity_age_count"], 1)
        self.assertEqual(rows[0]["geochronology_count"], 1)
        self.assertEqual(rows[0]["dendro_date_count"], 1)
        self.assertEqual(rows[0]["time_start_bp"], 200)
        self.assertEqual(rows[0]["time_end_bp"], 1600)
        temporal_summary = cast(dict[str, object], rows[0]["temporal_summary"])
        analysis_entity_age_rows = cast(
            list[dict[str, object]], rows[0]["analysis_entity_age_rows"]
        )
        geochronology_rows = cast(
            list[dict[str, object]], rows[0]["geochronology_rows"]
        )
        dendro_date_rows = cast(list[dict[str, object]], rows[0]["dendro_date_rows"])
        relative_period_rows = cast(
            list[dict[str, object]], rows[0]["relative_period_rows"]
        )
        dating_range_rows = cast(list[dict[str, object]], rows[0]["dating_range_rows"])
        self.assertEqual(temporal_summary["relative_period_count"], 1)
        self.assertEqual(temporal_summary["bibliography_count"], 4)
        self.assertEqual(analysis_entity_age_rows[0]["time_end_bp"], 1600)
        self.assertEqual(geochronology_rows[0]["time_start_bp"], 1150)
        self.assertEqual(dendro_date_rows[0]["time_start_bp"], 200)
        self.assertEqual(
            relative_period_rows[0]["normalized_period_label"], "quaternary"
        )
        self.assertEqual(dating_range_rows[0]["uncertainty_label"], "site aggregate")
        self.assertIn(("site_id",), seen_orders)
        self.assertIn(("site_id", "sample_group_id"), seen_orders)
        self.assertIn(("physical_sample_id", "analysis_entity_id"), seen_orders)

    def test_fetch_sead_rows_retries_retryable_network_errors(self) -> None:
        with (
            patch(
                "bijux_pollenomics.collection.sources.sead.collection.fetch_json",
                side_effect=[
                    URLError(OSError(51, "Network is unreachable")),
                    [{"site_id": 6468}],
                ],
            ),
            patch(
                "bijux_pollenomics.collection.sources.sead.acquisition.client.time.sleep"
            ),
        ):
            rows = fetch_sead_rows("tbl_sites", select="site_id")

        self.assertEqual(rows, [{"site_id": 6468}])
