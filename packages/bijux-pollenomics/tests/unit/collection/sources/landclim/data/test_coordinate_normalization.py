from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import unittest

import pytest

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


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("-10.20.59E", -Fraction(10 * 3600 + 20 * 60 + 59, 3600)),
        ("-9.24.57E", -Fraction(9 * 3600 + 24 * 60 + 57, 3600)),
        ("-0.30.00E", -Fraction(1, 2)),
        ("-17.30.00W", Fraction(35, 2)),
        ("-59.30.00N", -Fraction(119, 2)),
        ("-59.30.00S", Fraction(119, 2)),
    ],
)
def test_signed_source_degrees_apply_to_the_entire_dms_magnitude(
    token: str, expected: Fraction
) -> None:
    # Published signed degrees express a signed magnitude on the named axis.
    assert parse_coordinate(token) == pytest.approx(float(expected), rel=0, abs=2e-15)


def test_native_signed_longitude_is_preserved_in_site_projection(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.landclim.collection import (
        landclim_i_site_records,
    )
    from tests.support.workbooks import write_xlsx

    path = tmp_path / "native-signed-coordinate.xlsx"
    write_xlsx(
        path,
        {
            "SiteData": [
                [
                    "Country",
                    "Site name",
                    "Source",
                    "Latitude",
                    "Longitude",
                    "Elevation",
                    "Area",
                    "Basin",
                ],
                ["", "", "", "", "", "", "", "0-100 cal BP"],
                [
                    "SWE",
                    "Coordinate control",
                    "Native-token control",
                    "59.30.00N",
                    "-10.20.59E",
                    "",
                    "",
                    "L",
                ],
            ]
        },
    )
    [record] = landclim_i_site_records(path, (-11.0, 59.0, -9.0, 60.0), {})
    assert record.longitude == pytest.approx(
        -float(Fraction(37259, 3600)), rel=0, abs=2e-15
    )
    assert record.latitude == 59.5
    assert record.time_start_bp == 0 and record.time_end_bp == 100


if __name__ == "__main__":
    unittest.main()
