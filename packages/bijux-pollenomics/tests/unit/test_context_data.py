from __future__ import annotations

import json
from pathlib import Path
import tempfile
from typing import cast
import unittest
from unittest.mock import patch
from urllib.error import URLError

from bijux_pollenomics.data_downloader.contracts import (
    BOUNDARY_COLLECTION,
    LANDCLIM_GRID_GEOJSON,
    NEOTOMA_POINT_GEOJSON,
)
from bijux_pollenomics.data_downloader.models import ContextPointRecord
from bijux_pollenomics.data_downloader.neotoma import normalize_neotoma_rows
from bijux_pollenomics.data_downloader.sead import (
    collect_sead_data,
    fetch_sead_rows,
    fetch_sead_site_rows,
    normalize_sead_rows,
)
from bijux_pollenomics.data_downloader.shared import (
    write_context_points_csv,
    write_context_points_geojson,
)
from bijux_pollenomics.reporting.context import (
    build_context_layers,
    build_external_point_layer,
    build_external_polygon_layer,
)


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
            if url.endswith("/tbl_analysis_values"):
                return [{"analysis_value_id": 35, "analysis_entity_id": 30}]
            if url.endswith("/tbl_analysis_dating_ranges"):
                return [
                    {
                        "analysis_value_id": 35,
                        "low_value": 200,
                        "high_value": 800,
                        "age_type_id": 2,
                    }
                ]
            if url.endswith("/tbl_age_types"):
                return [{"age_type_id": 2, "age_type": "calibrated years BP"}]
            if url.endswith("/tbl_relative_dates"):
                return [{"relative_date_id": 45, "analysis_entity_id": 30}]
            if url.endswith("/tbl_datasets"):
                return [{"dataset_id": 40, "dataset_name": "Pollen counts"}]
            if url.endswith("/tbl_site_references"):
                return [{"site_reference_id": 50, "site_id": 6468, "biblio_id": 60}]
            raise AssertionError(f"Unexpected SEAD request: {url} params={params}")

        with patch(
            "bijux_pollenomics.data_downloader.sead.fetch_json",
            side_effect=fake_fetch_json,
        ):
            rows = fetch_sead_site_rows((4.0, 54.0, 35.0, 72.0))

        self.assertEqual(rows[0]["sample_group_count"], 1)
        self.assertEqual(rows[0]["physical_sample_count"], 1)
        self.assertEqual(rows[0]["analysis_entity_count"], 1)
        self.assertEqual(rows[0]["dataset_count"], 1)
        self.assertEqual(rows[0]["dataset_names"], ["Pollen counts"])
        self.assertEqual(rows[0]["reference_count"], 1)
        self.assertEqual(rows[0]["relative_date_count"], 1)
        self.assertEqual(rows[0]["dating_range_count"], 1)
        self.assertEqual(rows[0]["time_start_bp"], 200)
        self.assertEqual(rows[0]["time_end_bp"], 800)
        self.assertIn(("site_id",), seen_orders)
        self.assertIn(("site_id", "sample_group_id"), seen_orders)
        self.assertIn(("physical_sample_id", "analysis_entity_id"), seen_orders)

    def test_fetch_sead_rows_retries_retryable_network_errors(self) -> None:
        with (
            patch(
                "bijux_pollenomics.data_downloader.sead.fetch_json",
                side_effect=[
                    URLError(OSError(51, "Network is unreachable")),
                    [{"site_id": 6468}],
                ],
            ),
            patch(
                "bijux_pollenomics.data_downloader.sources.sead.api_client.time.sleep"
            ),
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
                "bijux_pollenomics.data_downloader.sead.fetch_sead_site_inventory",
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

        self.assertEqual(raw_payload["bbox"], [4.0, 54.0, 35.0, 72.0])
        self.assertEqual(raw_payload["inventory_summary"]["dataset_row_count"], 9)
        self.assertIn("tbl_analysis_dating_ranges", raw_payload["source_tables"])

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
            description="Test record",
            source_url="https://example.test/site-1",
            record_count=3,
            popup_rows=(("Time windows", "0-100 BP, 350-700 BP"),),
            time_start_bp=0,
            time_end_bp=700,
            time_mean_bp=350,
            time_label="0-700 BP",
        )

        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "records.csv"
            geojson_path = Path(tmp) / "records.geojson"

            write_context_points_csv(csv_path, [record])
            write_context_points_geojson(geojson_path, [record])

            csv_text = csv_path.read_text(encoding="utf-8")
            geojson = json.loads(geojson_path.read_text(encoding="utf-8"))
            geojson_features = cast(
                list[dict[str, object]], cast(dict[str, object], geojson)["features"]
            )

        self.assertIn("time_start_bp", csv_text)
        self.assertIn("time_end_bp", csv_text)
        self.assertIn("time_mean_bp", csv_text)
        self.assertIn("time_label", csv_text)
        properties = cast(dict[str, object], geojson_features[0]["properties"])
        self.assertEqual(properties["time_start_bp"], 0)
        self.assertEqual(properties["time_end_bp"], 700)
        self.assertEqual(properties["time_mean_bp"], 350)
        self.assertEqual(properties["time_label"], "0-700 BP")

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
        layer_features = cast(list[dict[str, object]], layer["features"])
        self.assertEqual(layer_features[0]["time_start_bp"], 0)
        self.assertEqual(layer_features[0]["time_end_bp"], 700)
        self.assertEqual(layer_features[0]["time_mean_bp"], 350)
        self.assertEqual(layer_features[0]["time_label"], "0-700 BP")

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


if __name__ == "__main__":
    unittest.main()
