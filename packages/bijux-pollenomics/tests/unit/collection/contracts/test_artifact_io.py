"""Collection artifact input/output contract coverage."""

from __future__ import annotations

import unittest
from pathlib import Path

from bijux_pollenomics.collection.contracts.artifacts import (
    BOUNDARY_COLLECTION,
    LANDCLIM_GRID_GEOJSON,
    LANDCLIM_TEMPORAL_GRID_GEOJSON,
    NEOTOMA_POINT_GEOJSON,
)


class ArtifactContractTests(unittest.TestCase):
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
