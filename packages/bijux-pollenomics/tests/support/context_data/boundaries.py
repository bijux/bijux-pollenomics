"""Country-boundary fixture shared by source normalization tests."""

import hashlib
import json
from pathlib import Path
import unittest

from bijux_pollenomics.collection.sources.boundaries.collection import (
    BOUNDARY_CODES,
    NATURAL_EARTH_ADMIN0_URL,
    NATURAL_EARTH_TERMS_URL,
    NATURAL_EARTH_VERSION,
)


class NordicBoundaryTestCase(unittest.TestCase):
    """Provide a minimal Sweden polygon for deterministic country resolution."""

    country_boundaries: dict[str, dict[str, object]]

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


def write_synthetic_boundary_manifest(raw_root: Path) -> None:
    """Bind synthetic country files to the real loader's receipt grammar."""
    artifacts = {
        country: {
            "path": f"{country.casefold()}.geojson",
            "sha256": hashlib.sha256(
                (raw_root / f"{country.casefold()}.geojson").read_bytes()
            ).hexdigest(),
        }
        for country in BOUNDARY_CODES
    }
    (raw_root / "source_manifest.json").write_text(
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
                "country_artifacts": artifacts,
            }
        )
        + "\n",
        encoding="utf-8",
    )


__all__ = ["NordicBoundaryTestCase", "write_synthetic_boundary_manifest"]
