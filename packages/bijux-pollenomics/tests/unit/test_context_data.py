from __future__ import annotations

import json
from pathlib import Path
import tempfile
from typing import cast
import unittest
from unittest.mock import patch
from urllib.error import URLError

from bijux_pollenomics.adna import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaSampleIdentity,
    AdnaSampleRecord,
)
from bijux_pollenomics.collection.contracts import (
    BOUNDARY_COLLECTION,
    LANDCLIM_GRID_GEOJSON,
    LANDCLIM_TEMPORAL_GRID_GEOJSON,
    NEOTOMA_POINT_GEOJSON,
)
from bijux_pollenomics.collection.exports import (
    write_context_points_csv,
    write_context_points_geojson,
)
from bijux_pollenomics.collection.models import ContextPointRecord
from bijux_pollenomics.collection.neotoma import normalize_neotoma_rows
from bijux_pollenomics.collection.sead import (
    collect_sead_data,
    fetch_sead_rows,
    fetch_sead_site_rows,
    materialize_sead_repository_surfaces,
    normalize_sead_rows,
    normalize_sead_temporal_evidence,
    refresh_sead_repository_rows,
    sead_dating_interval,
)
from bijux_pollenomics.reporting.context import (
    build_aadr_point_layer,
    build_context_layers,
    build_external_point_layer,
    build_external_polygon_layer,
)
from bijux_pollenomics.reporting.geography import build_published_geography_plan


class ContextDataTests(unittest.TestCase):
    def test_data_artifact_contracts_resolve_stable_paths(self) -> None:
        root = Path("/tmp/data")

        self.assertEqual(
            BOUNDARY_COLLECTION.path_under(root),
            root / "boundaries" / "normalized" / "nordic_country_boundaries.geojson",
        )
        self.assertEqual(
            NEOTOMA_POINT_GEOJSON.path_under(root),
            root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
        )
        self.assertEqual(
            LANDCLIM_GRID_GEOJSON.path_under(root),
            root / "landclim" / "normalized" / "nordic_reveals_grid_cells.geojson",
        )
        self.assertEqual(
            LANDCLIM_TEMPORAL_GRID_GEOJSON.path_under(root),
            root
            / "landclim"
            / "normalized"
            / "nordic_reveals_temporal_grid_cells.geojson",
        )

    def setUp(self) -> None:
        self.country_boundaries = {
            "Sweden": {
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
                        "properties": {"name": "Sweden"},
                    }
                ],
            }
        }

    def test_normalize_neotoma_rows_filters_to_nordic_bbox_and_reduces_polygons(
        self,
    ) -> None:
        rows = [
            {
                "siteid": 2961,
                "sitename": "Aborregol",
                "sitedescription": "Small lake.",
                "geography": json.dumps(
                    {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [17.0, 59.0],
                                [18.0, 59.0],
                                [18.0, 60.0],
                                [17.0, 60.0],
                                [17.0, 59.0],
                            ]
                        ],
                    }
                ),
                "altitude": 81,
                "collectionunits": [
                    {
                        "collectionunitid": 1,
                        "datasets": [{"datasetid": 10, "datasettype": "pollen"}],
                    }
                ],
            },
            {
                "siteid": 5000,
                "sitename": "Outside Nordic",
                "sitedescription": "Ignored.",
                "geography": json.dumps(
                    {"type": "Point", "coordinates": [-100.0, 40.0]}
                ),
                "altitude": 10,
                "collectionunits": [],
            },
        ]

        records = normalize_neotoma_rows(
            rows,
            bbox=(4.0, 54.0, 35.0, 72.0),
            country_boundaries=self.country_boundaries,
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].record_id, "2961")
        self.assertEqual(records[0].geometry_type, "Polygon")
        self.assertEqual(records[0].country, "Sweden")
        self.assertAlmostEqual(records[0].longitude, 17.5)
        self.assertAlmostEqual(records[0].latitude, 59.5)
        self.assertEqual(records[0].record_count, 1)

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
        self.assertEqual(records[0].name, "10412 Fjalkinge")
        self.assertEqual(records[0].country, "Sweden")
        self.assertEqual(records[0].category, "Environmental archaeology")
        self.assertEqual(records[0].popup_rows[0], ("Site ID", "6468"))
        self.assertEqual(records[0].time_start_bp, 200)
        self.assertEqual(records[0].time_end_bp, 800)
        self.assertEqual(records[0].time_mean_bp, 500)
        self.assertIsNotNone(records[0].temporal_semantics)
        self.assertEqual(
            records[0].temporal_semantics["comparability_posture"],
            "numeric_interval",
        )
        self.assertEqual(
            records[0].temporal_semantics["temporal_window_label"],
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
        self.assertEqual(first.layer_key, "sead-temporal-evidence")
        self.assertEqual(first.time_start_bp, 200)
        self.assertEqual(first.time_end_bp, 800)
        self.assertEqual(
            first.temporal_semantics["source_record_ids"],
            [34, 35],
        )

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
            "bijux_pollenomics.collection.sead.fetch_json",
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
        self.assertEqual(rows[0]["temporal_summary"]["relative_period_count"], 1)
        self.assertEqual(rows[0]["temporal_summary"]["bibliography_count"], 4)
        self.assertEqual(rows[0]["analysis_entity_age_rows"][0]["time_end_bp"], 1600)
        self.assertEqual(rows[0]["geochronology_rows"][0]["time_start_bp"], 1150)
        self.assertEqual(rows[0]["dendro_date_rows"][0]["time_start_bp"], 200)
        self.assertEqual(
            rows[0]["relative_period_rows"][0]["normalized_period_label"], "quaternary"
        )
        self.assertEqual(
            rows[0]["dating_range_rows"][0]["uncertainty_label"], "site aggregate"
        )
        self.assertIn(("site_id",), seen_orders)
        self.assertIn(("site_id", "sample_group_id"), seen_orders)
        self.assertIn(("physical_sample_id", "analysis_entity_id"), seen_orders)

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
        relative_row = rows[0]["relative_period_rows"][0]
        self.assertEqual(relative_row["interval_source"], "encoded_relative_age_label")

    def test_fetch_sead_site_rows_preserves_common_era_point_dates(self) -> None:
        def fake_fetch_json(
            url: str, params: list[tuple[str, str]] | None = None, **_: object
        ) -> object:
            _ = params
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
            "bijux_pollenomics.collection.sead.fetch_json",
            side_effect=fake_fetch_json,
        ):
            rows = fetch_sead_site_rows((4.0, 54.0, 35.0, 72.0))

        self.assertEqual(rows[0]["time_start_bp"], 196)
        self.assertEqual(rows[0]["time_end_bp"], 196)
        self.assertEqual(rows[0]["numeric_time_start_bp"], 196)
        self.assertEqual(rows[0]["numeric_time_end_bp"], 196)
        self.assertEqual(rows[0]["dating_range_rows"][0]["time_start_bp"], 196)
        self.assertEqual(rows[0]["dating_range_rows"][0]["time_end_bp"], 196)

    def test_fetch_sead_rows_retries_retryable_network_errors(self) -> None:
        with (
            patch(
                "bijux_pollenomics.collection.sead.fetch_json",
                side_effect=[
                    URLError(OSError(51, "Network is unreachable")),
                    [{"site_id": 6468}],
                ],
            ),
            patch("bijux_pollenomics.collection.sources.sead.api_client.time.sleep"),
        ):
            rows = fetch_sead_rows("tbl_sites", select="site_id")

        self.assertEqual(rows, [{"site_id": 6468}])

    def test_collect_sead_data_writes_inventory_summary(self) -> None:
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
                "dataset_count": 1,
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "sead"
            with patch(
                "bijux_pollenomics.collection.sead.fetch_sead_site_inventory",
                return_value=type(
                    "FetchResult",
                    (),
                    {
                        "rows": rows,
                        "inventory_summary": {
                            "site_row_count": 1,
                            "sample_group_row_count": 2,
                            "physical_sample_row_count": 3,
                            "analysis_entity_row_count": 4,
                            "analysis_value_row_count": 5,
                            "dating_range_row_count": 6,
                            "age_type_row_count": 7,
                            "relative_date_row_count": 8,
                            "dataset_row_count": 9,
                            "site_reference_row_count": 10,
                        },
                    },
                )(),
            ):
                report = collect_sead_data(
                    output_root=output_root,
                    country_boundaries=self.country_boundaries,
                    bbox=(4.0, 54.0, 35.0, 72.0),
                )

            raw_payload = json.loads(report.raw_path.read_text(encoding="utf-8"))
            temporal_geojson_exists = (
                output_root / "normalized" / "nordic_temporal_evidence.geojson"
            ).exists()

        self.assertEqual(raw_payload["bbox"], [4.0, 54.0, 35.0, 72.0])
        self.assertEqual(raw_payload["inventory_summary"]["dataset_row_count"], 9)
        self.assertIn("tbl_analysis_dating_ranges", raw_payload["source_tables"])
        self.assertTrue(temporal_geojson_exists)

    def test_materialize_sead_repository_surfaces_rebuilds_review_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            (data_root / "sead" / "raw").mkdir(parents=True, exist_ok=True)
            (data_root / "boundaries" / "raw").mkdir(parents=True, exist_ok=True)
            (data_root / "sead" / "raw" / "nordic_sites.json").write_text(
                json.dumps(
                    {
                        "source": "SEAD",
                        "endpoint": "https://browser.sead.se/postgrest/tbl_sites",
                        "generated_on": "2026-05-09",
                        "row_count": 1,
                        "inventory_summary": {
                            "analysis_entity_row_count": 4,
                            "dataset_row_count": 9,
                        },
                        "rows": [
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
                        ],
                    }
                ),
                encoding="utf-8",
            )
            for country in ("sweden", "denmark", "norway", "finland"):
                payload = (
                    self.country_boundaries["Sweden"]
                    if country == "sweden"
                    else {
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
                                "properties": {
                                    "ADM0_A3": {
                                        "denmark": "DNK",
                                        "norway": "NOR",
                                        "finland": "FIN",
                                    }[country]
                                },
                            }
                        ],
                    }
                )
                if country == "sweden":
                    payload = {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "geometry": self.country_boundaries["Sweden"][
                                    "features"
                                ][0]["geometry"],
                                "properties": {"ADM0_A3": "SWE"},
                            }
                        ],
                    }
                (data_root / "boundaries" / "raw" / f"{country}.geojson").write_text(
                    json.dumps(payload),
                    encoding="utf-8",
                )

            fixture_rows = json.loads(
                (data_root / "sead" / "raw" / "nordic_sites.json").read_text(
                    encoding="utf-8"
                )
            )["rows"]
            with (
                patch(
                    "bijux_pollenomics.collection.sead.validate_governed_sead_admission"
                ),
                patch(
                    "bijux_pollenomics.collection.sead._load_sead_acquisition_rows",
                    return_value=[],
                ),
                patch(
                    "bijux_pollenomics.collection.sead."
                    "build_sead_site_rows_from_acquisition_tables",
                    return_value=(fixture_rows, {}),
                ),
                patch(
                    "bijux_pollenomics.collection.sead._attach_sead_country_decisions"
                ),
                patch(
                    "bijux_pollenomics.collection.sead."
                    "write_sead_chronology_claim_bundle_from_snapshot"
                ),
            ):
                report = materialize_sead_repository_surfaces(data_root)

            normalized_payload = json.loads(
                report.normalized_geojson_path.read_text(encoding="utf-8")
            )
            feature = normalized_payload["features"][0]
            evidence_review = json.loads(
                (
                    data_root / "sead" / "review" / "evidence_legibility_review.json"
                ).read_text(encoding="utf-8")
            )
            access_model = json.loads(
                (data_root / "sead" / "review" / "access_model.json").read_text(
                    encoding="utf-8"
                )
            )
            temporal_review = json.loads(
                (data_root / "sead" / "review" / "temporal_review.json").read_text(
                    encoding="utf-8"
                )
            )
            recovery_requirements = json.loads(
                (
                    data_root / "sead" / "review" / "recovery_requirements.json"
                ).read_text(encoding="utf-8")
            )
            temporal_geojson = json.loads(
                (
                    data_root
                    / "sead"
                    / "normalized"
                    / "nordic_temporal_evidence.geojson"
                ).read_text(encoding="utf-8")
            )

        self.assertEqual(report.point_count, 1)
        self.assertEqual(temporal_geojson["features"], [])
        self.assertEqual(feature["properties"]["country"], "Sweden")
        self.assertEqual(
            feature["properties"]["temporal_semantics"]["comparability_posture"],
            "unresolved",
        )
        self.assertEqual(
            evidence_review["normalization_risk_counts"]["high_thin_site_inventory"],
            1,
        )
        self.assertEqual(
            access_model["access_visibility_counts"]["site_page_only"],
            1,
        )
        self.assertEqual(
            temporal_review["inventory_summary"]["temporal_capture_posture"],
            "site_inventory_only",
        )
        self.assertEqual(
            temporal_review["inventory_summary"]["dating_range_row_count"],
            0,
        )
        self.assertEqual(
            temporal_review["inventory_summary"]["site_inventory_only_row_count"],
            1,
        )
        self.assertEqual(
            temporal_review["rows"][0]["raw_capture_posture"],
            "site_inventory_only",
        )
        self.assertEqual(
            recovery_requirements["schema_version"],
            "sead-recovery-requirements.v1",
        )
        self.assertEqual(
            recovery_requirements["rows"][0]["requirement_key"],
            "unresolved_chronology_boundary",
        )
        self.assertEqual(recovery_requirements["rows"][0]["evidence_gap_count"], 1)

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
        )

        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "records.csv"
            geojson_path = Path(tmp) / "records.geojson"

            write_context_points_csv(csv_path, [record])
            write_context_points_geojson(geojson_path, [record])

            csv_text = csv_path.read_text(encoding="utf-8")
            csv_bytes = csv_path.read_bytes()
            geojson = json.loads(geojson_path.read_text(encoding="utf-8"))
            geojson_features = cast(
                list[dict[str, object]], cast(dict[str, object], geojson)["features"]
            )

        self.assertIn("time_start_bp", csv_text)
        self.assertIn("time_end_bp", csv_text)
        self.assertIn("time_mean_bp", csv_text)
        self.assertIn("time_label", csv_text)
        self.assertIn("temporal_semantics_json", csv_text)
        self.assertNotIn(b"\r\n", csv_bytes)
        self.assertIn("First line\nSecond line", csv_text)
        self.assertNotIn("First line   \n", csv_text)
        properties = cast(dict[str, object], geojson_features[0]["properties"])
        self.assertEqual(properties["time_start_bp"], 0)
        self.assertEqual(properties["time_end_bp"], 700)
        self.assertEqual(properties["time_mean_bp"], 350)
        self.assertEqual(properties["time_label"], "0-700 BP")
        self.assertEqual(
            properties["temporal_semantics"]["temporal_window_label"],
            "Recent and historical (0-1000 BP)",
        )

    def test_external_point_layers_enable_time_filter_when_temporal_properties_exist(
        self,
    ) -> None:
        layer = build_external_point_layer(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [17.0, 59.0]},
                        "properties": {
                            "layer_key": "landclim-sites",
                            "layer_label": "LandClim pollen sites",
                            "country": "Sweden",
                            "name": "Lake One",
                            "category": "Pollen sequence",
                            "time_start_bp": 0,
                            "time_end_bp": 700,
                        },
                    }
                ],
            }
        )

        self.assertTrue(layer["applies_time_filter"])
        self.assertTrue(layer["default_enabled"])
        layer_features = cast(list[dict[str, object]], layer["features"])
        self.assertEqual(layer_features[0]["time_start_bp"], 0)
        self.assertEqual(layer_features[0]["time_end_bp"], 700)
        self.assertEqual(layer_features[0]["time_mean_bp"], 350)
        self.assertEqual(layer_features[0]["time_label"], "0-700 BP")
        self.assertEqual(
            layer_features[0]["temporal_window_label"],
            "Recent and historical (0-1000 BP)",
        )

    def test_external_temporal_sead_layer_is_time_filterable_by_default(self) -> None:
        layer = build_external_point_layer(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [17.0, 59.0]},
                        "properties": {
                            "layer_key": "sead-temporal-evidence",
                            "layer_label": "SEAD temporal evidence",
                            "country": "Sweden",
                            "name": "Dated chronology",
                            "category": "Environmental archaeology chronology",
                            "time_start_bp": 1200,
                            "time_end_bp": 1800,
                        },
                    }
                ],
            }
        )

        self.assertTrue(layer["applies_time_filter"])
        self.assertTrue(layer["default_enabled"])
        layer_features = cast(list[dict[str, object]], layer["features"])
        self.assertEqual(layer_features[0]["time_start_bp"], 1200)
        self.assertEqual(layer_features[0]["time_end_bp"], 1800)

    def test_external_point_layers_do_not_treat_context_labels_as_numeric_time(
        self,
    ) -> None:
        layer = build_external_point_layer(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [17.0, 59.0]},
                        "properties": {
                            "layer_key": "sead-sites",
                            "layer_label": "SEAD environmental sites",
                            "country": "Sweden",
                            "name": "Undated site",
                            "category": "Environmental archive",
                            "time_label": "Relative chronology available",
                            "temporal_semantics": {
                                "comparability_posture": "context_only",
                                "temporal_window_key": "unresolved",
                                "temporal_window_label": "Unresolved",
                            },
                        },
                    }
                ],
            }
        )

        self.assertFalse(layer["applies_time_filter"])

    def test_external_point_layers_enable_time_filter_for_mixed_sead_chronology(
        self,
    ) -> None:
        layer = build_external_point_layer(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [17.0, 59.0]},
                        "properties": {
                            "layer_key": "sead-sites",
                            "layer_label": "SEAD environmental sites",
                            "country": "Sweden",
                            "name": "Dated site",
                            "category": "Environmental archive",
                            "time_start_bp": 1200,
                            "time_end_bp": 1800,
                        },
                    },
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [18.0, 60.0]},
                        "properties": {
                            "layer_key": "sead-sites",
                            "layer_label": "SEAD environmental sites",
                            "country": "Sweden",
                            "name": "Undated site",
                            "category": "Environmental archive",
                            "temporal_semantics": {
                                "comparability_posture": "unresolved",
                                "temporal_window_key": "unresolved",
                                "temporal_window_label": "Unresolved",
                            },
                        },
                    },
                ],
            }
        )

        self.assertTrue(layer["applies_time_filter"])
        self.assertFalse(layer["default_enabled"])

    def test_external_polygon_layers_enable_time_filter_when_temporal_properties_exist(
        self,
    ) -> None:
        layer = build_external_polygon_layer(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [16.0, 58.0],
                                    [17.0, 58.0],
                                    [17.0, 59.0],
                                    [16.0, 59.0],
                                    [16.0, 58.0],
                                ]
                            ],
                        },
                        "properties": {
                            "layer_key": "landclim-reveals-grid",
                            "layer_label": "LandClim REVEALS grid cells",
                            "country": "Sweden",
                            "time_start_bp": 100,
                            "time_end_bp": 1200,
                        },
                    }
                ],
            }
        )

        self.assertTrue(layer["applies_time_filter"])

    def test_build_aadr_point_layer_includes_release_version_in_label(self) -> None:
        layer = build_aadr_point_layer(samples=(), version="v66")

        self.assertEqual(layer["label"], "AADR-v66 aDNA samples")

    def test_build_aadr_point_layer_surfaces_provenance_rich_popup_rows(self) -> None:
        layer = build_aadr_point_layer(
            samples=(
                AdnaSampleRecord(
                    identity=AdnaSampleIdentity(
                        namespace="homo_sapiens:aadr_genetic_id",
                        stable_token="SE1",
                        accession_lineage=("species:Homo sapiens", "dataset:ho"),
                    ),
                    locality_identity=AdnaLocalityIdentity(
                        namespace="homo_sapiens:locality",
                        stable_token="homo_sapiens:aadr:uppsala",
                        locality_text="Uppsala",
                        political_entity="Sweden",
                        source_anchor_tokens=("SE1",),
                    ),
                    species_latin_name="Homo sapiens",
                    species_common_name="human",
                    source_family="AADR",
                    source_release="v66",
                    record_modality="metadata_only",
                    review_strength="curated_release_metadata",
                    provenance_quality="release_manifest_pinned",
                    master_id="SE1",
                    group_id="Sweden_Group",
                    locality="Uppsala",
                    political_entity="Sweden",
                    coordinates=AdnaCoordinate(
                        latitude=59.8586,
                        longitude=17.6389,
                        latitude_text="59.8586",
                        longitude_text="17.6389",
                        confidence="exact",
                    ),
                    publication="PaperA",
                    year_first_published="2022",
                    full_date="500 BCE",
                    chronology=AdnaChronology(
                        original_text="500 BCE",
                        time_start_bp=2200,
                        time_end_bp=2700,
                        time_mean_bp=2450,
                        dating_basis="bp_mean_and_stddev",
                    ),
                    data_type="HO",
                    molecular_sex="F",
                    datasets=("ho",),
                ),
            ),
            version="v66",
        )

        feature = cast(list[dict[str, object]], layer["features"])[0]
        popup = {
            row["label"]: row["value"]
            for row in cast(list[dict[str, str]], feature["popup_rows"])
        }

        self.assertEqual(layer["atlas_layer_key"], "homo_sapiens_direct")
        self.assertEqual(layer["contribution_role"], "direct")
        self.assertEqual(feature["species_latin_name"], "Homo sapiens")
        self.assertEqual(feature["evidence_role"], "direct")
        self.assertEqual(popup["Source release"], "v66")
        self.assertEqual(popup["Record modality"], "metadata_only")
        self.assertEqual(popup["Coordinate confidence"], "exact")
        self.assertEqual(popup["Dating basis"], "bp_mean_and_stddev")

    def test_build_context_layers_adds_fieldwork_point_when_gallery_media_exists(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            docs_root = Path(tmp) / "docs"
            output_dir = docs_root / "report" / "nordic-atlas"
            gallery_root = docs_root / "gallery"
            output_dir.mkdir(parents=True, exist_ok=True)
            gallery_root.mkdir(parents=True, exist_ok=True)
            (gallery_root / "2026-02-26-data-collection.JPG").write_bytes(b"jpeg")
            (gallery_root / "2026-02-26-data-collection.mp4").write_bytes(b"mp4")

            point_layers, polygon_layers, extra_artifacts = build_context_layers(
                samples=(),
                version="v66",
                output_dir=output_dir,
                context_root=None,
            )

        self.assertEqual(len(polygon_layers), 0)
        self.assertEqual(extra_artifacts, [])
        self.assertEqual(point_layers[1]["key"], "fieldwork-documentation")
        fieldwork_features = cast(list[dict[str, object]], point_layers[1]["features"])
        media_links = cast(
            list[dict[str, object]], fieldwork_features[0]["media_links"]
        )
        self.assertEqual(fieldwork_features[0]["title"], "Lyngsjön Lake field sampling")
        self.assertEqual(
            media_links[0]["url"],
            "../../gallery/2026-02-26-data-collection.JPG",
        )
        self.assertEqual(
            media_links[1]["url"],
            "../../gallery/2026-02-26-data-collection.mp4",
        )

    def test_fieldwork_layer_uses_public_path_during_isolated_build(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs_root = root / "docs"
            published_output_dir = docs_root / "report" / "regions" / "nordic"
            gallery_root = docs_root / "gallery"
            physical_output_dir = root / "artifacts" / "isolated-report"
            gallery_root.mkdir(parents=True, exist_ok=True)
            physical_output_dir.mkdir(parents=True, exist_ok=True)
            (gallery_root / "2026-02-26-data-collection.JPG").write_bytes(b"jpeg")

            point_layers, _, _ = build_context_layers(
                samples=(),
                version="v66",
                output_dir=physical_output_dir,
                published_output_dir=published_output_dir,
                context_root=None,
                geography_scope=build_published_geography_plan(
                    ("Sweden", "Denmark", "Norway", "Finland")
                ).regional_scopes[-1],
            )

        fieldwork_features = cast(list[dict[str, object]], point_layers[1]["features"])
        media_links = cast(
            list[dict[str, object]], fieldwork_features[0]["media_links"]
        )
        self.assertEqual(
            media_links[0]["url"],
            "../../../gallery/2026-02-26-data-collection.JPG",
        )


if __name__ == "__main__":
    unittest.main()
