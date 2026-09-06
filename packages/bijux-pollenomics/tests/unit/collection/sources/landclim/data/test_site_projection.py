from __future__ import annotations

import tempfile
import unittest
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from bijux_pollenomics.collection.sources.landclim.collection import (
    build_landclim_site_records,
    landclim_i_site_records,
)

from tests.support.geography import NORDIC_TEST_BBOX, SWEDEN_BOUNDARIES
from tests.support.workbooks import write_xlsx

CountryBoundaries = Mapping[str, Mapping[str, object]]


class LandClimSiteProjectionTests(unittest.TestCase):
    def test_landclim_i_site_records_keep_basin_type_separate_from_time_windows(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "landclim_i.xlsx"
            write_xlsx(
                path,
                {
                    "SiteData": [
                        [
                            "Country",
                            "Site name",
                            "Database name\\Author\\LandClimI member collating the data",
                            "Lat (DMS)",
                            "Long (DMS)",
                            "Elevation (masl)",
                            "Area of site (ha) (*Actual size)",
                            "Basin type (ie. Lake or Bog)",
                            "",
                            "",
                            "",
                            "",
                            "No. of dates for model (*incl. top)",
                        ],
                        [
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "0-100 cal BP",
                            "100-350 cal BP",
                            "350-700 cal BP",
                            "2700-3200 cal BP",
                            "5700-6200 cal BP",
                        ],
                        [
                            "SWE",
                            "Lake One",
                            "EPD",
                            "59.00.00N",
                            "17.00.00E",
                            "15",
                            "20",
                            "L",
                            "",
                            "L",
                            "",
                            "",
                            "4*",
                        ],
                    ],
                },
            )

            records = landclim_i_site_records(
                path,
                NORDIC_TEST_BBOX,
                cast(CountryBoundaries, SWEDEN_BOUNDARIES),
            )

            self.assertEqual(len(records), 1)
            popup = dict(records[0].popup_rows)
            self.assertEqual(popup["Site type"], "Lake")
            self.assertEqual(popup["Time windows"], "0-100 BP, 350-700 BP")
            self.assertEqual(records[0].time_start_bp, 0)
            self.assertEqual(records[0].time_end_bp, 700)
            self.assertEqual(records[0].time_mean_bp, 350)
            self.assertEqual(records[0].time_label, "0-100 BP to 350-700 BP")
            self.assertEqual(
                cast(dict[str, object], records[0].temporal_semantics)[
                    "comparability_posture"
                ],
                "numeric_interval",
            )

    def test_build_landclim_site_records_reads_both_landclim_i_workbooks_and_uses_reported_country(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            raw_paths = {
                "marquer_2017_reveals_taxa_grid_cells.xlsx": tmp_path / "marquer.xlsx",
                "landclim_i_land_cover_types.xlsx": tmp_path / "landclim_i_lct.xlsx",
                "landclim_i_plant_functional_types.xlsx": tmp_path
                / "landclim_i_pft.xlsx",
                "landclim_ii_site_metadata.xlsx": tmp_path / "landclim_ii.xlsx",
            }
            write_xlsx(
                raw_paths["marquer_2017_reveals_taxa_grid_cells.xlsx"],
                {
                    "Metadata": [
                        ["Grid", "Site", "", "Lat.", "Long.", "", "", "Basin type"]
                    ]
                },
            )
            landclim_i_rows: list[list[object]] = [
                [
                    "Country",
                    "Site name",
                    "Database name\\Author\\LandClimI member collating the data",
                    "Lat (DMS)",
                    "Long (DMS)",
                    "Elevation (masl)",
                    "Area of site (ha) (*Actual size)",
                    "Basin type (ie. Lake or Bog)",
                    "",
                ],
                ["", "", "", "", "", "", "", "0-100 cal BP"],
                [
                    "FIN",
                    "Fallback Site",
                    "EPD",
                    "60.00.00N",
                    "20.00.00E",
                    "10",
                    "2",
                    "L",
                    "L",
                ],
            ]
            write_xlsx(
                raw_paths["landclim_i_land_cover_types.xlsx"],
                {"SiteData": landclim_i_rows},
            )
            write_xlsx(
                raw_paths["landclim_i_plant_functional_types.xlsx"],
                {"Site Data": landclim_i_rows},
            )
            write_xlsx(
                raw_paths["landclim_ii_site_metadata.xlsx"],
                {
                    "LANDCLIMII metadata file": [
                        [
                            "SiteName",
                            "csvfilename",
                            "siteType",
                            "londd",
                            "latdd",
                            "Country",
                            "nTWs",
                        ],
                    ]
                },
            )

            records = build_landclim_site_records(
                raw_paths=raw_paths,
                bbox=NORDIC_TEST_BBOX,
                country_boundaries=cast(CountryBoundaries, SWEDEN_BOUNDARIES),
            )

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].country, "Finland")
            self.assertEqual(records[0].name, "Fallback Site")
            self.assertEqual(records[0].time_start_bp, 0)
            self.assertEqual(records[0].time_end_bp, 100)

    def test_landclim_ii_site_records_use_top_and_bottom_bp_as_interval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "landclim_ii.xlsx"
            write_xlsx(
                path,
                {
                    "LANDCLIMII metadata file": [
                        [
                            "SiteName",
                            "csvfilename",
                            "siteType",
                            "londd",
                            "latdd",
                            "Country",
                            "nTWs",
                            "TopBP",
                            "BotBP",
                        ],
                        [
                            "Lake Two",
                            "lake-two.csv",
                            "Lake",
                            "17.5",
                            "59.5",
                            "Sweden",
                            "4",
                            "150",
                            "2150",
                        ],
                    ]
                },
            )

            from bijux_pollenomics.collection.sources.landclim.collection import (
                landclim_ii_site_records,
            )

            records = landclim_ii_site_records(
                path, NORDIC_TEST_BBOX, cast(CountryBoundaries, SWEDEN_BOUNDARIES)
            )

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].time_start_bp, 150)
            self.assertEqual(records[0].time_end_bp, 2150)
            self.assertEqual(records[0].time_mean_bp, 1150)
            self.assertEqual(records[0].time_label, "150-2150 BP")
            popup = dict(records[0].popup_rows)
            self.assertEqual(
                cast(dict[str, object], records[0].temporal_semantics)[
                    "evidence_class"
                ],
                "pollen_site_sequence_coverage",
            )
            self.assertNotIn("Data owner or collector", popup)


if __name__ == "__main__":
    unittest.main()
