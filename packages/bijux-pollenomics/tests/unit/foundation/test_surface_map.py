from __future__ import annotations

import unittest

from bijux_pollenomics.foundation import SurfaceMap, build_surface_map


class SurfaceMapUnitTests(unittest.TestCase):
    def test_surface_map_lists_runtime_and_planned_surfaces(self) -> None:
        surface_map = build_surface_map()

        self.assertIsInstance(surface_map, SurfaceMap)
        self.assertGreaterEqual(len(surface_map.runtime_surfaces), 3)
        self.assertGreaterEqual(len(surface_map.planned_engine_surfaces), 2)
        self.assertIn("atlas bundle publication", surface_map.runtime_surfaces)


if __name__ == "__main__":
    unittest.main()
