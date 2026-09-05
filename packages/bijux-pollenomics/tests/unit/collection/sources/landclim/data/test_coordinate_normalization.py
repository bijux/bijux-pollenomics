from __future__ import annotations

import unittest

from bijux_pollenomics.collection.sources.landclim.collection import (
    feature_key_from_center,
    feature_key_from_geometry,
    grid_geometry_from_nw_cell_label,
    parse_coordinate,
)


class LandClimCoordinateNormalizationTests(unittest.TestCase):
    def test_landclim_grid_keys_match_between_workbook_and_csv_cells(self) -> None:
        geometry = grid_geometry_from_nw_cell_label("17°E 60°N")
        self.assertIsNotNone(geometry)
        if geometry is None:
            raise AssertionError("Expected grid geometry")
        self.assertEqual(
            feature_key_from_geometry(geometry), feature_key_from_center(17.5, 59.5)
        )

    def test_parse_coordinate_supports_decimal_and_dms_inputs(self) -> None:
        self.assertEqual(parse_coordinate("59.5"), 59.5)
        self.assertEqual(parse_coordinate("59.30.00N"), 59.5)
        self.assertEqual(parse_coordinate("17.30.00E"), 17.5)
        self.assertEqual(parse_coordinate("17.30.00W"), -17.5)
        self.assertEqual(parse_coordinate("59.30.00s"), -59.5)
        self.assertIsNone(parse_coordinate("59.30N"))
        self.assertIsNone(parse_coordinate(""))


if __name__ == "__main__":
    unittest.main()
