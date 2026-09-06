from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
from typing import cast
import unittest
from unittest.mock import patch

from bijux_pollenomics.collection.sources.boundaries.collection import (
    NATURAL_EARTH_ADMIN0_URL,
    NATURAL_EARTH_TERMS_URL,
    NATURAL_EARTH_VERSION,
    build_combined_country_boundaries,
    build_country_boundary_collection,
    collect_boundaries_data,
    load_country_boundaries,
)

GeoJsonFeature = dict[str, object]
GeoJsonCollection = dict[str, list[GeoJsonFeature] | str]


class BoundariesTests(unittest.TestCase):
    def test_build_country_boundary_collection_filters_natural_earth_by_adm0_code(
        self,
    ) -> None:
        global_boundaries = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [10.0, 55.0],
                                [11.0, 55.0],
                                [11.0, 56.0],
                                [10.0, 56.0],
                                [10.0, 55.0],
                            ]
                        ],
                    },
                    "properties": {"ADM0_A3": "DNK", "NAME": "Denmark"},
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [-45.0, 59.0],
                                [-40.0, 59.0],
                                [-40.0, 61.0],
                                [-45.0, 61.0],
                                [-45.0, 59.0],
                            ]
                        ],
                    },
                    "properties": {"ADM0_A3": "GRL", "NAME": "Greenland"},
                },
            ],
        }

        denmark = build_country_boundary_collection(global_boundaries, "DNK")
        denmark_features = cast(
            list[GeoJsonFeature], cast(GeoJsonCollection, denmark)["features"]
        )

        self.assertEqual(len(denmark_features), 1)
        properties = cast(dict[str, object], denmark_features[0]["properties"])
        self.assertEqual(properties["NAME"], "Denmark")

    def test_collect_boundaries_data_writes_country_files_and_combined_geojson(
        self,
    ) -> None:
        natural_earth_payload = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [16.0, 58.0],
                                [19.0, 58.0],
                                [19.0, 60.0],
                                [16.0, 60.0],
                                [16.0, 58.0],
                            ]
                        ],
                    },
                    "properties": {"ADM0_A3": "SWE", "NAME": "Sweden"},
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [4.0, 58.0],
                                [12.0, 58.0],
                                [12.0, 71.0],
                                [4.0, 71.0],
                                [4.0, 58.0],
                            ]
                        ],
                    },
                    "properties": {"ADM0_A3": "NOR", "NAME": "Norway"},
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [20.0, 60.0],
                                [31.0, 60.0],
                                [31.0, 70.0],
                                [20.0, 70.0],
                                [20.0, 60.0],
                            ]
                        ],
                    },
                    "properties": {"ADM0_A3": "FIN", "NAME": "Finland"},
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [8.0, 54.0],
                                [13.0, 54.0],
                                [13.0, 58.0],
                                [8.0, 58.0],
                                [8.0, 54.0],
                            ]
                        ],
                    },
                    "properties": {"ADM0_A3": "DNK", "NAME": "Denmark"},
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "boundaries"
            with patch(
                "bijux_pollenomics.collection.sources.boundaries.collection.fetch_natural_earth_admin0_payload",
                return_value=(
                    natural_earth_payload,
                    {
                        "schema_version": "natural-earth-boundary-receipt.v1",
                        "source": "Natural Earth",
                        "version": NATURAL_EARTH_VERSION,
                        "asset_url": NATURAL_EARTH_ADMIN0_URL,
                        "sha256": "a" * 64,
                        "license": "public_domain",
                        "license_url": NATURAL_EARTH_TERMS_URL,
                        "source_crs": "EPSG:4326",
                        "coordinate_transformation": "none",
                        "country_selection_field": "ADM0_A3",
                        "geometry_inclusion_policy": "retain_all_geometry_parts_from_each_selected_admin0_feature",
                    },
                ),
            ):
                country_boundaries, report = collect_boundaries_data(output_root)

            self.assertEqual(
                tuple(country_boundaries.keys()),
                ("Sweden", "Norway", "Finland", "Denmark"),
            )
            self.assertTrue((output_root / "raw" / "sweden.geojson").exists())
            self.assertTrue(report.combined_path.exists())
            self.assertTrue(report.manifest_path.exists())
            manifest = json.loads(report.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["license"], "public_domain")
            self.assertEqual(manifest["license_url"], NATURAL_EARTH_TERMS_URL)
            self.assertEqual(manifest["source_crs"], "EPSG:4326")
            self.assertEqual(manifest["coordinate_transformation"], "none")
            self.assertEqual(
                set(manifest["country_artifacts"]),
                {"Sweden", "Norway", "Finland", "Denmark"},
            )

            combined = build_combined_country_boundaries(country_boundaries)
            combined_features = cast(
                list[GeoJsonFeature], cast(GeoJsonCollection, combined)["features"]
            )
            self.assertEqual(len(combined_features), 4)
            self.assertEqual(
                cast(dict[str, object], combined_features[0]["properties"])[
                    "layer_key"
                ],
                "country-boundaries",
            )

    def test_load_country_boundaries_requires_valid_manifest(self) -> None:
        boundary_payload = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [10.0, 55.0],
                                [11.0, 55.0],
                                [11.0, 56.0],
                                [10.0, 56.0],
                                [10.0, 55.0],
                            ]
                        ],
                    },
                    "properties": {"ADM0_A3": "SWE"},
                }
            ],
        }
        payloads = {
            "sweden.geojson": boundary_payload,
            "norway.geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [4.0, 58.0],
                                    [5.0, 58.0],
                                    [5.0, 59.0],
                                    [4.0, 59.0],
                                    [4.0, 58.0],
                                ]
                            ],
                        },
                        "properties": {"ADM0_A3": "NOR"},
                    }
                ],
            },
            "finland.geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [20.0, 60.0],
                                    [21.0, 60.0],
                                    [21.0, 61.0],
                                    [20.0, 61.0],
                                    [20.0, 60.0],
                                ]
                            ],
                        },
                        "properties": {"ADM0_A3": "FIN"},
                    }
                ],
            },
            "denmark.geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [8.0, 54.0],
                                    [9.0, 54.0],
                                    [9.0, 55.0],
                                    [8.0, 55.0],
                                    [8.0, 54.0],
                                ]
                            ],
                        },
                        "properties": {"ADM0_A3": "DNK"},
                    }
                ],
            },
        }

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "boundaries"
            raw_dir = output_root / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            for filename, payload in payloads.items():
                (raw_dir / filename).write_text(json.dumps(payload), encoding="utf-8")

            self.assertIsNone(load_country_boundaries(output_root))

            country_artifacts = {
                country: {
                    "path": filename,
                    "sha256": hashlib.sha256(
                        (raw_dir / filename).read_bytes()
                    ).hexdigest(),
                }
                for country, filename in (
                    ("Sweden", "sweden.geojson"),
                    ("Norway", "norway.geojson"),
                    ("Finland", "finland.geojson"),
                    ("Denmark", "denmark.geojson"),
                )
            }
            (raw_dir / "source_manifest.json").write_text(
                json.dumps(
                    {
                        "schema_version": "natural-earth-boundary-receipt.v1",
                        "source": "Natural Earth",
                        "version": NATURAL_EARTH_VERSION,
                        "asset_url": NATURAL_EARTH_ADMIN0_URL,
                        "sha256": "a" * 64,
                        "license": "public_domain",
                        "license_url": NATURAL_EARTH_TERMS_URL,
                        "source_crs": "EPSG:4326",
                        "coordinate_transformation": "none",
                        "country_selection_field": "ADM0_A3",
                        "geometry_inclusion_policy": "retain_all_geometry_parts_from_each_selected_admin0_feature",
                        "country_artifacts": country_artifacts,
                    }
                ),
                encoding="utf-8",
            )

            loaded = load_country_boundaries(output_root)

        self.assertIsNotNone(loaded)
        if loaded is None:
            raise AssertionError("Expected boundaries payload to load")
        self.assertEqual(loaded["Sweden"], boundary_payload)

    def test_load_country_boundaries_refuses_tampered_country_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "boundaries"
            with patch(
                "bijux_pollenomics.collection.sources.boundaries.collection.fetch_natural_earth_admin0_payload",
                return_value=(
                    {
                        "type": "FeatureCollection",
                        "features": [
                            {
                                "type": "Feature",
                                "geometry": {
                                    "type": "Polygon",
                                    "coordinates": [
                                        [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]
                                    ],
                                },
                                "properties": {"ADM0_A3": code},
                            }
                            for code in ("SWE", "NOR", "FIN", "DNK")
                        ],
                    },
                    {
                        "schema_version": "natural-earth-boundary-receipt.v1",
                        "source": "Natural Earth",
                        "version": NATURAL_EARTH_VERSION,
                        "asset_url": NATURAL_EARTH_ADMIN0_URL,
                        "sha256": "b" * 64,
                        "license": "public_domain",
                        "license_url": NATURAL_EARTH_TERMS_URL,
                        "source_crs": "EPSG:4326",
                        "coordinate_transformation": "none",
                        "country_selection_field": "ADM0_A3",
                        "geometry_inclusion_policy": "retain_all_geometry_parts_from_each_selected_admin0_feature",
                    },
                ),
            ):
                collect_boundaries_data(output_root)
            sweden_path = output_root / "raw" / "sweden.geojson"
            sweden_path.write_text(
                sweden_path.read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                load_country_boundaries(output_root)


if __name__ == "__main__":
    unittest.main()
