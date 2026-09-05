from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import tempfile
from typing import cast
import unittest

from bijux_pollenomics.collection.sources.landclim.collection import (
    build_landclim_grid_geojson,
    build_landclim_temporal_grid_geojson,
)
from tests.support.geography import NORDIC_TEST_BBOX, SWEDEN_BOUNDARIES
from tests.support.workbooks import write_landclim_ii_zip, write_xlsx

GeoJsonFeature = dict[str, object]
GeoJsonCollection = dict[str, list[GeoJsonFeature] | str]
CountryBoundaries = Mapping[str, Mapping[str, object]]


class LandClimGridProjectionTests(unittest.TestCase):
    def test_landclim_grid_merge_uses_one_feature_for_same_cell(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            raw_paths = {
                "marquer_2017_reveals_taxa_grid_cells.xlsx": tmp_path
                / "marquer_2017_reveals_taxa_grid_cells.xlsx",
                "landclim_i_land_cover_types.xlsx": tmp_path
                / "landclim_i_land_cover_types.xlsx",
                "landclim_i_plant_functional_types.xlsx": tmp_path
                / "landclim_i_plant_functional_types.xlsx",
                "landclim_ii_grid_cell_quality.xlsx": tmp_path
                / "landclim_ii_grid_cell_quality.xlsx",
                "landclim_ii_reveals_results.zip": tmp_path
                / "landclim_ii_reveals_results.zip",
            }
            write_xlsx(
                raw_paths["marquer_2017_reveals_taxa_grid_cells.xlsx"],
                {
                    "Metadata": [
                        ["", "Site", "Source", "Lat.", "Long."],
                        ["GC-1", "Lake M", "EPD", "59.30.00N", "17.30.00E"],
                    ],
                    "Code time windows": [
                        ["Time window", "Code"],
                        ["0-100", "1"],
                    ],
                    "REVEALS 36GCs": [
                        ["", "Picea"],
                        ["GC1-1", "0.20"],
                    ],
                    "SE_REVEALS 36GCs": [
                        ["", "Picea"],
                        ["GC1-1", "0.02"],
                    ],
                },
            )
            write_xlsx(
                raw_paths["landclim_i_land_cover_types.xlsx"],
                {
                    "0-100BPmeanLC": [
                        ["Country", "", "Grid cell", "", "Open land"],
                        ["", "", "", "", ""],
                        ["SWE", "", "17°E 60°N", "", "0.25"],
                    ],
                    "0-100BPSE": [
                        ["Country", "", "Grid cell", "", "Open land"],
                        ["", "", "", "", ""],
                        ["SWE", "", "17°E 60°N", "", "0.03"],
                    ],
                },
            )
            write_xlsx(
                raw_paths["landclim_i_plant_functional_types.xlsx"],
                {
                    "0-100BPmeanLC": [
                        ["Country", "", "Grid cell", "", "PFT"],
                        ["", "", "", "", ""],
                        ["SWE", "", "17°E 60°N", "", "0.10"],
                    ],
                    "0-100BPSE": [
                        ["Country", "", "Grid cell", "", "PFT"],
                        ["", "", "", "", ""],
                        ["SWE", "", "17°E 60°N", "", "0.01"],
                    ],
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

            geojson = build_landclim_grid_geojson(
                raw_paths,
                NORDIC_TEST_BBOX,
                cast(CountryBoundaries, SWEDEN_BOUNDARIES),
            )
            geojson_features = cast(
                list[GeoJsonFeature], cast(GeoJsonCollection, geojson)["features"]
            )

            self.assertEqual(len(geojson_features), 1)
            properties = cast(dict[str, object], geojson_features[0]["properties"])
            self.assertNotIn("_dataset_labels", geojson_features[0])
            popup_rows = cast(list[dict[str, object]], properties["popup_rows"])
            popup = {row["label"]: row["value"] for row in popup_rows}
            dataset_text = cast(str, popup["Datasets"])
            self.assertIn("LandClim I land-cover types", dataset_text)
            self.assertIn("LandClim I plant functional types", dataset_text)
            self.assertIn("LandClim II REVEALS grids", dataset_text)
            self.assertEqual(popup["LandClim II quality"], "high")
            self.assertEqual(properties["time_start_bp"], 0)
            self.assertEqual(properties["time_end_bp"], 100)
            self.assertEqual(properties["time_mean_bp"], 50)
            self.assertEqual(properties["time_label"], "0-100 BP")

            temporal_geojson = build_landclim_temporal_grid_geojson(
                raw_paths,
                NORDIC_TEST_BBOX,
                cast(CountryBoundaries, SWEDEN_BOUNDARIES),
            )
            temporal_features = cast(
                list[GeoJsonFeature],
                cast(GeoJsonCollection, temporal_geojson)["features"],
            )
            self.assertEqual(len(temporal_features), 3)
            temporal_properties = [
                cast(dict[str, object], feature["properties"])
                for feature in temporal_features
            ]
            self.assertEqual(
                {properties["dataset_id"] for properties in temporal_properties},
                {"900966", "897303", "937075"},
            )
            self.assertTrue(
                all(
                    properties["time_start_bp"] == 0
                    and properties["time_end_bp"] == 100
                    for properties in temporal_properties
                )
            )
            landclim_ii = next(
                properties
                for properties in temporal_properties
                if properties["dataset_id"] == "937075"
            )
            self.assertEqual(
                cast(dict[str, float], landclim_ii["reconstruction_values"])["PICEA"],
                0.12,
            )
            self.assertEqual(
                cast(dict[str, float], landclim_ii["standard_errors"])["PICEA"],
                0.01,
            )
            self.assertEqual(
                cast(dict[str, object], landclim_ii["temporal_semantics"])[
                    "comparability_posture"
                ],
                "numeric_interval_with_caveat",
            )
            self.assertEqual(
                cast(dict[str, object], landclim_ii["temporal_semantics"])[
                    "evidence_class"
                ],
                "modeled_vegetation_time_window",
            )
            self.assertNotEqual(landclim_ii["category"], "Pollen observation")
            marquer = next(
                properties
                for properties in temporal_properties
                if properties["dataset_id"] == "900966"
            )
            self.assertEqual(
                cast(dict[str, float], marquer["reconstruction_values"])["Picea"],
                0.2,
            )
            self.assertEqual(
                cast(dict[str, float], marquer["standard_errors"])["Picea"], 0.02
            )
            self.assertEqual(
                marquer["bibliography_reference_keys"],
                ["marquer-et-al-2017", "sugita-2007-reveals"],
            )


if __name__ == "__main__":
    unittest.main()
