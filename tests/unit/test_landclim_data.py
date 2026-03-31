from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bijux_pollenomics.data_downloader.landclim import (
    build_landclim_raw_asset_summaries,
    build_landclim_site_records,
    build_landclim_grid_geojson,
    download_landclim_raw_assets,
    feature_key_from_center,
    feature_key_from_geometry,
    grid_geometry_from_nw_cell_label,
    inspect_landclim_ii_archive,
    landclim_i_site_records,
    parse_coordinate,
    resolve_landclim_marquer_asset_urls,
    resolve_landclim_tabular_asset_urls,
)
from tests.support.geography import NORDIC_TEST_BBOX, SWEDEN_BOUNDARIES
from tests.support.workbooks import write_landclim_ii_zip, write_xlsx


class LandClimDataTests(unittest.TestCase):
    def test_landclim_i_site_records_keep_basin_type_separate_from_time_windows(self) -> None:
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
                        ["", "", "", "", "", "", "", "0-100 cal BP", "100-350 cal BP", "350-700 cal BP", "2700-3200 cal BP", "5700-6200 cal BP"],
                        ["SWE", "Lake One", "EPD", "59.00.00N", "17.00.00E", "15", "20", "L", "", "L", "", "", "4*"],
                    ],
                },
            )

            records = landclim_i_site_records(path, NORDIC_TEST_BBOX, SWEDEN_BOUNDARIES)

            self.assertEqual(len(records), 1)
            popup = {label: value for label, value in records[0].popup_rows}
            self.assertEqual(popup["Site type"], "Lake")
            self.assertEqual(popup["Time windows"], "0-100 BP, 350-700 BP")
            self.assertEqual(records[0].time_start_bp, 0)
            self.assertEqual(records[0].time_end_bp, 700)
            self.assertEqual(records[0].time_mean_bp, 350)
            self.assertEqual(records[0].time_label, "0-100 BP to 350-700 BP")

    def test_landclim_grid_merge_uses_one_feature_for_same_cell(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            raw_paths = {
                "landclim_i_land_cover_types.xlsx": tmp_path / "landclim_i_land_cover_types.xlsx",
                "landclim_i_plant_functional_types.xlsx": tmp_path / "landclim_i_plant_functional_types.xlsx",
                "landclim_ii_grid_cell_quality.xlsx": tmp_path / "landclim_ii_grid_cell_quality.xlsx",
                "landclim_ii_reveals_results.zip": tmp_path / "landclim_ii_reveals_results.zip",
            }
            write_xlsx(
                raw_paths["landclim_i_land_cover_types.xlsx"],
                {
                    "0-100BPmeanLC": [
                        ["Country", "", "Grid cell", "", "Open land"],
                        ["", "", "", "", ""],
                        ["SWE", "", "17°E 60°N", "", "0.25"],
                    ]
                },
            )
            write_xlsx(
                raw_paths["landclim_i_plant_functional_types.xlsx"],
                {
                    "0-100BPmeanLC": [
                        ["Country", "", "Grid cell", "", "PFT"],
                        ["", "", "", "", ""],
                        ["SWE", "", "17°E 60°N", "", "0.10"],
                    ]
                },
            )
            write_xlsx(
                raw_paths["landclim_ii_grid_cell_quality.xlsx"],
                {
                    "GC_quality_by_TW": [
                        ["LCGRID_ID", "", "", "0-100 BP"],
                        ["GC001", "", "", "1"],
                    ]
                },
            )
            write_landclim_ii_zip(
                raw_paths["landclim_ii_reveals_results.zip"],
                [
                    {
                        "LCGRID_ID": "GC001",
                        "lonDD": "17.5",
                        "latDD": "59.5",
                        "PICEA": "0.12",
                    }
                ],
            )

            geojson = build_landclim_grid_geojson(raw_paths, NORDIC_TEST_BBOX, SWEDEN_BOUNDARIES)

            self.assertEqual(len(geojson["features"]), 1)
            properties = geojson["features"][0]["properties"]
            self.assertNotIn("_dataset_labels", geojson["features"][0])
            popup = {row["label"]: row["value"] for row in properties["popup_rows"]}
            self.assertIn("LandClim I land-cover types", popup["Datasets"])
            self.assertIn("LandClim I plant functional types", popup["Datasets"])
            self.assertIn("LandClim II REVEALS grids", popup["Datasets"])
            self.assertEqual(popup["LandClim II quality"], "high")
            self.assertEqual(properties["time_start_bp"], 0)
            self.assertEqual(properties["time_end_bp"], 100)
            self.assertEqual(properties["time_mean_bp"], 50)
            self.assertEqual(properties["time_label"], "0-100 BP")

    def test_inspect_landclim_ii_archive_validates_documented_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "landclim_ii_reveals_results.zip"
            write_landclim_ii_zip(path, [{"LCGRID_ID": "GC001", "lonDD": "17.5", "latDD": "59.5", "PICEA": "0.12"}])

            summary = inspect_landclim_ii_archive(path)

        self.assertEqual(summary["mean_file_count"], 25)
        self.assertEqual(summary["standard_error_file_count"], 25)
        self.assertEqual(summary["time_windows"][0], "0-100 BP")
        self.assertEqual(summary["time_windows"][-1], "11200-11700 BP")

    def test_inspect_landclim_ii_archive_rejects_missing_standard_error_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "landclim_ii_reveals_results.zip"
            write_landclim_ii_zip(
                path,
                [{"LCGRID_ID": "GC001", "lonDD": "17.5", "latDD": "59.5", "PICEA": "0.12"}],
                include_standard_errors=False,
            )

            with self.assertRaisesRegex(ValueError, "standard-error"):
                inspect_landclim_ii_archive(path)

    def test_landclim_grid_keys_match_between_workbook_and_csv_cells(self) -> None:
        geometry = grid_geometry_from_nw_cell_label("17°E 60°N")
        self.assertIsNotNone(geometry)
        self.assertEqual(feature_key_from_geometry(geometry), feature_key_from_center(17.5, 59.5))

    def test_parse_coordinate_supports_decimal_and_dms_inputs(self) -> None:
        self.assertEqual(parse_coordinate("59.5"), 59.5)
        self.assertEqual(parse_coordinate("59.30.00N"), 59.5)
        self.assertEqual(parse_coordinate("17.30.00E"), 17.5)
        self.assertEqual(parse_coordinate("17.30.00W"), -17.5)
        self.assertEqual(parse_coordinate("59.30.00s"), -59.5)
        self.assertIsNone(parse_coordinate("59.30N"))
        self.assertIsNone(parse_coordinate(""))

    def test_build_landclim_site_records_reads_both_landclim_i_workbooks_and_uses_reported_country(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            raw_paths = {
                "marquer_2017_reveals_taxa_grid_cells.xlsx": tmp_path / "marquer.xlsx",
                "landclim_i_land_cover_types.xlsx": tmp_path / "landclim_i_lct.xlsx",
                "landclim_i_plant_functional_types.xlsx": tmp_path / "landclim_i_pft.xlsx",
                "landclim_ii_site_metadata.xlsx": tmp_path / "landclim_ii.xlsx",
            }
            write_xlsx(raw_paths["marquer_2017_reveals_taxa_grid_cells.xlsx"], {"Metadata": [["Grid", "Site", "", "Lat.", "Long.", "", "", "Basin type"]]})
            landclim_i_rows = [
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
                ["FIN", "Fallback Site", "EPD", "60.00.00N", "20.00.00E", "10", "2", "L", "L"],
            ]
            write_xlsx(raw_paths["landclim_i_land_cover_types.xlsx"], {"SiteData": landclim_i_rows})
            write_xlsx(raw_paths["landclim_i_plant_functional_types.xlsx"], {"Site Data": landclim_i_rows})
            write_xlsx(
                raw_paths["landclim_ii_site_metadata.xlsx"],
                {
                    "LANDCLIMII metadata file": [
                        ["SiteName", "csvfilename", "siteType", "londd", "latdd", "Country", "nTWs"],
                    ]
                },
            )

            records = build_landclim_site_records(
                raw_paths=raw_paths,
                bbox=NORDIC_TEST_BBOX,
                country_boundaries=SWEDEN_BOUNDARIES,
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
                        ["SiteName", "csvfilename", "siteType", "londd", "latdd", "Country", "nTWs", "TopBP", "BotBP"],
                        ["Lake Two", "lake-two.csv", "Lake", "17.5", "59.5", "Sweden", "4", "150", "2150"],
                    ]
                },
            )

            from bijux_pollenomics.data_downloader.landclim import landclim_ii_site_records

            records = landclim_ii_site_records(path, NORDIC_TEST_BBOX, SWEDEN_BOUNDARIES)

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].time_start_bp, 150)
            self.assertEqual(records[0].time_end_bp, 2150)
            self.assertEqual(records[0].time_mean_bp, 1150)
            self.assertEqual(records[0].time_label, "150-2150 BP")

    def test_resolve_landclim_asset_urls_reads_pangaea_record_formats(self) -> None:
        marquer_html = '<a id="static-download-link" href="https://store.pangaea.de/Publications/Marquer-etal_2017/MARQUER_QSR2017.xlsx">Download dataset</a>'
        self.assertEqual(
            resolve_landclim_marquer_asset_urls(marquer_html),
            {
                "marquer_2017_reveals_taxa_grid_cells.xlsx": "https://store.pangaea.de/Publications/Marquer-etal_2017/MARQUER_QSR2017.xlsx"
            },
        )

        landclim_i_text = """/* DATA DESCRIPTION: */\nContent\tFile name\tFile format\tFile size [kByte]\tURL file\nLCT\tLandClimILCTs\tXLSX\t216.697\thttps://store.pangaea.de/Publications/Gaillard-Lemdahl_2019/LandClimILCTs.xlsx\nPFT\tLandClimIPFTs\tXLSX\t344.248\thttps://store.pangaea.de/Publications/Gaillard-Lemdahl_2019/LandClimIPFTs.xlsx\n"""
        self.assertEqual(
            resolve_landclim_tabular_asset_urls(landclim_i_text),
            {
                "landclim_i_land_cover_types.xlsx": "https://store.pangaea.de/Publications/Gaillard-Lemdahl_2019/LandClimILCTs.xlsx",
                "landclim_i_plant_functional_types.xlsx": "https://store.pangaea.de/Publications/Gaillard-Lemdahl_2019/LandClimIPFTs.xlsx",
            },
        )

        landclim_ii_text = """/* DATA DESCRIPTION: */\nContent\tBinary\nREVEALS\tLANDCLIMII.RV.results.JUN2021.zip\nQuality\tGC_quality_by_TW.xlsx\nContributors\tLandClimII_contributors.xlsx\nMetadata\tLandClimII_metadata.xlsx\nTaxa\tTaxa_to_PFT_PPE_and_FSP_values.csv\n"""
        self.assertEqual(
            resolve_landclim_tabular_asset_urls(landclim_ii_text),
            {
                "landclim_ii_reveals_results.zip": "https://download.pangaea.de/dataset/937075/files/LANDCLIMII.RV.results.JUN2021.zip",
                "landclim_ii_grid_cell_quality.xlsx": "https://download.pangaea.de/dataset/937075/files/GC_quality_by_TW.xlsx",
                "landclim_ii_contributors.xlsx": "https://download.pangaea.de/dataset/937075/files/LandClimII_contributors.xlsx",
                "landclim_ii_site_metadata.xlsx": "https://download.pangaea.de/dataset/937075/files/LandClimII_metadata.xlsx",
                "landclim_ii_taxa_pft_ppe_fsp_values.csv": "https://download.pangaea.de/dataset/937075/files/Taxa_to_PFT_PPE_and_FSP_values.csv",
            },
        )

    def test_download_landclim_raw_assets_rejects_empty_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch(
                "bijux_pollenomics.data_downloader.landclim.resolve_landclim_asset_urls",
                return_value={"landclim_i_land_cover_types.xlsx": "https://example.test/lct.xlsx"},
            ), patch(
                "bijux_pollenomics.data_downloader.landclim.fetch_binary",
                return_value=b"",
            ):
                with self.assertRaisesRegex(ValueError, "empty for landclim_i_land_cover_types.xlsx"):
                    download_landclim_raw_assets(Path(tmp))

    def test_build_landclim_raw_asset_summaries_records_source_urls_and_digests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "landclim_i_land_cover_types.xlsx"
            path.write_bytes(b"landclim")

            summaries = build_landclim_raw_asset_summaries(
                {"landclim_i_land_cover_types.xlsx": path},
                {"landclim_i_land_cover_types.xlsx": "https://example.test/lct.xlsx"},
            )

        self.assertEqual(summaries[0]["source_url"], "https://example.test/lct.xlsx")
        self.assertEqual(summaries[0]["size_bytes"], 8)
        self.assertEqual(
            summaries[0]["sha256"],
            "f2865d4bfbd5fa4f19f5336385ef80d21ea03711c748736d3124f804dc1c2e14",
        )
if __name__ == "__main__":
    unittest.main()
