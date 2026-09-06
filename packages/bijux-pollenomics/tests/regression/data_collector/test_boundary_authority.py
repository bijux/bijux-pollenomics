"""Regression coverage for data-collector boundary authority."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest
from bijux_pollenomics.collection.sources.boundaries.collection import (
    NATURAL_EARTH_ADMIN0_URL,
    NATURAL_EARTH_TERMS_URL,
    NATURAL_EARTH_VERSION,
)
from bijux_pollenomics.collection.workflow.collection import (
    build_staging_output_dir,
    collect_data,
)

pytestmark = pytest.mark.generated_artifacts


def _write_valid_boundary_manifest(raw_dir: Path) -> None:
    country_artifacts = {
        country: {
            "path": filename,
            "sha256": hashlib.sha256((raw_dir / filename).read_bytes()).hexdigest(),
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
                "geometry_inclusion_policy": (
                    "retain_all_geometry_parts_from_each_selected_admin0_feature"
                ),
                "country_artifacts": country_artifacts,
            }
        ),
        encoding="utf-8",
    )


class BoundaryAuthorityTests(unittest.TestCase):
    def test_collect_data_uses_local_boundaries_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            raw_dir = output_root / "boundaries" / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            boundary_payloads = {
                "sweden.geojson": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {"type": "Polygon", "coordinates": []},
                            "properties": {"ADM0_A3": "SWE"},
                        }
                    ],
                },
                "norway.geojson": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {"type": "Polygon", "coordinates": []},
                            "properties": {"ADM0_A3": "NOR"},
                        }
                    ],
                },
                "finland.geojson": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {"type": "Polygon", "coordinates": []},
                            "properties": {"ADM0_A3": "FIN"},
                        }
                    ],
                },
                "denmark.geojson": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {"type": "Polygon", "coordinates": []},
                            "properties": {"ADM0_A3": "DNK"},
                        }
                    ],
                },
            }
            for filename, payload in boundary_payloads.items():
                (raw_dir / filename).write_text(json.dumps(payload), encoding="utf-8")
            _write_valid_boundary_manifest(raw_dir)

            with (
                patch(
                    "bijux_pollenomics.collection.workflow.collection.fetch_country_boundaries"
                ) as fetch_boundaries,
                patch(
                    "bijux_pollenomics.collection.workflow.collection.collect_neotoma_data"
                ) as collect_neotoma,
            ):
                collect_neotoma.return_value.point_count = 6
                report = collect_data(
                    output_root=output_root, sources=("neotoma",), version="v62.0"
                )

            fetch_boundaries.assert_not_called()
            collect_neotoma.assert_called_once()
            self.assertEqual(report.boundary_source, "local")

    def test_collect_data_rejects_invalid_local_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"
            raw_dir = output_root / "boundaries" / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            invalid_payload = {"type": "Polygon"}
            for filename in (
                "sweden.geojson",
                "norway.geojson",
                "finland.geojson",
                "denmark.geojson",
            ):
                (raw_dir / filename).write_text(
                    json.dumps(invalid_payload), encoding="utf-8"
                )
            _write_valid_boundary_manifest(raw_dir)

            with self.assertRaisesRegex(ValueError, "FeatureCollection"):
                collect_data(
                    output_root=output_root, sources=("neotoma",), version="v62.0"
                )

    def test_collect_data_collects_landclim_with_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "data"

            with (
                patch(
                    "bijux_pollenomics.collection.workflow.collection.fetch_country_boundaries"
                ) as fetch_boundaries,
                patch(
                    "bijux_pollenomics.collection.workflow.collection.collect_landclim_data"
                ) as collect_landclim,
            ):
                fetch_boundaries.return_value = {"Sweden": {"features": []}}
                collect_landclim.return_value.site_count = 11
                collect_landclim.return_value.grid_cell_count = 7
                collect_landclim.return_value.temporal_grid_feature_count = 23

                report = collect_data(
                    output_root=output_root, sources=("landclim",), version="v62.0"
                )

            fetch_boundaries.assert_called_once()
            collect_landclim.assert_called_once_with(
                output_root=build_staging_output_dir(output_root / "landclim"),
                country_boundaries={"Sweden": {"features": []}},
                bbox=(4.0, 54.0, 35.0, 72.0),
            )
            self.assertEqual(report.landclim_site_count, 11)
            self.assertEqual(report.landclim_grid_cell_count, 7)
            self.assertEqual(report.landclim_temporal_grid_feature_count, 23)
